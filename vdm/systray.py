"""
    Vortex Download Manager (VDM)

    Multi-connection internet download manager, based on "LibCurl", and "youtube_dl". Original project, FireDM, by Mahmoud Elshahat.
    :copyright: (c) 2022 by Sixline
    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU GPLv3, see LICENSE.md for more details.

    Module description:
        system tray icon based on GTK and pystray, tested on windows and Manjaro using GTK 3.0
"""

import os
import awesometkinter as atk

from . import config
from .iconsbase64 import APP_ICON
from .utils import log, delete_file


class SysTray:
    """
    systray icon using pystray package
    """
    def __init__(self, main_window):
        self.main_window = main_window
        self.tray_icon_path = os.path.join(config.sett_folder, 'systray.png')  # path to icon
        self.icon = None
        self._hover_text = None
        self.Gtk = None
        self.active = False

    def show_main_window(self, *args):
        # unhide and bring on top
        self.main_window.focus()

    def minimize_to_systray(self, *args):
        self.main_window.hide()

    @property
    def tray_icon(self):
        """return pillow image"""
        try:
            img = atk.create_pil_image(b64=APP_ICON, size=48)

            return img
        except Exception as e:
            log('systray: tray_icon', e)
            if config.test_mode:
                raise e

    def run(self):
        # not supported on mac
        if config.operating_system == 'Darwin':
            log('Systray is not supported on mac yet')
            return

        options_map = {'Show': self.show_main_window,
                       'Minimize to Systray': self.minimize_to_systray,
                       'Quit': self.quit}

        # make our own Gtk statusIcon, since pystray failed to run icon properly on Gtk 3.0 from a thread
        if config.operating_system == 'Linux':
            try:
                import gi
                gi.require_version('Gtk', '3.0')
                from gi.repository import Gtk
                self.Gtk = Gtk

                # delete previous icon file (it might contains an icon file for old VDM versions)
                delete_file(self.tray_icon_path)

                # save file to settings folder
                self.tray_icon.save(self.tray_icon_path, format='png')

                # creating menu
                menu = Gtk.Menu()
                for option, callback in options_map.items():
                    item = Gtk.MenuItem(label=option)
                    item.connect('activate', callback)
                    menu.append(item)
                menu.show_all()

                APPINDICATOR_ID = config.APP_NAME

                # setup notify system, will be used in self.notify()
                gi.require_version('Notify', '0.7')
                from gi.repository import Notify as notify
                self.Gtk_notify = notify  # get reference for later deinitialize when quit systray
                self.Gtk_notify.init(APPINDICATOR_ID)  # initialize first

                # try appindicator
                try:
                    gi.require_version('AppIndicator3', '0.1')
                    from gi.repository import AppIndicator3 as appindicator

                    indicator = appindicator.Indicator.new(APPINDICATOR_ID, self.tray_icon_path, appindicator.IndicatorCategory.APPLICATION_STATUS)
                    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
                    indicator.set_menu(menu)

                    # use .set_name to prevent error, Gdk-CRITICAL **: gdk_window_thaw_toplevel_updates: assertion 'window->update_and_descendants_freeze_count > 0' failed
                    indicator.set_name = APPINDICATOR_ID

                    # can set label beside systray icon
                    # indicator.set_label('1.2 MB/s', '')

                    self.active = True
                    log('Systray active backend: Gtk.AppIndicator')
                    Gtk.main()
                    return
                except:
                    pass

                # try GTK StatusIcon
                def icon_right_click(icon, button, time):
                    menu.popup(None, None, None, icon, button, time)

                icon = Gtk.StatusIcon()
                icon.set_from_file(self.tray_icon_path)  # DeprecationWarning: Gtk.StatusIcon.set_from_file is deprecated
                icon.connect("popup-menu", icon_right_click)  # right click
                icon.connect('activate', self.show_main_window)  # left click
                icon.set_name = APPINDICATOR_ID

                self.active = True
                log('Systray active backend: Gtk.StatusIcon')
                Gtk.main()
                return
            except Exception as e:
                log('Systray Gtk 3.0:', e, log_level=2)
                self.active = False
        else:
            # let pystray run for other platforms, basically windows
            try:
                from pystray import Icon, Menu, MenuItem
                items = []
                for option, callback in options_map.items():
                    items.append(MenuItem(option, callback, default=True if option == 'Show' else False))

                menu = Menu(*items)
                self.icon = Icon(config.APP_NAME, self.tray_icon, menu=menu)
                self.active = True
                self.icon.run()
            except Exception as e:
                log('systray: - run() - ', e)
                self.active = False

    def shutdown(self):
        try:
            self.active = False
            self.icon.stop()  # must be called from main thread
        except:
            pass

        try:
            # if we use Gtk notify we should deinitialize
            self.Gtk_notify.uninit()
        except:
            pass

        try:
            # Gtk.main_quit(), if called from a thread might raise 
            # (Gtk-CRITICAL **:gtk_main_quit: assertion 'main_loops != NULL' failed)
            # should call this from main thread
            self.Gtk.main_quit()
        except:
            pass

    def notify(self, msg, title=None):
        """show os notifications, e.g. balloon pop up at systray icon on windows"""
        if getattr(self.icon, 'HAS_NOTIFICATION', False):
            self.icon.notify(msg, title=title)

        else:
            try:
                self.Gtk_notify.Notification.new(title, msg, self.tray_icon_path).show()  # to show notification
            except:
                try:
                    # fallback to plyer
                    import plyer
                    plyer.notification.notify(message=msg, title=title, app_name=config.APP_NAME,
                                              app_icon=self.tray_icon_path, timeout=5)
                except:
                    pass

    def quit(self, *args):
        """callback when selecting quit from systray menu"""
        # thread safe call for main window close
        self.main_window.run_method(self.main_window.quit)

