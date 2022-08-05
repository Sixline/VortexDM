# Renaming the project to Vortex Download Manager and will carry on where FireDM 2022.2.5 left off. Original project, FireDM, by Mahmoud Elshahat. RIP

## The original creator removed the project repository from Github but left it on PyPI. The latest version they published there, 2022.4.14, I believe was purposely sabotaged to not work and anybody who accepted the update in FireDM would be left with the broken version. ~~If you want to install from PyPI install 2022.2.5 and don't update. https://pypi.org/project/FireDM/2022.2.5~~ 2022.2.5 is now gone from PyPI.

Homepage: https://github.com/Sixline/VDM

![GitHub All Releases](https://img.shields.io/github/downloads/Sixline/VDM/total?color=orange&label=GitHub%20Releases)

![GitHub issues](https://img.shields.io/github/issues-raw/Sixline/VDM?color=brightgreen) - ![GitHub closed issues](https://img.shields.io/github/issues-closed-raw/Sixline/VDM?color=blueviolet)

![Logo](https://github.com/Sixline/FireDM/blob/main/icons/48x48.ico?raw=true)
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

# Portable VDM versions:
  
Run VDM without any installation (recommended) 
 - **Windows portable version** ([Download!](https://github.com/Sixline/VDM/releases/latest)):  
   available in .zip format.  
   unzip, and run from VDM.exe, no installation required.
   
 - **Linux portable version** ([Download!](https://github.com/Sixline/VDM/releases/latest)):   
   available in .AppImage format.  
   download file, then mark it as executable, and run it, no installation required,
   tested on ubuntu, mint, and manjaro.
   note: ffmpeg is not included and must be installed separately
   
   mark file as executable by right clicking the file> Properties> Permissions> Allow executing file as a program, or from terminal by `chmod +x VDM_xxx.AppImage`
   
   To check for ffmpeg use this command:
   ```sh
    which ffmpeg
   
    # expected output if installed
    /usr/bin/ffmpeg
   ```

   if ffmpeg is missing you can install it by `sudo apt install ffmpeg` on debian based or `sudo pacman -S ffmpeg` on Arch based distros.

## Manually installing VDM with pip (Linux):

Removed for now until project is added to PyPI.

## Running from source code inside virtual environment (Linux):
1- check python version (minimum version required is 3.6): `python3 --version`

2- install required packages first:
- Linux, ubuntu:
```sh
sudo apt install ffmpeg libcurl4-openssl-dev libssl-dev python3-pip python3-pil python3-pil.imagetk python3-tk python3-dbus gir1.2-appindicator3-0.1
sudo apt install fonts-symbola fonts-linuxlibertine fonts-inconsolata fonts-emojione
```

3- run below code to clone this repo, create virtual environment, install requirements, create launch script, and finally run FireDM

```sh
git clone --depth 1 https://github.com/VDM/VDM.git
python3 -m venv ./.env
source ./.env/bin/activate
python3 -m pip install -r ./VDM/requirements.txt
echo "source ./.env/bin/activate
python3 ./VDM/vdm.py \$@
" > vdm.sh
chmod +x ./vdm.sh
./vdm.sh
```

> optionally create .desktop file and add VDM to your applications
```sh
FireDMLSPATH=$(realpath ./vdm.sh)
echo "[Desktop Entry]
Name=Vortex Download Manager
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
cp ./FireDM/icons/vdm.png ~/.local/share/icons/hicolor/48x48/apps/vdm.png
```

# Known Issues:
- Linux X-server will raise an error if some fonts are missing especially emoji fonts - See Dependencies below

- Mac - Tkinter, as mentioned in "python.org" the Apple-supplied Tcl/Tk 8.5 has serious bugs that can cause application crashes. If you wish to use Tkinter, do not use the Apple-supplied Pythons. Instead, install and use a newer version of Python from python.org or a third-party distributor that supplies or links with a newer version of Tcl/Tk.

- systray icon: depends on Gtk+3 and AppIndicator3 on linux, please refer to your distro guides on how to install these packages if you need systray to run properly

# Dependencies:
- Python 3.6+: tested with python 3.6 on windows, and 3.7, 3.8 on linux
- tkinter
- [ffmpeg](https://www.ffmpeg.org/) : for merging audio with youtube DASH videos "it will be installed automatically on windows"
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
Normal pip install i.e `python -m pip install pycurl` probably will fail on Windows, your best choice is to use the VDM standalone/portable exe version.

For Linux users:
There is no issue since most Linux distros have cURL preinstalled. PycURL will link with the libcurl library and get built without issues. Checked with python versions 3.6, 3.7, and 3.8.

# How to contribute to this project:
1- By testing the application and opening [new issues](https://github.com/Sixline/VDM/issues/new) for bugs, feature requests, or suggestions.
2- Check the [Developer Guidelines](https://github.com/Sixline/VDM/blob/master/docs/developer_guide.md).
3- Check [open issues](https://github.com/Sixline/VDM/issues?q=is%3Aopen+is%3Aissue) and see if you can help.
4- Fork this repo and make a pull request.

# Contributors:
Please check [contributors.md](https://github.com/Sixline/FireDM/blob/master/contributors.md) for a list of contributors.