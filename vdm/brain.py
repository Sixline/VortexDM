"""
    Vortex Download Manager (VDM)

    Multi-connection internet download manager, based on "LibCurl", and "youtube_dl". Original project, FireDM, by Mahmoud Elshahat.
    :copyright: (c) 2022 by Sixline
    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU GPLv3, see LICENSE.md for more details.
"""
import os
import time
from threading import Thread
from queue import Queue
import concurrent.futures

from .video import merge_video_audio, pre_process_hls, post_process_hls, \
    convert_audio, download_subtitles, write_metadata
from . import config
from .config import Status
from .utils import (log, format_bytes, delete_file, rename_file, run_command, read_in_chunks)
from .worker import Worker
from .downloaditem import Segment


def brain(d=None):
    """main brain for a single download, it controls thread manger, file manager
    """

    # set status
    if d.status == Status.downloading:
        log('another brain thread may be running')
        return
    else:
        d.status = Status.downloading

    # first we will remove temp files because file manager is appending segments blindly to temp file
    delete_file(d.temp_file)
    delete_file(d.audio_file)

    # reset downloaded
    d.downloaded = 0

    log('\n')
    log('-' * 50)
    log(f'start downloading file: "{d.name}", size: {format_bytes(d.total_size)}, to: {d.folder}')
    log(f'url: "{d.url}" \n')

    # hls / m3u8 protocols
    if 'hls' in d.subtype_list:
        try:
            success = pre_process_hls(d)
            if not success:
                d.status = Status.error
                return
        except Exception as e:
            d.status = Status.error
            log('pre_process_hls()> error: ', e, showpopup=True)
            if config.test_mode:
                raise e
            return
    else:
        # build segments
        d.build_segments()

    # load progress info
    d.load_progress_info()

    # create some queues to send quit flag to threads
    fpr_q = Queue()
    spr_q = Queue()
    tm_q = Queue()
    fm_q = Queue()

    if d.type == config.MediaType.video:
        # run files processing reporter in a separate thread
        Thread(target=fpr, daemon=True, args=(d, fpr_q)).start()

    Thread(target=spr, daemon=True, args=(d, spr_q)).start()

    # run file manager in a separate thread
    Thread(target=file_manager, daemon=True, args=(d, fm_q)).start()

    # run thread manager in a separate thread
    Thread(target=thread_manager, daemon=True, args=(d, tm_q)).start()

    while True:
        time.sleep(0.1)  # a sleep time to make the program responsive

        if d.status not in Status.active_states:
            log(f'File {d.status}.', log_level=2)
            break

    # check file size
    if os.path.isfile(d.target_file):
        fs = os.path.getsize(d.target_file)
        if fs == 0:
            log('error, nothing downloaded, file size is zero:', d.name)
            d.status = Status.error
            os.unlink(d.target_file)

    # report quitting
    log(f'brain {d.uid}: quitting', log_level=2)
    for q in (spr_q, fpr_q, tm_q, fm_q):
        q.put('quit')

    log('-' * 50, '\n', log_level=2)


def file_manager(d, q, keep_segments=True):
    """write downloaded segments to a single file, and report download completed"""

    # create temp folder if it doesn't exist
    if not os.path.isdir(d.temp_folder):
        os.mkdir(d.temp_folder)

    # create temp files, needed for future opening in 'rb+' mode otherwise it will raise file not found error
    temp_files = set([seg.tempfile for seg in d.segments])
    for file in temp_files:
        open(file, 'ab').close()

    # report all blocks
    d.update_segments_progress()

    while True:
        time.sleep(0.1)

        job_list = [seg for seg in d.segments if not seg.completed]

        # sort segments based on ranges, faster in writing to target file
        try:
            if job_list and job_list[0].range:
                # it will raise "TypeError: 'NoneType' object is not subscriptable" if for example video is normal
                # and audio is fragmented, the latter will have range=None
                job_list = sorted(job_list, key=lambda seg: seg.range[0])
        except:
            pass

        for seg in job_list:

            # for segments which have no range, it must be appended to temp file in order, or final file will be
            # corrupted, therefore if the first non completed segment is not "downloaded", will exit loop
            if not seg.downloaded:
                if not seg.range:
                    break
                else:
                    continue

            # append downloaded segment to temp file, mark as completed
            try:
                seg.merge_errors = getattr(seg, 'merge_errors', 0)
                if seg.merge_errors > 10:
                    log('merge max errors exceeded for:', seg.name, seg.last_merge_error)
                    d.status = Status.error
                    break
                elif seg.merge_errors > 0:
                    time.sleep(1)

                if seg.merge:

                    # use 'rb+' mode if we use seek, 'ab' doesn't work, 'rb+' will raise error if file doesn't exist
                    # open/close target file with every segment will avoid operating system buffering, which cause
                    # almost 90 sec wait on some windows machine to be able to rename the file, after close it
                    # fd.flush() and os.fsync(fd) didn't solve the problem
                    if seg.range:
                        target_file = open(seg.tempfile, 'rb+')
                        # must seek exact position, segments are not in order for simple append
                        target_file.seek(seg.range[0])

                        # read file in chunks to save memory  in case of big segments
                        # read the exact segment size, sometimes segment has extra data as a side effect of
                        # auto segmentation
                        chunks = read_in_chunks(seg.name, bytes_range=(0, seg.range[1] - seg.range[0]), flag='rb')
                    else:
                        target_file = open(seg.tempfile, 'ab')
                        chunks = read_in_chunks(seg.name)

                    # write data
                    for chunk in chunks:
                        target_file.write(chunk)

                    # close file
                    target_file.close()

                seg.completed = True
                log('completed segment: ',  seg.basename, log_level=3)

                if not keep_segments and not config.keep_temp:
                    delete_file(seg.name)

            except Exception as e:
                seg.merge_errors += 1
                seg.last_merge_error = e
                log('failed to merge segment', seg.name, ' - ', seg.range, ' - ', e)

                if config.test_mode:
                    raise e

        # all segments already merged
        if not job_list:

            # handle HLS streams
            if 'hls' in d.subtype_list:
                log('handling hls videos')
                # Set status to processing
                d.status = Status.processing

                success = post_process_hls(d)
                if not success:
                    if d.status == Status.processing:
                        d.status = Status.error
                        log('file_manager()>  post_process_hls() failed, file: \n', d.name, showpopup=True)
                    break

            # handle dash video
            if 'dash' in d.subtype_list:
                log('handling dash videos', log_level=2)
                # merge audio and video
                output_file = d.target_file 

                # set status to processing
                d.status = Status.processing
                error, output = merge_video_audio(d.temp_file, d.audio_file, output_file, d)

                if not error:
                    log('done merging video and audio for: ', d.target_file, log_level=2)

                    # delete temp files
                    d.delete_tempfiles()

                else:  # error merging
                    d.status = Status.error
                    log('failed to merge audio for file: \n', d.name, showpopup=True)
                    break

            # handle audio streams
            if d.type == 'audio':
                log('handling audio streams')
                d.status = Status.processing
                success = convert_audio(d)
                if not success:
                    d.status = Status.error
                    log('file_manager()>  convert_audio() failed, file:', d.target_file, showpopup=True)
                    break
                else:
                    d.delete_tempfiles()

            else:
                # final / target file might be created by ffmpeg in case of dash video for example
                if os.path.isfile(d.target_file):
                    # delete temp files
                    d.delete_tempfiles()
                else:
                    # report video progress before renaming temp video file
                    d.update_media_files_progress()
                    
                    # rename temp file
                    success = rename_file(d.temp_file, d.target_file)
                    if success:
                        # delete temp files
                        d.delete_tempfiles()

            # download subtitles
            if d.selected_subtitles:
                Thread(target=download_subtitles, args=(d.selected_subtitles, d)).start()

            # if type is subtitle, will convert vtt to srt
            if d.type == 'subtitle' and 'hls' not in d.subtype_list and d.name.endswith('srt'):
                # ffmpeg file full location
                ffmpeg = config.ffmpeg_actual_path

                input_file = d.target_file
                output_file = f'{d.target_file}2.srt'  # must end with srt for ffmpeg to recognize output format

                log('verifying "srt" subtitle:', input_file, log_level=2)
                cmd = f'"{ffmpeg}" -y -i "{input_file}" "{output_file}"'

                error, _ = run_command(cmd, verbose=True)
                if not error:
                    delete_file(d.target_file)
                    rename_file(oldname=output_file, newname=input_file)
                    log('verified subtitle successfully:', input_file, log_level=2)
                else:
                    # if failed to convert
                    log("couldn't convert subtitle to srt, check file format might be corrupted")

            # write metadata
            if d.metadata_file_content and config.write_metadata:
                log('file manager()> writing metadata info to:', d.name, log_level=2)
                # create metadata file
                metadata_filename = d.target_file + '.meta'

                try:
                    with open(metadata_filename, 'w', encoding="utf-8") as f:
                        f.write(d.metadata_file_content)

                    # let ffmpeg write metadata to file
                    write_metadata(d.target_file, metadata_filename)

                except Exception as e:
                    log('file manager()> writing metadata error:', e)

                finally:
                    # delete meta file
                    delete_file(metadata_filename)

            # at this point all done successfully
            # report all blocks
            d.update_segments_progress()

            d.status = Status.completed
            # print('---------file manager done merging segments---------')
            break

        # change status or get quit signal from brain
        try:
            if d.status != Status.downloading or q.get_nowait() == 'quit':
                # print('--------------file manager cancelled-----------------')
                break
        except:
            pass

    # save progress info for future resuming
    if os.path.isdir(d.temp_folder):
        d.save_progress_info()

    # Report quitting
    log(f'file_manager {d.uid}: quitting', log_level=2)


def thread_manager(d, q):
    """create multiple worker threads to download file segments"""

    #   soft start, connections will be gradually increase over time to reach max. number
    #   set by user, this prevent impact on servers/network, and avoid "service not available" response
    #   from server when exceeding multi-connection number set by server.
    limited_connections = 1

    # create worker/connection list
    all_workers = [Worker(tag=i, d=d) for i in range(config.max_connections)]
    free_workers = set([w for w in all_workers])
    threads_to_workers = dict()

    num_live_threads = 0

    def sort_segs(segs):
        # sort segments based on their range in reverse to use .pop()
        def sort_key(seg):
            if seg.range:
                return seg.range[0]
            else:
                return seg.num

        def sort(_segs):
            return sorted(_segs, key=sort_key, reverse=True)

        try:
            video_segs = [seg for seg in segs if seg.media_type == config.MediaType.video]
            other_segs = [seg for seg in segs if seg not in video_segs]

            # put video at the end of the list to get processed first
            sorted_segs = sort(other_segs) + sort(video_segs)
            # log('sorted seg:', [f'{seg.media_type}-{seg.range}' for seg in sorted_segs])
        except Exception as e:
            sorted_segs = segs
            log('sort_segs error:', e)

        # print('segs:', [f'{seg.media_type}-{seg.num}' for seg in segs])
        # print('sorted_segs:', [f'{seg.media_type}-{seg.num}' for seg in sorted_segs])
        return sorted_segs

    # job_list
    job_list = [seg for seg in d.segments if not seg.downloaded]
    job_list = sort_segs(job_list)

    d.remaining_parts = len(job_list)

    # error track, if receive many errors with no downloaded data, abort
    downloaded = 0
    total_errors = 0
    max_errors = 100
    errors_descriptions = set()  # store unique errors
    error_timer = 0
    error_timer2 = 0
    conn_increase_interval = 0.5
    errors_check_interval = 0.2  # in seconds
    segmentation_timer = 0

    # speed limit
    sl_timer = time.time()

    def clear_error_q():
        # clear error queue
        for _ in range(config.error_q.qsize()):
            errors_descriptions.add(config.error_q.get())

    while True:
        time.sleep(0.001)  # a sleep time to while loop to make the app responsive

        # Failed jobs returned from workers, will be used as a flag to rebuild job_list --------------------------------
        if config.jobs_q.qsize() > 0:
            # rebuild job_list
            job_list = [seg for seg in d.segments if not seg.downloaded and not seg.locked]

            # sort segments based on its ranges smaller ranges at the end
            job_list = sort_segs(job_list)

            # empty queue
            for _ in range(config.jobs_q.qsize()):
                _ = config.jobs_q.get()

        # create new workers if user increases max_connections while download is running
        if config.max_connections > len(all_workers):
            extra_num = config.max_connections - len(all_workers)
            index = len(all_workers)
            for i in range(extra_num):
                index += i
                worker = Worker(tag=index, d=d)
                all_workers.append(worker)
                free_workers.add(worker)

        # allowable connections
        allowable_connections = min(config.max_connections, limited_connections)

        # dynamic connection manager ---------------------------------------------------------------------------------
        # check every n seconds for connection errors
        if time.time() - error_timer >= errors_check_interval:
            error_timer = time.time()
            errors_num = config.error_q.qsize()

            total_errors += errors_num
            d.errors = total_errors  # update errors property of download item

            clear_error_q()

            if total_errors >= 1 and limited_connections > 1:
                limited_connections -= 1
                conn_increase_interval += 1
                error_timer2 = time.time()
                log('Errors:', errors_descriptions, 'Total:', total_errors, log_level=3)
                log('Thread Manager: received server errors, connections limited to:', limited_connections, log_level=3)

            elif limited_connections < config.max_connections and time.time() - error_timer2 >= conn_increase_interval:
                error_timer2 = time.time()
                limited_connections += 1
                log('Thread Manager: allowable connections:', limited_connections, log_level=3)

            # reset total errors if received any data
            if downloaded != d.downloaded:
                downloaded = d.downloaded
                # print('reset errors to zero')
                total_errors = 0
                clear_error_q()

            if total_errors >= max_errors:
                d.status = Status.error

        # speed limit ------------------------------------------------------------------------------------------------
        # wait some time for dynamic connection manager to release all connections
        if time.time() - sl_timer < config.max_connections * errors_check_interval:
            worker_sl = (config.speed_limit // config.max_connections) if config.max_connections else 0
        else:
            worker_sl = (config.speed_limit // allowable_connections) if allowable_connections else 0

        # Threads ------------------------------------------------------------------------------------------------------
        if d.status == Status.downloading:
            if free_workers and num_live_threads < allowable_connections:
                seg = None
                if job_list:
                    seg = job_list.pop()

                # Auto file segmentation, share segments and help other workers
                elif time.time() - segmentation_timer >= 1:
                    segmentation_timer = time.time()

                    # calculate minimum segment size based on speed, e.g. for 3 MB/s speed, and 2 live threads,
                    # worker speed = 1.5 MB/sec, min seg size will be 1.5 x 6 = 9 MB
                    worker_speed = d.speed // num_live_threads if num_live_threads else 0
                    min_seg_size = max(config.SEGMENT_SIZE, worker_speed * 6)

                    filtered_segs = [seg for seg in d.segments if seg.range is not None
                                      and seg.remaining > min_seg_size * 2]

                    # sort segments based on its ranges smaller ranges at the end
                    filtered_segs = sort_segs(filtered_segs)

                    if filtered_segs:
                        current_seg = filtered_segs.pop()

                        # range boundaries
                        start = current_seg.range[0]
                        middle = start + current_seg.current_size + current_seg.remaining // 2
                        end = current_seg.range[1]

                        # assign new range for current segment
                        current_seg.range = [start, middle]

                        # create new segment
                        seg = Segment(name=os.path.join(d.temp_folder, f'{len(d.segments)}'), url=current_seg.url,
                                      tempfile=current_seg.tempfile, range=[middle + 1, end],
                                      media_type=current_seg.media_type)

                        # add to segments
                        d.segments.append(seg)
                        log('-' * 10, f'new segment: {seg.basename} {seg.range}, updated seg {current_seg.basename} '
                                      f'{current_seg.range}, minimum seg size:{format_bytes(min_seg_size)}', log_level=3)

                if seg and not seg.downloaded and not seg.locked:
                    worker = free_workers.pop()
                    # sometimes download chokes when remaining only one worker, will set higher minimum speed and
                    # less timeout for last workers batch
                    if len(job_list) + config.jobs_q.qsize() <= allowable_connections:
                        # worker will abort if speed less than 20 KB for 10 seconds
                        minimum_speed, timeout = 20 * 1024, 10
                    else:
                        minimum_speed = timeout = None  # default as in utils.set_curl_option

                    ready = worker.reuse(seg=seg, speed_limit=worker_sl, minimum_speed=minimum_speed, timeout=timeout)
                    if ready:
                        # check max download retries
                        if seg.retries >= config.max_seg_retries:
                            log('seg:', seg.basename, f'exceeded max. of ({config.max_seg_retries}) download retries,',
                                'try to decrease num of connections in settings and try again')
                            d.status = Status.error
                        else:
                            seg.retries += 1

                            thread = Thread(target=worker.run, daemon=True)
                            thread.start()
                            threads_to_workers[thread] = worker

                            # save progress info for future resuming
                            if os.path.isdir(d.temp_folder):
                                d.save_progress_info()

        # check thread completion
        for thread in list(threads_to_workers.keys()):
            if not thread.is_alive():
                worker = threads_to_workers.pop(thread)
                free_workers.add(worker)

        # update d param -----------------------------------------------------------------------------------------------
        num_live_threads = len(all_workers) - len(free_workers)
        d.live_connections = num_live_threads
        d.remaining_parts = d.live_connections + len(job_list) + config.jobs_q.qsize()

        # Required check if things goes wrong --------------------------------------------------------------------------
        if num_live_threads + len(job_list) + config.jobs_q.qsize() == 0:
            # rebuild job_list
            job_list = [seg for seg in d.segments if not seg.downloaded]
            if not job_list:
                break
            else:
                # remove an orphan locks
                for seg in job_list:
                    seg.locked = False

        # monitor status change or get quit signal from brain ----------------------------------------------------------
        try:
            if d.status != Status.downloading or q.get_nowait() == 'quit':
                break
        except:
            pass

    # update d param
    d.live_connections = 0
    d.remaining_parts = num_live_threads + len(job_list) + config.jobs_q.qsize()
    log(f'thread_manager {d.uid}: quitting', log_level=2)


def fpr(d, q):
    """file processing progress reporter

    Args:
        d: DownloadItem object
    """

    while True:

        d.update_media_files_progress()

        try:
            if d.status not in config.Status.active_states or q.get_nowait() == 'quit':
                break
        except:
            pass

        time.sleep(1)


def spr(d, q):
    """segments progress reporter

    Args:
        d: DownloadItem object
    """

    while True:

        try:
            if d.status not in config.Status.active_states or q.get_nowait() == 'quit':
                break
        except:
            pass

        # report active blocks only
        d.update_segments_progress(activeonly=True)

        time.sleep(1)