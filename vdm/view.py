"""
    Vortex Download Manager (VDM)

    Multi-connection internet download manager, based on "LibCurl", and "youtube_dl". Original project, FireDM, by Mahmoud Elshahat.
    :copyright: (c) 2022 by Sixline
    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU GPLv3, see LICENSE.md for more details.

    Module description:
        An interface for All views / GUIs
"""


from abc import ABC, abstractmethod


class IView(ABC):
    @abstractmethod
    def run(self):
        """run view mainloop if any"""
        pass

    @abstractmethod
    def quit(self):
        """quit view mainloop if any"""
        pass

    @abstractmethod
    def update_view(self, **kwargs):
        """update view, it will be called automatically by controller, when a model changes
        this method shouldn't block
        """
        pass

    @abstractmethod
    def get_user_response(self, msg, options, **kwargs):
        """get user choice and send it back to controller, 
        mainly this is a popup window or input() method in terminal

        Args:
            msg(str): a message to show
            options (list): a list of options, example: ['yes', 'no', 'cancel']

        Returns:
            (str): response from user as a selected item from "options"

        Example:
            msg ="File with the same name already exists\n" \
                 "/home/mahmoud/Downloads/7z1900.exe\n" \
                 "Do you want to overwrite file?"

            option = ['Overwrite', 'Cancel']

            get_user_response(msg, options)
        """
        pass
