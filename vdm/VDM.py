#!/usr/bin/env python
"""
    Vortex Download Manager (VDM)

    Multi-connection internet download manager, based on "LibCurl", and "youtube_dl". Original project, FireDM, by Mahmoud Elshahat.
    :copyright: (c) 2022 by Sixline
    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU GPLv3, see LICENSE.md for more details.

    Module description:
        This is main application module
"""

# standard modules
import os
import subprocess
import sys
import argparse
import re
import signal

# This code should stay on top to handle relative imports in case of direct call of VDM.py
if __package__ is None:
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(path))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))
    
    __package__ = 'vdm'
    import vdm


# local modules
from . import config, setting
from .controller import Controller
from .tkview import MainWindow
from .cmdview import CmdView
from .utils import parse_urls, parse_bytes, format_bytes
from .setting import load_setting
from .version import __version__


def pars_args(arguments):
    """parse arguments vector
    Args:
        arguments(list): list contains arguments, could be sys.argv[1:] i.e. without script name
    """

    description = """Vortex Download Manager (VDM) is an open-source python Internet download manager
        with a high speed multi-connection engine. It downloads general files and videos from youtube 
        and tons of other streaming websites. 
        Developed in Python, based on "LibCurl", "youtube_dl", and "Tkinter". 
        Source: https://github.com/Sixline/VDM """

    def iterable(txt):
        # process iterable in arguments, e.g. tuple or list,
        # example --window=(600,300)
        return re.findall(r'\d+', txt)

    def int_iterable(txt):
        return map(int, iterable(txt))

    def speed(txt):
        return parse_bytes(txt)

    # region cmdline arguments
    # some args' names are taken from youtube-dl, reference:
    # https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/options.py
    # Note: we should use "default=argparse.SUPPRESS" to discard option if not used by user,
    # and prevent default value overwrite in config module

    parser = argparse.ArgumentParser(
        prog='vdm',
        description=description,
        epilog='copyright: (c) 2022 Vortex Download Manager. license: GNU GPLv3, see LICENSE.md file for more details.'
               'Original project, FireDM, by Mahmoud Elshahat'
               'Isuues: https://github.com/Sixline/VDM/issues',
        usage='\n'
              '%(prog)s [OPTIONS] URL1 URL2 URL3 \n'
              'example: %(prog)s "https://somesite.com/somevideo" "https://somesite.com/anothervideo"\n'
              'Note: to run %(prog)s in GUI(Graphical User Interface) mode, use "--gui" option along with other '
              'arguments, or start %(prog)s without any arguments.',
        add_help=False
    )

    parser.add_argument('url', nargs='*',  # list of urls or empty list
                        help="""url / link of the file you want to download or multiple urls, if url contains special 
                        shell characters e.g. "&", it must be quoted by a single or double quotation to avoid shell 
                        error""")

    # ------------------------------------------------------------------------------------General options---------------
    general = parser.add_argument_group(title='General options')
    general.add_argument(
        '-h', '--help',
        action='help',
        help='show this help message and exit')
    general.add_argument(
        '-v', '--version',
        action='version', version='VDM version: ' + __version__,
        help='Print program version and exit')
    general.add_argument(
        '--show-settings',
        action='store_true', default=argparse.SUPPRESS,
        help='show current application settings and their current values and exit')
    general.add_argument(
        '--edit-config', dest='edit_config',
        type=str, metavar='EDITOR', default=argparse.SUPPRESS,
        action='store', nargs='?', const='nano',  # const if use argument without value
        help='Edit config file, you should specify your text editor executable, otherwise "nano" will be used')
    general.add_argument(
        '--ignore-config', dest='ignore_config', default=argparse.SUPPRESS,
        action='store_true',
        help='Do not load settings from config file. in ~/.config/VDM/ or (APPDATA/VDM/ on Windows)')
    general.add_argument(
        '--dlist', dest='ignore_dlist',
        action='store_false', default=argparse.SUPPRESS,
        help='load/save "download list" from/to  d-list config file. '
             'default="False in cmdline mode and True in GUI mode"')
    general.add_argument(
        '--ignore-dlist', dest='ignore_dlist',
        action='store_true', default=argparse.SUPPRESS,
        help='opposite of "--dlist" option')
    general.add_argument(
        '-g', '--gui',
        action='store_true',  default=argparse.SUPPRESS,
        help='use graphical user interface, same effect if you try running %(prog)s without any parameters')
    general.add_argument(
        '--interactive',
        action='store_true',  default=argparse.SUPPRESS,
        help='interactive command line')
    general.add_argument(
        '--imports-only',
        action='store_true',  default=argparse.SUPPRESS,
        help='import all packages and exit, useful when building AppImage or exe releases, since it '
             'will build pyc files and make application start faster')
    general.add_argument(
        '--persistent',
        action='store_true', default=argparse.SUPPRESS,
        help='save current options in global configuration file, used in cmdline mode.')

    # ----------------------------------------------------------------------------------------Filesystem options--------
    filesystem = parser.add_argument_group(title='Filesystem options')
    filesystem.add_argument(
        '-o', '--output',
        type=str, metavar='<PATH>', default=argparse.SUPPRESS,
        help='output file path, filename, or download folder: if input value is a file name without path, file will '
             f'be saved in current folder, if input value is a folder path only, '
             'remote file name will be used, '
             'be careful with video extension in filename, since ffmpeg will convert video based on extension')
    filesystem.add_argument(
        '-b', '--batch-file', default=argparse.SUPPRESS,
        type=argparse.FileType('r', encoding='UTF-8'), metavar='<PATH>',
        help='path to text file containing multiple urls to be downloaded, file should have '
             'every url in a separate line, empty lines and lines start with "#" will be ignored.')
    filesystem.add_argument(
        '--auto-rename',
        action='store_true', default=argparse.SUPPRESS,
        help=f'auto rename file if same name already exist on disk, default={config.auto_rename}')

    # ---------------------------------------------------------------------------------------Network Options------------
    network = parser.add_argument_group(title='Network Options')
    network.add_argument(
        '--proxy', dest='proxy',
        metavar='URL',  default=argparse.SUPPRESS,
        help='proxy url should have one of these schemes: (http, https, socks4, socks4a, socks5, or socks5h) '
             'e.g. "scheme://proxy_address:port", and if proxy server requires login '
             '"scheme://usr:pass@proxy_address:port", '
             f'examples: "socks5://127.0.0.1:8080",  "socks4://john:pazzz@127.0.0.1:1080", default="{config.proxy}"')

    # ---------------------------------------------------------------------------------------Authentication Options-----
    authentication = parser.add_argument_group(title='Authentication Options')
    authentication.add_argument(
        '-u', '--username',
        dest='username', metavar='USERNAME', default=argparse.SUPPRESS,
        help='Login with this account ID')
    authentication.add_argument(
        '-p', '--password',
        dest='password', metavar='PASSWORD', default=argparse.SUPPRESS,
        help='Account password.')

    # --------------------------------------------------------------------------------------Video Options---------------
    vid = parser.add_argument_group(title='Video Options')
    vid.add_argument(
        '--engine', dest='active_video_extractor',
        type=str, metavar='ENGINE', default=argparse.SUPPRESS,
        help="select video extractor engine, available choices are: ('youtube_dl', and 'yt_dlp'), "
             f"default={config.active_video_extractor}")
    vid.add_argument(
        '--quality', dest='quality',
        type=str, metavar='QUALITY', default=argparse.SUPPRESS,
        help="select video quality, available choices are: ('best', '1080p', '720p', '480p', '360p', "
             "and 'lowest'), default=best")
    vid.add_argument(
        '--prefer-mp4', dest='prefer_mp4',
        action='store_true', default=argparse.SUPPRESS,
        help='prefer mp4 streams if available, default=False')

    # --------------------------------------------------------------------------------------Workarounds-----------------
    workarounds = parser.add_argument_group(title='Workarounds')
    workarounds.add_argument(
        '--check-certificate', dest='ignore_ssl_cert',
        action='store_false', default=argparse.SUPPRESS,
        help=f'validate ssl certificate, default="{not config.ignore_ssl_cert}"')
    workarounds.add_argument(
        '--no-check-certificate', dest='ignore_ssl_cert',
        action='store_true', default=argparse.SUPPRESS,
        help=f'ignore ssl certificate validation, default="{config.ignore_ssl_cert}"')
    workarounds.add_argument(
        '--user-agent',
        metavar='UA', dest='custom_user_agent', default=argparse.SUPPRESS,
        help='Specify a custom user agent')
    workarounds.add_argument(
        '--referer', dest='referer_url',
        metavar='URL', default=argparse.SUPPRESS,
        help='Specify a custom referer, use if the video access is restricted to one domain')

    # --------------------------------------------------------------------------------------Post-processing Options-----
    postproc = parser.add_argument_group(title='Post-processing Options')
    postproc.add_argument(
        '--add-metadata', dest='write_metadata',
        action='store_true', default=argparse.SUPPRESS,
        help=f'Write metadata to the video file, default="{config.write_metadata}"')
    postproc.add_argument(
        '--no-metadata', dest='write_metadata',
        action='store_false', default=argparse.SUPPRESS,
        help=f'Don\'t Write metadata to the video file, default="{not config.write_metadata}"')
    postproc.add_argument(
        '--write-thumbnail', dest='download_thumbnail',
        action='store_true', default=argparse.SUPPRESS,
        help=f'Write thumbnail image to disk after downloading video file, default="{config.download_thumbnail}"')
    postproc.add_argument(
        '--no-thumbnail', dest='download_thumbnail',
        action='store_false', default=argparse.SUPPRESS,
        help='Don\'t Write thumbnail image to disk after downloading video file')
    postproc.add_argument(
        '--checksum', dest='checksum',
        action='store_true', default=argparse.SUPPRESS,
        help=f'calculate checksums for completed files MD5 and SHA256, default="{config.checksum}"')
    postproc.add_argument(
        '--no-checksum', dest='checksum',
        action='store_false', default=argparse.SUPPRESS,
        help='Don\'t calculate checksums')

    # -------------------------------------------------------------------------------------Application Update Options---
    appupdate = parser.add_argument_group(title='Application Update Options')
    appupdate.add_argument(
        '--update',
        action='store_true', dest='update_self', default=argparse.SUPPRESS,
        help='Update this Application and video libraries to latest version.')

    # -------------------------------------------------------------------------------------Downloader Options-----------
    downloader = parser.add_argument_group(title='Downloader Options')
    downloader.add_argument(
        '-R', '--retries', dest='refresh_url_retries',
        type=int, metavar='RETRIES', default=argparse.SUPPRESS,
        help=f'Number of retries to download a file, default="{config.refresh_url_retries}".')
    downloader.add_argument(
        '-l', '--speed-limit', dest='speed_limit',
        type=speed, metavar='LIMIT', default=argparse.SUPPRESS,
        help=f'download speed limit, in bytes per second (e.g. 100K or 5M), zero means no limit, '
             f'current value={format_bytes(config.speed_limit)}.')
    downloader.add_argument(
        '--concurrent', dest='max_concurrent_downloads',
        type=int, metavar='NUMBER', default=argparse.SUPPRESS,
        help=f'max concurrent downloads, default="{config.max_concurrent_downloads}".')
    downloader.add_argument(
        '--connections', dest='max_connections',
        type=int, metavar='NUMBER', default=argparse.SUPPRESS,
        help=f'max download connections per item, default="{config.max_connections}".')

    # -------------------------------------------------------------------------------------Debugging options------------
    debug = parser.add_argument_group(title='Debugging Options')
    debug.add_argument(
        '-V', '--verbose', dest='verbose',
        type=int, metavar='LEVEL', default=argparse.SUPPRESS,
        help=f'verbosity level 1, 2, or 3, default(cmdline mode)=1, default(gui mode)={config.log_level}.')
    debug.add_argument(
        '--keep-temp', dest='keep_temp',
        action='store_true', default=argparse.SUPPRESS,
        help=f'keep temp files for debugging, default="{config.keep_temp}".')
    debug.add_argument(
        '--remove-temp', dest='keep_temp',
        action='store_false', default=argparse.SUPPRESS,
        help='remove temp files after finish')

    # -------------------------------------------------------------------------------------GUI options------------------
    gui = parser.add_argument_group(title='GUI Options')
    gui.add_argument(
        '--theme', dest='current_theme',
        type=str, metavar='THEME', default=argparse.SUPPRESS,
        help=f'theme name, e.g. "Dark", default="{config.current_theme}".')
    gui.add_argument(
        '--monitor-clipboard', dest='monitor_clipboard',
        action='store_true', default=argparse.SUPPRESS,
        help=f'monitor clipboard, and process any copied url, default="{config.monitor_clipboard}".')
    gui.add_argument(
        '--no-clipboard', dest='monitor_clipboard',
        action='store_false', default=argparse.SUPPRESS,
        help='Don\'t monitor clipboard, in gui mode')
    gui.add_argument(
        '--window', dest='window_size',
        type=int_iterable, metavar='(WIDTH,HIGHT)', default=argparse.SUPPRESS,
        help=f'window size, example: --window=(600,400) no space allowed, default="{config.window_size}".')
    # ------------------------------------------------------------------------------------------------------------------
    # endregion

    args = parser.parse_args(arguments)
    sett = vars(args)

    return sett


def main(argv=sys.argv):
    """
    app main
    Args:
        argv(list): command line arguments vector, argv[0] is the script pathname if known
    """

    # workaround for missing stdout/stderr for windows Win32GUI app e.g. cx_freeze gui app
    try:
        sys.stdout.write('\n')
        sys.stdout.flush()
    except AttributeError:
        # dummy class to export a "do nothing methods", expected methods to be called (read, write, flush, close) 
        class Dummy:
            def __getattr__(*args):
                return lambda *args: None

        for x in ('stdout', 'stderr', 'stdin'):
            setattr(sys, x, Dummy())

    guimode = True if len(argv) == 1 or '--gui' in argv else False
    cmdmode = not guimode

    # read config file
    config_fp = os.path.join(config.sett_folder, 'setting.cfg')
    if '--ignore-config' not in argv:
        load_setting()

    sett = pars_args(argv[1:])

    if sett.get('referer_url'):
        sett['use_referer'] = True

    if any((sett.get('username'), sett.get('password'))):
        sett['use_web_auth'] = True

    if sett.get('proxy'):
        sett['enable_proxy'] = True

    if sett.get('output'):
        fp = os.path.realpath(sett.get('output'))
        if os.path.isdir(fp):
            folder = fp
        else:
            folder = os.path.dirname(fp)
            name = os.path.basename(fp)
            if name:
                sett['name'] = name

        if folder:
            sett['folder'] = folder
    elif cmdmode:
        sett['folder'] = os.path.realpath('.')

    verbose = sett.get('verbose')
    if verbose is None and cmdmode:
        sett['log_level'] = 1

    config.__dict__.update(sett)

    if sett.get('config'):
        for key in config.settings_keys:
            value = getattr(config, key)
            print(f'{key}: {value}')
        print('\nconfig file path:', config_fp)
        sys.exit(0)

    if sett.get('edit_config'):
        executable = sett.get('edit_config')
        cmd = f'{executable} {config_fp}'
        subprocess.run(cmd, shell=True)
        sys.exit(0)

    if sett.get('imports_only'):
        import importlib, time
        total_time = 0

        def getversion(mod):
            try:
                version = mod.version.__version__
            except:
                version = ''
            return version

        for module in ['plyer', 'certifi', 'youtube_dl', 'yt_dlp', 'pycurl', 'PIL', 'pystray', 'awesometkinter',
                       'tkinter']:
            start = time.time()

            try:
                m = importlib.import_module(module)
                version = getversion(m)
                total_time += time.time() - start
                print(f'imported module: {module} {version}, in {round(time.time() - start, 1)} sec')
            except Exception as e:
                print(module, 'package import error:', e)

        print(f'Done, importing modules, total time: {round(total_time, 2)} sec ...')
        sys.exit(0)

    # set ignore_dlist argument to True in cmdline mode if not explicitly used
    if sett.get('ignore_dlist') is None and not guimode:
        sett['ignore_dlist'] = True

    controller = None

    def cleanup():
        if guimode or sett.get('persistent'):
            setting.save_setting()
        controller.quit()
        import time
        time.sleep(1)  # give time to other threads to quit

    def signal_handler(signum, frame):
        print('\n\nuser interrupt operation, cleanup ...')
        signal.signal(signum, signal.SIG_IGN)  # ignore additional signals
        cleanup()
        print('\n\ndone cleanup ...')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # ------------------------------------------------------------------------------------------------------------------
    # if running application without arguments will start the gui, otherwise will run application in cmdline
    if guimode:
        # GUI
        controller = Controller(view_class=MainWindow, custom_settings=sett)
        controller.run()
    else:
        controller = Controller(view_class=CmdView, custom_settings=sett)
        controller.run()

        if sett.get('update_self'):
            controller.check_for_update(wait=True, threaded=False)
            sys.exit(0)

        urls = sett.pop('url')  # list of urls or empty list

        if sett.get('batch_file'):
            text = sett['batch_file'].read()
            urls += parse_urls(text)

        if not urls:
            print('No url(s) to download')

        elif sett.get('interactive'):
            for url in urls:
                controller.interactive_download(url, **sett)
        else:
            controller.cmdline_download(urls, **sett)

    cleanup()


if __name__ == '__main__':
    main(sys.argv)

