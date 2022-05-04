# FireDM user guide:
Parts of these guidelines has been taken from an
[article](https://www.ghacks.net/2020/08/13/firedm-is-an-open-source-download-manager-that-can-download-videos-and-playlists/)
about FireDM, thanks to Ashwin @ ghacks.net


FireDM is an open source download manager that can download videos and
playlists, written in Python.

The interface of FireDM has four tabs, The Main tab is used to add new
downloads. The program captures downloads from the clipboard, but you
can manually start a download by pasting a URL in the Link box.

When FireDM recognizes that the clipboard contains a link to a
downloadable file, it displays its interface. To be precise, the Main
tab is brought to focus. It displays the captured link, the name of the
file, its size, type (ZIP, EXE, etc), and whether the download can be
resumed or not.

![Main Tab](https://user-images.githubusercontent.com/58998813/92562020-939f2f80-f275-11ea-94ea-fe41c9c72abc.png)

Want to download videos? You can, copy the URL or paste it manually in
the link box and FireDM will pull up options to download the media. It
allows you to choose the videos to download, the video format and
resolution

![pl_main](https://user-images.githubusercontent.com/58998813/94432366-f3af3480-0196-11eb-8449-3e35bfb13e5c.png)

Need only audio stream, you can selct a variety of available formats,
like mp3, aac, ogg, beside ma, and webm.

![audio](https://user-images.githubusercontent.com/58998813/94432501-26f1c380-0197-11eb-9d25-59cbef8c2279.png)

For dash videos, "which have no audio" a proper audio will be
automatically selected, but if you need to select audio manually you
should enable manual dash audio selection option in settings tab.
![dash audio](https://user-images.githubusercontent.com/58998813/94432513-2b1de100-0197-11eb-86d5-6cd27763fba6.png)

You can change the folder where the file will be saved to, before
clicking on the download button. FireDM displays the download progress in
downloads tab that indicates the download's file size progress, the
speed, time remaining for the process to complete.

**what about subtitles?**  
you can press "sub" button in main tab and a window will show up with
available subtitles and captions  
you can select any number of subtitles with your preferred format, e.g.
srt, vtt, ttml, srv, etc ...

![subs](https://user-images.githubusercontent.com/58998813/94432649-5acce900-0197-11eb-98f5-d47221859dae.png)

Once the download has been completed, a notification appears near os
notification area e.g. the Windows Action Center.


Manage your queue from the Downloads tab. You can pause, resume
downloads, refresh the URL, open the download folder and delete files
from the queue.

![downloads tab](https://user-images.githubusercontent.com/58998813/92564079-e4fcee00-f278-11ea-83e1-9a272bc06b0f.png)

The download queue displays the filename, size, percentage of the
download that's been completed, the download speed, status, etc.

Right-click on an item in the download queue to view a context menu that
can be used to open the file or the folder where it is saved. The "watch
while downloading" option opens your default video player to play the
media as it is being downloaded. The menu also lets you copy the URL of
the web page, the file's direct link or the playlist's URL.

![rcm](https://user-images.githubusercontent.com/58998813/94441493-1c3d2b80-01a3-11eb-9a91-9d67e91375f7.png)


---


# Settings Tab:
FireDM has a lot of options you can tweak, below will list most options
briefly.
![rcm](https://user-images.githubusercontent.com/58998813/94432701-6f10e600-0197-11eb-9d5a-397980d8fa57.png)

### Select theme:
There is some default themes you can switch betweenthem, if you don't
like the available themes you can use "New" button to create your own
theme.

Below is a "theme editor" window where you can name your custom theme,
choose some basic colors and the rest of colors will be auto-selected,
but if you need more fine tuning you can click advanced
button

![rcm](https://user-images.githubusercontent.com/58998813/94432668-628c8d80-0197-11eb-9276-0f7d778c244f.png)

There is also an option to edit and delete themes, but these options
available only for custom themes not default themes.

### Systray:
you can enable/disable systray icon with an option tosendFireDM to
systray when closing main window.

### Monitor urls:
FireDM will monitor clipboard for any copied urls"enabled by default",
however you can disable this option anytime.

### Write metadata to video files:
video files have some metadata e.g.name, chapter, series, duration,
etc... which can be hardcoded into video file when it gets downloaded.

### Auto rename:
if file with the same name exist in download folder,with this option
enabled, firedm will rename the new file, generally will add a number
suffix to avoid overwriting existing file, if you disable this option, a
warning popup will show up to ask user to overwrite file or cancel
download.

![overwrite](https://user-images.githubusercontent.com/58998813/94441003-86090580-01a2-11eb-8b9f-326e2f52f45d.png)


### Show MD5 and SHA256:
A very handy feature that save your time to check downloaded file
integrity.

---

![overwrite](https://user-images.githubusercontent.com/58998813/94432706-70421300-0197-11eb-83d3-6be27caf841a.png)

### concurrent downloads:
number of maximum files downloads that can bedone in same time, set this
to 1 if you need to have only one download at a time and new added files
will be in pending list.

### connections per download:
maximum number of connections that every file download can establish
with the remote server in the same time.

### speed limit:
limit download speed for each download item, e.g. 100kb, 5 MB, etc..,
units can be upper or lower case.

### proxy:
you can use a proxy to access a restricted website, supported protocols
(http, https, socks4, and socks5)

proxy general format examples:

- http://proxy_address:port
- 157.245.224.29:3128
- or if authentication required:
  `http://username:password@proxyserveraddress:port`

then you should select proxy type:
- http
- https
- socks4
- socks5

Optionally you can choose to use proxy DNS by checking:
- 'Use proxy DNS' option

### login:
if website requires authentication you can add username and password,
these credential will not be saved in settings file.


### Referee url:
some servers will refuse downloading a file if you try to access
download link directly, as a workaround you should pass a referee url,
normally this is the website main webpage url.



## Using cookies with FireDM:

Passing cookies to FireDM is a good way to work around CAPTCHA, some websites require you to solve in particular
cases in order to get access (e.g. YouTube, CloudFlare).

you need to extract cookie file from your browser save it some where (for example: cookies.txt) then goto
Settings > Network > then check Use Cookies option
browse to select your cookies file ... done.

In order to extract cookies from browser use any conforming browser extension for exporting cookies.
For example, [cookies.txt](https://chrome.google.com/webstore/detail/cookiestxt/njabckikapfpffapmjgojcnbfjonfjfg) (for Chrome)
or [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) (for Firefox)

Note that the cookies file must be in Mozilla/Netscape format and the first line of the cookies file must be either
`# HTTP Cookie File or # Netscape HTTP Cookie File`.
Make sure you have correct newline format in the cookies file and convert newlines if necessary to correspond with your OS,
namely CRLF (\r\n) for Windows and LF (\n) for Unix and Unix-like systems (Linux, macOS, etc.).
HTTP Error 400: Bad Request when using cookies is a good sign of invalid newline format.


![settings screenshot 3](https://user-images.githubusercontent.com/58998813/94432708-70daa980-0197-11eb-95ee-e89ff05a46b2.png)

---

## Debugging:
There is some options to help developers catch problems:

### keep temp files:
An option to leave temp folder when done downloading for inspecting
segment files for errors.

### Re-raise exceptions:
crash application and show detailed error description, useful when
running FireDM from source.


---

## Update:

### check for update frequency:
FireDM will try to check for new version on github every "7 days as
default" it will first ask user for permission to do so, also frequency
can be changed or uncheck this option to disable periodic check for update

you can check for new FireDM version manually any time you press refresh
button in front of FireDM version.

for Youtube-dl you can check for new version and if found, FireDM will
ask user to install it automatically, after finish, you should restart
firedm for new youtube-dl version to be loaded, in case new youtube-dl
version doesn't work as expected, you can press "Rollback update" to
restore the last youtube-dl version


