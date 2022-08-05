#!/usr/bin/env python
"""
    Vortex Download Manager (VDM)

    Multi-connection internet download manager, based on "LibCurl", and "youtube_dl". Original project, FireDM, by Mahmoud Elshahat.
    :copyright: (c) 2022 by Sixline
    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU GPLv3, see LICENSE.md for more details.
"""

# The purpose of this module is checking and auto installing dependencies
import sys
import subprocess
import importlib.util

# add the required packages here without any version numbers
requirements = ['plyer', 'certifi', 'youtube_dl', 'yt_dlp', 'pycurl', 'PIL', 'pystray', 'awesometkinter']


def is_venv():
    """check if running inside virtual environment
    there is no 100% working method to tell, but we can check for both real_prefix and base_prefix"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return True
    else:
        return False


def install_missing_pkgs():

    # list of dependency
    missing_pkgs = [pkg for pkg in requirements if importlib.util.find_spec(pkg) is None]

    if missing_pkgs:
        print('required pkgs: ', requirements)
        print('missing pkgs: ', missing_pkgs)

        for pkg in missing_pkgs:
            # because 'pillow' is installed under different name 'PIL' will use pillow with pip github issue #60
            if pkg == 'PIL':
                pkg = 'pillow'

            # using "--user" flag is safer also avoid the need for admin privilege , but it fails inside venv, where pip
            # will install packages normally to user folder but venv still can't see those packages

            if is_venv():
                cmd = [sys.executable, "-m", "pip", "install", '--upgrade', pkg]  # no --user flag
            else:
                cmd = [sys.executable, "-m", "pip", "install", '--user', '--upgrade', pkg]

            print('running command:', ' '.join(cmd))
            subprocess.run(cmd, shell=False)




