"""
    Vortex Download Manager (VDM)

    Multi-connection internet download manager, based on "LibCurl", and "youtube_dl". Original project, FireDM, by Mahmoud Elshahat.
    :copyright: (c) 2022 by Sixline
    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU GPLv3, see LICENSE.md for more details.
"""
import datetime
import os
import io
import hashlib
import time
import re
import importlib
from importlib.util import find_spec
import webbrowser
from threading import Thread
import subprocess
import shlex
import certifi
import shutil
import json
import zipfile
import urllib.request
import platform
import subprocess

# 3rd party
try:
    import pycurl
except:
    print('pycurl not found')

__package__ = 'vdm'

from . import config


def threaded(func):
    """a decorator to run any function / method in a thread
    you can pass threaded=False option when calling the decorated function if you need to disable threadding"""

    def wraper(*args, **kwargs):
        if kwargs.get('threaded', True):
            Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()
        else:
            func(*args, **kwargs)

    return wraper


def thread_after(seconds, func, *args, **kwargs):
    """ run any function / method after certain time delay in a thread"""

    def delayer():
        time.sleep(seconds)
        func(*args, **kwargs)

    Thread(target=delayer, daemon=True).start()


def ignore_errors(func):
    """a decorator to run any function / method in a try-except block to ignore errors"""

    def wraper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            pass

    return wraper


def set_curl_options(c, http_headers=None):
    """take pycurl object as an argument and set basic options

    Args:
        c: pycurl object.
        http_headers: a dictionary of initialization options.

    Return:
        None

    Side effect:
        change  pycurl object "c" inplace
    """
    # use default headers if no http-headers assigned or passed empty headers
    http_headers = http_headers or config.http_headers

    # notes for setopt:  setopt(option, value) ref: https://curl.se/libcurl/c/curl_easy_setopt.html
    # option is an upper case constant, or a number, e.g. pycurl.HTTPPROXYTUNNEL=61
    # curl ref: https://github.com/curl/curl/blob/master/include/curl/curl.h#L1073

    c.setopt(pycurl.USERAGENT, config.http_headers['User-Agent'])

    # http headers must be in a list format
    headers = [f'{k}:{v}' for k, v in http_headers.items()]

    c.setopt(pycurl.HTTPHEADER, headers)

    # set proxy, must be string empty '' means no proxy
    if config.proxy:
        c.setopt(pycurl.PROXY, config.proxy)

    # referer
    if config.referer_url:
        c.setopt(pycurl.REFERER, config.referer_url)
    else:
        c.setopt(pycurl.AUTOREFERER, 1)

    # cookies
    if config.use_cookies:
        c.setopt(pycurl.COOKIEFILE, config.cookie_file_path)

    # website authentication
    if config.username or config.password:
        c.setopt(pycurl.USERNAME, config.username)
        c.setopt(pycurl.PASSWORD, config.password)

    # re-directions
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.MAXREDIRS, 10)

    c.setopt(pycurl.NOSIGNAL, 1)  # option required for multithreading safety
    c.setopt(pycurl.NOPROGRESS, 1)
    c.setopt(pycurl.CAINFO, certifi.where())  # for https sites and ssl cert handling
    c.setopt(pycurl.PROXY_CAINFO, certifi.where())

    # /* set this to 1L to allow HTTP/0.9 responses or 0L to disallow */
    #   CURLOPT(CURLOPT_HTTP09_ALLOWED, CURLOPTTYPE_LONG, 285)
    # c.setopt(285, 1)  # option doesn't exist in pycurl

    # verifies SSL certificate
    # fix for pycurl.error: (43, 'CURLOPT_SSL_VERIFYHOST no longer supports 1 as value!'), issue #183
    # reference: https://curl.haxx.se/libcurl/c/CURLOPT_SSL_VERIFYHOST.html
    if config.ignore_ssl_cert:
        c.setopt(pycurl.SSL_VERIFYPEER, 0)
        c.setopt(pycurl.SSL_VERIFYHOST, 0)

    # time out
    c.setopt(pycurl.CONNECTTIMEOUT, 10)  # limits the connection phase, it has no impact once it has connected.

    # abort if download speed slower than 1024 byte/sec during 10 seconds
    c.setopt(pycurl.LOW_SPEED_LIMIT, 1024)
    c.setopt(pycurl.LOW_SPEED_TIME, 10)

    # verbose
    if config.log_level >= 4:
        c.setopt(pycurl.VERBOSE, 1)
    else:
        c.setopt(pycurl.VERBOSE, 0)

    # it tells curl not to include headers with the body
    c.setopt(pycurl.HEADEROPT, 0)

    c.setopt(pycurl.TIMEOUT, 300)
    c.setopt(pycurl.AUTOREFERER, 1)

    # Accept encoding "compressed content"
    c.setopt(pycurl.ACCEPT_ENCODING, '')


def get_headers(url, verbose=False, http_headers=None, seg_range=None):
    """return dictionary of headers"""

    log('get_headers()> getting headers for:', url, log_level=3)

    curl_headers = {}

    def header_callback(header_line):
        header_line = header_line.decode('iso-8859-1')
        header_line = header_line

        if ':' not in header_line:
            return

        key, value = header_line.split(':', 1)
        key = key.strip().lower()  # lower() key for easy comparison
        value = value.strip()  # don't lower(), it will affect important values, e.g. filename, issue #330
        curl_headers[key] = value
        if verbose:
            print(key, ':', value)

    def write_callback(data):
        return -1  # send terminate flag

    def debug_callback(handle, type, data, size=0, userdata=''):
        """it takes output from curl verbose and pass it to my log function"""
        try:
            log(data.decode("utf-8"))
        except:
            pass
        return 0

    # region curl options
    c = pycurl.Curl()

    # set general curl options
    set_curl_options(c, http_headers)

    # set special curl options
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.WRITEFUNCTION, write_callback)
    c.setopt(pycurl.HEADERFUNCTION, header_callback)

    if seg_range:
        c.setopt(pycurl.RANGE, f'{seg_range[0]}-{seg_range[1]}')  # download segment only not the whole file
    # endregion

    try:
        c.perform()
    except Exception as e:
        # write callback will terminate libcurl to discard the body, we only need the headers, an exception will be
        # raised e.g. (23, 'FFailed writing body') or (23, 'Failure writing output to destination')
        if '23' not in repr(e):
            log('get_headers()>', e)

    # add status code and effective url to headers
    curl_headers['status_code'] = c.getinfo(pycurl.RESPONSE_CODE)
    curl_headers['eff_url'] = c.getinfo(pycurl.EFFECTIVE_URL)

    # return headers
    return curl_headers


def download(url, fp=None, verbose=True, http_headers=None, decode=True, return_buffer=False, seg_range=None):
    """
    simple file download, into bytesio buffer and store it on disk if file_name is given

    Args:
        url: string url/link
        fp(str): output file path
        verbose: bool, log events if true
        http_headers: key, value dict for http headers to be sent to the server
        decode(bool): decode downloaded data, used for text / string type data
        return_buffer(bool): return io.BytesIO() buffer containing downloaded data
        seg_range(iter): list or tuple containing start-byte, end-byte of file range, used if request part of the file

    Return:
        downloaded data
    """

    data = None

    if not url:
        log('download()> url not valid:', url)
        return None

    if verbose:
        log('download()> downloading', url)

    def set_options():
        # set general curl options
        set_curl_options(c, http_headers)

        # set special curl options
        c.setopt(pycurl.URL, url)

        if seg_range:
            c.setopt(pycurl.RANGE, f'{seg_range[0]}-{seg_range[1]}')  # download segment only not the whole file

    # pycurl initialize
    c = pycurl.Curl()
    set_options()

    # create buffer to hold download data
    buffer = io.BytesIO()
    c.setopt(c.WRITEDATA, buffer)

    try:
        # run libcurl
        c.perform()

        # after PyCurl done writing download data into buffer the current "cursor" position is at the end
        # bring position back to start of the buffer
        buffer.seek(0)
        data = buffer.read()

        if fp:
            # save file name
            with open(fp, 'wb') as file:
                file.write(data)
                file.close()

        if decode:
            try:
                data = data.decode()
            except Exception as e:
                if verbose:
                    log('download()> can\'t decode data, will return data as is, details:', e)

    except Exception as e:
        log('download():', e)
    finally:
        # close curl
        c.close()

        if return_buffer:
            buffer.seek(0)
            return buffer
        else:
            return data


def simpledownload(url, fp=None, return_data=True, overwrite=False):
    """download with urllib"""
    if not overwrite and fp and os.path.isfile(fp):
        return

    print('download:', url)
    response = urllib.request.urlopen(url)
    chunk_size = 1024 * 1024 * 5  # 5 MB
    size = response.getheader('content-length')

    if size:
        size = int(size)
        chunk_size = max(size // 10 + (1 if size % 10 else 0), chunk_size)
    data = b''
    done = 0

    while True:
        start = time.time()
        chunk = response.read(chunk_size)
        if chunk:
            data += chunk

            done += len(chunk)

            elapsed_time = time.time() - start

            if elapsed_time:
                speed = format_bytes(round(len(chunk) / elapsed_time, 1), tail='/s')
            else:
                speed = ''
            percent = done * 100 // size if size else 0
            bar_length = percent // 10
            progress_bar = f'[{"=" * bar_length}{" " * (10 - bar_length)}]'
            progress = f'{progress_bar} {format_bytes(done)} of {format_bytes(size)} - {speed}' \
                       f' - {percent}%' if percent else ''
            print(f'\r{progress}            ', end='')
        else:
            print()
            break

    if fp:
        if not os.path.isdir(os.path.dirname(fp)):
            os.makedirs(os.path.dirname(fp))
        with open(fp, 'wb') as f:
            f.write(data)

    if return_data:
        return data
    else:
        return True


my_print=print# replaced on cli mode
def log(*args, log_level=1, start='>> ', end='\n', sep=' ', showpopup=False, **kwargs):
    """print messages to stdout and execute any function or method in config.log_callbacks

    Args:
        args: comma separated messages to be printed
        log_level (int): used to filter messages, 1 to 3 for verbose
        start (str): prefix appended to start of string
        end (str): tail of string
        sep (str): separator used to join text "args"
        showpopup (bool): if True will show popup gui message

    Returns:
        None
        """

    if log_level > config.log_level:
        return

    text = sep.join(map(str, args))

    try:
        my_print(start + text + end, end='', **kwargs)

        # execute registered log callbacks
        if log_level == 1:  # pass only log level 1 messages to gui
            for f in config.log_callbacks:
                f(start, text, end)

        # popup
        if showpopup and config.log_popup_callback:
            config.log_popup_callback(start, text, end)

    except Exception as e:
        my_print(e)


def validate_file_name(fname):
    """clean file name"""

    def replace(c):
        # filter for tkinter safe character range
        if ord(c) not in range(65536):
            return ''
        # The first 32 characters in the ASCII-table are unprintable control codes, 127 epresents the command DEL.
        elif ord(c) < 32 or ord(c) == 127:
            return ''
        elif c in '\'"':
            return ''
        elif c in '~`#$&*()\\|[]{};<>/?!^,:':
            return '_'
        else:
            return c

    try:
        clean_name = ''.join(map(replace, fname))

        # max. allowed filename length 255 on windows,
        # https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file?redirectedfrom=MSDN
        if len(clean_name) > 255:
            clean_name = clean_name[0:245] + clean_name[-10:]  # add last 10 characters "including file extension"
    except:
        clean_name = fname

    return clean_name


def delete_folder(folder, verbose=False):
    try:
        shutil.rmtree(folder)
        if verbose:
            log('done deleting folder:', folder)
        return True
    except Exception as e:
        if verbose:
            log('delete_folder()> ', e)
        return False


def delete_file(file, verbose=False):
    try:
        os.unlink(file)
        if verbose:
            log('done deleting file:', file)
        return True
    except Exception as e:
        if verbose:
            log('delete_file()> ', e)
        return False


def rename_file(oldname=None, newname=None, verbose=False):
    if oldname == newname:
        return True
    elif os.path.isfile(newname):
        log('rename_file()>  destination file already exist')
        return False
    try:
        shutil.move(oldname, newname)
        log('done renaming file:', oldname, '... to:', newname, start='\n', log_level=3)
        return True
    except Exception as e:
        if verbose:
            log('rename_file()> ', e)
        return False


def run_command(cmd, verbose=True, shell=False, hide_window=True, d=None, nonblocking=False,
                ignore_stderr=False, striplines=True):
    """
    run command in a subprocess

    Args:
        cmd: string of actual command to be executed
        verbose: if true will re-route subprocess output to log()
        shell: True or False
        hide_window: True or False, hide shell window
        d: DownloadItem object mainly use "status" property to terminate subprocess
        nonblocking: if True, run subprocess and exit in other words it will not block until finish subprocess
    
    Return:
        error (True or False), output (string of stdout/stderr output)
    """

    # override shell parameter currently can't kill subprocess if shell=True at least on windows, more investigation required
    shell = False

    if verbose:
        log('running command:', cmd, log_level=2)

    error, output = True, f'error running command {cmd}'

    try:

        # split command if shell parameter set to False
        if not shell:
            cmd = shlex.split(cmd)

        # startupinfo to hide terminal window on windows
        if hide_window and platform.system() == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        else:
            startupinfo = None

        # start subprocess using Popen instead of subprocess.run() to get a real-time output
        # since run() gets the output only when finished
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=None if ignore_stderr else subprocess.STDOUT,
                                   encoding='utf-8', errors='replace', shell=shell, startupinfo=startupinfo)

        if nonblocking:
            return

        # update reference in download item, it will be cancelled with status, see DownloadItem.status property setter
        if d:
            d.subprocess = process

        output = ''

        for line in process.stdout:
            if striplines:
                line = line.strip()
            output += line
            if verbose:
                log(line)

            # # monitor kill switch
            # if d and d.status == config.Status.cancelled:
            #     log('terminate run_command()>', cmd)
            #     process.kill()
            # return 1, 'Cancelled by user'

        # wait for subprocess to finish, process.wait() is not recommended
        process.communicate()

        # get return code
        process.poll()
        error = process.returncode  # non zero value indicate an error

    except Exception as e:
        log('error running command: ', e, ' - cmd:', cmd)

    return error, output


def print_object(obj):
    if obj is None:
        print(obj, 'is None')
        return
    for k, v in vars(obj).items():
        try:
            print(k, '=', v)
        except:
            pass


def update_object(obj, new_values):
    """update an object attributes from a supplied dictionary"""
    # avoiding obj.__dict__.update(new_values) as it will set a new attribute if it doesn't exist

    for k, v in new_values.items():
        if hasattr(obj, k):
            try:
                setattr(obj, k, v)
            except AttributeError:  # in case of read only attribute
                log(f"update_object(): can't update property: {k}, with value: {v}")
            except Exception as e:
                log(f'update_object(): error, {e}, property: {k}, value: {v}')
    return obj


def translate_server_code(code):
    """Lookup server code and return a readable code description"""
    server_codes = {

        # Informational.
        100: ('continue',),
        101: ('switching_protocols',),
        102: ('processing',),
        103: ('checkpoint',),
        122: ('uri_too_long', 'request_uri_too_long'),
        200: ('ok', 'okay', 'all_ok', 'all_okay', 'all_good', '\\o/', '✓'),
        201: ('created',),
        202: ('accepted',),
        203: ('non_authoritative_info', 'non_authoritative_information'),
        204: ('no_content',),
        205: ('reset_content', 'reset'),
        206: ('partial_content', 'partial'),
        207: ('multi_status', 'multiple_status', 'multi_stati', 'multiple_stati'),
        208: ('already_reported',),
        226: ('im_used',),

        # Redirection.
        300: ('multiple_choices',),
        301: ('moved_permanently', 'moved', '\\o-'),
        302: ('found',),
        303: ('see_other', 'other'),
        304: ('not_modified',),
        305: ('use_proxy',),
        306: ('switch_proxy',),
        307: ('temporary_redirect', 'temporary_moved', 'temporary'),
        308: ('permanent_redirect',),

        # Client Error.
        400: ('bad_request', 'bad'),
        401: ('unauthorized',),
        402: ('payment_required', 'payment'),
        403: ('forbidden',),
        404: ('not_found', '-o-'),
        405: ('method_not_allowed', 'not_allowed'),
        406: ('not_acceptable',),
        407: ('proxy_authentication_required', 'proxy_auth', 'proxy_authentication'),
        408: ('request_timeout', 'timeout'),
        409: ('conflict',),
        410: ('gone',),
        411: ('length_required',),
        412: ('precondition_failed', 'precondition'),
        413: ('request_entity_too_large',),
        414: ('request_uri_too_large',),
        415: ('unsupported_media_type', 'unsupported_media', 'media_type'),
        416: ('requested_range_not_satisfiable', 'requested_range', 'range_not_satisfiable'),
        417: ('expectation_failed',),
        418: ('im_a_teapot', 'teapot', 'i_am_a_teapot'),
        421: ('misdirected_request',),
        422: ('unprocessable_entity', 'unprocessable'),
        423: ('locked',),
        424: ('failed_dependency', 'dependency'),
        425: ('unordered_collection', 'unordered'),
        426: ('upgrade_required', 'upgrade'),
        428: ('precondition_required', 'precondition'),
        429: ('too_many_requests', 'too_many'),
        431: ('header_fields_too_large', 'fields_too_large'),
        444: ('no_response', 'none'),
        449: ('retry_with', 'retry'),
        450: ('blocked_by_windows_parental_controls', 'parental_controls'),
        451: ('unavailable_for_legal_reasons', 'legal_reasons'),
        499: ('client_closed_request',),

        # Server Error.
        500: ('internal_server_error', 'server_error', '/o\\', '✗'),
        501: ('not_implemented',),
        502: ('bad_gateway',),
        503: ('service_unavailable', 'unavailable'),
        504: ('gateway_timeout',),
        505: ('http_version_not_supported', 'http_version'),
        506: ('variant_also_negotiates',),
        507: ('insufficient_storage',),
        509: ('bandwidth_limit_exceeded', 'bandwidth'),
        510: ('not_extended',),
        511: ('network_authentication_required', 'network_auth', 'network_authentication'),
    }

    return server_codes.get(code, ' ')[0]


def open_file(fp, silent=False):
    """open file with default application, e.g. video files will be played by default video player
    Args:
        fp(str): file path
        silent(bool): if True, ignore subprocess output
    """
    try:
        # file should have non-zero size
        size = os.path.getsize(fp)
        if not size:
            return

        if platform.system() == 'Windows':
            os.startfile(fp)
            return

        if platform.system() == 'Linux':
            cmd = f'xdg-open "{fp}"'

        elif platform.system() == 'Darwin':
            cmd = f'open "{fp}"'

        # run command
        if silent:
            # ignore output, useful when playing video files, to stop player junk to fill up terminal
            subprocess.Popen(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(shlex.split(cmd))

    except Exception as e:
        log('open_file(): ', e, log_level=2)


def open_folder(path):
    """
    open target folder in file manager and select the file if path is file
    
    Args:
        path: path to folder or file

    Return:
        None
    """

    log('utils> open_folder()> ', path, log_level=2)
    try:
        if os.path.isdir(path):
            file = None
            folder = path
        elif os.path.isfile(path):
            file = path
            folder = os.path.dirname(path)
        else:
            # try parent folder
            file = None
            folder = os.path.dirname(path)
            print(folder)

        if platform.system() == 'Windows':
            if file:
                # open folder and select the file
                cmd = f'explorer /select, "{file}"'
                subprocess.Popen(shlex.split(cmd))
            else:
                os.startfile(folder)

        else:
            # linux
            cmd = f'xdg-open "{folder}"'
            subprocess.Popen(shlex.split(cmd))
    except Exception as e:
        log('utils> open_folder()> ', e, log_level=2)


def load_json(fp):
    try:
        with open(fp, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        log('load_json() > error: ', e, fp)


def save_json(fp, data):
    try:
        with open(fp, 'w') as f:
            json.dump(data, f, indent=4)
            return data
    except Exception as e:
        log('save_json() > error: ', e, fp)


def natural_sort(my_list):
    """ Sort the given list in the way that humans expect.
    source: https://blog.codinghorror.com/sorting-for-humans-natural-sort-order/

    Example:
        >>> natural_sort(['c2', 'c10', 'c1'])
        ['c1', 'c2', 'c10']

        # in other hand sorted will give wrong order
        >>> sorted(['c2', 'c10', 'c1'])
        ['c1', 'c10', 'c2']
    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(my_list, key=alphanum_key)


def format_seconds(t, tail='', sep=' ', percision=1, fullunit=False):
    """
        format seconds integer into string with proper time unit

        Args:
            t(int): seconds quantity
            tail(str): optional suffix
            sep(str): separator between number and unit, default is one space
            percision(int): number of digits after decimal point
            fullunit(bool): if True, use full unit name, e.g. "month" instead of "m"

        Return:
            (str): representation of seconds with a proper unit

        Example:
            >>> format_seconds(90)
            '1.5 m'
        """

    result = ''

    try:
        t = int(t)
        units = ['second', 'minute', 'hour', 'day', 'month', 'year'] if fullunit else ['s', 'm', 'h', 'D', 'M', 'Y']
        thresholds = [1, 60, 3600, 86400, 2592000, 31536000]

        if t >= 0:
            for i in range(len(units)):
                threshold = thresholds[i + 1] if i < len(units) - 1 else t + 1
                if t < threshold:
                    unit = units[i]
                    num = round(t / thresholds[i], percision)
                    # remove zeros after decimal point
                    num = int(num) if num % 1 == 0 else num
                    s = 's' if num > 1 and fullunit else ''
                    result = f'{num}{sep}{unit}{s}{tail}'
                    break
    except:
        pass

    return result


def parse_bytes(bytestr):
    """Parse a string indicating a byte quantity into an integer., example format: 536.71KiB, 31.5 mb, etc...
    modified from original source at youtube-dl.common

    Args:
        bytestr(str): byte quantity, e.g. 5 mb, 30k, etc..., unit will be calculated based on the first letter in
        the string, the following letters are ignored, also spaces are stripped

    Return:
        (int): bytes

    Example:
        >>> parse_bytes('30k')
        30720
        >>> parse_bytes('5 mb')
        5242880
        >>> parse_bytes('3 giga bytessss')
        3221225472
    """

    try:
        # if input value is int return it as it is
        if isinstance(bytestr, int):
            return bytestr

        # remove spaces from string
        bytestr = bytestr.replace(' ', '').lower()

        matchobj = re.match(r'(?i)^(\d+(?:\.\d+)?)([kMGTPEZY]\S*)?$', bytestr)
        if matchobj is None:
            return 0
        number = float(matchobj.group(1))
        unit = matchobj.group(2).lower()[0:1] if matchobj.group(2) else ''
        multiplier = 1024.0 ** 'bkmgtpezy'.index(unit)
        return int(round(number * multiplier))
    except:
        return 0


def format_bytes(bytesint, tail='', sep=' ', percision=2):
    """
    format bytes integer into string with proper unit

    Args:
        bytesint(int): bytes quantity
        tail(str): optional suffix
        sep(str): separator between number and unit, default is one space
        percision(int): number of digits after decimal point

    Return:
        (str): representation of bytes with a proper unit

    Example:
        >>> format_bytes(1500)
        '1.46 KB'
    """

    try:
        # Byte, Kilobyte, Megabyte, Gigabyte, Terabyte, Petabyte, Exabyte, Zettabyte, Yottabyte
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
        for i in range(len(units)):
            threshold = 1024 ** (i + 1) if i < len(units) - 1 else bytesint + 1
            if bytesint < threshold:
                unit = units[i]
                num = round(bytesint / (1024 ** i), percision)
                # remove zeros after decimal point
                num = int(num) if num % 1 == 0 else num
                return f'{num}{sep}{unit}{tail}'
    except:
        return bytesint


def is_pkg_exist(pkg_name):
    """
    return True if pkg exist in sys.path and can be imported

    Args:
        pkg_name(str): package name, spaces will be stripped

    >>> is_pkg_exist('   vdm  ')
    True
    >>> is_pkg_exist('blahx123456789x')
    False
    """
    pkg_name = pkg_name.strip()
    if importlib.util.find_spec(pkg_name) is not None:
        return True
    else:
        return False


def auto_rename(file_name, forbidden_names):
    """
    rename file to avoid clash with existing file names

    Args:
        file_name(str): file name without path
        forbidden_names(list, tuple): filenames not allowed to use, e.g. existing files names in same folder, etc...

    Return:
        new name or None

    Example:
        >>> auto_rename('video.mp4', ('video.mp4', 'video_2.mp4'))
        'video_3.mp4'
    """

    name, ext = os.path.splitext(file_name)

    for i in range(2, 1000000):
        new_name = f'{name}_{i}{ext}'
        if new_name not in forbidden_names:
            return new_name


def calc_md5(fp=None, buffer=None):
    """
    calculate md5 hash
        Args:
            fp (str): file path
            buffer (io.buffer): file like object

        Return:
            (str): MD5 hexadecimal string

        Example:
            >>> buf = io.BytesIO(b'hello world!')
            >>> calc_md5(buffer=buf)
            'fc3ff98e8c6a0d3087d515c0473f8677'
    """
    try:
        if fp:
            buffer = open(fp, 'rb')

        md5_hash = hashlib.md5()

        # read file in chunks to save memory in case of big files
        chunk_size = 1024 * 1024  # 1 Megabyte at a time

        while True:
            chunk = buffer.read(chunk_size)
            if not chunk:
                break
            md5_hash.update(chunk)

        if fp:
            buffer.close()

        return md5_hash.hexdigest()

    except Exception as e:
        return f'calc_md5()> error, {str(e)}'


def calc_sha256(fp=None, buffer=None):
    """calculate sha26 hash
    Args:
        fp (str): file path
        buffer (io.buffer): file like object

    Return:
        (str): sha26 hexadecimal string

    Example:
        >>> buf = io.BytesIO(b'hello world!')
        >>> calc_sha256(buffer=buf)
        '7509e5bda0c762d2bac7f90d758b5b2263fa01ccbc542ab5e3df163be08e6ca9'
    """
    try:
        if fp:
            buffer = open(fp, 'rb')

        sha256_hash = hashlib.sha256()

        # read file in chunks to save memory in case of big files
        chunk_size = 1024 * 1024  # 1 Megabyte at a time

        while True:
            chunk = buffer.read(chunk_size)
            if not chunk:
                break
            sha256_hash.update(chunk)

        if fp:
            buffer.close()

        return sha256_hash.hexdigest()

    except Exception as e:
        return f'calc_sha256()> error, {str(e)}'


def calc_md5_sha256(fp=None, buffer=None):
    """calculate both md5 and sha26
    Args:
        fp (str): file path
        buffer (io.buffer): file like object

    Return:
        (str, str): 2-tuple of MD5, SHA256 hexadecimal string

    Example:
        >>> buf = io.BytesIO(b'hello world!')
        >>> calc_md5_sha256(buffer=buf)
        ('fc3ff98e8c6a0d3087d515c0473f8677', '7509e5bda0c762d2bac7f90d758b5b2263fa01ccbc542ab5e3df163be08e6ca9')
    """
    try:
        if fp:
            buffer = open(fp, 'rb')

        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()

        # read file in chunks to save memory in case of big files
        chunk_size = 1024 * 1024  # 1 Megabyte at a time

        while True:
            chunk = buffer.read(chunk_size)
            if not chunk:
                break
            md5_hash.update(chunk)
            sha256_hash.update(chunk)

        if fp:
            buffer.close()

        return md5_hash.hexdigest(), sha256_hash.hexdigest()

    except Exception as e:
        return f'calc_md5_sha256()> error, {str(e)}'


def get_range_list(file_size, minsize):
    """
    return a list of ranges to improve watch while downloading feature
    
    Args:
        file_size(int): file size in bytes
        minsize(int): minimum segment size

    Return:
        list of ranges i.e. [[0, 100], [101, 2000], ... ]

    Example:
        >>> get_range_list(1000000, 102400)
        [[0, 999999]]
        >>> get_range_list(3000000, 102400)
        [[0, 149999], [150000, 449999], [450000, 899999], [900000, 1499999], [1500000, 2999999]]
        >>> get_range_list(0, 102400)
        [None]
    """

    if file_size == 0:
        return [None]
    elif file_size < minsize * 100 / 5:
        return [[0, file_size - 1]]

    range_list = []

    sizes = []
    # make first segments smaller to finish quickly and be ready for watch while 
    # downloading other segments
    for i in (5, 10, 15, 20):  # 5%, 10%, etc..
        sizes.append(i * file_size // 100)
    remaining = file_size - sum(sizes)  # almost 50% remaining
    sizes.append(remaining)

    start = 0
    for s in sizes:
        range_list.append([start, start + s - 1])
        start += s

    return range_list


def run_thread(f, *args, daemon=True, **kwargs):
    """run a callable in a thread

    Args:
        f (callable): any callable need to be run in a thread
        args: f's args
        daemon (bool): Daemon threads are abruptly stopped at shutdown. Their resources (such as open files,
                      database transactions, etc.) may not be released properly. If you want your threads to stop
                      gracefully, make them non-daemonic and use a suitable signalling mechanism
        kwargs: f's kwargs

    Example:
        def foo(name, greetings='hello'):
            print(greetings, name)

        run_thread(foo, 'John', greetings='hi')

    Returns:
        a thread reference
    """

    t = Thread(target=f, args=args, kwargs=kwargs, daemon=daemon)
    t.start()

    return t


def generate_unique_name(*args, prefix='', suffix=''):
    """generate unique name from any number of parameters which have a string representation

    Args:
        args: any arguments that have a string representation
        prefix (str): concatenated at the begining of hashed value
        suffix (str): concatenated at the end of hashed value

    Example:
        >>> generate_unique_name('duck can quack', 'cat', prefix='uid')
        'uid159e7e2ca7a89ee77348f97b4660e56e'

    """

    def get_md5(binary_data):
        return hashlib.md5(binary_data).hexdigest()

    name = ''.join([str(x) for x in args])

    try:
        name = get_md5(name.encode())
    except:
        pass

    return prefix + name + suffix


def open_webpage(url):
    """open webpage in default browser
    Args:
        url(str): webpage url
    """
    try:
        webbrowser.open_new(url)
    except Exception as e:
        log('utils.open_webpage()> error:', e)


def parse_urls(text):
    """parse urls in a text, every url in a separate line, empty lines and lines start with # will be ignored

    Example:
        >>> parse_urls('url1 \\n url2  \\n # comment \\n url3 \\n url2')
        ['url1', 'url2', 'url3']
    """
    urls = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith('#') and line not in urls:
            urls.append(line)
    return urls


def get_pkg_path(pkg_name):
    """get package installation path without importing"""
    spec = find_spec(pkg_name)
    if spec:
        pkg_path = os.path.dirname(spec.origin)
    else:
        pkg_path = None
    return pkg_path


def get_pkg_version(pkg):
    """parse version number for a package
    using .dist-info folder or version.py/version.pyc files

    Args:
        pkg(str): name or path of the package

    Returns:
        (str): version number or empty string
    """

    if os.path.isdir(pkg):
        pkg_path = pkg
    else:
        pkg_name = os.path.basename(pkg)
        pkg_path = get_pkg_path(pkg_name)

    if not pkg_path:
        return ''

    version = ''

    # read version.py file
    try:
        version_module = {}
        fp = os.path.join(pkg_path, 'version.py')
        with open(fp) as f:
            txt = f.read()
            exec(txt, version_module)  # then we can use it as: version_module['__version__']
            version = version_module.get('__version__')
            if not version:
                match = re.search(r'_*version_*=[\'\"](.*?)[\'\"]', txt.replace(' ', ''), re.IGNORECASE)
                version = match.groups()[0]
    except:
        pass

    if not version:
        # read version.pyc file, will be limited to specific versions format, e.g. 2.3.4, or 2021.8.30
        try:
            fp = os.path.join(pkg_path, 'version.pyc')
            with open(fp, 'rb') as f:
                text = f.read()
                match = re.search(rb'\d+\.\d+\.\d+', text)
                version = match.group().decode('utf-8')
        except:
            pass

    if not version:
        # parse .dist-info folder e.g: youtube_dl-2021.5.16.dist-info or VDM-2021.2.9.dist-info
        try:
            parent_folder = os.path.dirname(pkg_path)
            pkg_name = os.path.basename(pkg_path)

            for folder_name in os.listdir(parent_folder):
                match = re.match(pkg_name + r'-(.*?)\.dist-info', folder_name, re.IGNORECASE)
                if match:
                    version = match.groups()[0]
                    break
        except:
            pass

    return version


def import_file(fp, exec_module=True):
    module_name = os.path.basename(fp).replace('.py', '')
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, fp)
    module = importlib.util.module_from_spec(spec)
    if exec_module:
        spec.loader.exec_module(module)
    return module


def zip_extract(z_fp, extract_folder):
    """extract compressed zip file
    Args:
        z_fp(str): zip file path
        extract_folder(str): target folder path
    """
    with zipfile.ZipFile(z_fp, 'r') as z:
        z.extractall(path=extract_folder)


def create_folder(folder_path):
    os.makedirs(folder_path, exist_ok=True)


def get_media_duration(seconds):
    """
        function to convert time (in seconds) to duration of a video or audio
        Args:
            seconds: seconds to be converted to time format
        Return:
            (str): duration string, e.g. 2:46:30
    """
    try:
        # seconds' fraction should be neglected e.g 977.92 should converted to 0:16:17 instead of 0:16:17.920000
        seconds = int(seconds)
        conversion = datetime.timedelta(seconds=seconds)
        result = str(conversion)
    except:
        result = ''

    return result


def check_write_permission(target_folder, create_dirs=True):
    """check target folder for write permission"""

    try:
        if create_dirs:
            os.makedirs(target_folder, exist_ok=True)

        fn = 'vdm-testfile'
        existing_names = os.listdir(target_folder)
        if fn in existing_names:
            fn = auto_rename(fn, existing_names)

        fp = os.path.join(target_folder, fn)

        with open(fp, 'w') as f:
            f.write('#')

        os.unlink(fp)
        success = True
    except:
        success = False

    return success


def read_in_chunks(fn, bytes_range=None, chunk_size=10_485_760, flag='rb'):
    """read bytes range from target file, in chunks to save memory, useful in handling big files
    Args:
        fn(str): file name with full path
        bytes_range(iter): list or tuple of required bytes range,
                           example [2, 4] for file contains b'0123456789', data will be b'234'
        chunk_size(int): size of chunks in bytes, default=10_485_760 = 10Mb
        flag(str): read file flag, e.g. 'r', 'w', 'r+'
    """

    with open(fn, flag) as fh:
        if bytes_range:
            fh.seek(bytes_range[0])

        while True:
            if bytes_range:
                pos = fh.tell()
                if pos > bytes_range[1]:
                    break
                elif pos + chunk_size > bytes_range[1]:
                    chunk_size = bytes_range[1] - pos + 1
            data = fh.read(chunk_size)

            if not data:
                break
            yield data


__all__ = [
    'get_headers', 'download', 'format_bytes', 'format_seconds', 'log', 'validate_file_name', 'delete_folder',
    'run_command', 'print_object', 'update_object', 'translate_server_code', 'open_file', 'delete_file', 'rename_file',
    'load_json', 'save_json', 'natural_sort', 'is_pkg_exist', 'parse_bytes', 'set_curl_options', 'open_folder',
    'auto_rename', 'calc_md5', 'calc_md5_sha256', 'calc_sha256', 'get_range_list',
    'run_thread', 'generate_unique_name', 'open_webpage', 'threaded', 'parse_urls', 'get_media_duration',
    'get_pkg_path', 'get_pkg_version', 'import_file', 'zip_extract', 'create_folder', 'simpledownload', 'ignore_errors',
    'check_write_permission', 'thread_after', 'read_in_chunks'
]

if __name__ == '__main__':
    print('Run doctest ...')
    import doctest

    doctest.testmod(verbose=False)
    print('done ...')
