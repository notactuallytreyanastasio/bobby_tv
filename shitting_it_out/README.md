# Bobby TV Streaming System (shitting_it_out)

A lightweight 24/7 streaming system that broadcasts Archive.org content to stream.place using OBS, with smart storage management and satirical news tickers.

**Last Updated**: September 2024
**Status**: Production Ready
**Stream Endpoint**: rtmps://stream.place:1935/live

## Overview

This system creates a continuous TV channel that:
- Streams vintage content from Archive.org 24/7
- Manages storage intelligently (only keeps 2 videos at a time)
- Displays your Bluesky posts as a news ticker
- Broadcasts to stream.place via RTMP

## 🎯 Key Innovation: The OBS Feeder

The **OBS Feeder** (`obs_feeder.py`) is the secret sauce that makes seamless 24/7 streaming possible:

### How It Works
1. OBS reads a **single file**: `streaming_videos/current_stream.mp4`
2. The feeder **atomically swaps** this file with new content
3. OBS never knows the file changed - it just keeps playing
4. Result: Seamless transitions with no interruption!

### Why This Matters
- No complex playlist management in OBS
- No VLC source needed
- Works with basic Media Source
- Zero-interruption transitions
- Automatic video rotation

## Components

### Core Systems

1. **Video Manager** (`video_manager.py`)
   - Downloads videos from Archive.org catalog
   - Maintains 2-video rotation (current + next)
   - Respects 40GB storage limit
   - Auto-cleanup of watched content

2. **Stream Coordinator** (`stream_coordinator.py`)
   - Monitors playback progress
   - Rotates videos automatically
   - Downloads new content just-in-time
   - Maintains continuous playback

3. **OBS Controller** (`obs_controller.py`)
   - Generates OBS configuration
   - Sets up RTMP streaming to stream.place
   - Creates scene collections
   - Alternative FFmpeg streaming option

4. **Overlay Generator** (`overlay_generator.py`)
   - Creates HTML overlays for OBS
   - Channel branding and logo
   - "Now Playing" information
   - News ticker display

5. **Bluesky Ticker** (`bluesky_ticker.py`)
   - Fetches your Bluesky posts
   - Formats them for ticker display
   - Auto-refreshes content
   - Caches posts locally

## Quick Start

### Fastest Way to Stream

```bash
# One-time setup
make setup

# Start streaming
make stream
```

That's it! The Makefile handles everything.

### Manual Setup (if needed)

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install requests

# 2. Download initial videos
python video_manager.py maintain

# 3. Generate overlays
python overlay_generator.py full

# 4. Start the feeder
python obs_feeder.py run
```

### 2. Configure Streaming

Edit `obs_config/streaming_config.json`:
```json
{
  "rtmp": {
    "server": "rtmp://stream.place/live",
    "stream_key": "YOUR_STREAM_KEY_HERE"
  }
}
```

### 3. Configure Bluesky (Optional)

Edit `overlays/bluesky_config.json`:
```json
{
  "handle": "your-handle.bsky.social",
  "app_password": "YOUR_APP_PASSWORD"
}
```

### 4. Configure OBS Studio

**IMPORTANT**: We use a single file that gets swapped seamlessly!

1. **Add Media Source** (NOT VLC Source):
   - Name: "Bobby TV Stream"
   - Local File: `/path/to/shitting_it_out/streaming_videos/current_stream.mp4`
   - ✅ **Loop** (CRITICAL!)
   - ✅ Restart playback when source becomes active

2. **Add Browser Source** for overlay:
   - URL: `file:///path/to/shitting_it_out/overlays/full_overlay.html`
   - Width: 1920, Height: 1080
   - Make sure it's ABOVE the Media Source

3. **Configure Stream Settings**:
   - Settings → Stream
   - Service: Custom
   - Server: `rtmps://stream.place:1935/live`
   - Stream Key: (get from stream.place)

4. **Start the Feeder** (in terminal):
   ```bash
   make stream  # This keeps videos rotating
   ```

5. **Start Streaming** in OBS

**Option B: Direct FFmpeg (lighter weight)**
```bash
python obs_controller.py ffmpeg  # Shows the command
# Then run the FFmpeg command it outputs
```

### 5. Run Stream Coordinator

Keep this running to manage video rotation:
```bash
python stream_coordinator.py run
```

## Storage Management

The system intelligently manages disk space:
- **Maximum storage**: 40GB
- **Videos maintained**: 2 (current + next)
- **Max video size**: 10GB per video
- **Auto-cleanup**: Deletes watched videos
- **Just-in-time downloads**: Gets next video while current plays

## Commands Reference

### Video Manager
```bash
python video_manager.py maintain  # Download/maintain videos
python video_manager.py cleanup   # Remove old videos
python video_manager.py status    # Show storage status
python video_manager.py playlist  # Generate OBS playlist
```

### Stream Coordinator
```bash
python stream_coordinator.py run      # Run main coordinator
python stream_coordinator.py status   # Show current status
python stream_coordinator.py rotate   # Force rotation
python stream_coordinator.py playlist # Generate active playlist
```

### OBS Controller
```bash
python obs_controller.py setup       # Show setup instructions
python obs_controller.py scenes      # Generate scene collection
python obs_controller.py profile     # Generate OBS profile
python obs_controller.py ffmpeg      # Show FFmpeg command
python obs_controller.py set-key KEY # Set stream key
```

### Overlay Generator
```bash
python overlay_generator.py ticker       # Generate ticker only
python overlay_generator.py full        # Generate full overlay
python overlay_generator.py instructions # Show OBS instructions
```

### Bluesky Ticker
```bash
python bluesky_ticker.py fetch    # Fetch and display posts
python bluesky_ticker.py generate # Generate ticker data
python bluesky_ticker.py daemon   # Run auto-refresh daemon
python bluesky_ticker.py test     # Test authentication
```

## File Structure

```
shitting_it_out/
├── video_manager.py         # Video download/rotation
├── stream_coordinator.py    # Playback monitoring
├── obs_controller.py        # OBS configuration
├── overlay_generator.py     # HTML overlay creation
├── bluesky_ticker.py        # Bluesky integration
├── streaming_videos/        # Video storage (created automatically)
│   ├── *.mp4               # Downloaded videos
│   ├── playlist.json       # Playlist state
│   └── obs_playlist.m3u    # OBS playlist file
├── overlays/               # HTML overlays (created automatically)
│   ├── ticker.html         # Ticker only
│   ├── full_overlay.html   # Complete overlay
│   └── ticker_data.json    # Bluesky posts
└── obs_config/             # OBS settings (created automatically)
    └── streaming_config.json
```

## Architecture

```
[Archive.org API] → [Video Manager] → [Local Storage (2 videos)]
                                              ↓
                                      [Stream Coordinator]
                                              ↓
                                         [OBS Studio]
                                              ↓
                                      [HTML Overlays]
                                     [Bluesky Ticker]
                                              ↓
                                       [RTMP Stream]
                                              ↓
                                      [stream.place]
```

## Requirements

- Python 3.8+
- OBS Studio (or FFmpeg for direct streaming)
- 50GB free disk space (40GB for videos + overhead)
- Internet connection for Archive.org downloads
- stream.place account for broadcasting

## Tips

1. **Raspberry Pi**: Use FFmpeg instead of OBS for better performance
2. **Network**: Ensure stable upload bandwidth for streaming
3. **Content**: The system randomly selects from 1,300+ Archive.org titles
4. **Monitoring**: Keep `stream_coordinator.py` running for automatic rotation
5. **Customization**: Edit config files to change branding, colors, speeds

## Troubleshooting

- **No videos downloading**: Check database path is correct (`../b_roll/media_library.db`)
- **OBS not playing**: Ensure VLC source is set to loop playlist
- **Ticker not updating**: Check Bluesky credentials in config
- **Stream dropping**: Verify RTMP settings and network stability

## License

This project uses content from Archive.org's public domain collection.