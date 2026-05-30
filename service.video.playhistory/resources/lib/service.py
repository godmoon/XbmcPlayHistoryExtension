import os
import sys

import xbmc

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from playhistory.common import get_profile_path, log
from playhistory.database import PlayHistoryDB
from playhistory.player import PlaybackTracker

log("service.py loaded", xbmc.LOGINFO)


def run():
    log("run() enter", xbmc.LOGINFO)
    db_dir = get_profile_path()
    db_path = os.path.join(db_dir, "playhistory.db")
    db = PlayHistoryDB(db_path)
    tracker = PlaybackTracker(db)
    monitor = xbmc.Monitor()

    log("Play History service started")

    while not monitor.abortRequested():
        tracker.poll()
        if monitor.waitForAbort(1):
            break

    log("Play History service stopped")


run()
log("exiting service.py", xbmc.LOGINFO)
