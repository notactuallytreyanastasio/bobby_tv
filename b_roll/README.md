# B-Roll Media Library

Archive.org media crawler and SQLite database for The Bobbing Channel.

## Overview

This tool crawls the Archive.org collection at https://archive.org/details/markpines and maintains a SQLite database of all 1,327 media items (27TB total). The database enables browsing and planning programming for the channel without downloading the actual media files.

## Installation

### First Time Setup
```bash
# Navigate to b_roll directory
cd ~/bobby_tv/b_roll

# Create Python virtual environment
python3 -m venv tv

# Activate virtual environment
source tv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Crawler

### Always Start With
```bash
# Navigate to project
cd ~/bobby_tv/b_roll

# Activate virtual environment (REQUIRED)
source tv/bin/activate
```

### Crawl/Update the Collection
```bash
# This will fetch all items from markpines collection
# Updates existing database with any new items
python crawler.py
```
Expected output:
```
Archive.org markpines Collection Crawler
Collection URL: https://archive.org/details/markpines

✓ Database initialized
Crawling collection: markpines

Fetching page 1...
Found 1327 total items in collection!
...
✓ Saved 1327 items to database
```

### View Library Statistics
```bash
# Shows current database contents
python crawler.py --stats
```
Expected output:
```
═══ Collection Statistics ═══
Total items: 1327

By media type:
  movies: 1321
  collection: 5
  audio: 1

Most downloaded:
  74,503 - Skit and Swinger Compilation Tape
  ...
```

### Quick Database Queries
```bash
# Count total items
python -c "import sqlite3; conn = sqlite3.connect('media_library.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM media'); print(f'Total items: {cursor.fetchone()[0]}')"

# List 10 random movies
python -c "import sqlite3; conn = sqlite3.connect('media_library.db'); cursor = conn.cursor(); cursor.execute('SELECT title FROM media WHERE mediatype=\"movies\" ORDER BY RANDOM() LIMIT 10'); [print(f'- {row[0]}') for row in cursor.fetchall()]"

# Find most downloaded items
python -c "import sqlite3; conn = sqlite3.connect('media_library.db'); cursor = conn.cursor(); cursor.execute('SELECT title, downloads FROM media ORDER BY downloads DESC LIMIT 5'); [print(f'{row[1]:,} - {row[0][:50]}') for row in cursor.fetchall()]"
```

## Troubleshooting

### "No module named 'requests'" or similar
You forgot to activate the virtual environment:
```bash
source tv/bin/activate
```

### Database is empty after crawling
Check if the crawler found items:
```bash
python crawler.py 2>&1 | grep "Found"
```
If it shows "Found 0 total items", the collection might have moved.

### Want to start fresh
```bash
# Backup existing database
mv media_library.db media_library.db.backup

# Re-run crawler (will create new database)
python crawler.py
```

### Restore from backup
```bash
mv media_library.db.backup media_library.db
```

## Database

The SQLite database (`media_library.db`) contains:

- **1,327 total items**
  - 1,321 movies
  - 5 collections
  - 1 audio item
- **27TB total size**
- **Metadata fields**: identifier, title, creator, date, mediatype, description, downloads, item_url, thumbnail_url

## Collection

The crawler fetches items from the `markpines` collection on Archive.org:
- Collection URL: https://archive.org/details/markpines
- Uses Archive.org Search API
- No authentication required (public collection)

## Next Steps

- Build web interface for browsing the media library
- Create playlists and programming schedules
- Set up streaming pipeline to serve content from Archive.org to stream.place