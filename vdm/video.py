"""
    Vortex Download Manager (VDM)

    Multi-connection internet download manager, based on "LibCurl", and "youtube_dl". Original project, FireDM, by Mahmoud Elshahat.
    :copyright: (c) 2022 by Sixline
    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU GPLv3, see LICENSE.md for more details.
"""
import copy
import os
import re
import time
from urllib.parse import urljoin
import importlib
import io
import base64
import shlex
import subprocess

from . import config
from .downloaditem import DownloadItem, Segment
from .utils import (log, validate_file_name, get_headers, format_bytes, run_command, delete_file, download, rename_file,
                    run_thread, import_file)


# todo: change docstring to google format and clean unused code


# youtube-dl
ytdl = None  # youtube-dl will be imported in a separate thread to save loading time

youtube_dl = None  # youtube-dl will be imported in a separate thread to save loading time
yt_dlp = None  # yt_dlp will be imported in a separate thread to save loading time


class Logger(object):
    """used for capturing youtube-dl stdout/stderr output"""

    def debug(self, msg):
        log(msg)

    def error(self, msg):
        # filter an error message when quitting youtube-dl by setting config.ytdl_abort
        if msg == "ERROR: 'NoneType' object has no attribute 'headers'": return
        log(msg)

    def warning(self, msg):
        log(msg)

    def __repr__(self):
        return "youtube-dl Logger"


def get_ytdl_options():
    # reference: https://github.com/ytdl-org/youtube-dl/blob/a8035827177d6b59aca03bd717acb6a9bdd75ada/youtube_dl/__init__.py#L317
    ydl_opts = {'ignoreerrors': True, 'logger': Logger()}  # 'prefer_insecure': False, 'no_warnings': False,
    if config.proxy:
        # youtube-dl accept socks4a, but not socks5h,
        # https://github.com/ytdl-org/youtube-dl/blob/a8035827177d6b59aca03bd717acb6a9bdd75ada/youtube_dl/utils.py#L5404
        proxy = config.proxy.replace('socks5h', 'socks5')
        ydl_opts['proxy'] = proxy

    # set Referer website
    if config.referer_url:
        # this is not accessible via youtube-dl options, changing standard headers is the only way
        ytdl.utils.std_headers['Referer'] = config.referer_url

    # verify / bypass server's ssl certificate
    ydl_opts['nocheckcertificate'] = config.ignore_ssl_cert

    # website authentication
    if config.username or config.password:
        ydl_opts['username'] = config.username
        ydl_opts['password'] = config.password

    # cookies: https://github.com/ytdl-org/youtube-dl/blob/master/README.md#how-do-i-pass-cookies-to-youtube-dl
    if config.use_cookies:
        ydl_opts['cookiefile'] = config.cookie_file_path

    # subtitle
    # ydl_opts['listsubtitles'] = True  # this is has a problem with playlist
    # ydl_opts['allsubtitles'] = True  # has no effect
    ydl_opts['writesubtitles'] = True
    ydl_opts['writeautomaticsub'] = True

    # if config.log_level >= 3:
        # ydl_opts['verbose'] = True  # it make problem with Frozen VDM, extractor doesn't work
    # elif config.log_level <= 1:
    #     ydl_opts['quiet'] = True  # it doesn't work

    return ydl_opts


class Video(DownloadItem):
    """represent a youtube video object, interface for youtube-dl"""

    def __init__(self, url, vid_info=None):
        super().__init__(folder=config.download_folder)
        self.type = 'video'
        self.resumable = True
        self.vid_info = vid_info  # a youtube-dl dictionary contains video information
        # let youtube-dl fetch video info
        if self.vid_info is None:
            with ytdl.YoutubeDL(get_ytdl_options()) as ydl:
                self.vid_info = ydl.extract_info(url, download=False, process=True)

        self.webpage_url = self.vid_info.get('webpage_url', None) or url

        # set url
        self.url = self.webpage_url

        self.simpletitle = validate_file_name(self.vid_info.get('title') or f'video{int(time.time())}')
        self.title = self.simpletitle
        self.name = self.title

        # streams
        self.all_streams = []
        self.stream_menu = []  # streams names
        self.stream_menu_map = []  # actual stream objects in same order like streams names in stream_menu
        self.names_map = {'mp4_videos': [], 'other_videos': [], 'audio_streams': [], 'extra_streams': []}
        self.audio_streams = []
        self.video_streams = []

        self._selected_stream = None

        # thumbnail
        self.thumbnail_url = ''

        # flag for processing raw video info by youtube-dl
        self.processed = False

        self.setup()

    def __repr__(self):
        return f'Video_object(name:{self.name}, url:{self.url})'

    def setup(self):
        # url = self.vid_info.get('url', None) or self.vid_info.get('webpage_url', None) or self.vid_info.get('id', None)

        # sometimes url is just video id when fetch playlist info with process=False, try to get complete url
        # example, playlist url: https://www.youtube.com/watch?v=ethlD9moxyI&list=PL2aBZuCeDwlSXza3YLqwbUFokwqQHpPbp
        # video url = C4C8JsgGrrY
        # After processing will get webpage url = https://www.youtube.com/watch?v=C4C8JsgGrrY
        self.url = self.vid_info.get('webpage_url', None) or self.url

        self.simpletitle = validate_file_name(self.vid_info.get('title') or f'video{int(time.time())}')
        self.title = validate_file_name(self.get_title()) or self.simpletitle
        self.name = self.title

        # video duration
        self.duration = self.vid_info.get('duration', None)

        # thumbnail
        self.thumbnail_url = self.vid_info.get('thumbnail', '')

        # subtitles
        self.subtitles = self.vid_info.get('subtitles', {})
        self.automatic_captions = self.vid_info.get('automatic_captions', {})

        # use youtube-dl headers
        self.http_headers = self.vid_info.get('http_headers') or config.http_headers

        # use custom user agent if any
        if config.custom_user_agent:
            self.http_headers['User-Agent'] = config.custom_user_agent

        # don't accept compressed contents
        self.http_headers['Accept-Encoding'] = '*;q=0'

        # get metadata
        self.metadata_file_content = get_metadata(self.vid_info)

        # build streams
        self._process_streams()

        # select default stream
        if self.all_streams:
            self.select_stream(index=1)

    def get_title(self, outtmpl=None):
        # get video title template
        outtmpl = outtmpl or config.video_title_template or '%(title)s'

        # remove extension, it will be added later depend on stream type
        outtmpl = outtmpl.replace('.%(ext)s', '')

        # get global youtube_dl options
        options = get_ytdl_options()
        options['outtmpl'] = outtmpl

        ydl = ytdl.YoutubeDL(options)

        # get video title template
        if self.all_streams:
            info = self.vid_info
            if self.audio_stream:
                info.update(**self.audio_stream.stream_info)
            info.update(**self.selected_stream.stream_info)
            title = ydl.prepare_filename(info)
            return title

    def _process_streams(self):
        all_streams = [Stream(x) for x in self.vid_info['formats']]
        all_streams.reverse()  # get higher quality first

        # streams have mediatype = (normal, dash, audio, others)
        # arrange streams as follows: video mp4, video other formats, audio
        video_streams = [stream for stream in all_streams if stream.mediatype not in ('audio', 'others')]
        audio_streams = [stream for stream in all_streams if stream.mediatype == 'audio']
        extra_streams = []

        # filter repeated video streams and prefer normal over dash
        v_names = []
        for i, stream in enumerate(video_streams[:]):
            if stream.raw_name in v_names and stream.mediatype == 'dash':
                extra_streams.append(stream)
            v_names.append(stream.raw_name)

        # sort and rebuild video streams again
        video_streams = sorted([stream for stream in video_streams if stream not in extra_streams], key=lambda stream: stream.quality, reverse=True)

        # sort video streams mp4 first
        mp4_videos = [stream for stream in video_streams if stream.extension == 'mp4']
        other_videos = [stream for stream in video_streams if stream.extension != 'mp4']

        # add extra audio formats
        if audio_streams:
            # sort audio streams from best to lowest
            audio_streams = sorted(audio_streams, key=lambda stream: stream.quality, reverse=True)
            bestaudio = audio_streams[0]
            webms = [stream for stream in audio_streams if stream.extension == 'webm']
            webm = webms[0] if webms else bestaudio

            m4as = [stream for stream in audio_streams if stream.extension == 'm4a']
            m4a = m4as[0] if m4as else bestaudio

            existing_extensions = [stream.extension for stream in audio_streams]

            for ext in config.audio_ext_choices:
                if ext in existing_extensions:
                    continue
                elif ext in ('aac', 'mp3'):
                    source = m4a
                elif ext in ('opus', 'ogg'):
                    source = webm
                else:
                    source = bestaudio
                if not source:
                    continue
                aud = copy.copy(source)
                aud.extension = ext
                audio_streams.append(aud)

        # update all streams with sorted ones
        all_streams = video_streams + audio_streams + extra_streams

        # create a name map
        names_map = {'mp4_videos': [stream.name for stream in mp4_videos],
                     'other_videos': [stream.name for stream in other_videos],
                     'audio_streams': [stream.name for stream in audio_streams],
                     'extra_streams': [stream.name for stream in extra_streams]}

        # build menu
        stream_menu = ['Video streams:                     '] + [stream.name for stream in mp4_videos] + [stream.name for stream in other_videos]  \
                      + ['', 'Audio streams:                 '] + [stream.name for stream in audio_streams]
                      # + ['', 'Extra streams:                 '] + [stream.name for stream in extra_streams]

        # stream menu map will be used to lookup streams from stream menu, can't use dictionary to allow repeated key names
        stream_menu_map = [None] + mp4_videos + other_videos + [None, None] + audio_streams + [None, None] + extra_streams

        # update properties
        self.all_streams = all_streams
        self.stream_menu = stream_menu
        self.stream_menu_map = stream_menu_map
        self.names_map = names_map  # {'mp4_videos': [], 'other_videos': [], 'audio_streams': [], 'extra_streams': []}
        self.audio_streams = audio_streams
        self.video_streams = video_streams
        self.mp4_videos = mp4_videos

    def select_stream(self, format_id=None, index=None, name=None, raw_name=None, quality=None,
                      extension=None, mediatype=None, dashaudio='best'):
        """
        select main stream
        Args:
            format_id: stream id from youtube-dl
            index(int): index number from stream menu
            name(str): stream name
            raw_name(str): stream raw name
            quality(int or str): video quality, e.g. 1080, or best, or lowest
            extension(str): extension
            mediatype(str): video or audio
            dashaudio(str): dash audio quality (best, lowest)
        Return:
            stream

        Side effect:
            set self.selected_stream
        """

        stream = self.get_stream(format_id=format_id, index=index, name=name, raw_name=raw_name, quality=quality,
                                 extension=extension, mediatype=mediatype)

        if stream:
            self.selected_stream = stream

            if stream.mediatype == 'dash' and dashaudio != 'best':
                self.select_audio(quality=dashaudio)

    def get_stream(self, format_id=None, index=None, name=None, raw_name=None, quality=None,
                   extension=None, mediatype=None, fragmented=None):
        """
        get video or audio stream
        Args:
            format_id: stream id from youtube-dl
            index(int): index number from stream menu
            name(str): stream name
            raw_name(str): stream raw name
            quality(int or str): video quality, e.g. 1080, or best, or lowest
            extension(str): extension
            mediatype(str): video or audio
            fragmented(bool): True for fragmented streams
        Return:
            stream
        """
        streams = self.all_streams
        try:
            if index is not None:
                stream = self.stream_menu_map[index]
            else:
                # filter streams ---------------------------------------------------------------------------------------
                if mediatype in (config.MediaType.video, config.MediaType.audio):
                    # stream mediatype = (audio, dash, normal)
                    _mediatype = ('dash', 'normal') if mediatype == config.MediaType.video else (config.MediaType.audio,)
                    streams = [stream for stream in streams if stream.mediatype in _mediatype] or streams
                else:
                    pass

                if format_id is not None:
                    streams = [stream for stream in streams if stream.format_id == format_id] or streams

                if name:
                    streams = [stream for stream in streams if name == stream.name] or streams

                if raw_name:
                    streams = [stream for stream in streams if raw_name == stream.raw_name] or streams

                if extension:
                    extension = extension.replace('.', '')
                    streams = [stream for stream in streams if stream.extension == extension] or streams

                if fragmented is not None:
                    streams = [stream for stream in streams if stream.fragments] or streams

                if quality:
                    quality = quality.lower()

                    if quality == 'best':
                        streams = sorted(streams, key=lambda item: item.quality, reverse=True)
                    elif quality == 'lowest':
                        streams = sorted(streams, key=lambda item: item.quality)
                    else:
                        q_dict = {v.lower(): k for k, v in config.vq.items()}
                        quality = q_dict.get(quality, quality)

                        if isinstance(quality, str):
                            # extract numbers from quality text
                            match = re.match(r'\d+', quality)
                            if match:
                                quality = match.group()

                            quality = int(quality)

                        if isinstance(quality, int):
                            streams = sorted(streams, key=lambda item: abs(quality - item.quality))

                # select stream ----------------------------------------------------------------------------------------
                stream = streams[0]

        except:
            stream = None

        return stream

    @property
    def selected_stream(self):
        if not self._selected_stream and self.all_streams:
            self._selected_stream = self.all_streams[0]  # select first stream

        return self._selected_stream

    @selected_stream.setter
    def selected_stream(self, stream):
        if type(stream) is not Stream:
            raise TypeError('value must be a Stream object')

        self._selected_stream = stream
        self.selected_quality = stream.name

        self.update_param()

    def get_thumbnail(self):
        """get video thumbnail and store it as base64 text in self.thumbnail"""
        size = (220, 115)

        if self.thumbnail_url and not self.thumbnail:
            try:
                from PIL import Image
                log('downloading Thumbnail', log_level=2)
                buffer = download(self.thumbnail_url, verbose=False, return_buffer=True, decode=False)
                import awesometkinter
                img = Image.open(buffer)
                img = img.resize(size, resample=Image.LANCZOS)
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                self.thumbnail = base64.b64encode(buffer.getvalue())
            except Exception as e:
                log('vide.get_thumbnail() error:', e, log_level=2)

    def update_param(self):
        """Mainly used when select a stream for current video object"""
        # log('Video_object.update_param', log_level=3)
        # reset segments first
        self.segments.clear()
        self.total_size = 0
        self.title = self.get_title() or self.title

        # do some parameters updates
        stream = self.selected_stream
        self.extension = '.' + stream.extension
        self.name = self.title + self.extension
        self.eff_url = stream.url
        self.size = stream.size
        self.fragment_base_url = stream.fragment_base_url
        self.fragments = stream.fragments
        self.protocol = stream.protocol
        self.format_id = stream.format_id
        self.manifest_url = stream.manifest_url
        self.resolution = stream.resolution
        self.abr = stream.abr
        self.tbr = stream.tbr

        # set type ---------------------------------------------------------------------------------------
        self.type = 'audio' if stream.mediatype == 'audio' else 'video'

        # set subtype
        self.subtype_list.clear()

        if stream.mediatype in ('dash', 'normal'):
            self.subtype_list.append(stream.mediatype)

        if 'm3u8' in self.protocol:
            self.subtype_list.append('hls')

        if self.fragments:
            self.subtype_list.append('fragmented')

        if 'f4m' in self.protocol:
            self.subtype_list.append('f4m')

        if 'ism' in self.protocol:
            self.subtype_list.append('ism')

        self.select_audio()

        # update http-headers
        self.http_headers = stream.http_headers or self.http_headers or config.http_headers

    def select_audio(self, audio_stream=None, quality='best'):
        video_stream = self.selected_stream

        if video_stream.mediatype == 'dash':
            # sort dash audios with highest quality first
            streams = sorted([stream for stream in self.all_streams if stream.mediatype == 'audio'],
                             key=lambda stream: stream.quality, reverse=True)

            if streams and not audio_stream:
                # filter based on fragmented flag
                streams = [stream for stream in streams if stream.isfragmented == video_stream.isfragmented] or streams

                # filter for compatible extension, faster muxing by ffmpeg,
                # also to avoid errors when muxing m4a audio with webm video using "-c copy" flag, example ffmpeg error
                # [webm@xx] Only VP8 or VP9 or AV1 video and Vorbis or Opus audio and WebVTT subtitles are supported for WebM.
                ext = 'm4a' if video_stream.extension == 'mp4' else video_stream.extension
                streams = [stream for stream in streams if stream.extension == ext] or streams

                if quality == 'lowest':
                    audio_stream = streams[-1]
                else:
                    audio_stream = streams[0]

            if audio_stream:
                self.audio_stream = audio_stream
                self.audio_quality = self.audio_stream.name
                self.audio_url = audio_stream.url
                self.audio_size = audio_stream.size
                self.audio_fragment_base_url = audio_stream.fragment_base_url
                self.audio_fragments = audio_stream.fragments
                self.audio_format_id = audio_stream.format_id

            # log('downloaditem.select_audio:', self.audio_quality, log_level=3)

            # re-build segments
            self.build_segments()

            # re-calculate total size
            self.total_size = self.calculate_total_size()
        else:
            self.audio_url = None
            self.audio_fragment_base_url = None
            self.audio_fragments = None
            self.audio_format_id = None

    def refresh(self):
        # todo, use vid_info as property instead of this
        """will be used in case we updated vid_info dictionary from youtube-dl"""
        # reset properties and rebuild streams
        self.setup()


class Stream:
    def __init__(self, stream_info):
        # fetch data from youtube-dl stream_info dictionary
        self.stream_info = stream_info
        self.format_id = stream_info.get('format_id', '')
        self.url = stream_info.get('url', None)
        self.player_url = stream_info.get('player_url', None)
        self.extension = stream_info.get('ext', None)
        self.width = stream_info.get('width', 0)
        self.height = stream_info.get('height', 0)
        self.fps = stream_info.get('fps', None)  # frame per second
        self.format_note = stream_info.get('format_note', '')
        self.acodec = stream_info.get('acodec', None)
        self.abr = stream_info.get('abr', 0)
        self.tbr = stream_info.get('tbr', 0)  # for videos == BANDWIDTH/1000
        self.size = stream_info.get('filesize', None)
        # self.quality = stream_info.get('quality', None)
        self.vcodec = stream_info.get('vcodec', None)
        self.res = stream_info.get('resolution', None)
        self.downloader_options = stream_info.get('downloader_options', None)
        self.format = stream_info.get('format', None)
        self.container = stream_info.get('container', None)

        # hls stream specific
        self.manifest_url = stream_info.get('manifest_url', '')

        # get http-headers
        self.http_headers = stream_info.get('http_headers')

        # fragmented video streams
        self.fragment_base_url = stream_info.get('fragment_base_url', None)
        self.fragments = stream_info.get('fragments', None)

        # protocol
        self.protocol = stream_info.get('protocol', '')

        # calculate some values
        self.rawbitrate = stream_info.get('abr', 0) * 1024
        self._mediatype = None
        self.resolution = f'{self.width}x{self.height}' if (self.width and self.height) else ''

        # ignore fragmented streams, and hls (m3u8), the size coming from headers is not correct
        if self.fragments or 'm3u8' in self.protocol:
            self.size = 0

        # get missing size
        elif not isinstance(self.size, int) or self.size == 0:
            self.size = self.get_size()

    def get_size(self):
        headers = get_headers(self.url, http_headers=self.http_headers)
        size = int(headers.get('content-length', 0))
        log('stream.get_size()>', self.name, format_bytes(size), log_level=3)
        return size

    @property
    def isfragmented(self):
        return True if self.fragments else False

    @property
    def name(self):
        fps = f' - {self.fps} fps' if self.fps else ''
        wh = f' - {self.width}x{self.height}' if self.height else ''
        q = config.vq.get(self.quality, self.quality)
        return f'    {self.extension} - {q}{wh} - {format_bytes(self.size)} - id:{self.format_id}{fps}'

    @property
    def raw_name(self):
        return f'    {self.extension} - {self.quality}'

    @property
    def quality(self):
        try:
            if self.mediatype == 'audio':
                return int(self.abr)
            else:
                # some video streams has its resolution's height different from its quality,
                # e.g. 1280 width x 676 height is actually 720p quality, will use the nearest standard quality
                height = int(self.height)
                if height not in config.standard_video_qualities:
                    height = sorted(config.standard_video_qualities, key=lambda item: abs(height - item))[0]

                return height
        except:
            return 0

    def __repr__(self, include_size=True):
        return self.name

    @property
    def mediatype(self):
        if not self._mediatype:
            if self.vcodec != 'none':
                self._mediatype = 'normal' if self.acodec != 'none' else 'dash'
            elif self.acodec != 'none':
                self._mediatype = 'audio'
            else:
                self._mediatype = 'others'

        return self._mediatype


def run_ffmpeg(cmd, d):
    """run ffmpeg in a subprocess"""
    if d.status == config.Status.cancelled:
        return 1, 'exit by user'

    cmd = shlex.split(cmd)

    # startupinfo to hide terminal window on Windows
    if config.operating_system == 'Windows':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    else:
        startupinfo = None

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               encoding='utf-8', errors='replace', shell=False, startupinfo=startupinfo)
    d.ffmpeg_process = process

    output = ''
    for line in process.stdout:
        line = line.strip()
        output += line
        log(line)
        if d.status == config.Status.cancelled:
            process.communicate(input=b'q')
            return 1, 'exit by user'

    # wait for subprocess to finish, process.wait() is not recommended
    process.communicate()

    # get return code
    process.poll()
    error = process.returncode  # non zero value indicate an error

    return error, 'done'


def merge_video_audio(video, audio, output, d):
    """merge video file and audio file into output file, d is a reference for current DownloadItem object"""
    log('merging video and audio')

    cmd = f'"{config.ffmpeg_actual_path}" -loglevel error -stats -y -i "{video}" -i "{audio}"'
    fastcmd = cmd + f' -c copy "{output}"'  # fast process, copy audio, format must match [mp4, m4a] and [webm, webm]
    slowcmd = cmd + f' "{output}"'  # slow, mix different formats

    error, output = run_ffmpeg(fastcmd, d)

    if error:
        error, output = run_ffmpeg(slowcmd, d)

    return error, output


def load_user_extractors(engine=youtube_dl):
    # load user's video extractors
    extractors_folder = os.path.join(config.sett_folder, 'extractors')
    if not os.path.isdir(extractors_folder):
        return

    for fname in os.listdir(extractors_folder):
        if not fname.endswith('.py'):
            continue
        try:
            fp = os.path.join(extractors_folder, fname)
            module = import_file(fp)

            extractors = {}
            for key, value in module.__dict__.items():
                if key.startswith('__') or value is module.InfoExtractor:
                    continue
                try:
                    if issubclass(value, module.InfoExtractor):
                        extractors[key] = value
                except:
                    pass

            # print('extractors:', extractors)

            for ie_key, ie in extractors.items():
                setattr(engine.extractor, ie_key, ie)
                engine.extractor._ALL_CLASSES.insert(0, ie)
        except Exception as e:
            log('load_user_extractors() error,', e, log_level=2)
            raise


def load_extractor_engines(reload=False):
    """import extractor engines
    should call this from a thread because sometimes youtube_dl takes around 20 seconds to get imported and impact
    app startup time

    Args:
        reload (bool): if true it will reload modules instead of importing, needed after modules update
    """

    # youtube-dl ----------------------------------------------------------------------------------------------------
    def import_youtube_dl():
        global youtube_dl
        start = time.time()

        if reload and youtube_dl:
            importlib.reload(youtube_dl)
        else:
            import youtube_dl

        config.youtube_dl_version = youtube_dl.version.__version__

        # calculate loading time
        load_time = time.time() - start
        log(f'youtube_dl version: {config.youtube_dl_version}, load_time= {int(load_time)} seconds', log_level=2)

        # get a random user agent and update headers
        if not config.custom_user_agent:
            config.http_headers['User-Agent'] = youtube_dl.utils.random_user_agent()

        # set default extractor
        if config.active_video_extractor == 'youtube_dl':
            set_default_extractor('youtube_dl')

        load_user_extractors(engine=youtube_dl)

    # yt_dlp ----------------------------------------------------------------------------------------------------
    def import_yt_dlp():
        global yt_dlp

        start = time.time()

        if reload and yt_dlp:
            importlib.reload(yt_dlp)
        else:
            import yt_dlp

        config.yt_dlp_version = yt_dlp.version.__version__

        # calculate loading time
        load_time = time.time() - start
        log(f'yt_dlp version: {config.yt_dlp_version}, load_time= {int(load_time)} seconds', log_level=2)

        # set default extractor
        if config.active_video_extractor == 'yt_dlp':
            set_default_extractor('yt_dlp')

        load_user_extractors(engine=yt_dlp)

    run_thread(import_youtube_dl, daemon=True)
    run_thread(import_yt_dlp, daemon=True)


def set_default_extractor(extractor=None):
    """set default extractor engine, e.g. select between youtube-dl and yt_dlp"""
    extractor = extractor or config.active_video_extractor

    global ytdl
    ytdl = youtube_dl if extractor == 'youtube_dl' else yt_dlp
    log('set default extractor engine to:', extractor, ytdl, log_level=2)


def set_interrupt_switch(ydl):
    """ set interrupt / kill switch for youtube-dl
    Args:
        ydl: an instance of YoutubeDL class
    """

    def urlopen_decorator(func):
        def newfunc(self, *args):
            # print('urlopen started ............................................')
            if config.ytdl_abort:
                # print('urlopen aborted ............................................')
                raise Exception(f'video extractor aborted by user')
                # return None
            data = func(self, *args)
            return data

        return newfunc

    try:
        # override urlopen in Youtube-dl or yt_dlp for interrupting session anytime
        ydl.urlopen = urlopen_decorator(ydl.urlopen)
    except Exception as e:
        log('video.set_interrupt_switch() error:', e)


def pre_process_hls(d):
    """
    handle m3u8 manifest file, build a local m3u8 file, and build DownloadItem segments
    :param d: DownloadItem() object
    :return True if success and False if fail
    """

    log('pre_process_hls()> start processing', d.name)

    # create temp_folder if doesn't exist
    if not os.path.isdir(d.temp_folder):
        try:
            os.makedirs(d.temp_folder)
        except Exception as e:
            log('HLS pre processing Failed:', e, showpopup=True)
            return False

    # some servers will change the contents of m3u8 file dynamically, not sure how often
    # ex: https://www.dplay.co.uk/show/help-my-house-is-haunted/video/the-skirrid-inn/EHD_259618B
    # solution is to download master manifest again, then get the updated media url
    # X-STREAM: must have BANDWIDTH, X-MEDIA: must have TYPE, GROUP-ID, NAME=="language name"
    # tbr for videos calculated by youtube-dl == BANDWIDTH/1000
    def refresh_urls(m3u8_doc, m3u8_url):
        # using youtube-dl internal function
        extract_m3u8_formats = youtube_dl.extractor.common.InfoExtractor._parse_m3u8_formats

        # get formats list [{'format_id': 'hls-160000mp4a.40.2-spa', 'url': 'http://ex.com/exp=15...'}, ...]
        # what we need is format_id and url
        formats = extract_m3u8_formats(None, m3u8_doc, m3u8_url, m3u8_id='hls')  # not sure about  m3u8_id='hls'
        for item in formats:
            url = item.get('url')
            # url = urljoin(d.manifest_url, url)
            format_id = item.get('format_id')

            # get format id without m3u8-id "hls-"
            stripped_format_id = format_id.replace('hls-', '') if format_id.startswith('hls-') else format_id

            # video check
            if d.format_id and (d.format_id == format_id or stripped_format_id in d.format_id):
                # print('old video url, new video url:\n', d.eff_url, '\n', url)
                d.eff_url = url

            # audio check
            if d.audio_format_id and (d.audio_format_id == format_id or stripped_format_id in d.audio_format_id):
                # print('old video url, new video url:\n', d.audio_url, '\n', url)
                d.audio_url = url

    def not_supported(m3u8_doc):
        # return msg if there is un supported protocol found in the m3u8 file

        if m3u8_doc:
            # SAMPLE-AES is not supported by ffmpeg, and mostly this will be a protected DRM stream, which shouldn't be downloaded
            if '#EXT-X-KEY:METHOD=SAMPLE-AES' in m3u8_doc:
                return 'Error: SAMPLE-AES encryption is not supported'

        return None

    def is_encrypted(m3u8_doc):
        if m3u8_doc:
            # check if file encrypted, example: #EXT-X-KEY:METHOD=AES-128,URI="xxx",IV=0x8f6109d91fffb816bcd43fefe018db49
            if '#EXT-X-KEY' in m3u8_doc:
                return True

        return False

    # maybe the playlist is a direct media playlist and not a master playlist
    if d.manifest_url:
        log('master manifest:   ', d.manifest_url)
        master_m3u8 = download_m3u8(d.manifest_url, http_headers=d.http_headers)
    else:
        log('No master manifest')
        master_m3u8 = None

    if master_m3u8:
        # save master m3u8 file for debugging, and update subtitles
        name = 'master.m3u8'
        local_file = os.path.join(d.temp_folder, name)
        with open(os.path.join(d.temp_folder, local_file), 'w') as f:
            f.write(master_m3u8)

        # master playlist doesn't have "#EXT-X-TARGETDURATION" tag, only media playlist has it
        if not "#EXT-X-TARGETDURATION" in master_m3u8:
            refresh_urls(master_m3u8, d.manifest_url)

    log('video m3u8:        ', d.eff_url)
    video_m3u8 = download_m3u8(d.eff_url, http_headers=d.http_headers)

    # abort if no video_m3u8
    if not video_m3u8:
        log("Failed to get valid m3u8 file", showpopup=True)
        return False

    audio_m3u8 = None
    if 'dash' in d.subtype_list:
        log('audio m3u8:        ', d.audio_url)
        audio_m3u8 = download_m3u8(d.audio_url, http_headers=d.http_headers)

    # save remote m3u8 files to disk
    with open(os.path.join(d.temp_folder, 'remote_video.m3u8'), 'w') as f:
        f.write(video_m3u8)

    if 'dash' in d.subtype_list:
        with open(os.path.join(d.temp_folder, 'remote_audio.m3u8'), 'w') as f:
            f.write(audio_m3u8)

    # check if m3u8 file has unsupported protocols
    for m3u8_doc in (video_m3u8, audio_m3u8):
        x = not_supported(m3u8_doc)
        if x:
            log(x, showpopup=True)
            return False

    # check if file is encrypted
    if is_encrypted(video_m3u8) and 'encrypted' not in d.subtype_list:
        # d.subtype_list.append('encrypted')
        d.subtype_list = d.subtype_list + ['encrypted']  # if you use "append" changes will not be reported to "Controller" 

    log(d.subtype_list)

    # ---------------------------------------------------------------------------------------------------------

    # process remote m3u8 files -------------------------------------------------------------------------------
    def process_m3u8(m3u8_doc, stream_type='video'):
        """
        process m3u8 file, extract urls, build local m3u8 file, and build segments for download item
        :param m3u8_doc: m3u8 as a text
        :param stream_type: 'video' or 'audio'
        :return: None
        """

        url = d.eff_url if stream_type == 'video' else d.audio_url

        media_playlist = MediaPlaylist(d, url, m3u8_doc, stream_type)

        segments = media_playlist.create_segment_list()
        d.segments += segments

        # write m3u8 file with absolute paths for debugging
        name = 'remote_video2.m3u8' if stream_type == 'video' else 'remote_audio2.m3u8'
        file_path = os.path.join(d.temp_folder, name)
        with open(os.path.join(d.temp_folder, file_path), 'w') as f:
            f.write(media_playlist.create_remote_m3u8_doc())

        # write local m3u8 file
        name = 'local_video.m3u8' if stream_type == 'video' else 'local_audio.m3u8'
        file_path = os.path.join(d.temp_folder, name)
        with open(os.path.join(d.temp_folder, file_path), 'w') as f:
            f.write(media_playlist.create_local_m3u8_doc())

    # reset segments first
    d.segments = []

    # send video m3u8 file for processing
    process_m3u8(video_m3u8, stream_type='video')

    # send audio m3u8 file for processing
    if 'dash' in d.subtype_list:
        process_m3u8(audio_m3u8, stream_type='audio')

    log('pre_process_hls()> done processing', d.name)

    return True


def post_process_hls(d):
    """ffmpeg will process m3u8 files"""

    log('post_process_hls()> start processing', d.name)

    local_video_m3u8_file = os.path.join(d.temp_folder, 'local_video.m3u8')
    local_audio_m3u8_file = os.path.join(d.temp_folder, 'local_audio.m3u8')

    def process_file(infp, outfp):
        cmd = f'"{config.ffmpeg_actual_path}" -loglevel error -stats -y' \
              f' -protocol_whitelist "file,http,https,tcp,tls,crypto"  ' \
              f'-allowed_extensions ALL ' \
              f'-i "{infp}"'
        fastcmd = cmd + f' -c copy "file:{outfp}"'
        slowcmd = cmd + f' "file:{outfp}"'

        error, output = run_ffmpeg(fastcmd, d)

        if error:
            # retry without "-c copy" parameter, takes longer time
            error, output = run_ffmpeg(slowcmd, d)

            if error:
                log('post_process_hls()> ffmpeg failed:', output)
                return False

    process_file(local_video_m3u8_file, d.temp_file)

    if 'dash' in d.subtype_list:
        process_file(local_audio_m3u8_file, d.audio_file)

    log('post_process_hls()> done processing', d.name)

    return True


def convert_audio(d):
    """
    convert audio formats
    :param d: DownloadItem object
    :return: bool True for success or False when failed
    """
    # famous formats: mp3, aac, wav, ogg
    infile = d.temp_file
    outfile = d.target_file

    # look for compatible formats and use "copy" parameter for faster processing
    cmd1 = f'"{config.ffmpeg_actual_path}" -loglevel error -stats -y -i "{infile}" -acodec copy "{outfile}"'

    # general command, consume time
    cmd2 = f'"{config.ffmpeg_actual_path}" -loglevel error -stats -y -i "{infile}" "{outfile}"'

    # run command1
    error, _ = run_command(cmd1, verbose=True, hide_window=True, d=d)

    if error:
        error, _ = run_command(cmd2, verbose=True, hide_window=True, d=d)

    if error:
        return False
    else:
        return True


# parse m3u8 lines
def parse_m3u8_line(line):
    """extract attributes from m3u8 lines, source youtube-dl, utils.py"""
    # get a dictionary of attributes from line
    # examples:
    # {'TYPE': 'AUDIO', 'GROUP-ID': '160000mp4a.40.2', 'LANGUAGE': 'eng', 'NAME': 'eng'}
    # {'BANDWIDTH': '233728', 'AVERAGE-BANDWIDTH': '233728', 'RESOLUTION': '320x180', 'FRAME-RATE': '25.000', 'VIDEO-RANGE': 'SDR', 'CODECS': 'avc1.42C015,mp4a.40.2', 'AUDIO': '64000mp4a.40.2'}

    info = {}
    for (key, val) in re.findall(r'(?P<key>[A-Z0-9-]+)=(?P<val>"[^"]+"|[^",]+)(?:,|$)', line):
        if val.startswith('"'):
            val = val[1:-1]
        info[key] = val
    return info


def download_m3u8(url, http_headers=config.http_headers):
    data = None
    try:
        # download the manifest from m3u8 file descriptor located at url
        data = download(url, verbose=False, http_headers=http_headers)

        # verify file is m3u8 format
        if data and '#EXT' in repr(data):
            return data

    except Exception as e:
        log(e)

    log('received invalid m3u8 file from server')
    if config.log_level >= 3:
        log('\n---------------------------------------\n', data, '\n---------------------------------------\n')
    return None


def parse_subtitles(m3u8_doc, m3u8_url):
    # check subtitles in master m3u8, for some reasons youtube-dl doesn't recognize subtitles in m3u8 files
    # link: https://www.dplay.co.uk/show/ghost-loop/video/dead-and-breakfast/EHD_297528B
    # if youtube-dl fixes this problem in future, there is no need for this batch
    subtitles = {}
    lines = m3u8_doc.splitlines()
    for i, line in enumerate(lines):
        info = parse_m3u8_line(line)

        # example line with subtitle: #EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="100wvtt.vtt",LANGUAGE="en",NAME="en",AUTOSELECT=YES,DEFAULT=NO,FORCED=NO,URI="exp=1587480854~ac....."
        # example parsed info: {'TYPE': 'SUBTITLES', 'GROUP-ID': '100wvtt.vtt', 'LANGUAGE': 'en', 'NAME': 'en', 'AUTOSELECT': 'YES', 'DEFAULT': 'NO', 'FORCED': 'NO', 'URI': 'exp=1587480854~ac.....'}
        if info.get('TYPE', '').lower() in ('subtitle', 'subtitles'):
            # subtitles = {language1:[sub1, sub2, ...], language2: [sub1, ...]}, where sub = {'url': 'http://x.com/s2', 'ext': 'vtt'}
            language = info.get('LANGUAGE') or info.get('NAME') or f'sub{i}'
            url = info.get('URI')
            if not url: continue

            # get absolute url
            url = urljoin(m3u8_url, url)

            # add sub
            subtitles.setdefault(language, [])  # set default key value if not exist
            subtitles[language].append({'url': url, 'ext': 'vtt'})
            print("{'url': url, 'ext': ext}:", {'url': url, 'ext': 'vtt'})

    return subtitles


def download_sub(lang_name, url, extension, d):
    try:
        file_name = f'{os.path.splitext(d.target_file)[0]}_{lang_name}.{extension}'

        # create download item object for subtitle
        sub_d = DownloadItem()
        sub_d.name = os.path.basename(file_name)
        sub_d.folder = os.path.dirname(file_name)
        sub_d.url = d.url
        sub_d.eff_url = url
        sub_d.type = 'subtitle'
        sub_d.http_headers = d.http_headers

        # if d type is hls video will download subtitle file to check if its type is m3u8 or not
        if 'hls' in d.subtype_list:
            log('downloading subtitle', file_name)
            data = download(url, http_headers=d.http_headers)

            # check if downloaded file is an m3u8 file
            if data and '#EXT' in repr(data):
                sub_d.subtype_list.append('hls')

        # execute_command('start_download', sub_d)

    except Exception as e:
        log('download_subtitle() error', e)


def download_subtitles(subs, d, ext='srt'):
    """
    download subtitles
    :param subs: expecting format template: {language1:[sub1, sub2, ...], language2: [sub1, ...]}, where sub = {'url': 'xxx', 'ext': 'xxx'}
    :param d: DownloadItem object that has the subtitles
    :param ext: subtitle format / extension
    :param http_headers: request http headers
    :return: True if it completed successfully, else False
    """

    for lang, lang_subs in subs.items():
        selected_sub = None
        for sub in lang_subs:
            # print(sub)
            if ext == sub['ext']:
                selected_sub = sub
            elif ext == 'srt' and 'vtt' == sub['ext']:
                # if vtt is available will send it as if it is srt and it will be handled in download_sub by ffmpeg
                sub['ext'] = 'srt'
                selected_sub = sub
        if lang_subs and not selected_sub:
            selected_sub = lang_subs[0]

        if selected_sub:
            download_sub(lang, selected_sub.get('url'), selected_sub.get('ext'), d)


def get_metadata(info):
    # Modified from youtube-dl ffmpeg.py file
    # source: https://github.com/ytdl-org/youtube-dl/blob/9a7e5cb88aa3a80f7b4d37424ca7cb3bd144cdc8/youtube_dl/postprocessor/ffmpeg.py#L433
    metadata = {}

    def add(meta_list, info_list=None):
        if not info_list:
            info_list = meta_list
        if not isinstance(meta_list, (list, tuple)):
            meta_list = (meta_list,)
        if not isinstance(info_list, (list, tuple)):
            info_list = (info_list,)
        for info_f in info_list:
            if info.get(info_f) is not None:
                for meta_f in meta_list:
                    metadata[meta_f] = info[info_f]
                break

    # See [1-4] for some info on media metadata/metadata supported
    # by ffmpeg.
    # 1. https://kdenlive.org/en/project/adding-meta-data-to-mp4-video/
    # 2. https://wiki.multimedia.cx/index.php/FFmpeg_Metadata
    # 3. https://kodi.wiki/view/Video_file_tagging
    # 4. http://atomicparsley.sourceforge.net/mpeg-4files.html

    add('title', ('track', 'title'))
    add('date', 'upload_date')
    add(('description', 'comment'), 'description')
    add('purl', 'webpage_url')
    add('track', 'track_number')
    add('artist', ('artist', 'creator', 'uploader', 'uploader_id'))
    add('genre')
    add('album')
    add('album_artist')
    add('disc', 'disc_number')
    add('show', 'series')
    add('season_number')
    add('episode_id', ('episode', 'episode_id'))
    add('episode_sort', 'episode_number')

    # prepare all metadata as a file content https://ffmpeg.org/ffmpeg-all.html#AC_002d3-Metadata

    def ffmpeg_escape(text):
        # Metadata keys or values containing special characters 
        # (‘=’, ‘;’, ‘#’, ‘\’ and a newline) must be escaped with a backslash ‘\’.
        text = str(text)  # fix passed integers or non string types
        return re.sub(r'(=|;|#|\\|\n)', r'\\\1', text)

    metadata_file_content = ';FFMETADATA1\n'  # file must start with this tag

    # add above tags
    for (name, value) in metadata.items():
        try:
            metadata_file_content += f'{ffmpeg_escape(name)}={ffmpeg_escape(value)}\n'
        except Exception as e:
            log('get_metadata()> error:', 'name, type:', name, type(name), 'value, type:', value, type(value), 'error:', e)

    # add empty line, not necessary, just for better viewing file while debugging
    metadata_file_content += '\n'

    # chapters
    chapters = info.get('chapters', [])
    if chapters:
        for chapter in chapters:
            metadata_file_content += '[CHAPTER]\nTIMEBASE=1/1000\n'
            metadata_file_content += 'START=%d\n' % (chapter['start_time'] * 1000)
            metadata_file_content += 'END=%d\n' % (chapter['end_time'] * 1000)
            chapter_title = chapter.get('title')
            if chapter_title:
                metadata_file_content += 'title=%s\n' % ffmpeg_escape(chapter_title)

            # add empty line, not necessary, just for better viewing file while debugging
            metadata_file_content += '\n'

    return metadata_file_content


def write_metadata(input_file, meta_file):
    file, ext = os.path.splitext(input_file)
    out_file = file + '_2' + ext
    cmd = f'"{config.ffmpeg_actual_path}" -loglevel error -stats -y -i "{input_file}"  -i "{meta_file}" -map_metadata 1 -codec copy "{out_file}"'
    error, output = run_command(cmd, verbose=True)
    if error:
        return False
    else:
        delete_file(input_file)
        rename_file(out_file, input_file)
        return True


class Key(Segment):
    def __init__(self):
        super().__init__(self)
        self.name = None
        self.url = None  # URI
        self.method = None  # encryption method, METHOD: NONE, AES-128, and SAMPLE-AES ,  NONE = no encryption
        self.iv = None
        self.raw_line = None

    def __repr__(self):
        return self.create_line()

    def create_line(self):
        info = parse_m3u8_line(self.raw_line)
        return self.raw_line.replace(info.get('URI', '__NONE__'), self.url)


class MediaPlaylist:
    def __init__(self, d, url, m3u8_doc, stream_type):
        """

        :param d: DownloadItem()
        :param url: m3u8 url
        :param m3u8_doc: string representation of m3u8_doc
        :param stream_type: video or audio
        """
        self.d = d
        self.url = url  # playlist url
        self.m3u8_doc = m3u8_doc
        self.stream_type = stream_type

        self.playlist_version = None
        self.playlist_type = None
        self.media_sequence = None
        self.seg_duration = 0
        self.max_seg_duration = None  # #EXT-X-TARGETDURATION
        self.total_duration = 0
        self.encrypted = False
        self.encryption_type = None
        self.current_key = None
        self.segments = []
        self.parse_m3u8_doc()

    def parse_m3u8_doc(self):
        """read m3u8 file and build segments and encryption keys"""
        lines = self.m3u8_doc.splitlines()
        lines = [line.strip() for line in lines if line.strip()]

        for i, line in enumerate(lines):

            if line.startswith('#EXT-X-VERSION'):
                self.playlist_version = line.split(':')[1]
            elif line.startswith('#EXT-X-PLAYLIST-TYPE'):
                self.playlist_type = line.split(':')[1]
            elif line.startswith('#EXT-X-MEDIA-SEQUENCE'):
                self.media_sequence = line.split(':')[1]
            elif line.startswith('#EXT-X-TARGETDURATION'):
                self.max_seg_duration = line.split(':')[1]

            elif line.startswith('#EXT-X-KEY'):
                key = Key()
                key.raw_line = line
                info = parse_m3u8_line(line)
                key.url = info.get('URI')
                key.method = info.get('METHOD')
                key.iv = info.get('IV')
                if key.method and key.url:
                    if key.url.startswith('skd://'):
                        # replace skd:// with https://
                        key.url = key.url.replace('skd://', 'https://')

                    key.url = urljoin(self.url, key.url)
                    self.encrypted = True
                    self.encryption_type = key.method
                    self.current_key = key

            # stream #EXTINF tag must be followed by stream url
            elif line.startswith('#EXTINF'):
                try:
                    self.seg_duration = float(line.split(':')[1].split(',')[0])
                    self.total_duration += self.seg_duration
                except:
                    pass

                next_line = lines[i + 1]
                seg = Segment()
                seg.media_type = self.stream_type
                seg.url = next_line if not next_line.startswith('#') else None
                seg.duration = self.seg_duration
                seg.key = copy.copy(self.current_key)

                if seg.url:
                    if seg.url.startswith('skd://'):
                        # replace skd:// with https://
                        seg.url = seg.url.replace('skd://', 'https://')

                    seg.url = urljoin(self.url, seg.url)
                    self.segments.append(seg)

            elif line.startswith('#EXT-X-ENDLIST'):
                # print('end of playlist')
                break

        # naming
        for i, seg in enumerate(self.segments):
            seg.name = os.path.join(self.d.temp_folder, f'{self.stream_type}_seg_{i + 1}.ts')

            if seg.key:
                seg.key.name = f'{seg.name}.key'

    def summary(self):
        print('M3u8 playlist')
        print('url:', self.url)
        print('media duration:', self.total_duration // 60, 'minutes')
        print('Encryption:', self.encryption_type)
        print('Number of segments:', len(self.segments))

        for seg in self.segments:
            print(seg)

    def create_m3u8_doc(self, segments):
        lines = []

        # start of playlist
        lines.append('#EXTM3U')

        # general tags
        lines.append(f'#EXT-X-VERSION:{self.playlist_version}')
        lines.append(f'#EXT-X-PLAYLIST-TYPE:{self.playlist_type}')
        lines.append(f'#EXT-X-TARGETDURATION:{self.max_seg_duration}')
        lines.append(f'#EXT-X-MEDIA-SEQUENCE:{self.media_sequence}')

        # segments
        for seg in segments:
            if seg.key:
                lines.append(seg.key.create_line())
            lines.append(f'#EXTINF:{seg.duration},')
            lines.append(seg.url)

        # end of playlist
        lines.append('#EXT-X-ENDLIST')

        m3u8_doc = '\n'.join(lines)
        # print(m3u8_doc)
        return m3u8_doc

    def create_remote_m3u8_doc(self):
        return self.create_m3u8_doc(self.segments)

    def create_local_m3u8_doc(self):
        segments = copy.deepcopy(self.segments)
        for seg in segments:
            seg.url = seg.name.replace('\\', '/')

            if seg.key:
                seg.key.url = seg.key.name.replace('\\', '/')

        return self.create_m3u8_doc(segments)

    def create_segment_list(self):

        merge = 'encrypted' not in self.d.subtype_list  # merge non-encrypted streams only
        temp_file = self.d.temp_file if self.stream_type == 'video' else self.d.audio_file

        segment_list = []
        segments = self.segments.copy()

        # Segment(name=seg_name, num=i, range=None, size=0, url=abs_url, tempfile=d.temp_file, merge=merge)
        for i, seg in enumerate(segments):
            seg_key_pair = [seg]
            if seg.key:
                seg_key_pair.append(seg.key)

            for segment in seg_key_pair:
                segment.num = i
                segment.range = None
                segment.size = 0
                segment.tempfile = temp_file
                segment.merge = merge
                segment_list.append(segment)

        return segment_list


def get_media_info(url=None, info=None, ytdloptions=None, interrupt=False):
    """this is an adapter function for youtube-dl to extract the video(s) information the URL refers to """

    url = url or info.get('url') or info.get('webpage_url')

    # we import youtube-dl in separate thread to minimize startup time, will wait in loop until it gets imported
    if ytdl is None:
        log(f'loading {config.active_video_extractor} ...')
        while not ytdl:
            time.sleep(1)  # wait until module gets imported

    # get global youtube_dl options
    options = get_ytdl_options()

    if ytdloptions:
        options.update(ytdloptions)

    ydl = ytdl.YoutubeDL(options)

    # set interrupt / kill switch
    if interrupt:
        set_interrupt_switch(ydl)

    if not info:
        # fetch info by youtube-dl
        info = ydl.extract_info(url, download=False, process=False)
    try:
        # get media type, refer to youtube-dl/extractor/generic.py
        # possible values: playlist, multi_video, url, and url_transparent
        _type = info.get('_type', 'video')

        # handle types: url and url transparent
        if _type in ('url', 'url_transparent'):
            _url = info.get('url') or info.get('webpage_url') or url
            info = ydl.extract_info(_url, download=False, ie_key=info.get('ie_key'), process=False)
            _type = info.get('_type', 'video')

        # don't process direct links, refer to youtube-dl/extractor/generic.py
        if info.get('direct'):
            log('controller._create_video_playlist()> No streams found')
            info = None

        # process info, avoid playlist / multi_video -------------------------------------------------
        if _type not in ('playlist', 'multi_video') and 'entries' not in info:
            info = ydl.process_ie_result(info, download=False)
    except Exception as e:
        log('video.get_media_info() error:', e, log_level=3)

    return info


def process_video(vid):
    """process video info and refresh Video object properties,
    typically required when video is a part of unprocessed video playlist"""
    try:
        vid.busy = True  # busy flag will be used to show progress bar or a busy mouse cursor
        # vid_info = self._process_video_info(vid.vid_info)
        vid_info = get_media_info(info=vid.vid_info)

        if vid_info:
            vid.vid_info = vid_info
            vid.refresh()

            vid.get_thumbnail()

            log('_process_video_info()> processed url:', vid.url, log_level=3)
            vid.processed = True
        else:
            log('_process_video()> Failed,  url:', vid.url, log_level=3)
    except Exception as e:
        log('_process_video()> error:', e)
        if config.test_mode:
            raise e
    finally:
        vid.busy = False





















