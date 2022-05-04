#!/usr/bin/env python3
"""
    FireDM

    multi-connections internet download manager, based on "pyCuRL/curl", and "youtube_dl""

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        build an executable (exe) for windows using existing template or download a template from github
        this module can be executed from any operating system e.g. linux, windows, etc..
        to create exe version from scratch use exe_fullbuild.py on windows os
"""

import os
import re
import sys
import json
import shutil
import subprocess

fp = os.path.realpath(os.path.abspath(__file__))
current_folder = os.path.dirname(fp)
project_folder = os.path.dirname(os.path.dirname(current_folder))
sys.path.insert(0,  project_folder)  # for imports to work

from firedm.utils import simpledownload, zip_extract, get_pkg_version


APP_NAME = 'FireDM'

build_folder = current_folder
app_folder = os.path.join(build_folder, APP_NAME)

# check for app folder existence, otherwise download latest version from github
if not os.path.isdir(app_folder):
    print('downloading ', APP_NAME)
    data = simpledownload('https://api.github.com/repos/firedm/firedm/releases/latest').decode("utf-8")
    # example: "browser_download_url": "https://github.com/firedm/FireDM/releases/download/2021.2.9/FireDM_2021.2.9.zip"
    data = json.loads(data)
    assets = data['assets']

    url = None
    for asset in assets:
        filename = asset.get('name', '')
        if filename.lower().endswith('zip'):  # e.g. FireDM_2021.2.9.zip
            url = asset.get('browser_download_url')
            break

    if url:
        # download file
        z_fp = os.path.join(build_folder, filename)
        if not os.path.isfile(z_fp):
            simpledownload(url, z_fp)

        # unzip
        print('extracting, please wait ...')
        zip_extract(z_fp, build_folder)
        os.remove(z_fp)

    else:
        print('Failed to download latest version, download manually '
              'from https://github.com/firedm/FireDM/releases/latest')
        exit(1)

lib_folder = os.path.join(app_folder, 'lib')

# update packages,  ----------------------------------------------------------------------------------------------------
print('update packages')

# update firedm pkg
src_folder = os.path.join(project_folder, 'firedm')
target_folder = os.path.join(lib_folder, 'firedm')
shutil.rmtree(target_folder, ignore_errors=True)
shutil.copytree(src_folder, target_folder,  dirs_exist_ok=True)

# update other packages
pkgs = ['youtube_dl', 'yt_dlp', 'awesometkinter', 'certifi', 'python_bidi']
cmd = f'{sys.executable} -m pip install {" ".join(pkgs)} --upgrade --no-compile   --no-deps --target "{lib_folder}" '
subprocess.run(cmd, shell=True)


# get application version ----------------------------------------------------------------------------------------------
version = get_pkg_version(os.path.join(project_folder, 'firedm'))

# edit info for exe files ----------------------------------------------------------------------------------------------
cmd = f'{sys.executable} -m pip install pe_tools'
subprocess.run(cmd, shell=True)

for fname in ('firedm.exe', 'FireDM-GUI.exe'):
    fp = os.path.join(app_folder, fname)
    info = {
        'Comments': 'https://github.com/firedm/FireDM',
        'CompanyName': 'FireDM',
        'FileDescription': 'FireDM download manager',
        'FileVersion': version,
        'InternalName': fname,
        'LegalCopyright': '2019-2021 by Mahmoud Elshahat',
        'LegalTrademarks': 'FireDM',
        'OriginalFilename': fname,
        'ProductName': 'FireDM',
        'ProductVersion': version,
        'legalcopyright': 'copyright(c) 2019-2021 by Mahmoud Elshahat'
    }

    param = ' -V '.join([f'"{k}={v}"' for k, v in info.items()])
    cmd = f'peresed -V {param} {fp}'
    subprocess.run(cmd, shell=True)
        
# create zip file
output_filename = f'{APP_NAME}_{version}'
print(f'prepare final zip filename: {output_filename}.zip')
fname = shutil.make_archive(output_filename, 'zip', base_dir=APP_NAME)

print('Done ...........')
