# Bob TV - The Bobbing Channel

A 24/7 streaming TV channel broadcasting vintage content from Archive.org, built with Elixir and Phoenix LiveView.

## Features

### 🎬 Catalog Explorer
- Browse 1,327+ vintage movies, audio, and collections
- Filter by media type, year, and search
- Retro TV aesthetic with scanlines and static effects
- Random shuffle for discovery
- Programming block suggestions

### 📡 Streaming System (In Development)
- Automated 24/7 broadcasting to stream.place
- Smart video rotation with zero interruptions
- Minimal storage usage (2 videos at a time)
- Real-time overlays and tickers
- OBS Studio integration

### 📊 LiveView Dashboard (Coming Soon)
- Real-time streaming status
- Download progress monitoring
- Storage management
- Playback statistics

## Quick Start

### Prerequisites
- Elixir 1.15+
- Erlang/OTP 25+
- SQLite3
- FFmpeg (for streaming features)
- OBS Studio (optional, for broadcasting)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/bobby_tv.git
cd bobby_tv/bob_tv

# Install dependencies
mix deps.get

# Set up the database
mix ecto.migrate

# Start the Phoenix server
mix phx.server
```

Now visit [`localhost:4000/catalog`](http://localhost:4000/catalog) to browse the media library.

## Project Structure

```
bob_tv/
├── lib/
│   ├── bob_tv/           # Business logic
│   │   ├── catalog/      # Media catalog
│   │   └── streaming/    # Streaming system (WIP)
│   └── bob_tv_web/       # Web interface
│       └── live/         # LiveView modules
├── priv/
│   ├── repo/migrations/  # Database migrations
│   └── static/           # Static assets
└── assets/               # CSS and JavaScript
```

## Configuration

### Database
The application uses the existing SQLite database from the Python implementation:
```elixir
# config/dev.exs
config :bob_tv, BobTv.Repo,
  database: Path.expand("../../b_roll/media_library.db", __DIR__)
```

### Streaming (Coming Soon)
Set these environment variables for streaming:
```bash
export STREAM_URL=rtmp://stream.place/live
export STREAM_KEY=your_stream_key
export MAX_STORAGE_GB=40
```

## Development

### Running Tests
```bash
mix test
```

### Code Formatting
```bash
mix format
```

### Generating Documentation
```bash
mix docs
```

## Architecture

The application follows OTP principles with supervised processes:

- **Catalog System**: Browse and search media from Archive.org
- **Video Manager**: Downloads and manages video files
- **Stream Coordinator**: Controls playback and file rotation
- **Overlay Generator**: Creates real-time HTML overlays
- **Dashboard**: LiveView interface for monitoring

## API Endpoints

- `GET /catalog` - Browse media catalog
- `GET /catalog/:id` - View media details
- `GET /api/stats` - JSON statistics

## Contributing

This is a personal project for The Bobbing Channel, but suggestions are welcome!

## License

This project is for educational and archival purposes, using public domain content from Archive.org.

## Acknowledgments

- Archive.org for hosting vintage content
- stream.place for streaming infrastructure
- The Elixir/Phoenix community

---

*The Bobbing Channel - Bringing public-access TV vibes to modern streaming*
