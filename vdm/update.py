"""
    Vortex Download Manager (VDM)

    Multi-connection internet download manager, based on "LibCurl", and "youtube_dl". Original project, FireDM, by Mahmoud Elshahat.
    :copyright: (c) 2022 by Sixline
    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU GPLv3, see LICENSE.md for more details.
"""

# todo: change docstring to google format and clean unused code
# check and update application

import hashlib
import json
import py_compile
import re
import shutil
import sys
import zipfile, tarfile
import queue
import time
from threading import Thread
from distutils.dir_util import copy_tree
import os
import webbrowser
from packaging.version import parse as parse_version

from . import config
from .utils import log, download, run_command, delete_folder, delete_file


def open_update_link():
    """open browser window with latest release url on github for frozen application or source code url"""
    url = config.LATEST_RELEASE_URL if config.FROZEN else config.APP_URL
    webbrowser.open_new(url)


def check_for_new_version():
    """
    Check for new VDM version

    Return:
        changelog text or None

    """

    latest_version = '0'
    changelog = None

    try:
        if config.FROZEN:
            # use github API to get latest version
            url = 'https://api.github.com/repos/Sixline/VDM/releases/latest'
            contents = download(url, verbose=False)

            if contents:
                j = json.loads(contents)
                latest_version = j.get('tag_name', '0')

        else:
            # check pypi version
            latest_version, _ = get_pkg_latest_version('vortexdm')

        if parse_version(latest_version) > parse_version(config.APP_VERSION):
            log('Found new version:', str(latest_version))

            # download change log file
            url = 'https://github.com/Sixline/VDM/raw/master/ChangeLog.txt'
            changelog = download(url, verbose=False)
    except Exception as e:
        log('check_for_new_version()> error:', e)

    return changelog


def get_pkg_latest_version(pkg, fetch_url=True):
    """get latest stable package release version on https://pypi.org/
    reference: https://warehouse.pypa.io/api-reference/
    Available strategies:
    1 - rss feed (faster and lighter), send xml info with latest release version but no info on "wheel file" url,
        pattern example: https://pypi.org/rss/project/youtube-dl/releases.xml
        example data:
                    <item>
                    <title>2020.12.14</title>
                    <link>https://pypi.org/project/youtube-dl/2020.12.14/</link>
                    <description>YouTube video downloader</description>
                    <author>dstftw@gmail.com</author>
                    <pubDate>Sun, 13 Dec 2020 17:59:21 GMT</pubDate>
                    </item>

    2- json, (slower and bigger file), send all info for the package
        url pattern: f'https://pypi.org/pypi/{pkg}/json' e.g.    https://pypi.org/pypi/vdm/json
        received json will be a dict with:
        keys = 'info', 'last_serial', 'releases', 'urls'
        releases = {'release_version': [{dict for wheel file}, {dict for tar file}], ...}
        dict for wheel file = {"filename":"yt_dlp-2020.10.24.post6-py2.py3-none-any.whl", 'url': 'file url'}
        dict for tar file = {"filename":"yt_dlp-2020.10.24.post6.tar.gz", 'url': 'file url'}


    Args:
        pkg (str): package name
        fetch_url (bool): if true, will use json API to get download url, else it will use rss feed to get version only

    Return:
        2-tuple(str, str): latest_version, and download url (for wheel file) if available
    """

    # download json info
    url = f'https://pypi.org/pypi/{pkg}/json' if fetch_url else f'https://pypi.org/rss/project/{pkg}/releases.xml'

    # get BytesIO object
    log(f'check for {pkg} latest version on pypi.org...')
    contents = download(url, verbose=False)
    latest_version = None
    url = None

    if contents:
        # rss feed
        if not fetch_url:
            match = re.findall(r'<title>(\d+.\d+.\d+.*)</title>', contents)
            latest_version = max([parse_version(release) for release in match]) if match else None

            if latest_version:
                latest_version = str(latest_version)
        # json
        else:
            j = json.loads(contents)

            releases = j.get('releases', {})
            if releases:

                latest_version = max([parse_version(release) for release in releases.keys()]) or None
                if latest_version:
                    latest_version = str(latest_version)

                    # get latest release url
                    release_info = releases[latest_version]
                    for _dict in release_info:
                        file_name = _dict['filename']
                        url = None
                        if file_name.endswith('.whl'):
                            url = _dict['url']
                            break

        return latest_version, url

    else:
        log(f"get_pkg_latest_version() --> couldn't check for {pkg}, url is unreachable")
        return None, None


def get_target_folder(pkg):
    # determine target folder
    current_directory = config.current_directory
    if config.FROZEN:  # windows cx_freeze
        # current directory is the directory of exe file
        target_folder = os.path.join(config.current_directory, 'lib')
    elif config.isappimage:
        # keep every package in isolated folder, to add individual package path to sys.path if it has newer version
        # than same pkg in AppImage's site-packages folder
        target_folder = os.path.join(config.sett_folder, config.appimage_update_folder, f'updated-{pkg}')
    else:
        target_folder = None

    return target_folder


def update_pkg(pkg, url):
    """updating a package in frozen application folder
    expect to download and extract a wheel file e.g. "yt_dlp-2020.10.24.post6-py2.py3-none-any.whl", which in fact
    is a zip file

    Args:
        pkg (str): package name
        url (str): download url (for a wheel file)
    """

    log(f'start updating {pkg}')

    target_folder = get_target_folder(pkg)

    # check if the application is frozen, e.g. runs from a windows cx_freeze executable
    # if run from source, we will update system installed package and exit
    if not target_folder:
        cmd = f'"{sys.executable}" -m pip install {pkg} --upgrade'
        error, output = run_command(cmd)
        if not error:
            log(f'successfully updated {pkg}')
        return True

    # paths
    temp_folder = os.path.join(target_folder, f'temp_{pkg}')
    extract_folder = os.path.join(temp_folder, 'extracted')
    z_fn = f'{pkg}.zip'
    z_fp = os.path.join(temp_folder, z_fn)

    target_pkg_folder = os.path.join(target_folder, pkg)
    bkup_folder = os.path.join(target_folder, f'{pkg}_bkup')
    new_pkg_folder = None

    # make temp folder
    log('making temp folder in:', target_folder)
    os.makedirs(temp_folder, exist_ok=True)

    def bkup():
        # backup current package folder
        log(f'delete previous backup and backup current {pkg}:')
        delete_folder(bkup_folder)
        shutil.copytree(target_pkg_folder, bkup_folder)

    def tar_extract():
        with tarfile.open(z_fp, 'r') as tar:
            tar.extractall(path=extract_folder)

    def zip_extract():
        with zipfile.ZipFile(z_fp, 'r') as z:
            z.extractall(path=extract_folder)

    extract = zip_extract

    def overwrite_pkg():
        delete_folder(target_pkg_folder)
        shutil.move(new_pkg_folder, target_pkg_folder)
        log('new package copied to:', target_pkg_folder)

    # start processing -------------------------------------------------------
    log(f'start updating {pkg} please wait ...')

    try:
        # use a thread to show some progress while backup
        t = Thread(target=bkup)
        t.start()
        while t.is_alive():
            log('#', start='', end='')
            time.sleep(0.3)

        log('\n', start='')

        # download from pypi
        log(f'downloading {pkg} raw files')
        data = download(url, fp=z_fp)
        if not data:
            log(f'failed to download {pkg}, abort update')
            return

        # extract tar file
        log(f'extracting {z_fn}')

        # use a thread to show some progress while unzipping
        t = Thread(target=extract)
        t.start()
        while t.is_alive():
            log('#', start='', end='')
            time.sleep(0.3)

        log('\n', start='')
        log(f'{z_fn} extracted to: {temp_folder}')

        # define new pkg folder
        new_pkg_folder = os.path.join(extract_folder, pkg)

        # delete old package and replace it with new one
        log(f'overwrite old {pkg} files')
        overwrite_pkg()

        # clean old files
        log('delete temp folder')
        delete_folder(temp_folder)
        log(f'{pkg} ..... done updating')
        return True
    except Exception as e:
        log(f'update_pkg()> error', e)


def rollback_pkg_update(pkg):
    """rollback last package update

    Args:
        pkg (str): package name
    """

    target_folder = get_target_folder(pkg)

    if not target_folder:
        log(f'rollback {pkg} update is currently working on windows exe and Linux AppImage versions', showpopup=True)
        return

    log(f'rollback last {pkg} update ................................')

    # paths
    target_pkg_folder = os.path.join(target_folder, pkg)
    bkup_folder = os.path.join(target_folder, f'{pkg}_bkup')

    try:
        # find a backup first
        if os.path.isdir(bkup_folder):
            log(f'delete active {pkg} module')
            delete_folder(target_pkg_folder)

            log(f'copy backup {pkg} module')
            shutil.copytree(bkup_folder, target_pkg_folder)

            log(f'Done restoring {pkg} module, please restart Application now', showpopup=True)
        else:
            log(f'No {pkg} backup found')

    except Exception as e:
        log('rollback_pkg_update()> error', e)




