import xbmc

from .common import log, get_setting


class PlaybackTracker:
    def __init__(self, db):
        self.db = db
        self.current_file = None
        self.resume_time = 0
        self.total_time = 0
        self.was_playing = False
        self._ready = False

    def poll(self):
        try:
            if not self._ready:
                if not xbmc.Player().isPlayingVideo():
                    self._ready = True
                return

            player = xbmc.Player()
            is_playing = player.isPlayingVideo()

            if is_playing:
                file_path = player.getPlayingFile()
                if not file_path:
                    return

                if file_path != self.current_file:
                    self._on_new_file(file_path, player)
                else:
                    self.resume_time = player.getTime()
                    self.total_time = player.getTotalTime()

                self.was_playing = True

            elif self.was_playing and self.current_file:
                self._on_stop(player)
                self.was_playing = False

        except Exception as e:
            log("poll error: {}".format(e), xbmc.LOGERROR)

    def _on_new_file(self, file_path, player):
        if self.current_file:
            self._on_stop(player)

        title = xbmc.getInfoLabel("Player.Title")
        track_video = get_setting("track_video_only", False)
        if track_video and not player.isPlayingVideo():
            return

        self.current_file = file_path
        self.resume_time = player.getTime()
        self.total_time = player.getTotalTime()

        log("new file: {} title={}".format(file_path, title))
        self.db.add_play_start(file_path, title, "video", get_setting("max_history", 100))

    def _on_stop(self, player):
        file_path = self.current_file
        rtime = self.resume_time
        ttime = self.total_time
        self.current_file = None
        self.resume_time = 0
        self.total_time = 0
        log("stop: file={} resume={} total={}".format(file_path, rtime, ttime))
        if ttime > 0:
            self.db.update_play_stop(file_path, rtime, ttime)
