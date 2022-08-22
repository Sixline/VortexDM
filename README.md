![Logo](https://raw.githubusercontent.com/Sixline/VortexDM/main/icons/vortexdm.png)
Vortex Download Manager (VortexDM) is an open-source Python Internet download manager with a high speed multi-connection engine. It downloads general files and videos. Developed in Python, based on "PycURL" and "youtube_dl".

Original project, FireDM, by Mahmoud Elshahat.

Homepage: https://github.com/Sixline/VortexDM  
PyPI Homepage: https://pypi.org/project/vortexdm

[![GitHub Issues](https://img.shields.io/github/issues-raw/Sixline/VortexDM?color=brightgreen)](https://github.com/Sixline/VortexDM/issues) - [![GitHub Closed Issues](https://img.shields.io/github/issues-closed-raw/Sixline/VortexDM?color=blueviolet)](https://github.com/Sixline/VortexDM/issues?q=is%3Aissue+is%3Aclosed)

**Features**:
* High download speeds based on PycURL
* Multi-connection downloading
* Automatic file segmentation
* Automatic refresh for dead links
* Resume uncompleted downloads
* Support for YouTube and a lot of other stream websites using youtube-dl to fetch info and PycURL to download media
* Download entire videos, playlists, or selected videos
* Download fragmented video streams and encrypted/nonencrypted HLS media streams
* Watch videos while downloading *some videos will have no audio until they finish downloading*
* Download video subtitles
* Write video metadata to downloaded files
* Checking for application updates
* Scheduled downloads
* Re-using existing connections
* Clipboard monitor
* Proxy support (http, https, socks4, and socks5)
* User/pass authentication, referee link, video thumbnail, and subtitles
* Use custom cookie files
* MD5 and SHA256 checksums
* Custom GUI themes
* Set download speed limit
* Shell commands or computer shutdown on download completion
* Control number of the concurrent downloads and maximum connections

# How to use VortexDM:
Running in command line: show help by typing `vortexdm -h`

Running the GUI: Refer to the user guide at https://github.com/Sixline/VortexDM/blob/master/docs/user_guide.md

# Portable VortexDM Versions:
  
Run VortexDM without any installation (recommended) 
 - **Windows Portable Version** ([Download!](https://github.com/Sixline/VortexDM/releases/latest)):  
   Available in .zip format. Built with 64-bit Python 3.10+ and will only work on 64-bit Windows 10+.  
   Unzip and run VortexDM-GUI.exe, no installation required.
   
 - **Linux Portable Version**  
  Removing this section for now as I am not familiar with building AppImages. Will revisit.

## Manually installing VortexDM with pip (Linux Only - Debian/Ubuntu Based Shown):
1- Check python version (minimum version required is 3.7): `python3 --version`

2- Install required packages:
```sh
sudo apt install ffmpeg libcurl4-openssl-dev libssl-dev python3-pip python3-pil python3-pil.imagetk python3-tk python3-dbus gir1.2-appindicator3-0.1
sudo apt install fonts-symbola fonts-linuxlibertine fonts-inconsolata fonts-emojione
```

3- Install Vortex Download Manager using pip:

```sh
python3 -m pip install vortexdm --user --upgrade --no-cache
```

## Running from source code inside a Python virtual environment (Linux Only - Debian/Ubuntu Based Shown):
1- Check python version (minimum version required is 3.7): `python3 --version`

2- Install required packages:
```sh
sudo apt install ffmpeg libcurl4-openssl-dev libssl-dev python3-pip python3-pil python3-pil.imagetk python3-tk python3-dbus gir1.2-appindicator3-0.1
sudo apt install fonts-symbola fonts-linuxlibertine fonts-inconsolata fonts-emojione
```

3- Run below code to clone this repo, create a Python virtual environment, install the requirements, create launch script, and finally run VortexDM

```sh
git clone https://github.com/Sixline/VortexDM
python3 -m venv ./.env
source ./.env/bin/activate
python3 -m pip install -r ./VortexDM/requirements.txt
echo "source ./.env/bin/activate
python3 ./VortexDM/vortexdm.py \$@
" > vortexdm.sh
chmod +x ./vortexdm.sh
./vortexdm.sh
```

> Optionally create .desktop file and add VortexDM to your applications
```sh
VortexDMLSPATH=$(realpath ./vortexdm.sh)
echo "[Desktop Entry]
Name=VortexDM
GenericName=VortexDM
Comment=Vortex Download Manager
Exec=$VortexDMLSPATH
Icon=vortexdm
Terminal=false
Type=Application
Categories=Network;
Keywords=Internet;download
" > VortexDM.desktop
cp ./VortexDM.desktop ~/.local/share/applications/
mkdir -p ~/.local/share/icons/hicolor/48x48/apps/
cp ./VortexDM/icons/vortexdm.png ~/.local/share/icons/hicolor/48x48/apps/vortexdm.png
```

# Known Issues:
- Linux Xserver will raise an error if some fonts are missing, especially emoji fonts - See Dependencies below

- Mac - Tkinter - Can have issues depending on versions. See here: https://www.python.org/download/mac/tcltk

- Systray Icon: Depends on GTK 3+ and AppIndicator3 on Linux. Install these packages if you need systray to run properly.

# Dependencies:
- Python 3.7+: Tested with Python 3.10+ on Windows 10 and Ubuntu Linux
- [Tkinter](https://docs.python.org/3/library/tkinter.html): standard Python interface to the Tcl/Tk GUI toolkit.
- [FFmpeg](https://www.ffmpeg.org/): for merging audio with DASH videos.
- Fonts: (Linux Xserver will raise an error if some fonts are missing, especially emoji fonts. Below are the 
recommended fonts to be installed.

    ```
    ttf-linux-libertine 
    ttf-inconsolata 
    ttf-emojione
    ttf-symbola
    noto-fonts
    ```
- [PycURL](http://pycurl.io/docs/latest/index.html): a Python interface to libcurl, the multiprotocol file transfer library. Used as the download engine.
- [youtube_dl](https://github.com/ytdl-org/youtube-dl): Famous YouTube downloader, limited use for meta information extraction only but videos are downloaded using PycURL.
- [yt_dlp](https://github.com/yt-dlp/yt-dlp): yt-dlp is a youtube-dl fork based on the now inactive youtube-dlc.
- [Certifi](https://github.com/certifi/python-certifi): required by PycURL for validating the trustworthiness of SSL certificates.
- [Plyer](https://github.com/kivy/plyer): for systray area notification.
- [AwesomeTkinter](https://github.com/Aboghazala/AwesomeTkinter): for application GUI.
- [Pillow](https://python-pillow.org): the friendly PIL fork. PIL is an acronym for Python Imaging Library.
- [pystray](https://github.com/moses-palmer/pystray): for systray icon.

**Note for PycURL:**
For Windows users who wants to run from source or use pip:
Unfortunately, PycURL removed binary versions for Windows and it now has to be built from source. See here: http://pycurl.io/docs/latest/install.html#windows
`python -m pip install pycurl` will fail on Windows, your best choice is to use the portable version.

# How to contribute to this project:
1- By testing the application and opening [new issues](https://github.com/Sixline/VortexDM/issues/new) for bugs, feature requests, or suggestions.

2- Check the [Developer Guidelines](https://github.com/Sixline/VortexDM/blob/master/docs/developer_guide.md).

3- Check [open issues](https://github.com/Sixline/VortexDM/issues?q=is%3Aopen+is%3Aissue) and see if you can help.

4- Fork this repo and make a pull request.

# Contributors:
Please check [contributors.md](https://github.com/Sixline/VortexDM/blob/master/contributors.md) for a list of contributors.
