"""
    Vortex Download Manager (VortexDM)

    A multi-connection internet download manager, based on "PycURL" and "youtube_dl". Original project, FireDM, by Mahmoud Elshahat.
    :copyright: (c) 2022 by Sixline
    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU GPLv3, see LICENSE.md for more details.

    Module description:
        build an executable (exe) for windows using cx_freeze
        you should execute this module from command line using: "python exe-fullbuild.py build" on windows only.
        
        *Can be used for 32-bit Windows but you will need to find or build a 32-bit version of ffmpeg. BtbN doesn't auto-build a 32-bit version.*
"""

import os
import sys
import shutil
import subprocess

from cx_Freeze import setup, Executable

APP_NAME = 'VortexDM'

# to run setup.py directly
if len(sys.argv) == 1:
    sys.argv.append("build")

# get current directory
fp = os.path.realpath(os.path.abspath(__file__))
current_folder = os.path.dirname(fp)

project_folder = os.path.dirname(os.path.dirname(current_folder))
build_folder = current_folder
app_folder = os.path.join(build_folder, APP_NAME)
icon_path = os.path.join(project_folder, 'icons', 'vortexdm.ico') # best use size 48, and must be an "ico" format
version_fp = os.path.join(project_folder, 'vortexdm', 'version.py')
requirements_fp = os.path.join(project_folder, 'requirements.txt')
main_script_path = os.path.join(project_folder, 'vortexdm.py')

sys.path.insert(0,  project_folder)  # for imports to work
from vortexdm.utils import simpledownload, delete_folder, delete_file, create_folder, zip_extract

# create build folder
create_folder(build_folder)

# get version
version_module = {}
with open(version_fp) as f:
    exec(f.read(), version_module)  # then we can use it as: version_module['__version__']
    version = version_module['__version__']

# get required packages
with open(requirements_fp) as f:
    packages = [line.strip().split(' ')[0] for line in f.readlines() if line.strip()] + ['vortexdm']

# clean names
packages = [pkg.replace(';', '') for pkg in packages]

# filter some packages
for pkg in ['distro', 'Pillow']:
    if pkg in packages:
        packages.remove(pkg)

# add keyring to packages
packages.append('keyring')
   
print(packages)

includes = []
include_files = []
excludes = ['numpy', 'test', 'setuptools', 'unittest', 'PySide2']

cmd_target_name = f'{APP_NAME.lower()}.exe'
gui_target_name = f'{APP_NAME}-GUI.exe'

executables = [
    Executable(main_script_path, base='Console', target_name=cmd_target_name),
    Executable(main_script_path, base='Win32GUI', target_name=gui_target_name, icon=icon_path),
]

setup(

    version=version,
    description=f"{APP_NAME}",
    author="Sixline - Original project, FireDM, by Mahmoud Elshahat",
    name=APP_NAME,

    options={"build_exe": {
        "includes": includes,
        'include_files': include_files,
        "excludes": excludes,
        "packages": packages,
        'build_exe': app_folder,
        'include_msvcr': True,
    }
    },

    executables=executables
)

# Post processing

# ffmpeg
ffmpeg_zip_path = os.path.join(current_folder, 'ffmpeg-master-latest-win64-gpl.zip')
ffmpeg_extract_path = os.path.join(current_folder, 'ffmpeg-master-latest-win64-gpl')
ffmpeg_path = os.path.join(ffmpeg_extract_path, 'ffmpeg-master-latest-win64-gpl', 'bin', 'ffmpeg.exe')
if not os.path.isfile(os.path.join(app_folder, 'ffmpeg.exe')):
    if not os.path.isfile(ffmpeg_zip_path):
        # Download 64-bit BtbN auto-build. BtbN doesn't auto-build a 32-bit version.
        simpledownload('https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip', fp=ffmpeg_zip_path)
        print('Download done! Extracting and moving ffmpeg.exe...')
        zip_extract(z_fp=ffmpeg_zip_path, extract_folder=ffmpeg_extract_path)
    shutil.copy(ffmpeg_path, os.path.join(app_folder, 'ffmpeg.exe'))
    print('Cleaning up...')
    delete_folder(ffmpeg_extract_path, verbose=True)
    delete_file(ffmpeg_zip_path, verbose=True)


# write resource fields for exe files
# install pe-tools  https://github.com/avast/pe_tools
cmd = f'"{sys.executable}" -m pip install pe_tools'
subprocess.run(cmd, shell=True)

for fname in (cmd_target_name, gui_target_name):
    fp = os.path.join(app_folder, fname)
    info = {
        'Comments': 'https://github.com/Sixline/VortexDM',
        'CompanyName': 'Vortex Download Manager',
        'FileDescription': 'Vortex Download Manager',
        'FileVersion': version,
        'InternalName': fname,
        'LegalCopyright': 'copyright: (c) 2022 by Sixline - Original project, FireDM, by Mahmoud Elshahat',
        'LegalTrademarks': 'Vortex Download Manager',
        'OriginalFilename': fname,
        'ProductName': 'Vortex Download Manager',
        'ProductVersion': version,
        'legalcopyright': 'copyright: (c) 2022 by Sixline - Original project, FireDM, by Mahmoud Elshahat'
    }

    param = ' -V '.join([f'"{k}={v}"' for k, v in info.items()])
    cmd = f'"{sys.executable}" -m pe_tools.peresed -V {param} "{fp}"'
    subprocess.run(cmd, shell=True)

# Check if 32 or 64 bit for zip file name
if sys.maxsize > 2**32:
   win_arch = 64
else:
   win_arch = 32

# create zip file
output_filename = f'{APP_NAME}-{version}-win{win_arch}'
print(f'Preparing zip file: {output_filename}.zip')
fname = shutil.make_archive(output_filename, 'zip', root_dir=build_folder, base_dir='VortexDM')
delete_folder(app_folder, verbose=True) 

print(f'Done! {output_filename}.zip')
