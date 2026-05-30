import os
import sys

import xbmc
import xbmcaddon
import xbmcvfs

ADDON = xbmcaddon.Addon("service.video.playhistory")
ADDON_ID = "service.video.playhistory"
ADDON_NAME = ADDON.getAddonInfo("name")
ADDON_VERSION = ADDON.getAddonInfo("version")
ADDON_PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo("path"))


def log(msg, level=xbmc.LOGDEBUG):
    xbmc.log("[{}] {}".format(ADDON_ID, msg), level)


def get_setting(key, default=None):
    if ADDON.getSetting(key) == "":
        return default
    val = ADDON.getSetting(key)
    if val == "true":
        return True
    elif val == "false":
        return False
    try:
        return int(val)
    except ValueError:
        return val


def get_profile_path():
    path = ADDON_PROFILE
    if not os.path.exists(path):
        os.makedirs(path)
    return path
