# Bobby TV Streaming System Makefile
# Start everything with: make stream

.PHONY: help stream setup install deps videos overlays feeder coordinator status stop clean logs commit

# Default target - show help
help:
	@echo "Bobby TV Streaming System"
	@echo "========================="
	@echo ""
	@echo "Quick Start:"
	@echo "  make setup       - First time setup (install deps, create dirs)"
	@echo "  make stream      - Start streaming (runs feeder + overlays)"
	@echo "  make stop        - Stop all streaming processes"
	@echo ""
	@echo "Individual Components:"
	@echo "  make videos      - Download initial videos"
	@echo "  make overlays    - Generate/update HTML overlays"
	@echo "  make feeder      - Run OBS video feeder (swaps videos)"
	@echo "  make coordinator - Run stream coordinator (manages downloads)"
	@echo ""
	@echo "Utilities:"
	@echo "  make status      - Show system status"
	@echo "  make logs        - Tail all logs"
	@echo "  make clean       - Clean up old videos and cache"
	@echo "  make commit      - Commit current changes to git"

# Complete setup for first time
setup: install deps videos overlays
	@echo "✅ Setup complete! Run 'make stream' to start broadcasting"

# Install virtual environment
install:
	@echo "🔧 Setting up Python virtual environment..."
	@test -d venv || python3 -m venv venv
	@. venv/bin/activate && pip install --upgrade pip
	@. venv/bin/activate && pip install requests
	@echo "✅ Virtual environment ready"

# Install system dependencies
deps:
	@echo "📦 Checking system dependencies..."
	@which ffmpeg > /dev/null || echo "⚠️  Please install ffmpeg: brew install ffmpeg"
	@which obs > /dev/null || echo "⚠️  Please install OBS Studio from https://obsproject.com"
	@mkdir -p streaming_videos/queue
	@mkdir -p streaming_videos/played
	@mkdir -p overlays
	@mkdir -p obs_config
	@mkdir -p recordings
	@echo "✅ Dependencies checked"

# Download initial videos
videos:
	@echo "📥 Downloading initial videos..."
	@. venv/bin/activate && python video_manager.py maintain
	@. venv/bin/activate && python video_manager.py status

# Generate overlays
overlays:
	@echo "🎨 Generating overlays..."
	@. venv/bin/activate && python overlay_generator.py full
	@echo "✅ Overlays ready at:"
	@echo "   file://$$(pwd)/overlays/full_overlay.html"

# Start OBS feeder (main streaming process)
feeder:
	@echo "🎬 Starting OBS feeder..."
	@echo "Configure OBS to read: $$(pwd)/streaming_videos/current_stream.mp4"
	@. venv/bin/activate && python obs_feeder.py run

# Start stream coordinator (background downloads)
coordinator:
	@echo "📡 Starting stream coordinator..."
	@. venv/bin/activate && python stream_coordinator.py run

# Main streaming target - runs everything needed
stream:
	@echo "🚀 Starting Bobby TV Stream..."
	@echo "================================"
	@echo ""
	@echo "1. Starting video feeder..."
	@. venv/bin/activate && python obs_feeder.py init
	@echo ""
	@echo "2. OBS Configuration:"
	@echo "   - Media Source: $$(pwd)/streaming_videos/current_stream.mp4"
	@echo "   - Browser Source: file://$$(pwd)/overlays/full_overlay.html"
	@echo "   - Stream Server: rtmps://stream.place:1935/live"
	@echo ""
	@echo "3. Starting feeder (press Ctrl+C to stop)..."
	@. venv/bin/activate && python obs_feeder.py run

# Run both feeder and coordinator in parallel
stream-full:
	@echo "🚀 Starting Bobby TV Full System..."
	@make -j2 feeder coordinator

# Show current status
status:
	@echo "📊 Bobby TV Status"
	@echo "=================="
	@. venv/bin/activate && python video_manager.py status
	@echo ""
	@. venv/bin/activate && python obs_feeder.py status
	@echo ""
	@echo "Streaming Config:"
	@cat obs_config/streaming_config.json | grep -E '"server"|"stream_key"' | head -2

# Stop all processes
stop:
	@echo "🛑 Stopping all Bobby TV processes..."
	@pkill -f "python obs_feeder.py" || true
	@pkill -f "python stream_coordinator.py" || true
	@pkill -f "python video_manager.py" || true
	@echo "✅ All processes stopped"

# Clean up old files
clean:
	@echo "🧹 Cleaning up..."
	@rm -f streaming_videos/played/*.mp4
	@rm -f overlays/posts_cache.json
	@rm -f overlays/ticker_data.json
	@rm -f *.log
	@echo "✅ Cleanup complete"

# Watch logs
logs:
	@echo "📜 Streaming logs (Ctrl+C to stop)..."
	@tail -f *.log 2>/dev/null || echo "No logs yet"

# Quick git commit
commit:
	@echo "📝 Committing changes..."
	@git add -A
	@git status --short
	@read -p "Commit message: " msg; \
	git commit -m "$$msg"

# Development targets
dev-overlay:
	@echo "🔄 Regenerating overlay with live reload..."
	@. venv/bin/activate && python overlay_generator.py full
	@echo "Overlay updated - refresh OBS browser source"

dev-test-video:
	@echo "🎥 Testing video rotation..."
	@. venv/bin/activate && python obs_feeder.py swap

# OBS specific helpers
obs-playlist:
	@echo "📝 Generating OBS playlist..."
	@. venv/bin/activate && python video_manager.py playlist

obs-config:
	@echo "📺 OBS Configuration Instructions:"
	@. venv/bin/activate && python obs_controller.py setup

# System info
info:
	@echo "ℹ️  System Information"
	@echo "===================="
	@echo "Working directory: $$(pwd)"
	@echo "Python version: $$(python3 --version)"
	@echo "FFmpeg: $$(which ffmpeg || echo 'NOT INSTALLED')"
	@echo "OBS: $$(which obs || echo 'NOT INSTALLED')"
	@echo "Disk space: $$(df -h . | tail -1 | awk '{print $$4}' ) free"
	@echo ""
	@ls -la streaming_videos/*.mp4 2>/dev/null | wc -l | xargs echo "Videos ready:"
	@ls -la streaming_videos/queue/*.mp4 2>/dev/null | wc -l | xargs echo "Videos in queue:"