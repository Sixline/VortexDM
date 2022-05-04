Homepage: https://github.com/firedm/FireDM

[![Downloads](https://static.pepy.tech/personalized-badge/pyidm?period=total&units=international_system&left_color=grey&right_color=blue&left_text=PyIDM%20Downloads%20(pypi))](https://pepy.tech/project/pyidm)
[![Downloads](https://static.pepy.tech/personalized-badge/firedm?period=total&units=international_system&left_color=grey&right_color=blue&left_text=FireDM%20Downloads%20(pypi))](https://pepy.tech/project/firedm)

![GitHub All Releases](https://img.shields.io/github/downloads/firedm/firedm/total?color=blue&label=GitHub%20Releases)

![GitHub issues](https://img.shields.io/github/issues-raw/firedm/firedm?color=blue) - ![GitHub closed issues](https://img.shields.io/github/issues-closed-raw/firedm/firedm?color=blue)

![logo](https://github.com/firedm/FireDM/blob/master/icons/48x48.png)
FireDM is a python open source (Internet Download Manager) 
with multi-connections, high speed engine, 
it downloads general files and videos from youtube and tons of other streaming websites . <br>
Developed in Python, based on "LibCurl", and "youtube_dl".

[**Download Latest version!!**](https://github.com/firedm/FireDM/releases/latest)

![screenshot](https://user-images.githubusercontent.com/58998813/134947539-0bec3cf4-fd02-47d4-b9be-e370c645d648.png)

[more screenshots ...](https://github.com/firedm/FireDM/issues/13#issuecomment-928043472)

---
**Features**:
* High download speeds "based on LibCurl"
* Multi-connection downloading "Multithreading"
* Automatic file segmentation.
* Automatic refresh for dead links.
* Resume uncompleted downloads.
* Support for Youtube, and a lot of stream websites "using youtube-dl to fetch info and libcurl to download media".
* download entire video playlist or selected videos.
* download fragmented video streams, and encrypted/nonencrypted HLS media streams.
* watch videos while downloading* "some videos will have no audio until
  finish downloading".
* download video subtitles.
* write video metadata to downloaded files.
* check for application updates.
* Scheduling downloads
* Re-using existing connection to remote server.
* Clipboard Monitor.
* proxy support (http, https, socks4, and socks5).
* user/pass authentication, referee link, use cookies, video thumbnail,
  subtitles.
* use custom cookies files.
* MD5 and SHA256 checksums.
* Custom gui themes.
* Set download Speed limit
* User can run shell commands or shutdown computer on download completion.
* Control number of Concurrent downloads and Max. connections per each download.

---
# How to use FireDM:
running in command line: show help by typing `firedm -h`  <br>

running GUI: Refer to user guide at https://github.com/firedm/FireDM/blob/master/docs/user_guide.md

----------------------
# Portable FireDM versions:
  
Run FireDM without any installation (recommended) 
 - **Windows portable version** ([Download!](https://github.com/firedm/FireDM/releases/latest)):  
   available in .zip format.  
   unzip, and run from FireDM.exe, no installation required.
   
 - **Linux portable version** ([Download!](https://github.com/firedm/FireDM/releases/latest)):   
   available in .AppImage format.  
   download file, then mark it as executable, and run it, no installation required,
   tested on ubuntu, mint, and manjaro.<br>
   note: ffmpeg is not included and must be installed separately if not exist <br>
   
   mark file as executable by right clicking the file> Properties> Permissions> Allow executing file as a program, 
   or from terminal by `chmod +x FireDM_xxx.AppImage` <br>
   
   To check for ffmpeg use this command:
   ```sh
    which ffmpeg
   
    # expected output if installed
    /usr/bin/ffmpeg
   ```

   if ffmpeg is missing you can install it by `sudo apt install ffmpeg` on debian based or `sudo pacman -S ffmpeg`
    on Arch based distros.
----------------------

## Manually installing FireDM with pip (Linux):
1- check python version (minimum version required is 3.6): `python3 --version`

2- install required packages first:<br>
- Linux, ubuntu:<br>
```sh
sudo apt install ffmpeg libcurl4-openssl-dev libssl-dev python3-pip python3-pil python3-pil.imagetk python3-tk python3-dbus gir1.2-appindicator3-0.1
sudo apt install fonts-symbola fonts-linuxlibertine fonts-inconsolata fonts-emojione
```

3- install firedm using pip:<br>

```sh
python3 -m pip install firedm --user --upgrade --no-cache
```

## Running from source code inside virtual environment (Linux):
1- check python version (minimum version required is 3.6): `python3 --version`

2- install required packages first:<br>
- Linux, ubuntu:<br>
```sh
sudo apt install ffmpeg libcurl4-openssl-dev libssl-dev python3-pip python3-pil python3-pil.imagetk python3-tk python3-dbus gir1.2-appindicator3-0.1
sudo apt install fonts-symbola fonts-linuxlibertine fonts-inconsolata fonts-emojione
```

3- run below code to clone this repo, create virtual environment, install requirements, create launch script, and finally run FireDM

```sh
git clone --depth 1 https://github.com/firedm/FireDM.git
python3 -m venv ./.env
source ./.env/bin/activate
python3 -m pip install -r ./FireDM/requirements.txt
echo "source ./.env/bin/activate
python3 ./FireDM/firedm.py \$@
" > firedm.sh
chmod +x ./firedm.sh
./firedm.sh
```

> optionally create .desktop file and add FireDM to your applications
```sh
FireDMLSPATH=$(realpath ./firedm.sh)
echo "[Desktop Entry]
Name=FireDM
GenericName=FireDM
Comment=FireDM Download Manager
Exec=$FireDMLSPATH
Icon=firedm
Terminal=false
Type=Application
Categories=Network;
Keywords=Internet;download
" > FireDM.desktop
cp ./FireDM.desktop ~/.local/share/applications/
mkdir -p ~/.local/share/icons/hicolor/48x48/apps/
cp ./FireDM/icons/48x48.png ~/.local/share/icons/hicolor/48x48/apps/firedm.png
```

## Arch-linux (AUR):
 - Firedm available for arch linux on AUR https://aur.archlinux.org/packages/firedm/ , Special Thanks to qontinuum for maintaining this package.

---

# Known Issues:
- Linux X-server will raise an error if some fonts are missing especially emoji fonts, for more info refer to [issue #200](https://github.com/firedm/FireDM/issues/200).


- Mac - Tkinter, as mentioned in "python.org" the Apple-supplied Tcl/Tk 8.5 has serious bugs that can cause application crashes. If you wish to use Tkinter, do not use the Apple-supplied Pythons. Instead, install and use a newer version of Python from python.org or a third-party distributor that supplies or links with a newer version of Tcl/Tk. <br>
refer to [issue #113](https://github.com/firedm/FireDM/issues/113)

- systray icon: depends on Gtk+3 and AppIndicator3 on linux, please refer to your distro guides on how to install these packages if you need systray to run properly
---

# Dependencies:
- Python 3.6+: tested with python 3.6 on windows, and 3.7, 3.8 on linux
- tkinter
- [ffmpeg](https://www.ffmpeg.org/) : for merging audio with youtube DASH videos "it will be installed automatically on windows"
- Fonts: (Linux X-server will raise an error if some fonts are missing especially emoji fonts, below are the 
recommended fonts to be installed, for more info refer to [issue #200](https://github.com/firedm/FireDM/issues/200).)

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
- [awesometkinter](https://github.com/Aboghazala/AwesomeTkinter): for
  application gui.
- [pillow](https://python-pillow.org/): imaging library for python
- [pystray](https://github.com/moses-palmer/pystray): for systray icon

**Note for pycurl:** <br>
for windows users who wants to run from source or use pip:
unfortunately, pycurl removed binary versions for windows and this link "https://dl.bintray.com/pycurl/pycurl/" is now dead, and one has to build pycurl from source which is not an easy task, details are here http://pycurl.io/docs/latest/install.html#windows
normal pip install i.e `python -m pip install pycurl` probably will fail on windows, your best choice is to use FireDM standalone/portable exe version.


for linux users:
there is no issues, since most linux distros have curl preinstalled, so pycurl will link with libcurl library to get built with no issues, checked with python versions 3.6, 3.7, and 3.8 working with no problems.
<br>


---
# what is the benefit of open source, compared to closed-source/Proprietary software if both are free?
As said, **"if the product is free, then you are the product"**, most
free closed-source software collect data about you, some of them are
toxic and plant trojans/spy-wares in your system, with open source,
nothing hidden, and source code exposed to thousands of programmers, no
one can play dirty games.


Need to mention, this project is never made to compete with other
download managers, it is just a "hopefully useful" addition.

---

<br>

# How to contribute to this project:
1- by testing the application and opening
[new issue](https://github.com/firedm/FireDM/issues/new) for bug
reporting, feature request, or suggestions.  
2- check
[developer guidelines](https://github.com/firedm/FireDM/blob/master/docs/developer_guide.md).  
3- check
[todo list](https://github.com/firedm/FireDM/blob/master/todo.md).  
4- check open issues, see if you can help.  
5- fork this repo and pull request

<br>

---

# Some articles/reviews on this project*:
- [ghacks](https://www.ghacks.net/2020/08/13/pyidm-is-an-open-source-download-manager-that-can-download-videos-and-playlists/)
- [softpedia](https://www.softpedia.com/get/Internet/Download-Managers/PyIDM.shtml)
- [hackermilk](http://hackermilk.info/2020/01/an_open_source_alternative_to_internet.html)

  *help edit this list by writing a comment in
  [this issue](https://github.com/firedm/FireDM/issues/136)
---

# contributors:
Please check
[contributors.md](https://github.com/firedm/FireDM/blob/master/contributors.md)
for a list of contributors

---

# Feedback:
your feedback is most welcomed by filling a
[new issue](https://github.com/firedm/FireDM/issues/new)  
or email to: info.pyidm@gmail.com <br>


---

Author:  
Mahmoud Elshahat  
2019-2021

