"""
    FireDM

    multi-connections internet download manager, based on "LibCurl", and "youtube_dl".

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    File description:
        This is the main script in AppImage release, responsible for sourcing firedm and other packages from 2 locations
        and load the newer version of each package.
        should be copied to AppDir
"""

import os
from packaging.version import parse
from importlib.util import find_spec
import sys
import shutil
import re


def get_pkg_path(pkg_name):
    """get package installation path without importing"""
    spec = find_spec(pkg_name)
    if spec:
        pkg_path = os.path.dirname(spec.origin)
    else:
        pkg_path = None
    return pkg_path


def get_pkg_version(pkg):
    """parse version number for a package
    using .dist-info folder or version.py/version.pyc files

    Args:
        pkg(str): name or path of the package

    Returns:
        (str): version number or empty string
    """

    if os.path.isdir(pkg):
        pkg_path = pkg
    else:
        pkg_name = os.path.basename(pkg)
        pkg_path = get_pkg_path(pkg_name)

    if not pkg_path:
        return ''

    version = ''

    # read version.py file
    try:
        version_module = {}
        fp = os.path.join(pkg_path, 'version.py')
        with open(fp) as f:
            txt = f.read()
            exec(txt, version_module)  # then we can use it as: version_module['__version__']
            version = version_module.get('__version__')
            if not version:
                match = re.search(r'_*version_*=[\'\"](.*?)[\'\"]', txt.replace(' ', ''), re.IGNORECASE)
                version = match.groups()[0]
    except:
        pass

    if not version:
        # read version.pyc file, will be limited to specific versions format, e.g. 2.3.4, or 2021.8.30
        try:
            fp = os.path.join(pkg_path, 'version.pyc')
            with open(fp, 'rb') as f:
                text = f.read()
                match = re.search(rb'\d+\.\d+\.\d+', text)
                version = match.group().decode('utf-8')
        except:
            pass

    if not version:
        # parse .dist-info folder e.g: youtube_dl-2021.5.16.dist-info or FireDM-2021.2.9.dist-info
        try:
            parent_folder = os.path.dirname(pkg_path)
            pkg_name = os.path.basename(pkg_path)

            for folder_name in os.listdir(parent_folder):
                match = re.match(pkg_name + r'-(.*?)\.dist-info', folder_name, re.IGNORECASE)
                if match:
                    version = match.groups()[0]
                    break
        except:
            pass

    return version


home_folder = os.path.expanduser('~')
fp = os.path.realpath(__file__)
AppDir = os.path.dirname(fp)
sett_folder = f'{home_folder}/.config/FireDM'
site_pkgs = os.path.join(AppDir, 'usr/lib/python3.6/site-packages')
appimage_update_folder = os.path.join(sett_folder, 'appimage-update-folder')
firedm_src = os.path.join(AppDir, 'usr/src')

os.makedirs(appimage_update_folder, exist_ok=True)
sys.path.insert(0, firedm_src)

pkgs = []
for d in os.listdir(appimage_update_folder):
    folders = os.listdir(os.path.join(appimage_update_folder, d))
    if folders:
        pkg_full_path = os.path.join(appimage_update_folder, d, folders[0])
        pkgs.append(pkg_full_path)

# ignore old packages
for pkg in pkgs[:]:
    pkg_name = os.path.basename(pkg)
    pkg_version = get_pkg_version(pkg)
    if pkg_name == 'firedm':
        src_folder = firedm_src
    else:
        src_folder = site_pkgs
    orig_pkg_version = get_pkg_version(os.path.join(src_folder, pkg_name))

    # print(pkg, 'orig_pkg_version:', orig_pkg_version, ' - pkg_version:', pkg_version)

    origver = parse(orig_pkg_version)
    ver = parse(pkg_version)

    if origver > ver:
        pkgs.remove(pkg)

if pkgs:
    print('sourcing updated packages:')
    # add pkgs to sys.path
    for pkg in pkgs:
        sys.path.insert(0, os.path.dirname(pkg))
        print(pkg)

from firedm import FireDM, config

config.isappimage = True
config.appimage_update_folder = appimage_update_folder
config.ffmpeg_actual_path = os.path.join(AppDir, 'usr/bin/ffmpeg')

# fix second argument is an empty string
if len(sys.argv) > 1 and not sys.argv[1]:
    sys.argv.pop(1)

# launch application
FireDM.main()
