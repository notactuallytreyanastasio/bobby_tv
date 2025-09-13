# Catalog Explorer

A retro TV-themed web interface for browsing The Bobbing Channel's media library.

## Features

- 📺 **Browse 1,327 items** from the markpines Archive.org collection
- 🔍 **Search & Filter** by type, year, popularity, or text search
- 🎲 **Random Discovery** to find hidden gems
- 📊 **Programming Ideas** with curated blocks for channel planning
- 🌙 **Night Mode** for late-night browsing
- ⚡ **Retro TV Aesthetic** with scanlines, static, and CRT effects

## Setup

```bash
# Navigate to catalog explorer
cd ~/bobby_tv/catalog_explorer

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install Flask
pip install -r requirements.txt
```

## Running

```bash
# Make sure you're in the catalog_explorer directory
cd ~/bobby_tv/catalog_explorer

# Activate virtual environment
source venv/bin/activate

# Run the app
python app.py
```

Then open in your browser:
- Local: http://localhost:5000
- Network: http://[your-pi-ip]:5000

## Interface Guide

### Main Browse View
- **Grid of thumbnails** - Click any item to see details
- **Filters** - Type (movies/audio/collections), Sort (random/popular/date/title/size)
- **Search** - Find items by title, description, or creator
- **Year filter** - Browse by specific years
- **Programming blocks** - Suggested content blocks at the top

### Detail View
- Full metadata for each item
- Direct link to Archive.org
- Similar items suggestions
- Copy link functionality

### Keyboard Shortcuts
- `R` - Jump to random item
- `N` - Toggle night mode
- `/` - Focus search box

## Database

Uses the SQLite database from `../b_roll/media_library.db` with 1,327 items.

## Customization

The retro TV aesthetic includes:
- Animated scanlines
- TV static effect
- CRT screen curvature on thumbnails
- Retro fonts (VT323, Press Start 2P)
- Classic TV color scheme (cyan, green, yellow)
- Channel switching effects

## Notes

- Thumbnails are loaded from Archive.org's image service
- The interface is responsive and works on mobile
- All data is read-only - this is a browsing interface
- Perfect for discovering content for programming The Bobbing Channel!