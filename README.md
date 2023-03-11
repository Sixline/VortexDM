# Renaming the project to Vortex Download Manager and will carry on where FireDM 2022.2.5 left off. Original project, FireDM, by Mahmoud Elshahat. RIP

The original creator removed the project repository from Github but left it on PyPI. The latest version they published there, 2022.4.14, I believe was purposely sabotaged to not work and anybody who accepted the update in FireDM would be left with the broken version. ~~If you want to install from PyPI install 2022.2.5 and don't update. https://pypi.org/project/FireDM/2022.2.5~~ 2022.2.5 is now gone from PyPI.

Homepage: https://github.com/Sixline/VDM  
PyPI Homepage: https://pypi.org/project/vortexdm

[![GitHub Issues](https://img.shields.io/github/issues-raw/Sixline/VDM?color=brightgreen)](https://github.com/Sixline/VDM/issues) - [![GitHub Closed Issues](https://img.shields.io/github/issues-closed-raw/Sixline/VDM?color=blueviolet)](https://github.com/Sixline/VDM/issues?q=is%3Aissue+is%3Aclosed)

![Logo](https://raw.githubusercontent.com/Sixline/VDM/main/icons/vdm.png)
Vortex Download Manager (VDM) is an open-source python Internet download manager with a high speed multi-connection engine. It downloads general files and videos from youtube and tons of other streaming websites.

Developed in Python, based on "LibCurl", and "youtube_dl".

**Features**:
* High download speeds based on LibCurl
* Multi-connection downloading
* Automatic file segmentation
* Automatic refresh for dead links
* Resume uncompleted downloads
* Support for Youtube, and a lot of other stream websites using youtube-dl to fetch info and libcurl to download media
* Download entire video, playlist, or selected videos
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

# How to use VDM:
Running in command line: show help by typing `vdm -h`

Running the GUI: Refer to the user guide at https://github.com/Sixline/VDM/blob/master/docs/user_guide.md

# Portable VDM Versions:
  
Run VDM without any installation (recommended) 
 - **Windows Portable Version** ([Download!](https://github.com/Sixline/VDM/releases/latest)):  
   Available in .zip format. Built with 64-bit Python 3.10+ and will only work on 64-bit Windows 10+.  
   Unzip and run VortexDM-GUI.exe, no installation required.
   
 - **Linux Portable Version**  
  Removing this section for now as I am not familiar with building AppImages. Will revisit.

## Manually installing VDM with pip (Linux Only - Debian/Ubuntu Based Shown):
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

## Running from source code inside virtual environment (Linux Only - Debian/Ubuntu Based Shown):
1- Check python version (minimum version required is 3.7): `python3 --version`

2- Install required packages:
```sh
sudo apt install ffmpeg libcurl4-openssl-dev libssl-dev python3-pip python3-pil python3-pil.imagetk python3-tk python3-dbus gir1.2-appindicator3-0.1
sudo apt install fonts-symbola fonts-linuxlibertine fonts-inconsolata fonts-emojione
```

3- Run below code to do following,
  a- clone this repo, 
  b- create Python virtual environment,
  c- install the requirements,
  d- create launch script, 
  e- and finally run VDM.

```sh

##1---  DOWNLOAD LATEST GIT
##---------------------------

git clone https://github.com/mrustad67/VortexDM.git

###2--- CREATE VIRUAL ENVIORMENT TO RUN PYTHON VORTEX DM
###------------------------------------------------------

python3 -m venv ./.env

###  ACTIVATE VIRTAL ENVIRMENT FOR FUNCTIONING
###-------------------------------------------

source ./.env/bin/activate

### INSTALL ALL DEPENDENCIES FROM PIP AS MENTIONED IN requirements.txt
-----------------------------------------------------------------------

python3 -m pip install -r ./VortexDM/requirements.txt

### CHANGE INTO VRTOX DIRECTORY CREATED BY GIT = ~/VortexDM
###--------------------------------------------

### WRITE NECESSARY COMMNDS TO SHELL SCRIPT FROM vdm.py TO vdm.sh, from within DIRECTORY CREATED BY GIT = ~/VortexDM
--------------------------------------------------------------------
echo "source ./.env/bin/activate
python3 ./vdm.py \$@ " > vdm.sh

### MAKE SHELL SCRIPT vdm.sh EXECUTABL , from within DIRECTORY CREATED BY GIT = ~/VortexDM
###---------------------------------

chmod +x ./vdm.sh

### RUN THE CREATED SHELL SCRIPT TO RUN VORTEX DOWNLOAD MANAGER PROGRAM, , from within DIRECTORY CREATED BY GIT = ~/VortexDM
###--------------------------------------------------------------------

./vdm.sh
```

> Optionally create .desktop file and add VDM to your applications
```sh
VDMLSPATH=$(realpath ./vdm.sh)
echo "[Desktop Entry]
Name=VortexDM
GenericName=VDM
Comment=Vortex Download Manager
Exec=$VDMLSPATH
Icon=vdm
Terminal=false
Type=Application
Categories=Network;
Keywords=Internet;download
" > VDM.desktop
cp ./VDM.desktop ~/.local/share/applications/
mkdir -p ~/.local/share/icons/hicolor/48x48/apps/
cp ./VDM/icons/vdm.png ~/.local/share/icons/hicolor/48x48/apps/vdm.png
```

# Known Issues:
- Linux X-server will raise an error if some fonts are missing especially emoji fonts - See Dependencies below

- Mac - Tkinter, as mentioned in "python.org" the Apple-supplied Tcl/Tk 8.5 has serious bugs that can cause application crashes. If you wish to use Tkinter, do not use the Apple-supplied Pythons. Instead, install and use a newer version of Python from python.org or a third-party distributor that supplies or links with a newer version of Tcl/Tk.

- systray icon: depends on Gtk+3 and AppIndicator3 on linux, please refer to your distro guides on how to install these packages if you need systray to run properly

# Dependencies:
- Python 3.7+: Tested with Python 3.10+ on Windows 10 and Ubuntu Linux
- tkinter
- [ffmpeg](https://www.ffmpeg.org/) : for merging audio with youtube DASH videos
- Fonts: (Linux X-server will raise an error if some fonts are missing especially emoji fonts, below are the 
recommended fonts to be installed

    ```
    ttf-linux-libertine 
    ttf-inconsolata 
    ttf-emojione
    ttf-symbola
    noto-fonts
    ```
- [pycurl](http://pycurl.io/docs/latest/index.html): is a Python interface to libcurl / curl as our download engine,
- [youtube_dl](https://github.com/ytdl-org/youtube-dl): famous youtube downloader, limited use for meta information extraction only but videos are downloaded using pycurl
- [yt_dlp](https://github.com/yt-dlp/yt-dlp): a fork of youtube-dlc which is inturn a fork of youtube-dl
- [certifi](https://github.com/certifi/python-certifi): required by 'pycurl' for validating the trustworthiness of SSL certificates,
- [plyer](https://github.com/kivy/plyer): for systray area notification.
- [awesometkinter](https://github.com/Aboghazala/AwesomeTkinter): for application gui.
- [pillow](https://python-pillow.org/): imaging library for python
- [pystray](https://github.com/moses-palmer/pystray): for systray icon

**Note for PycURL:**
For Windows users who wants to run from source or use pip:
Unfortunately, PycURL removed binary versions for Windows and it now has to be built from source. See here: http://pycurl.io/docs/latest/install.html#windows
`python -m pip install pycurl` will fail on Windows, your best choice is to use the portable version.

# How to contribute to this project:
1- By testing the application and opening [new issues](https://github.com/Sixline/VDM/issues/new) for bugs, feature requests, or suggestions.

2- Check the [Developer Guidelines](https://github.com/Sixline/VDM/blob/master/docs/developer_guide.md).

3- Check [open issues](https://github.com/Sixline/VDM/issues?q=is%3Aopen+is%3Aissue) and see if you can help.

4- Fork this repo and make a pull request.

# Contributors:
Please check [contributors.md](https://github.com/Sixline/VDM/blob/master/contributors.md) for a list of contributors.
