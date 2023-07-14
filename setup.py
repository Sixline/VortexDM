"""
    Vortex Download Manager (VortexDM)

    A multi-connection internet download manager, based on "PycURL" and "youtube_dl". Original project, FireDM, by Mahmoud Elshahat.
    :copyright: (c) 2023 by Sixline
    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU GPLv3, see LICENSE.md for more details.
"""

import os
import setuptools

# get current directory
path = os.path.realpath(os.path.abspath(__file__))
current_directory = os.path.dirname(path)

# get version
version = {}
with open(f"{current_directory}/vortexdm/version.py") as f:
    exec(f.read(), version)  # then we can use it as: version['__version__']

# get long description from readme
with open(f"{current_directory}/README.md", "r") as fh:
    long_description = fh.read()

try:
    with open(f"{current_directory}/requirements.txt", "r") as fh:
        requirements = fh.readlines()
except:
    requirements = ['plyer', 'certifi', 'youtube_dl', 'yt_dlp', 'pycurl', 'pillow >= 6.0.0', 'pystray',
                    'awesometkinter >= 2021.3.19']

setuptools.setup(
    name="vortexdm",
    version=version['__version__'],
    scripts=[],  # ['VortexDM.py'], no need since added an entry_points
    author="Mahmoud Elshahat",
    maintainer="Sixline",
    description="Vortex Download Manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Sixline/VortexDM ",
    packages=setuptools.find_packages(),
    keywords="vortexdm vdm firedm internet download manager youtube hls pycurl curl youtube-dl tkinter",
    project_urls={
        'Source': 'https://github.com/Sixline/VortexDM',
        'Tracker': 'https://github.com/Sixline/VortexDM/issues',
        'Releases': 'https://github.com/Sixline/VortexDM/releases',
    },
    install_requires=requirements,
    entry_points={
        # our executable: "exe file on windows for example"
        'console_scripts': [
            'vortexdm = vortexdm.VortexDM:main',
        ]},
    classifiers=[
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
