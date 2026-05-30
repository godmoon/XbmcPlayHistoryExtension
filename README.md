# Play History — Kodi 播放历史插件

Record playback history with resume support. Automatically tracks every file you play, lets you browse history in reverse chronological order, and resume from where you left off.

自动记录 Kodi 播放历史，支持断点续播。按时间倒序浏览，一键从中断处继续观看。

---

## Features / 功能

- **Auto-recording** — tracks every video/movie/episode you play
- **Resume support** — pick up where you stopped, even after Kodi restart
- **Single record per file** — replaying the same file bumps it to the top and resets resume position
- **Context menu** — click a record to resume, play from start, or delete
- **Background service** — runs automatically when Kodi starts
- **Script entry** — launch from Program add-ons to browse history
- **Bilingual UI** — English and Chinese

---

## Installation / 安装

### From ZIP (recommended)

1. **Build the package** (see [Packaging](#packaging--打包))
2. Open Kodi → **Add-ons** → **Install from zip file**
3. Select the ZIP
4. Restart Kodi (the service starts automatically on boot)

### Manual (development)

```bash
cp -r service.video.playhistory ~/.kodi/addons/
```

---

## Usage / 使用

### Service (automatic)

No action needed. The service starts when Kodi boots and records everything you play. Log entries are tagged `[service.video.playhistory]` in the Kodi log.

### Browse history

**Programs add-ons** → **Play History** → click any entry:

- **Resume** (if < 95% watched) — continues from saved position
- **Play from start**
- **Delete entry**

### History entry format

```
Title (XX%) [MM:SS/HH:MM:SS]  YYYY-MM-DD HH:MM:SS
```

Example: `Breaking Bad S01E01 (45%) [13:37/30:00]  2026-05-30 20:15:00`

---

## Packaging / 打包

Kodi requires ZIP v1.0 format. **Do not use** Python's `zipfile.ZIP_DEFLATED` (creates v2.0, rejected by Kodi).

### Linux / macOS

```bash
rm -f service.video.playhistory-*.zip
cd /path/to/repo
zip -r service.video.playhistory-1.0.3.zip service.video.playhistory/
```

### Windows (PowerShell)

```powershell
Remove-Item .\service.video.playhistory-*.zip -ErrorAction SilentlyContinue
Compress-Archive -Path .\service.video.playhistory -DestinationPath .\service.video.playhistory-1.0.3.zip
```

### Verify

```bash
unzip -l service.video.playhistory-1.0.3.zip | head -5
```

Expected output starts with:

```
Archive:  service.video.playhistory-1.0.3.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
        0  2026-05-30 09:24   service.video.playhistory/
```

---

## Project Structure / 项目结构

```
service.video.playhistory/
├── addon.xml                    # Add-on metadata & entry points
├── default.py                   # Script entry (Program add-ons)
├── icon.png                     # Add-on icon
├── resources/
│   ├── settings.xml             # Settings UI definition
│   ├── lib/
│   │   ├── service.py           # Service entry: polling loop
│   │   └── playhistory/
│   │       ├── __init__.py
│   │       ├── common.py        # Shared helpers (paths, logging, settings)
│   │       ├── database.py      # SQLite layer (upsert, cleanup)
│   │       ├── gui.py           # History browser dialog
│   │       └── player.py        # Playback state machine (poll)
│   └── skins/
│       └── default/720p/
│           └── DialogPlayHistory.xml   # (legacy) WindowXML skin
```

---

## Technical Notes / 技术说明

### Polling vs Callbacks

Uses polling (`xbmc.Monitor.waitForAbort(1)` + `xbmc.Player().isPlayingVideo()`) rather than `Monitor.onNotification` or `xbmc.Player` subclass. Reason: callback events may not process reliably when the addon thread blocks in `waitForAbort()`.

### State machine safety

`PlaybackTracker._on_stop()` resets `current_file` / `resume_time` / `total_time` **before** the DB call. If the DB call fails, the next poll cycle will not re-trigger the same stop event infinitely.

### Phantom first-recording prevention

A `_ready` flag waits until no video is playing before the tracker becomes active, avoiding phantom entries for videos already in progress when the service starts.

### Single record per file (upsert)

`add_play_start` uses `SELECT` + `UPDATE`/`INSERT` instead of a `UNIQUE` constraint. Replaying the same file updates `play_start` to now and clears `play_end`/`resume_time`/`total_time`, bumping it to the top of the history without creating a duplicate.

### SQLite compatibility

`UPDATE ... ORDER BY ... LIMIT` is not valid in SQLite. The codebase uses subquery patterns instead.

### ZIP format

Kodi rejects Python's `zipfile.ZIP_DEFLATED` (ZIP v2.0). Always use `zip -r` (Linux/macOS) or `Compress-Archive` (Windows) to produce a v1.0 compatible ZIP.

---

## License / 许可

GNU General Public License v2.0 or later — see [LICENSE](LICENSE).
