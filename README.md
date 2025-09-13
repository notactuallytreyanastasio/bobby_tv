# The Bobbing Channel (Bobby TV)

A 24/7 streaming television channel broadcasting vintage Archive.org content to stream.place, complete with satirical news tickers and professional overlays.

## 🚀 Quick Start

```bash
# Launch the control center
./bobby_tv.sh

# Select option 1 to start streaming
```

That's it! The system handles everything else automatically.

## 📺 What Is This?

The Bobbing Channel is a fully automated TV station that:
- Streams 24/7 to stream.place (AT Protocol streaming platform)
- Broadcasts curated content from Archive.org's public domain collection
- Features satirical news tickers with Onion-style headlines
- Runs efficiently on minimal hardware (Raspberry Pi compatible)
- Manages storage intelligently (only keeps 2 videos at a time)

## 🎯 The Vision

> "I made a television channel for stream.place using my media collection that is unique and interesting."

This project realizes that vision with:
- **1,327+ curated titles** from https://archive.org/details/@mark_pines_archive_project
- **Smart rotation** - downloads and deletes content automatically
- **Professional presentation** - overlays, tickers, channel branding
- **Zero maintenance** - runs forever once started

## 📁 Project Components

### 1. `catalog_explorer/` - Content Browser
Web interface for browsing the media library
- Browse 1,327+ Archive.org items
- Search by type, year, popularity
- Visual grid layout
- Runs at http://localhost:5001

### 2. `shitting_it_out/` - Broadcasting Engine
The core streaming system
- **OBS Feeder**: Seamlessly swaps videos with zero interruption
- **Video Manager**: Downloads and rotates content (2 videos max)
- **Overlay Generator**: Creates HTML overlays with news ticker
- **Stream Coordinator**: Manages the whole operation

### 3. `b_roll/` - Content Database
SQLite database of curated Archive.org content
- 1,327 items with metadata
- Curated from @mark_pines_archive_project

## 🏗 Architecture

```
[Archive.org] → [Video Manager] → [Local Storage] → [OBS Feeder] → [OBS] → [stream.place]
                                    (2 videos)           ↓
                                                   [HTML Overlay]
                                                   (News Ticker)
```

### Key Innovation: The OBS Feeder

Traditional streaming requires complex playlist management. Our solution:
1. OBS reads ONE file: `current_stream.mp4`
2. The feeder atomically swaps this file with new content
3. OBS never knows the file changed - seamless playback!

## 🛠 Setup Instructions

### Prerequisites
- Python 3.8+
- OBS Studio
- 50GB free disk space
- FFmpeg (optional, for better performance)

### Installation

1. **Run the launcher**:
   ```bash
   ./bobby_tv.sh
   ```

2. **Select option 6** (Setup Everything)

3. **Configure OBS**:
   - Add Media Source → Point to `streaming_videos/current_stream.mp4`
   - Add Browser Source → Point to `overlays/full_overlay.html`
   - Settings → Stream → Server: `rtmps://stream.place:1935/live`
   - Get stream key from stream.place

4. **Start streaming** (option 1 in launcher)

## 📊 Features

### Automatic Content Management
- Downloads videos from Archive.org on-demand
- Keeps only 2 videos locally (current + next)
- Deletes watched content automatically
- Respects disk space limits (40GB default)

### Professional Overlays
- Time display (top-left)
- Channel branding (top-right)
- Scrolling news ticker (bottom)
- "Now Playing" information
- Customizable via HTML/CSS

### News Ticker Headlines
Satirical headlines scroll across the bottom:
- "Local Man Discovers Pause Button After 47 Years of Continuous Viewing"
- "Netflix Algorithm Achieves Sentience, Still Can't Find Anything Good"
- "Study Finds 87% of Remote Controls Lost in Same Couch for Past Decade"

## 🎮 Control Center

The `bobby_tv.sh` script provides easy control:
- **Option 1**: Start streaming
- **Option 2**: Browse catalog
- **Option 3**: Download videos
- **Option 4**: Update overlays
- **Option 5**: Check status
- **Option 6**: Setup everything
- **Option 7**: Stop all services

## 📈 Performance

- **Storage**: Uses only 40GB max (configurable)
- **Bandwidth**: 4Mbps upload for streaming
- **CPU**: Minimal (runs on Raspberry Pi)
- **Memory**: ~500MB for Python scripts

## 🔧 Customization

### Change Headlines
Edit `shitting_it_out/overlay_generator.py` to add your own headlines

### Adjust Storage Limits
Edit `shitting_it_out/video_manager.py`:
- `MAX_STORAGE_GB`: Maximum storage to use
- `VIDEOS_TO_MAINTAIN`: Number of videos to keep ready

### Modify Overlay Style
Edit `overlays/full_overlay.html` for custom styling

## 📚 Documentation

- `shitting_it_out/README.md` - Detailed streaming setup
- `shitting_it_out/CLAUDE.md` - Technical implementation notes
- `catalog_explorer/README.md` - Catalog browser documentation

## 🤝 Credits

- Archive.org for the incredible content library
- stream.place for AT Protocol streaming
- @mark_pines_archive_project for content curation

---

**Status**: Production Ready
**Platform**: stream.place
**Content**: https://archive.org/details/@mark_pines_archive_project
**Last Updated**: September 2024