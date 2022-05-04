#!/bin/sh

# FireDM
#
#    multi-connections internet download manager, based on "pyCuRL/curl", and "youtube_dl""
#
#    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
#    :license: GNU LGPLv3, see LICENSE for more details.
#
#    Module description:
#         build AppImage from scratch, will use latest FireDM version on pypi
#         using appimage-builder https://appimage-builder.readthedocs.io/en/latest/examples/pyqt.html example
#         Requirements
#          - modern Debian/Ubuntu system
#          - python3 and pip
#          - appimage-builder
#          - apt-get

# get FireDM version
echo Please provide FireDM version number e.g. 2021.2.15
read version

# install required build tools:
sudo apt install -y python3-pip python3-setuptools patchelf desktop-file-utils libgdk-pixbuf2.0-dev fakeroot strace

# Install appimagetool AppImage
sudo wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage -O /usr/local/bin/appimagetool
sudo chmod +x /usr/local/bin/appimagetool

# Installing appimage-builder
sudo pip3 install appimage-builder

# Remove any previous build
rm -rf AppDir  | true

# create desktop entry file
cat <<EOF > firedm.desktop
[Desktop Entry]
Version=1.0
Name=FireDM
GenericName=FireDM
Comment=FireDM Download Manager
Icon=firedm
Exec=python3 -m firedm
Terminal=false
Type=Application
Categories=Network;
Keywords=Internet;download
EOF

# create yaml file, note: you should edit version number
cat <<EOF > AppImageBuilder.yml
version: 1

AppDir:
  app_info:
    exec: usr/bin/python3
    exec_args: -m firedm
    icon: firedm
    id: firedm
    name: FireDM
    version: $version
  apt:
    arch: amd64
    exclude: []
    include:
    - python3
    - python3-pkg-resources
    - libcurl4-openssl-dev
    - libssl-dev
    - python3-pil
    - python3-pil.imagetk
    - python3-tk
    - fonts-symbola
    - fonts-linuxlibertine
    - fonts-inconsolata
    - fonts-emojione
    - python3-pip
    - python3-setuptools
    - python3-pycurl
    sources:
    - key_url: http://keyserver.ubuntu.com/pks/lookup?op=get&search=0x3b4fe6acc0b21f32
      sourceline: deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ bionic main restricted
        universe multiverse
  path: ./AppDir
  runtime:
    env:
      PATH: ${APPDIR}/usr/bin:${PATH}
      PYTHONHOME: ${APPDIR}/usr
      PYTHONPATH: ${APPDIR}/usr/lib/python3.6/site-packages
      SSL_CERT_FILE: ${APPDIR}/usr/lib/python3.6/site-packages/certifi/cacert.pem
      TCL_LIBRARY: ${APPDIR}/usr/share/tcltk/tcl8.6
      TKPATH: ${TK_LIBRARY}
      TK_LIBRARY: ${APPDIR}/usr/share/tcltk/tk8.6
AppImage:
  arch: x86_64
  sign-key: None
  update-information: None

EOF

# copy icon
mkdir -p "./AppDir/usr/share/icons/hicolor/48x48/apps/" && cp ../../icons/48x48.png "./AppDir/usr/share/icons/hicolor/48x48/apps/firedm.png"

# Install application dependencies
python3 -m pip install --upgrade pip
python3 -m pip install --ignore-installed --prefix=/usr --root=./AppDir -r firedm

appimage-builder --skip-test
