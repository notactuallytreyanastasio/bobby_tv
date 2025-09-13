# B-Roll Media Library

Archive.org media crawler and SQLite database for The Bobbing Channel.

## Overview

This tool crawls the Archive.org collection at https://archive.org/details/markpines and maintains a SQLite database of all 1,327 media items (27TB total). The database enables browsing and planning programming for the channel without downloading the actual media files.

## Installation

```bash
python3 -m venv tv
source tv/bin/activate
pip install -r requirements.txt
```

## Usage

### Crawl the collection
```bash
python crawler.py
```

### Show library statistics
```bash
python crawler.py --stats
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