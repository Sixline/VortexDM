import awesometkinter as atk

# main colors
MAIN_BG = "#1c1c21"
MAIN_FG = "white"

# side frame colors
SF_BG = "#000300"
SF_FG = "white"
SF_BTN_BG = "#d9dc4b"
SF_CHKMARK = "#d9dc4b"

THUMBNAIL_BG = "#000300"  # color of thumbnail frame in Home
THUMBNAIL_FG = "#d9dc4b"  # color of base thumbnail photo
THUMBNAIL_BD = "#d9dc4b"  # thumbnail border color

# progressbar
PBAR_BG = "#26262b"
PBAR_FG = "#d9dc4b"
PBAR_TXT = "white"

ENTRY_BD_COLOR = "#000300"

BTN_BG = "#d9dc4b"
BTN_FG = "black"
BTN_HBG = "#000300"  # highlight background
BTN_ABG = "#000300"  # active background
BTN_AFG = "white"

# heading e.g. "Network:" heading in Settings tab
HDG_BG = "#d9dc4b"
HDG_FG = "black"

# scrollbar
SBAR_BG = "#1c1c21"
SBAR_FG = "white"

# right click menu
RCM_BG = "#1c1c21"
RCM_FG = "white"
RCM_ABG = "#d9dc4b"
RCM_AFG = "black"

# titlebar
TITLE_BAR_BG = "#d9dc4b"
TITLE_BAR_FG = "black"

# selection color for DItem
SEL_BG = "#000300"
SEL_FG = "white"

builtin_themes = {
    "Black & White & Midnight": {
        "MAIN_BG": "white",
        "SF_BG": "Black",
        "SF_BTN_BG": "White",
        "SF_FG": "#f2a541",
        "BTN_BG": "#631d76",
        "BTN_FG": "white",
        "BTN_HBG": "white",
        "RCM_FG": "black",
        "RCM_ABG": "#631d76",
        "RCM_AFG": "white",
        "SEL_BG": "#f2a541",
        "SEL_FG": "black",
        "TITLE_BAR_BG": "#631d76",
        "TITLE_BAR_FG": "white",
    },
    "Black_Grey": {
        "MAIN_BG": "#393939",
        "SF_BG": "#202020",
        "SF_BTN_BG": "#7A7A7A",
        "PBAR_FG": "#06B025",
        "SF_CHKMARK": "#C6C6C6",
        "THUMBNAIL_FG": "#797979",
        "THUMBNAIL_BD": "#797979",
        "BTN_FG": "white",
        "BTN_HBG": "#C6C6C6",
        "BTN_ABG": "#C6C6C6",
        "HDG_FG": "white",
        "SBAR_BG": "#171717",
        "SBAR_FG": "#4D4D4D",
        "RCM_ABG": "#414141",
        "RCM_AFG": "white",
        "SEL_BG": "#004D8A"
    },
    "Black_Grey_Shade-of-Pink": {
        "MAIN_BG": "#444444",
        "SF_BG": "#171717",
        "SF_BTN_BG": "#EDEDED",
        "PBAR_FG": "#DA0037",
        "MAIN_FG": "#EDEDED",
        "SF_FG": "#EDEDED",
        "SF_CHKMARK": "#DA0037",
        "THUMBNAIL_FG": "#DA0037",
        "PBAR_TXT": "#DA0037",
        "BTN_AFG": "#DA0037",
        "SBAR_BG": "#171717",
        "SBAR_FG": "#DA0037",
        "RCM_FG": "#EDEDED",
        "RCM_AFG": "#DA0037",
        "SEL_FG": "#EDEDED",
        "THUMBNAIL_BD": "#EDEDED",
    },
    "Dark": {
        "MAIN_BG": "#1c1c21",
        "SF_BG": "#000300",
        "SF_BTN_BG": "#d9dc4b",
        "THUMBNAIL_FG": "#d9dc4b",
        "PBAR_FG": "#d9dc4b",
        "THUMBNAIL_BD": "#d9dc4b",
    },
    "Gainsboro-SandyBrown-Teal": {
        "MAIN_BG": "#DDDDDD",
        "SF_BG": "#F5A962",
        "SF_BTN_BG": "#3C8DAD",
        "PBAR_FG": "#125D98",
        "SF_FG": "#125D98",
        "SF_CHKMARK": "#125D98",
        "THUMBNAIL_FG": "#125D98",
        "PBAR_TXT": "#125D98",
        "BTN_FG": "#DDDDDD",
        "HDG_FG": "#DDDDDD",
        "SBAR_FG": "#125D98",
        "RCM_FG": "#125D98",
        "RCM_AFG": "#DDDDDD",
        "TITLE_BAR_FG": "#125D98",
        "SEL_FG": "#125D98",
    },
    "Green-Brown": {
        "MAIN_BG": "#3A6351",
        "SF_BG": "#F2EDD7",
        "SF_BTN_BG": "#A0937D",
        "PBAR_FG": "#5F939A",
        "BTN_ABG": "#446d5b",
    },
    "Orange_Black": {
        "SF_BTN_BG": "#e09f3e",
        "PBAR_FG": "#FFFFFF",
        "SF_CHKMARK": "white",
        "PBAR_BG": "#0a0a0a",
        "SBAR_FG": "#e09f3e",
        "MAIN_BG": "#1c1c21",
        "SF_BG": "#000300",
    },
    "Red_Black": {
        "SF_BTN_BG": "#960000",
        "PBAR_FG": "#e09f3e",
        "SF_CHKMARK": "#e09f3e",
        "PBAR_BG": "#0a0a0a",
        "BTN_FG": "white",
        "HDG_FG": "white",
        "SBAR_FG": "#960000",
        "RCM_AFG": "white",
        "MAIN_BG": "#1c1c21",
        "SF_BG": "#000300",
        "TITLE_BAR_FG": "white",
    },
    "White & Black": {
        "MAIN_BG": "white",
        "SF_BG": "white",
        "SF_BTN_BG": "black",
        "PBAR_BG": "white",
        "ENTRY_BD_COLOR": "black",
        "BTN_FG": "white",
        "BTN_AFG": "black",
        "HDG_FG": "white",
        "RCM_FG": "black",
        "RCM_AFG": "white",
        "TITLE_BAR_FG": "white",
        "SEL_BG": "#d8d8d8",
    },
    "White_BlueCryola": {
        "MAIN_BG": "white",
        "SF_BG": "white",
        "SF_BTN_BG": "#2d82b7",
        "SF_CHKMARK": "black",
        "BTN_FG": "white",
        "BTN_HBG": "black",
        "BTN_AFG": "#2d82b7",
        "HDG_FG": "white",
        "SBAR_FG": "#2d82b7",
        "RCM_FG": "black",
        "RCM_AFG": "white",
        "TITLE_BAR_FG": "white",
        "SEL_BG": "#58a7d6",
        "SEL_FG": "white",
    },
    "White_DimGrey_BrightYellowCrayola": {
        "MAIN_BG": "white",
        "SF_BG": "#716969",
        "SF_BTN_BG": "#fbb13c",
        "PBAR_FG": "#fbb13c",
        "SF_CHKMARK": "white",
        "THUMBNAIL_BG": "#fbb13c",
        "BTN_BG": "black",
        "BTN_FG": "white",
        "BTN_ABG": "#fbb13c",
        "HDG_BG": "white",
        "RCM_FG": "black",
        "RCM_ABG": "#716969",
        "RCM_AFG": "white",
        "BTN_AFG": "black",
        "TITLE_BAR_BG": "black",
        "TITLE_BAR_FG": "white",
    },
    "White_RoyalePurple_GoldFusion": {
        "MAIN_BG": "white",
        "SF_BG": "#7d5ba6",
        "SF_BTN_BG": "white",
        "PBAR_FG": "#7d5ba6",
        "THUMBNAIL_BG": "#72705b",
        "BTN_BG": "#72705b",
        "BTN_FG": "white",
        "BTN_HBG": "black",
        "SBAR_FG": "#7d5ba6",
        "RCM_FG": "black",
        "RCM_ABG": "#7d5ba6",
        "RCM_AFG": "white",
        "SEL_BG": "black",
        "TITLE_BAR_BG": "#72705b",
        "TITLE_BAR_FG": "white",
    },
    "White_UpsdellRed_Marigold": {
        "MAIN_BG": "white",
        "SF_BG": "white",
        "SF_BTN_BG": "#b10f2e",
        "SF_CHKMARK": "#eca72c",
        "BTN_FG": "white",
        "BTN_HBG": "black",
        "BTN_AFG": "#b10f2e",
        "HDG_FG": "white",
        "SBAR_FG": "#b10f2e",
        "RCM_FG": "black",
        "RCM_AFG": "white",
        "TITLE_BAR_FG": "white",
        "SEL_BG": "#eca72c",
    },
    "Yellow-Foil-covered Sneakers": {
        "MAIN_BG": "#333652",
        "SF_BG": "#90adc6",
        "SF_BTN_BG": "#fad02c",
        "PBAR_FG": "#e9eaec",
        "MAIN_FG": "#e9eaec",
        "SF_CHKMARK": "#e9eaec",
        "BTN_HBG": "#e9eaec",
        "SBAR_FG": "#90adc6",
        "RCM_FG": "#e9eaec",
        "THUMBNAIL_FG": "#e9eaec",
        "THUMBNAIL_BD": "#e9eaec",
    },

    "White-grey-blue": {
        "MAIN_BG": "#f6f6f6",
        "SF_BG": "#d6cebf",
        "SF_BTN_BG": "#368ee6",
        "PBAR_FG": "#0085ff",
        "BTN_FG": "white",
        "HDG_FG": "white",
        "RCM_FG": "black",
        "TITLE_BAR_FG": "white"
    },
    "White-sky-blue": {
        "MAIN_BG": "#ffffff",
        "SF_BG": "#d0eaff",
        "SF_BTN_BG": "#009ddc",
        "PBAR_FG": "#009ddc",
        "BTN_FG": "white",
        "HDG_FG": "white",
        "RCM_FG": "black",
        "TITLE_BAR_FG": "white"
    },

    "Light-Orange": {
        "MAIN_BG": "white",
        "SF_BG": "#ffad00",
        "SF_BTN_BG": "#006cff",
        "PBAR_FG": "#006cff",
        "THUMBNAIL_FG": "#006cff",
        "HDG_FG": "white",
        "RCM_FG": "black",
        "SBAR_FG": "#ffad00"
    }
}

# key:(reference key, description), reference key will be used to get the color value in case of missing key, but in
# case of some font keys, reference key is refering to background color which will be used to calculate font color
# if reference key is None, this means it can't be calculated if missing
theme_map = {
    'MAIN_BG': (None, 'Main background'),
    'MAIN_FG': ('MAIN_BG', 'Main text color'),
    'SF_BG': (None, 'Side frame background'),
    'SF_BTN_BG': (None, 'Side frame button color'),
    'SF_FG': ('SF_BG', 'Side frame text color'),
    'SF_CHKMARK': ('SF_BTN_BG', 'Side Frame check mark color'),
    'THUMBNAIL_BG': ('SF_BG', 'Thumbnail background'),
    'THUMBNAIL_FG': ('MAIN_FG', 'Default Thumbnail image color'),
    'THUMBNAIL_BD': ('MAIN_FG', 'Thumbnail border color'),
    'PBAR_BG': (None, 'Progressbar inactive ring color'),
    'PBAR_FG': ('MAIN_FG', 'Progressbar active ring color'),
    'PBAR_TXT': ('MAIN_BG', 'Progressbar text color'),
    'ENTRY_BD_COLOR': ('SF_BG', 'Entry widget border color'),
    'BTN_BG': ('SF_BTN_BG', 'Button background'),
    'BTN_FG': ('BTN_BG', 'Button text color'),
    'BTN_HBG': ('SF_BG', 'Button highlight background'),
    'BTN_ABG': ('SF_BG', 'Button active background'),
    'BTN_AFG': ('BTN_ABG', 'Button active text color'),
    'HDG_BG': ('SF_BTN_BG', 'Heading title background'),
    'HDG_FG': ('HDG_BG', 'Heading title text color'),
    'SBAR_BG': ('MAIN_BG', 'Scrollbar background'),
    'SBAR_FG': ('MAIN_FG', 'scrollbar active color'),
    'RCM_BG': ('MAIN_BG', 'Right click menu background'),
    'RCM_FG': ('RCM_BG', 'Right click menu text color'),
    'RCM_ABG': ('BTN_BG', 'Right click menu active background'),
    'RCM_AFG': ('RCM_ABG', 'Right click menu active text color'),
    'TITLE_BAR_BG': ('BTN_BG', 'Window custom titlebar background'),
    'TITLE_BAR_FG': ('BTN_FG', 'Window custom titlebar text color'),
    'SEL_BG': ('SF_BG', 'Download item selection background'),
    'SEL_FG': ('SF_FG', 'Download item selection foreground')}

# fonts keys in theme map
theme_fonts_keys = ('MAIN_FG', 'SF_FG', 'BTN_FG', 'BTN_AFG', 'PBAR_TXT', 'HDG_FG', 'RCM_FG', 'RCM_AFG')


def calculate_missing_theme_keys(theme):
    """calculate missing key colors
    Args:
        theme (dict): theme dictionary
    """

    # make sure we have main keys
    main_keys = ('MAIN_BG', 'SF_BG', 'SF_BTN_BG')
    for key in main_keys:
        theme.setdefault(key, globals()[key])

    # progressbar
    theme.setdefault('PBAR_BG', atk.calc_contrast_color(theme['MAIN_BG'], 10))

    for k, v in theme_map.items():
        if k not in theme_fonts_keys:
            fallback_key = v[0]
            if fallback_key is not None:
                theme.setdefault(k, theme.get(fallback_key, globals()[fallback_key]))

    for key in theme_fonts_keys:
        bg_key = theme_map[key][0]
        bg = theme.get(bg_key, globals()[bg_key])
        theme.setdefault(key, atk.calc_font_color(bg))


def strip_theme(theme):
    """remove any keys that can be calculated, make user themes more compact
        Args:
            theme (dict): theme dictionary

        Return:
            (dict): new stripped theme
    """

    main_keys = ('MAIN_BG', 'SF_BG', 'SF_BTN_BG')
    dummy_theme = {k: theme[k] for k in main_keys}
    calculate_missing_theme_keys(dummy_theme)
    # dummy_theme = {k: v for k, v in dummy_theme.items() if k not in main_keys}
    for k in main_keys:
        dummy_theme[k] = None

    theme = {k: v for k, v in theme.items() if v != dummy_theme[k]}
    return theme


# calculate missing keys for builtin themes
for t in builtin_themes.values():
    calculate_missing_theme_keys(t)

if __name__ == '__main__':
    keys = sorted(builtin_themes.keys())
    for name in keys:
        theme = builtin_themes[name]
        print(f'"{name}": ', '{')
        for k, v in strip_theme(theme).items():
            print(f'    "{k}": "{v}",')
        print('},')
