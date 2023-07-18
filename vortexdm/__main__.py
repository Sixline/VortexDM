#!/usr/bin/env python3
"""
    Vortex Download Manager (VortexDM)

    A multi-connection internet download manager, based on "PycURL" and "youtube_dl". Original project, FireDM, by Mahmoud Elshahat.
    :copyright: (c) 2023 by Sixline
    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU GPLv3, see LICENSE.md for more details.
"""
# main module executed when run command
# python -m vortexdm

import sys

if __package__ is None and not hasattr(sys, 'frozen'):
    # direct call of __main__.py
    import os.path
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

from vortexdm import VortexDM

if __name__ == '__main__':
    VortexDM.main()