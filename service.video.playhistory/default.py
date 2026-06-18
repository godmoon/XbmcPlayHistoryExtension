import os
import sys

import xbmc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "resources", "lib"))

from playhistory.common import get_profile_path, ADDON_NAME
from playhistory.database import PlayHistoryDB
from playhistory.gui import show_history

if __name__ == "__main__":
    db_dir = get_profile_path()
    db_path = os.path.join(db_dir, "playhistory.db")
    db = PlayHistoryDB(db_path)
    show_history(db)
