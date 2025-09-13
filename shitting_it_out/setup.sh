#!/bin/bash

echo "🎬 Bobby TV Streaming System Setup"
echo "=================================="

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p streaming_videos
mkdir -p overlays
mkdir -p obs_config
mkdir -p recordings

# Create initial configs
echo "Creating initial configuration files..."

# Create streaming config if it doesn't exist
if [ ! -f "obs_config/streaming_config.json" ]; then
    cat > obs_config/streaming_config.json << 'EOF'
{
  "rtmp": {
    "server": "rtmp://stream.place/live",
    "stream_key": "YOUR_STREAM_KEY_HERE"
  },
  "video": {
    "resolution": "1920x1080",
    "fps": 30,
    "bitrate": 4000
  },
  "audio": {
    "bitrate": 128,
    "sample_rate": 44100
  },
  "scenes": {}
}
EOF
    echo "✓ Created obs_config/streaming_config.json"
fi

# Create Bluesky config if it doesn't exist
if [ ! -f "overlays/bluesky_config.json" ]; then
    cat > overlays/bluesky_config.json << 'EOF'
{
  "handle": "your-handle.bsky.social",
  "app_password": "",
  "fetch_count": 20,
  "include_replies": false,
  "include_reposts": true,
  "cache_minutes": 5
}
EOF
    echo "✓ Created overlays/bluesky_config.json"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit obs_config/streaming_config.json with your stream key"
echo "2. Edit overlays/bluesky_config.json with your Bluesky credentials (optional)"
echo "3. Activate the virtual environment: source venv/bin/activate"
echo "4. Download initial videos: python video_manager.py maintain"
echo "5. Generate overlays: python overlay_generator.py full"
echo "6. Start streaming!"
echo ""
echo "For detailed instructions, see README.md"