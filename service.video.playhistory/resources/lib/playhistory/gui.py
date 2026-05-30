import os

import xbmc
import xbmcgui

from .common import ADDON_NAME, log


def _format_time(seconds):
    if not seconds or seconds <= 0:
        return "0:00"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return "{}:{:02d}:{:02d}".format(h, m, s)
    else:
        return "{}:{:02d}".format(m, s)


def _format_datetime(iso_str):
    if not iso_str:
        return ""
    try:
        dt = iso_str.replace("T", " ")
        if "." in dt:
            dt = dt.split(".")[0]
        return dt
    except Exception:
        return iso_str[:19]


def _get_display_title(item):
    title = item.get("title", "")
    if title:
        return title
    file_path = item.get("file_path", "")
    if not file_path:
        return "Unknown"
    name = os.path.basename(file_path)
    name = name.rsplit(".", 1)[0] if "." in name else name
    return name


def show_history(db):
    try:
        items = db.get_history(limit=50)
    except Exception as e:
        xbmcgui.Dialog().ok(ADDON_NAME, "Database error: {}".format(e))
        return
    if not items:
        xbmcgui.Dialog().ok(ADDON_NAME,
            "No playback history yet.\n\n"
            "Check Kodi log for [service.video.playhistory]\n"
            "to verify the service is running.\n\n"
            "Database: {}".format(db._db_path))
        return

    while True:
        list_items = []
        for item in items:
            title = _get_display_title(item)
            total = item.get("total_time", 0) or 0
            resume = item.get("resume_time", 0) or 0
            played = ""
            if total > 0 and resume > 0:
                pct = int((resume / total) * 100)
                played = " ({}%)".format(pct)
            progress = ""
            if total > 0:
                progress = " [{}/{}]".format(_format_time(resume), _format_time(total))
            time_str = _format_datetime(item.get("play_start", ""))
            label = "{}{}{}  {}".format(title, played, progress, time_str)
            list_items.append(label)

        selected = xbmcgui.Dialog().select("{} - Play History".format(ADDON_NAME), list_items)
        if selected < 0:
            break

        item = items[selected]
        file_path = item.get("file_path", "")
        if not file_path:
            continue

        resume_time = item.get("resume_time", 0) or 0
        total_time = item.get("total_time", 0) or 0

        labels = []
        actions = []

        if resume_time > 0 and total_time > 0:
            resume_pct = resume_time / total_time
            if resume_pct < 0.95:
                labels.append("从 {} 继续播放".format(_format_time(resume_time)))
                actions.append("resume")

        labels.append("从头开始播放")
        actions.append("play")

        labels.append("删除此记录")
        actions.append("delete")

        choice = xbmcgui.Dialog().contextmenu(labels)
        if choice < 0:
            continue

        action = actions[choice]
        if action == "resume":
            _play_with_resume(file_path, resume_time)
            break
        elif action == "play":
            _play_from_start(file_path)
            break
        elif action == "delete":
            db.delete_entry(item["id"])
            items = db.get_history(limit=50)
            xbmcgui.Dialog().notification(ADDON_NAME, "记录已删除", xbmcgui.NOTIFICATION_INFO, 2000)
            if not items:
                xbmcgui.Dialog().ok(ADDON_NAME, "记录已全部删除")
                break


def _navigate_to_dir(file_path):
    dir_path = os.path.dirname(file_path)
    if dir_path:
        xbmc.executebuiltin('ActivateWindow(Videos,"{}")'.format(dir_path))


def _wait_for_playback_end():
    player = xbmc.Player()
    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        if not player.isPlayingVideo() and not player.isPlayingAudio():
            break
        if monitor.waitForAbort(1):
            break


def _play_with_resume(file_path, resume_time):
    player = xbmc.Player()
    player.play(file_path)
    wait_ms = 0
    while wait_ms < 8000:
        if player.isPlayingVideo() or player.isPlayingAudio():
            break
        xbmc.sleep(100)
        wait_ms += 100
    if player.isPlayingVideo() or player.isPlayingAudio():
        player.seekTime(resume_time)
    _wait_for_playback_end()
    _navigate_to_dir(file_path)


def _play_from_start(file_path):
    xbmc.Player().play(file_path)
    _wait_for_playback_end()
    _navigate_to_dir(file_path)