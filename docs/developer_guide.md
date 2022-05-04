### Developer Guide

This Guide for developer who want to contribute or understand how this project work, feel free to improve this guide anytime


### Purpose of this project:
This project is built upon famous youtube-dl project, with a proper use of 
multithreading and the use of Libcurl as a download engine, it willl reach 
upto 10x higher speeds in case of hls or fragmented video files,
in addition it can download general files too.

GUI, is based on tkinter, which is a lightweight and responsive.

This project is never made to compete with other download managers, it
is just a "hopefully useful" Simple enough and fast video downloader.


---


### Current project logic:
Generally FireDM is using Libcurl as a download engine via threads to
achieve multi-connections, for videos, youtube-dl is our player, where
its sole role is to extract video information from a specific url "No
other duties for youtube-dl".  
FFMPEG will be used for post processing e.g. mux audio and video, merge
HLS video segments into one video file, and other useful media
manipulation.


Current application design adopts "MVC" design pattern, where "Model" in model.py, 
controller in controller.py and view is tkview.py for tkinter gui or cmdview.py 
which run interactively in terminal.

also an "observer" pattern is used to notify controller when model "data object" 
chenage its state.

Work flow using gui as follow:
- user enter a url in url entry widget.
- gui will ask controller to process url.
- controller will make a data object e.g. ObservableDownloadItem() and call its 
  url_update method which send http request to remote server and based on the received 
  'response headers' from server it will update properties like name, size, mime type, 
  download url, etc..., and controller will be notified with changes.
- in case mime type is html, then controller will pass url to youtube-dl to search for
  videos, and it will create ObservableVideo() object.
- controller will send update messages to gui and it will show file info in main tab.
- when user press download button, gui will ask controller to download current file,
  controller will make some pre-download checks and if all ok, it will create a thread
  to run 'brain function' to download the file 
- brain function will run both 'thread manager' and file manager
- thread manager will make multiple connection to download file in "chunks"
- file manager will write completed chunks into the target file
- after completing all chunks, a post processing will be run if necessary, e.g. ffmpeg
  will mux audio and video in one final video file.


---


### Files:

- **FireDM.py:** main file, it will start application in either
  interactive terminal mode or in gui mode.

- **config.py:** Contains all shared variables and settings.

- **utils.py:** all helper functions.

- **tkview.py:** This module has application gui, designed by tkinter.

- **settings.py:** this where we save / load settings, and download items list

- **brain.py:** every download item object will be sent to brain to
  download it, this module has thread manager, and file manager

- **cmdview.py:** an interactive user interface run in terminal.

- **controller.py:** a part of "MVC" design, where it will contain the
  application logic and communicate to both Model and view

- **model.py:** contains "ObservableDownloadItem", "ObservableVideo" which acts 
  as Model in "MVC" design with "observer" design.

- **downloaditem.py:** It has DownloadItem class which contains
  information for a download item, and you will find a lot of
  DownloadItem objects in this project named shortly as "d" or
  "self.d".

- **video.py:** it contains Video class which is subclassed from
  DownloadItem, for video objects. also this file has most video related
  function, e.g. merge_video_audio, pre_process_hls, etc...

- **worker.py:** Worker class object acts as a standalone workers, every
  worker responsible for downloading a chunk or file segment.

- **update.py:** contains functions for updating FireDM frozen version
  "currently cx_freeze windows portable version", also update
  youtube-dl.

- **version.py:** contains version number, which is date based, example
  content, __version__ = '2020.8.13'

- **dependency.py:** contains a list of required external packages for
  FireDM to run and has "install_missing_pkgs" function to install the
  missing packages automatically.

- **ChangeLog.txt:** Log changes to each new version.

---

### Documentation format:
  code documentation if found doesn't follow a specific format,
  something that should be fixed, the selected project format should
  follow Google Python Style Guide, resources:

- [Example Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html#example-google)
- ["Google Python Style Guide"](http://google.github.io/styleguide/pyguide.html)


---

### How can I contribute to this project:
- check open issues in this project and find something that you can fix.
- It's recommended that you open an issue first to discuss what you want
  to do, this will create a better communication with other developers
  working on the project.
- pull request, and add a good description of your modification.
- it doesn't matter how small the change you make, it will make a
  difference.



