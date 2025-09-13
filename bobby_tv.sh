#!/bin/bash

# Bobby TV Launcher
# Main entry point for the Bobby TV project
# Run this from the project root to start any component

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directories
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
CATALOG_DIR="$PROJECT_ROOT/catalog_explorer"
STREAMING_DIR="$PROJECT_ROOT/shitting_it_out"
CRAWLER_DIR="$PROJECT_ROOT/b_roll"

# ASCII Art Banner
show_banner() {
    echo -e "${BLUE}"
    cat << "EOF"
    ____        __    __          _______ _    __
   / __ )____  / /_  / /_  __  __/_  __/| |  / /
  / __  / __ \/ __ \/ __ \/ / / / / /   | | / /
 / /_/ / /_/ / /_/ / /_/ / /_/ / / /    | |/ /
/_____/\____/_.___/_.___/\__, / /_/     |___/
                        /____/
       24/7 Archive.org Streaming System
EOF
    echo -e "${NC}"
}

# Show main menu
show_menu() {
    echo -e "${GREEN}=== Bobby TV Control Center ===${NC}"
    echo ""
    echo "1) 📺 Start Streaming (OBS + Feeder)"
    echo "2) 🔍 Browse Catalog (Web Explorer)"
    echo "3) 📥 Download Videos"
    echo "4) 🎨 Update Overlays"
    echo "5) 📊 System Status"
    echo "6) 🛠  Setup Everything"
    echo "7) 🛑 Stop All Services"
    echo "8) 📚 Documentation"
    echo "9) 🚪 Exit"
    echo ""
}

# Start streaming
start_streaming() {
    echo -e "${GREEN}Starting Bobby TV Stream...${NC}"
    cd "$STREAMING_DIR"

    # Check if setup is needed
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}First time setup needed...${NC}"
        make setup
    fi

    echo -e "${BLUE}Opening OBS configuration instructions...${NC}"
    make obs-config

    echo ""
    echo -e "${GREEN}Starting video feeder...${NC}"
    echo -e "${YELLOW}Configure OBS to read: ${STREAMING_DIR}/streaming_videos/current_stream.mp4${NC}"
    echo ""

    make stream
}

# Start catalog explorer
start_catalog() {
    echo -e "${GREEN}Starting Catalog Explorer...${NC}"
    cd "$CATALOG_DIR"

    # Check for venv
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Setting up virtual environment...${NC}"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        source venv/bin/activate
    fi

    echo -e "${BLUE}Opening browser at http://localhost:5001${NC}"
    python app.py &
    sleep 2
    open http://localhost:5001 2>/dev/null || xdg-open http://localhost:5001 2>/dev/null || echo "Please open http://localhost:5001"
}

# Download videos
download_videos() {
    echo -e "${GREEN}Downloading videos from Archive.org...${NC}"
    cd "$STREAMING_DIR"

    if [ ! -d "venv" ]; then
        python3 -m venv venv
        source venv/bin/activate
        pip install requests
    else
        source venv/bin/activate
    fi

    python video_manager.py maintain
    python video_manager.py status
}

# Update overlays
update_overlays() {
    echo -e "${GREEN}Updating stream overlays...${NC}"
    cd "$STREAMING_DIR"

    source venv/bin/activate 2>/dev/null || {
        python3 -m venv venv
        source venv/bin/activate
        pip install requests
    }

    python overlay_generator.py full
    echo -e "${BLUE}Overlay updated at: file://${STREAMING_DIR}/overlays/full_overlay.html${NC}"
}

# Show status
show_status() {
    echo -e "${GREEN}=== System Status ===${NC}"

    # Check streaming status
    echo -e "\n${YELLOW}Streaming System:${NC}"
    cd "$STREAMING_DIR"
    if [ -d "venv" ]; then
        source venv/bin/activate
        python video_manager.py status 2>/dev/null || echo "Not initialized"
        python obs_feeder.py status 2>/dev/null || echo "Feeder not running"
    else
        echo "Not set up yet"
    fi

    # Check catalog
    echo -e "\n${YELLOW}Catalog Explorer:${NC}"
    if pgrep -f "catalog_explorer/app.py" > /dev/null; then
        echo "✅ Running at http://localhost:5001"
    else
        echo "❌ Not running"
    fi

    # Check disk space
    echo -e "\n${YELLOW}Disk Space:${NC}"
    df -h "$PROJECT_ROOT" | tail -1

    # Check processes
    echo -e "\n${YELLOW}Active Processes:${NC}"
    ps aux | grep -E "obs_feeder|video_manager|app.py" | grep -v grep || echo "None running"
}

# Setup everything
setup_all() {
    echo -e "${GREEN}Setting up Bobby TV system...${NC}"

    # Setup streaming
    echo -e "\n${YELLOW}Setting up streaming system...${NC}"
    cd "$STREAMING_DIR"
    make setup

    # Setup catalog
    echo -e "\n${YELLOW}Setting up catalog explorer...${NC}"
    cd "$CATALOG_DIR"
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi

    echo -e "\n${GREEN}✅ Setup complete!${NC}"
}

# Stop all services
stop_all() {
    echo -e "${RED}Stopping all Bobby TV services...${NC}"

    # Stop streaming
    pkill -f "obs_feeder.py" 2>/dev/null || true
    pkill -f "video_manager.py" 2>/dev/null || true
    pkill -f "stream_coordinator.py" 2>/dev/null || true

    # Stop catalog
    pkill -f "catalog_explorer/app.py" 2>/dev/null || true

    echo -e "${GREEN}✅ All services stopped${NC}"
}

# Show documentation
show_docs() {
    echo -e "${BLUE}=== Bobby TV Documentation ===${NC}"
    echo ""
    echo "📁 Project Structure:"
    echo "  • catalog_explorer/ - Web UI for browsing Archive.org content"
    echo "  • shitting_it_out/  - Streaming system (OBS integration)"
    echo "  • b_roll/          - Archive.org crawler and database"
    echo ""
    echo "📺 Quick Start Guide:"
    echo "  1. Run option 6 (Setup) first time"
    echo "  2. Run option 1 to start streaming"
    echo "  3. Configure OBS with displayed settings"
    echo "  4. Start streaming in OBS"
    echo ""
    echo "📚 For detailed docs, see:"
    echo "  • ${STREAMING_DIR}/README.md"
    echo "  • ${CATALOG_DIR}/README.md"
    echo ""
    read -p "Press Enter to continue..."
}

# Main loop
main() {
    show_banner

    while true; do
        show_menu
        read -p "Select option [1-9]: " choice

        case $choice in
            1) start_streaming ;;
            2) start_catalog ;;
            3) download_videos ;;
            4) update_overlays ;;
            5) show_status ;;
            6) setup_all ;;
            7) stop_all ;;
            8) show_docs ;;
            9) echo -e "${GREEN}Goodbye!${NC}"; exit 0 ;;
            *) echo -e "${RED}Invalid option${NC}" ;;
        esac

        echo ""
        read -p "Press Enter to continue..."
        clear
        show_banner
    done
}

# Run main function
main "$@"