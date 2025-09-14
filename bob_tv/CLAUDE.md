# Claude Context for Bob TV Elixir Application

## Project Overview
Bob TV is the Elixir/Phoenix LiveView implementation of The Bobbing Channel - a 24/7 streaming TV channel that broadcasts vintage content from Archive.org to stream.place. This is a port and enhancement of the original Python implementation.

## Current State (as of 2025-09-14)

### ✅ Completed
- **Catalog Explorer LiveView**: Full port of Python catalog browser
  - Browse 1,327 items from Archive.org
  - Filter by type, year, search
  - Detail views with similar items
  - Retro TV aesthetic with scanlines
- **Database Integration**: Connected to existing SQLite database
  - Added proper id column for Ecto compatibility
  - All indexes maintained
  - 1,327 media items accessible

### 🚧 In Progress
- **Streaming System Port**: Converting Python streaming system to Elixir
  - OBS Feeder → StreamCoordinator GenServer
  - Video Manager → VideoManager GenServer
  - Overlay Generator → OverlayGenerator GenServer
  - Bluesky Ticker → BlueskySocial GenServer

## Architecture

### Current Module Structure
```
lib/
├── bob_tv/
│   ├── application.ex        # OTP Application
│   ├── repo.ex               # Ecto Repo
│   ├── catalog.ex            # Catalog context
│   └── catalog/
│       └── media.ex          # Media schema
├── bob_tv_web/
│   ├── router.ex             # Phoenix Router
│   ├── endpoint.ex           # Phoenix Endpoint
│   ├── live/
│   │   └── catalog_live/
│   │       ├── index.ex      # Catalog browser LiveView
│   │       ├── index.html.heex
│   │       ├── show.ex       # Media detail LiveView
│   │       └── show.html.heex
│   └── components/
│       └── layouts/
│           └── catalog.html.heex  # Catalog layout
```

### Planned Streaming Architecture
```
lib/bob_tv/
├── streaming/
│   ├── supervisor.ex         # Top-level supervisor
│   ├── video_manager.ex      # GenServer for video downloads
│   ├── stream_coordinator.ex # GenServer for playback control
│   ├── overlay_generator.ex  # GenServer for HTML overlays
│   └── bluesky_social.ex    # GenServer for social integration
├── streaming_web/
│   └── live/
│       └── dashboard_live.ex # LiveView monitoring dashboard
```

## Database Schema

### Media Table (SQLite)
```sql
CREATE TABLE media (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  identifier TEXT UNIQUE NOT NULL,  -- Archive.org identifier
  title TEXT,
  description TEXT,
  creator TEXT,
  date TEXT,
  year INTEGER,
  mediatype TEXT,
  collection TEXT,
  downloads INTEGER,
  item_size INTEGER,
  item_url TEXT,
  thumbnail_url TEXT,
  crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Key Implementation Details

### 1. Catalog Explorer
- Uses Phoenix LiveView for real-time updates
- Maintains exact styling from Python version
- Pagination with 48 items per page
- Random shuffle by default
- Programming ideas section for content discovery

### 2. Streaming System (To Be Implemented)

#### Video Manager GenServer
```elixir
# Responsibilities:
- Download videos from Archive.org
- Maintain exactly 2 videos (current + next)
- Enforce storage limits (40GB max, 10GB per video)
- Track played history (last 100)
- Clean up watched videos
```

#### Stream Coordinator GenServer
```elixir
# Responsibilities:
- Monitor playback with ffprobe Port
- Atomic file swapping for OBS
- Trigger next video preparation at 75% playback
- Maintain streaming state
```

#### Using Elixir Ports for FFmpeg
```elixir
# Example port usage for ffprobe
port = Port.open({:spawn_executable, "/usr/bin/ffprobe"}, [
  :binary,
  :exit_status,
  args: ["-v", "error", "-show_entries", "format=duration",
         "-of", "json", video_path]
])
```

### 3. LiveView Dashboard (To Be Implemented)
- Real-time streaming status
- Current/next video info
- Download progress
- Storage usage
- Playback statistics
- Process health monitoring

## Configuration

### Environment Variables Needed
```bash
# Streaming configuration
STREAM_URL=rtmp://stream.place/live
STREAM_KEY=your_stream_key
ARCHIVE_ORG_COLLECTION=markpines

# Storage limits
MAX_STORAGE_GB=40
MAX_VIDEO_SIZE_GB=10

# Bluesky integration (optional)
BLUESKY_HANDLE=your.handle
BLUESKY_APP_PASSWORD=your_app_password
```

### Phoenix Configuration
- Port: 4000 (development)
- Database: `../b_roll/media_library.db` (SQLite)
- LiveView signing salt configured

## Development Workflow

### Starting the Application
```bash
cd bob_tv
mix deps.get
mix ecto.migrate  # Already run, database has id column
mix phx.server
```

### Accessing the Application
- Catalog Explorer: http://localhost:4000/catalog
- Dashboard (future): http://localhost:4000/dashboard
- API Stats: http://localhost:4000/api/stats

### Running Tests
```bash
mix test
```

## Key Differences from Python Implementation

### Improvements in Elixir Version
1. **Process Supervision**: Automatic restart on failures
2. **Real-time Updates**: LiveView for instant UI updates
3. **Better Concurrency**: Elixir's actor model for parallel operations
4. **Unified Application**: No need for multiple terminal sessions
5. **Web Dashboard**: Built-in monitoring interface
6. **Message Passing**: Direct process communication vs file-based

### Architecture Changes
- JSON state files → ETS tables / Database
- Multiple Python scripts → Supervised GenServers
- Makefile orchestration → OTP Application supervision
- File polling → Message passing
- Manual process management → Automatic supervision

## Common Tasks

### Add a New Video Source
1. Update `VideoManager` selection logic
2. Add source to configuration
3. Update dashboard to show new source

### Modify Overlay Style
1. Edit templates in `OverlayGenerator`
2. Update CSS in generated HTML
3. Refresh OBS browser source

### Debug Streaming Issues
1. Check dashboard at `/dashboard`
2. View logs: `mix phx.server`
3. Inspect ETS tables: `:ets.tab2list(:streaming_state)`
4. Check Port status for FFmpeg processes

## Gotchas and Important Notes

1. **SQLite Locking**: The database can lock with multiple connections. Consider connection pooling settings.

2. **File Operations**: Use atomic operations for video file swapping to prevent OBS interruptions.

3. **Port Management**: Always trap exits and handle Port deaths gracefully.

4. **Storage Management**: Monitor disk space actively - streaming stops if disk is full.

5. **Archive.org Rate Limiting**: Implement exponential backoff for download retries.

## Next Steps

### Immediate Priorities
1. ✅ Complete catalog explorer
2. 🚧 Implement VideoManager GenServer
3. 🚧 Implement StreamCoordinator GenServer
4. 🚧 Create LiveView dashboard
5. 🚧 Set up supervision tree

### Future Enhancements
- WebRTC support for lower latency
- Multi-channel support
- Scheduled programming blocks
- Viewer statistics
- Chat integration
- Mobile-responsive UI

## Testing Checklist

- [ ] Catalog loads and paginates correctly
- [ ] Search and filters work
- [ ] Video downloads start automatically
- [ ] File swapping doesn't interrupt stream
- [ ] Dashboard updates in real-time
- [ ] Processes restart on failure
- [ ] Storage limits are enforced
- [ ] Recently played videos are avoided

## Resources

- [Phoenix LiveView Docs](https://hexdocs.pm/phoenix_live_view)
- [Elixir Port Documentation](https://hexdocs.pm/elixir/Port.html)
- [OTP Supervision](https://elixir-lang.org/getting-started/mix-otp/supervisor-and-application.html)
- [Archive.org API](https://archive.org/developers/internetarchive/)
- [stream.place Documentation](https://stream.place/docs)

## Contact for Questions

This is a personal project for The Bobbing Channel. The goal is to create a unique, automated TV channel with curated vintage content, bringing the public-access TV aesthetic to modern streaming.