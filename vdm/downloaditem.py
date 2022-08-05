"""
    Vortex Download Manager (VDM)

    Multi-connection internet download manager, based on "LibCurl", and "youtube_dl". Original project, FireDM, by Mahmoud Elshahat.
    :copyright: (c) 2022 by Sixline
    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU GPLv3, see LICENSE.md for more details.
"""

# Download Item Class

import os
import mimetypes
import time
from collections import deque
from threading import Lock
from urllib.parse import urljoin, unquote, urlparse

from .utils import (validate_file_name, get_headers, translate_server_code, log, delete_file, delete_folder, save_json,
                    load_json, get_range_list)
from . import config
from .config import MediaType


class Segment:
    def __init__(self, name=None, num=None, range=None, size=0, url=None, tempfile=None, seg_type='', merge=True,
                 media_type=MediaType.general, d=None):
        self.d = d  # reference to parent download item
        self.name = name  # full path file name
        # self.basename = os.path.basename(self.name)
        self.num = num
        self._range = range  # a list of start and end bytes
        self.size = size
        # todo: change bool (downloaded, and completed) to (isdownloaded, and iscompleted), and down_bytes to downloaded
        self.downloaded = False
        self._down_bytes = 0
        self.completed = False  # done downloading and merging into tempfile
        self.tempfile = tempfile
        self.headers = {}
        self.url = url
        self.seg_type = seg_type
        self.merge = merge
        self.key = None
        self.locked = False  # set True by the worker which is currently downloading this segment
        self.media_type = media_type
        self.retries = 0  # number of download retries

        # override size if range available
        if range:
            self.size = range[1] - range[0] + 1

    @property
    def current_size(self):
        try:
            size = os.path.getsize(self.name)
        except:
            size = 0
        return size

    @property
    def down_bytes(self):
        return self._down_bytes if self._down_bytes > 0 else self.current_size

    @down_bytes.setter
    def down_bytes(self, value):
        self._down_bytes = value

    @property
    def remaining(self):
        return max(self.size - self.current_size, 0)

    @property
    def range(self):
        return self._range

    @range.setter
    def range(self, value):
        self._range = value
        if value:
            self.size = value[1] - value[0] + 1

    @property
    def basename(self):
        if self.name:
            return os.path.basename(self.name)
        else:
            return 'undefined'

    def get_size(self):
        http_headers = self.d.http_headers if self.d else None
        self.headers = get_headers(self.url, http_headers=http_headers)
        try:
            self.size = int(self.headers.get('content-length', 0))
            print('Segment num:', self.num, 'getting size:', self.size)
        except:
            pass
        return self.size

    def __repr__(self):
        return repr(self.__dict__)


class DownloadItem:
    """base class for download items"""

    def __init__(self, url='', name='', folder=''):
        """initialize

        Args:
            url (str): download link
            name (str): file name including extension e.g. myvideo.mp4
            folder (str): download folder
        """
        # unique name for download item, will be calculated based on name and target folder
        self.uid = None

        self.title = ''  # file name without extension
        self._name = name
        self.extension = ''  # note: filename extension includes a dot, ex: '.mp4'

        self.folder = os.path.abspath(folder)
        self.alternative_temp_folder = config.temp_folder

        self.url = url
        self.eff_url = ''

        self.size = 0
        self._video_size = 0
        self._total_size = 0
        self.resumable = False

        # type and subtypes
        self.type = ''  # general, video, audio
        self.subtype_list = []  # it might contains one or more eg "hls, dash, fragmented, normal"

        self._segment_size = config.SEGMENT_SIZE

        self.live_connections = 0
        self._downloaded = 0
        self._lock = None  # Lock() to access downloaded property from different threads
        self._status = config.Status.cancelled

        self._remaining_parts = 0
        self.total_parts = 0

        # connection status
        self.status_code = 0
        self.status_code_description = ''

        # audio
        self.audio_stream = None
        self.audio_url = None
        self.audio_size = 0
        self.is_audio = False
        self.audio_quality = None

        # media files progress 
        self.video_progress = 0
        self.audio_progress = 0
        self.merge_progress = 0

        # postprocessing callback is a string represent any function name need to be called after done downloading
        # this function must be available or imported in brain.py namespace
        self.callback = ''

        # schedule download
        self.sched = None

        # speed
        self._speed = 0
        self.prev_downloaded_value = 0
        self.speed_buffer = deque()  # store some speed readings for calculating average speed afterwards
        self.speed_timer = 0
        self.speed_refresh_rate = 0.5  # calculate speed every n seconds

        # segments
        self.segments = []

        # fragmented video parameters will be updated from video subclass object / update_param()
        self.fragment_base_url = None
        self.fragments = None

        # fragmented audio parameters will be updated from video subclass object / update_param()
        self.audio_fragment_base_url = None
        self.audio_fragments = None

        # protocol
        self.protocol = ''

        # format id, youtube-dl specific
        self.format_id = None
        self.audio_format_id = None

        # quality for video and audio
        self.abr = None
        self.tbr = None  # for video equal Bandwidth/1000
        self.resolution = None  # for videos only example for 720p: 1280x720

        # hls m3u8 manifest url
        self.manifest_url = ''

        # thumbnails
        self.thumbnail_url = None
        self.thumbnail = None  # base64 string

        # playlist info
        self.playlist_url = ''
        self.playlist_title = ''

        # selected stream name for video objects
        self.selected_quality = None

        # subtitles
        # template: {language1:[sub1, sub2, ...], language2: [sub1, ...]}, where sub = {'url': 'xxx', 'ext': 'xxx'}
        self.subtitles = {}
        self.automatic_captions = {}
        self.selected_subtitles = {}  # chosen subtitles that will be downloaded

        # accept html contents
        self.accept_html = False  # if server sent html contents instead of bytes

        # errors
        self.errors = 0  # an indicator for server, network, or other errors while downloading

        # subprocess references
        self.subprocess = None

        # test
        self.seg_names = []

        # http-headers
        self.http_headers = {}

        # metadata
        self.metadata_file_content = ''
        
        # shutdown computer after completing download
        self.shutdown_pc = False

        # custom command to run in terminal after completing download
        self.on_completion_command = ''

        self.segments_progress = []
        self.segments_progress_bool = []

        # properties names that will be saved on disk
        self.saved_properties = ['_name', 'folder', 'url', 'eff_url', 'playlist_url', 'playlist_title', 'size',
                                 'resumable', 'selected_quality', '_segment_size', '_downloaded', '_status',
                                 '_remaining_parts', 'total_parts', 'audio_url', 'audio_size', 'type', 'subtype_list', 'fragments',
                                 'fragment_base_url', 'audio_fragments', 'audio_fragment_base_url',
                                 '_total_size', 'protocol', 'manifest_url', 'selected_subtitles',
                                 'abr', 'tbr', 'format_id', 'audio_format_id', 'resolution', 'audio_quality',
                                 'http_headers', 'metadata_file_content', 'title', 'extension', 'sched', 'thumbnail_url']

        # property to indicate a time consuming operation is running on download item now
        self.busy = False

    def __repr__(self):
        return f'DownloadItem object(name:{self.name}, url:{self.url})'

    @property
    def remaining_parts(self):
        return self._remaining_parts

    @remaining_parts.setter
    def remaining_parts(self, value):
        self._remaining_parts = value

        # should recalculate total size again with every completed segment, most of the time segment size won't be
        # available until actually downloaded this segment, "check worker.report_completed()"
        self.total_size = self.calculate_total_size()

    @property
    def video_size(self):
        return self._video_size or self.size

    @video_size.setter
    def video_size(self, value):
        self._video_size = value

    @property
    def total_size(self):
        # recalculate total size only if there is size change in segment size
        if not self._total_size:
            self._total_size = self.calculate_total_size()

        return self._total_size

    @total_size.setter
    def total_size(self, value):
        self._total_size = value

    @property
    def speed(self):
        """average speed"""
        if self.status != config.Status.downloading:  # or not self.speed_buffer:
            self._speed = 0
        else:
            if not self.prev_downloaded_value:
                self.prev_downloaded_value = self.downloaded

            time_passed = time.time() - self.speed_timer
            if time_passed >= self.speed_refresh_rate:
                self.speed_timer = time.time()
                delta = self.downloaded - self.prev_downloaded_value
                self.prev_downloaded_value = self.downloaded
                _speed = delta / time_passed
                if _speed >= 0:
                    # to get a stable speed reading will use an average of multiple speed readings
                    self.speed_buffer.append(_speed)
                avg_speed = sum(self.speed_buffer) / len(self.speed_buffer)
                if len(self.speed_buffer) >= 10:
                    self.speed_buffer.popleft()

                self._speed = int(avg_speed) if avg_speed > 0 else 0

        return self._speed

    @property
    def lock(self):
        # Lock() to access downloaded property from different threads
        if not self._lock:
            self._lock = Lock()
        return self._lock

    @property
    def downloaded(self):
        return self._downloaded

    @downloaded.setter
    def downloaded(self, value):
        """this property might be set from threads, expecting int (number of bytes)"""
        if not isinstance(value, int):
            return

        with self.lock:
            self._downloaded = value

    @property
    def progress(self):
        p = 0

        if self.status == config.Status.completed:
            p = 100

        elif self.total_size == 0 and self.segments:
            if len(self.segments) == 1:
                seg = self.segments[0]
                if seg.completed and seg.current_size == 0:
                    p = 0
            else:
                # to handle fragmented files
                finished = len([seg for seg in self.segments if seg.completed])
                p = round(finished * 100 / len(self.segments), 1)
        elif self.total_size:
            p = round(self.downloaded * 100 / self.total_size, 1)

        # make progress 99% if not completed
        if p >= 100:
            if not self.status == config.Status.completed:
                p = 99
            else:
                p = 100

        return p

    @property
    def eta(self):
        """estimated time remaining to finish download"""
        ret = ''
        try:
            if self.status == config.Status.downloading:
                ret = int((self.total_size - self.downloaded) / self.speed)
        except:
            pass

        return ret

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

        # kill subprocess if currently active
        if self.subprocess and value in (config.Status.cancelled, config.Status.error):
            self.kill_subprocess()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_value):
        # validate new name
        self._name = validate_file_name(new_value)

        self.title, self.extension = os.path.splitext(self._name)

    @property
    def temp_folder(self):
        fp = self.alternative_temp_folder if os.path.isdir(self.alternative_temp_folder) else self.folder
        name = f'vdm_{self.uid}'
        return os.path.join(fp, name)

    @property
    def target_file(self):
        """return file name including path"""
        return os.path.join(self.folder, self.name)

    @property
    def temp_file(self):
        """return temp file name including path"""
        name = f'_temp_{self.name}'.replace(' ', '_')
        return os.path.join(self.temp_folder, name)

    @property
    def audio_file(self):
        """return temp file name including path"""
        name = f'audio_for_{self.name}'.replace(' ', '_')
        return os.path.join(self.temp_folder, name)

    @property
    def segment_size(self):
        return self._segment_size

    @segment_size.setter
    def segment_size(self, value):
        self._segment_size = value if value <= self.size else self.size
        # print('segment size = ', self._segment_size)

    @property
    def video_segments(self):
        return [seg for seg in self.segments if seg.media_type == MediaType.video]

    @property
    def audio_segments(self):
        return [seg for seg in self.segments if seg.media_type == MediaType.audio]

    def select_subs(self, subs_names=None):
        """
        search subtitles names and build a dict of name:url for all selected subs
        :param subs_names: list of subs names
        :return: None
        """
        if not isinstance(subs_names, list):
            return

        subs = {}
        # search for subs
        for k in subs_names:
            v = self.subtitles.get(k) or self.automatic_captions.get(k)
            if v:
                subs[k] = v

        self.selected_subtitles = subs

        # print('self.selected_subtitles:', self.selected_subtitles)

    def calculate_total_size(self):
        # this is heavy and should be used carefully, calculate size by getting every segment's size
        def guess_size(seglist):
            known_sizes = [seg.size for seg in seglist if seg.size]
            unknown_sizes_num = len(seglist) - len(known_sizes)
            tsize = sum(known_sizes)

            # guess remaining segments' sizes
            if known_sizes and unknown_sizes_num:
                avg_seg_size = sum(known_sizes) // len(known_sizes)
                tsize += avg_seg_size * unknown_sizes_num
            return tsize

        total_size = 0

        if self.segments:

            # get video segments
            video_segs = [seg for seg in self.segments if seg.media_type == MediaType.video]

            # get audio segments
            audio_segs = [seg for seg in self.segments if seg.media_type == MediaType.audio]

            # get other segments if any
            other_segs = [seg for seg in self.segments if seg not in (*video_segs, *audio_segs)]

            # calculate sizes
            video_size = guess_size(video_segs)
            audio_size = guess_size(audio_segs)
            othres_size = guess_size(other_segs)

            self.video_size = video_size
            self.audio_size = audio_size
            total_size = video_size + audio_size + othres_size

            self.total_parts = len(self.segments)

        total_size = total_size or self.size

        return total_size

    def kill_subprocess(self):
        """it will kill any subprocess running for this download item, ex: ffmpeg merge video/audio"""
        try:
            # to work subprocess should have shell=False
            self.subprocess.kill()
            log('run_command()> cancelled', self.subprocess.args)
            self.subprocess = None
        except Exception as e:
            log('DownloadItem.kill_subprocess()> error', e)

    def update(self, url):
        """get headers and update properties (eff_url, name, ext, size, type, resumable, status code/description)"""
        # log('*'*20, 'update download item')

        if url in ('', None):
            return

        headers = get_headers(url, http_headers=self.http_headers)
        # print('update d parameters:', headers)

        # update headers
        # print('update()> url, self.url', url, self.url)
        self.url = url
        self.eff_url = headers.get('eff_url')
        self.status_code = headers.get('status_code', '')
        self.status_code_description = f"{self.status_code} - {translate_server_code(self.status_code)}"

        # get file name
        name = ''
        if 'content-disposition' in headers:
            # example 'content-disposition': 'attachment; filename="proxmox-ve_6.3-1.iso"; modification-date="wed, 25 nov 2020 16:51:19 +0100"; size=852299776;'
            # when both "filename" and "filename*" are present in a single header field value, "filename*" should be used
            # more info at https://tools.ietf.org/html/rfc6266

            try:
                content = headers['content-disposition'].split(';')
                match = [x for x in content if 'filename*' in x.lower()]
                if not match:
                    match = [x for x in content if 'filename' in x.lower()]

                name = match[0].split('=')[1].strip('"')
            except:
                pass

        if not name:
            name = headers.get('file-name', '')
        
        if not name:
            # extract name from url
            basename = urlparse(url).path
            name = basename.strip('/').split('/')[-1]

            # decode percent-encoded strings, example 'silver%20bullet' >> 'silver bullet'
            name = unquote(name)

        # file size
        size = int(headers.get('content-length', 0))

        # type
        content_type = headers.get('content-type', '').split(';')[0]

        # file extension:
        ext = os.path.splitext(name)[1]
        if not ext:  # if no ext in file name
            ext = mimetypes.guess_extension(content_type, strict=False) if content_type not in ('N/A', None) else ''

            if ext:
                name += ext

        self.name = name
        self.extension = ext
        self.size = size
        self.type = content_type
        self.resumable = self.is_resumable(url, headers)

        # build segments
        self.build_segments()

        log('headers:', headers, log_level=3)

    def is_resumable(self, url, headers):
        # check resume support / chunk downloading
        resumable = headers.get('accept-ranges', 'none') != 'none'
        size = int(headers.get('content-length', 0))

        if not resumable and size > config.SEGMENT_SIZE:
            # 'status_code': 206, 'content-length': '401', 'content-range': 'bytes 100-500/40772008'
            seg_range = [100, 500]  # test range 401 bytes
            h = get_headers(url, seg_range=seg_range, http_headers=self.http_headers)

            if h.get('status_code') == 206 and int(h.get('content-length', 0)) == 401:
                resumable = True

        return resumable

    def delete_tempfiles(self, force_delete=False):
        """delete temp files and folder for a given download item"""

        if force_delete or not config.keep_temp:
            delete_folder(self.temp_folder)
            delete_file(self.temp_file)
            delete_file(self.audio_file)

    def build_segments(self):
        # log('-'*20, 'build segments')
        # don't handle hls videos
        if 'hls' in self.subtype_list:
            return

            # handle fragmented video
        if self.fragments:
            # print(self.fragments)
            # example 'fragments': [{'path': 'range/0-640'}, {'path': 'range/2197-63702', 'duration': 9.985},]
            _segments = [Segment(name=os.path.join(self.temp_folder, str(i)), num=i, range=None, size=0,
                                 url=urljoin(self.fragment_base_url, x.get('path', '')), tempfile=self.temp_file,
                                 media_type=MediaType.video)
                         for i, x in enumerate(self.fragments)]

        else:
            # general files or video files with known sizes and resumable
            if self.resumable and self.size:
                # get list of ranges i.e. [[0, 100], [101, 2000], ... ]
                range_list = get_range_list(self.size, config.SEGMENT_SIZE)
            else:
                range_list = [None]  # add None in a list to make one segment with range=None

            _segments = [
                Segment(name=os.path.join(self.temp_folder, str(i)), num=i, range=x,
                        url=self.eff_url, tempfile=self.temp_file, media_type=self.type)
                for i, x in enumerate(range_list)]

        # get an audio stream to be merged with dash video
        if 'dash' in self.subtype_list:
            # handle fragmented audio
            if self.audio_fragments:
                # example 'fragments': [{'path': 'range/0-640'}, {'path': 'range/2197-63702', 'duration': 9.985},]
                audio_segments = [
                    Segment(name=os.path.join(self.temp_folder, str(i) + '_audio'), num=i, range=None, size=0,
                            url=urljoin(self.audio_fragment_base_url, x.get('path', '')), tempfile=self.audio_file,
                            media_type=MediaType.audio)
                    for i, x in enumerate(self.audio_fragments)]

            else:
                range_list = get_range_list(self.audio_size, config.SEGMENT_SIZE)

                audio_segments = [
                    Segment(name=os.path.join(self.temp_folder, str(i) + '_audio'), num=i, range=x,
                            url=self.audio_url, tempfile=self.audio_file, media_type=MediaType.audio)
                    for i, x in enumerate(range_list)]

            # append to main list
            _segments += audio_segments

        seg_names = [f'{seg.basename}:{seg.range}' for seg in _segments]
        log(f'Segments-{self.name}, ({len(seg_names)}):', seg_names, log_level=3)

        # pass additional parametrs
        for seg in _segments:
            seg.d = self

        self.segments = _segments

    def save_progress_info(self):
        """save segments info to disk"""
        progress_info = [{'name': seg.name, 'downloaded': seg.downloaded, 'completed': seg.completed, 'size': seg.size,
                          '_range': seg.range, 'media_type': seg.media_type}
                         for seg in self.segments]
        file = os.path.join(self.temp_folder, 'progress_info.txt')
        save_json(file, progress_info)

    def load_progress_info(self):
        """
        load progress info from disk, update segments' info, verify actual segments' size on disk
        :return: None
        """

        # check if file already exist
        if self.status != config.Status.completed and os.path.isfile(self.target_file):
            log('file already exist .............', self.target_file)
            # report completed
            self.status = config.Status.completed 
            self.size = os.path.getsize(self.target_file)
            self.downloaded = self.size
            self.delete_tempfiles()

        # log('load_progress_info()> Loading progress info')
        progress_info = []

        # load progress info from temp folder if exist
        progress_fp = os.path.join(self.temp_folder, 'progress_info.txt')
        if os.path.isfile(progress_fp):
            data = load_json(progress_fp)
            if isinstance(data, list):
                progress_info = data

        # # delete any segment which is not in progress_info file
        # if os.path.isdir(self.temp_folder):
        #     fps = [item.get('name', '') for item in progress_info] + [progress_fp]
        #     for f_name in os.listdir(self.temp_folder):
        #         fp = os.path.join(self.temp_folder, f_name)
        #         if fp not in fps:
        #             delete_file(fp, verbose=True)

        # update segments from progress info
        if progress_info:
            downloaded = 0
            # log('load_progress_info()> Found previous download on the disk')

            # verify segments on disk
            for item in progress_info:
                # reset flags
                item['downloaded'] = False
                item['completed'] = False

                try:
                    size_on_disk = os.path.getsize(item.get('name'))
                    downloaded += size_on_disk
                    if size_on_disk > 0 and size_on_disk == item.get('size'):
                        item['downloaded'] = True
                except:
                    continue

            # for dynamic made segments will build new segments from progress info
            if self.size and self.resumable and not self.fragments and 'hls' not in self.subtype_list:
                self.segments.clear()
                for i, item in enumerate(progress_info):
                    try:
                        seg = Segment()
                        seg.__dict__.update(item)

                        # update tempfile and url
                        if seg.media_type == MediaType.audio:
                            seg.tempfile = self.audio_file
                            seg.url = self.audio_url
                        else:
                            seg.tempfile = self.temp_file
                            seg.url = self.eff_url

                        self.segments.append(seg)
                    except:
                        pass
                log('load_progress_info()> rebuild segments from previous download for:', self.name)

            # for fixed segments will update segments list only
            elif self.segments:
                for seg, item in zip(self.segments, progress_info):
                    if seg.name == item.get('name'):
                        seg.__dict__.update(item)
                log('load_progress_info()> updated current segments for:', self.name)

            # update self.downloaded
            self.downloaded = downloaded

            # update media files progress
            self.update_media_files_progress()

    def update_media_files_progress(self):
        """get the percentage of media files completion, e.g. temp video file, audio file, and final target file

        """

        if self.status == config.Status.completed:
            self.video_progress = 100
            self.audio_progress = 100
            self.merge_progress = 100
            return

        def _get_progress(fp, full_size):
            try:
                current_size = os.path.getsize(fp)
            except:
                current_size = 0

            if current_size == 0 or full_size == 0:
                progress = 0
            else:
                progress = round(current_size * 100 / full_size, 2)

                if progress > 100:
                    progress = 100

            return progress

        self.video_progress = _get_progress(self.temp_file, self.video_size)

        if 'normal' in self.subtype_list:
            self.audio_progress = self.video_progress
        else:
            self.audio_progress = _get_progress(self.audio_file, self.audio_size)
            
        self.merge_progress = _get_progress(self.target_file, self.total_size)

    def update_segments_progress(self, activeonly=False):
        """set self.segments_progress, e.g [total size, [(starting range, length, total file size), ...]]"""
        segments_progress = None

        if self.status == config.Status.completed:
            segments_progress = [100, [(0, 100)]]

        else:
            spb = self.segments_progress_bool
            c = (lambda seg: seg not in spb) if activeonly else (lambda seg: True)  # condition
            total_size = self.total_size

            try:
                # handle hls or fragmented videos
                if any([x in self.subtype_list for x in ('hls', 'fragmented')]):
                    # one hls file might contain more than 5000 segment with unknown sizes
                    # will use segments numbers as a starting point and segment size = 1

                    total_size = len(self.segments)
                    sp = [(self.segments.index(seg), 1) for seg in self.segments if seg.downloaded and c(seg)]

                # handle other video types
                elif self.type == MediaType.video:

                    vid = [(seg.range[0], seg.down_bytes) for seg in self.video_segments if c(seg)]
                    aud = [(seg.range[0] + self.video_size - 1, seg.down_bytes) for seg in self.audio_segments if c(seg)]

                    sp = vid + aud

                # handle non video items
                else:
                    sp = [(seg.range[0], seg.down_bytes) for seg in self.segments if c(seg)]

                sp = [item for item in sp if item[1]]
                spb.extend([seg for seg in self.segments if seg.downloaded])
                segments_progress = [total_size, sp]

            except Exception as e:
                if config.test_mode:
                    log('update_segments_progress()>', e)

        self.segments_progress = segments_progress
        return segments_progress
