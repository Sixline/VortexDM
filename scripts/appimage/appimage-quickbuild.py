#!/usr/bin/env python3
"""
    FireDM

    multi-connections internet download manager, based on "pyCuRL/curl", and "youtube_dl""

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        build an executable (exe) for windows using existing template or download a template from github
        you should execute this module from command line using: "python buildexe.py"
        this module can be executed from any operating system e.g. linux, windows, etc..
        to create exe version from scratch use cx_setup.py on windows os
"""

import os
import subprocess
import sys
import json
import shutil
import yaml  # pip install PyYAML

fp = os.path.realpath(os.path.abspath(__file__))
current_folder = os.path.dirname(fp)

APP_NAME = 'FireDM'

build_folder = current_folder
extracted_squashfs = os.path.join(build_folder, 'squashfs-root')
AppDir = os.path.join(build_folder, 'AppDir')
project_folder = os.path.dirname(os.path.dirname(current_folder))

sys.path.insert(0,  project_folder)  # for imports to work
from firedm.utils import simpledownload, get_pkg_version, delete_folder


# get application version ----------------------------------------------------------------------------------------------
version = get_pkg_version(os.path.join(project_folder, 'firedm'))

# check for app folder existence, otherwise download latest version from github
if not os.path.isdir(AppDir):
    print('downloading ', APP_NAME)
    data = simpledownload('https://api.github.com/repos/firedm/firedm/releases/latest').decode("utf-8")
    # "browser_download_url": "https://github.com/firedm/FireDM/releases/download/2021.2.9/FireDM-2021.2.9-x86_64.AppImage"
    data = json.loads(data)
    assets = data['assets']

    url = None
    for asset in assets:
        filename = asset.get('name', '')
        if filename.lower().endswith('appimage'):  # e.g. FireDM-2021.2.9-x86_64.AppImage
            url = asset.get('browser_download_url')
            break

    if url:
        # download file
        z_fp = os.path.join(build_folder, filename)
        if not os.path.isfile(z_fp):
            simpledownload(url, z_fp)

        # extract and rename
        print('extracting, please wait ...')
        cmd = f'cd "{build_folder}"'  # make executable
        cmd += f' && chmod +x "{z_fp}"'  # make executable
        cmd += f' && "{z_fp}" --appimage-extract'  # extract appimage as "squashfs-root"
        cmd += f' &&  rm "{z_fp}"'
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL)

        cmd = f'mv "{extracted_squashfs}" "{AppDir}"'  # rename
        subprocess.run(cmd, shell=True)

    else:
        print('Failed to download latest version, download manually '
              'from https://github.com/firedm/FireDM/releases/latest')
        exit(1)

site_pkgs_folder = f'{AppDir}/usr/lib/python3.6/site-packages'

# delete firedm in site packages ---------------------------------------------------------------------------------------
print('delete old firedm files in sitepackages')
target_folder = os.path.join(site_pkgs_folder, 'firedm')
delete_folder(target_folder, verbose=True)

# copy firedm ----------------------------------------------------------------------------------------------------------
print('copy firedm')
src_folder = os.path.join(project_folder, 'firedm')
target_folder = os.path.join(AppDir, 'usr/src/firedm')
shutil.copytree(src_folder, target_folder,  dirs_exist_ok=True)

# update pkgs ----------------------------------------------------------------------------------------------------------
print('update packages')

# update other packages
pkgs = ['youtube_dl', 'yt_dlp', 'awesometkinter', 'certifi', 'python_bidi', 'distro']
cmd = f'{sys.executable} -m pip install {" ".join(pkgs)} --upgrade --no-compile   --no-deps --target "{site_pkgs_folder}" '
subprocess.run(cmd, shell=True)

# copy icon ------------------------------------------------------------------------------------------------------------
print('copy application icon')
icon_src = os.path.join(project_folder, 'icons', '48x48.png')
icon_target = f'{AppDir}/usr/share/icons/hicolor/48x48/apps/firedm.png'
os.makedirs(os.path.dirname(icon_target), exist_ok=True)
for fp in [icon_target, f'{AppDir}/firedm.png']:
    shutil.copyfile(icon_src, fp)

# create .desktop file -------------------------------------------------------------------------------------------------
print('creating firedm.desktop file')

contents = f"""[Desktop Entry]
X-AppImage-Arch=x86_64
X-AppImage-Version={version}
X-AppImage-Name=FireDM
Name=FireDM
GenericName=FireDM
Comment=FireDM Download Manager
Exec=/usr/bin/python3 -m firedm
Icon=firedm
Terminal=false
Type=Application
Categories=Network;
Keywords=Internet;download
"""
desktop_fp1 = f'{AppDir}/firedm.desktop'
desktop_fp2 = f'{AppDir}/usr/share/applications/firedm.desktop'
with open(desktop_fp1, 'w') as f1, open(desktop_fp2, 'w') as f2:
    f1.write(contents)
    f2.write(contents)

# copy run.py ----------------------------------------------------------------------------------------------------------
print('copy run.py')
src = 'run.py'
dst = f'{AppDir}/run.py'
shutil.copyfile(src, dst)

# edit .env file -------------------------------------------------------------------------------------------------------
print('edit ".env" file')

env_fp = os.path.join(AppDir, '.env')
with open(env_fp) as f:
    data = f.readlines()

for i, line in enumerate(data):
    if line.startswith('EXEC_PATH'):
        data[i] = 'EXEC_PATH=$APPDIR/usr/bin/python3\n'
    elif line.startswith('EXEC_ARGS'):
        # Use '$@' to forward CLI parameters
        data[i] = 'EXEC_ARGS=$APPDIR/run.py $@\n'

with open(env_fp, 'w') as f:
    f.writelines(data)

# Start FireDM with "--imports-only" flag to build pyc files for new packages  -----------------------------------------
print('starting FireDM')
subprocess.run(f'{AppDir}/AppRun --imports-only', shell=True)

# build AppImage from current AppDir folder and using appimagetool -----------------------------------------------------
print('build AppImage file from AppDir')
url = 'https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage'
appimagetool = os.path.join(current_folder, 'appimagetool-x86_64.AppImage')
simpledownload(url, fp=appimagetool)
subprocess.run(f'chmod +x {appimagetool}', shell=True)

filename = f'{APP_NAME}-{version}-x86_64.AppImage'
subprocess.run(f'{appimagetool} {AppDir} {filename}', shell=True)
print('Done')

