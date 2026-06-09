import os

import xbmc
import xbmcgui
import xbmcvfs

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

        labels = []
        actions = []

        if xbmc.Player().isPlayingVideo():
            labels.append("倍速控制")
            actions.append("speed")

        labels.append("播放")
        actions.append("play")

        labels.append("删除此记录")
        actions.append("delete")

        choice = xbmcgui.Dialog().contextmenu(labels)
        if choice < 0:
            continue

        action = actions[choice]
        if action == "speed":
            show_speed_control()
            continue
        elif action == "play":
            resume_time = item.get("resume_time", 0) or 0
            total_time = item.get("total_time", 0) or 0
            if resume_time > 0 and total_time > 0 and (resume_time / total_time) < 0.95:
                _play_from_history(db, file_path, resume_time)
            else:
                _play_from_history(db, file_path)
            break
        elif action == "delete":
            db.delete_entry(item["id"])
            items = db.get_history(limit=50)
            xbmcgui.Dialog().notification(ADDON_NAME, "记录已删除", xbmcgui.NOTIFICATION_INFO, 2000)
            if not items:
                xbmcgui.Dialog().ok(ADDON_NAME, "记录已全部删除")
                break


def show_speed_control():
    player = xbmc.Player()
    if not player.isPlayingVideo():
        xbmcgui.Dialog().notification(ADDON_NAME, "没有正在播放的视频", xbmcgui.NOTIFICATION_WARNING, 2000)
        return

    speeds = ["0.25x", "0.5x", "0.75x", "1.0x (正常)", "1.25x", "1.5x", "2.0x", "3.0x"]
    values = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0]

    current = player.getSpeed()
    default = -1
    for i, v in enumerate(values):
        if abs(current - v) < 0.01:
            default = i
            break

    selected = xbmcgui.Dialog().select("选择播放速度 - {:.2f}x (当前)".format(current) if current != 1.0 else "选择播放速度", speeds, preselect=default)
    if selected >= 0:
        player.setSpeed(values[selected])
        xbmcgui.Dialog().notification(ADDON_NAME, "播放速度: {}".format(speeds[selected]), xbmcgui.NOTIFICATION_INFO, 1500)


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


def _play_from_history(db, file_path, resume_time=None):
    if resume_time:
        ret = xbmcgui.Dialog().contextmenu(["从 {} 继续播放".format(_format_time(resume_time)), "从头开始播放"])
        if ret < 0:
            return
        resume = (ret == 0)
    else:
        resume = False

    if not _setup_playlist(file_path):
        xbmc.Player().play(file_path)

    if resume:
        for _ in range(200):
            p = xbmc.Player()
            if p.isPlayingVideo() and p.getTotalTime() > 0:
                p.seekTime(resume_time)
                break
            xbmc.sleep(100)

    _wait_for_playback_end()

    try:
        p = xbmc.Player()
        rtime = p.getTime()
        ttime = p.getTotalTime()
        if rtime > 0:
            db.update_play_stop(file_path, rtime, ttime)
    except Exception:
        pass

    xbmc.sleep(500)
    _navigate_to_dir(file_path)


def _setup_playlist(file_path):
    try:
        dir_path = os.path.dirname(file_path)
        if not dir_path:
            return False

        result = xbmcvfs.listdir(dir_path)
        if not result or len(result) < 2:
            return False

        files = result[1]
        if not files:
            return False

        target = os.path.basename(file_path).lower()
        videos = sorted(
            [f for f in files if os.path.splitext(f)[1].lower() in _VIDEO_EXTS],
            key=str.lower,
        )
        if len(videos) < 2:
            return False

        pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        pl.clear()
        pos = 0
        for i, f in enumerate(videos):
            full = os.path.join(dir_path, f)
            pl.add(full, xbmcgui.ListItem(path=full))
            if f.lower() == target:
                pos = i

        pl.setposition(pos)
        xbmc.Player().play(pl)
        return True
    except Exception:
        return False


_VIDEO_EXTS = frozenset({
    '.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.m4v',
    '.mpg', '.mpeg', '.webm', '.ts', '.ogv', '.3gp', '.divx',
    '.mts', '.m2ts', '.vob', '.iso',
})