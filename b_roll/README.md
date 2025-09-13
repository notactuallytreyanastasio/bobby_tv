# B-Roll Media Library

Archive.org media crawler and SQLite database for The Bobbing Channel.

## Purpose

This tool crawls the Archive.org collection at https://archive.org/details/@mark_pines_archive_project and builds a local SQLite database of all available media with metadata. This allows us to browse and plan programming for the channel without downloading the actual media files.

## Features

- Crawls all uploads from a specified Archive.org user
- Extracts comprehensive metadata (title, description, thumbnails, duration, etc.)
- Stores everything in a SQLite database for fast querying
- Provides statistics on the media collection
- Handles video, audio, and other media types

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Initial crawl
```bash
python crawler.py
```

### Show library statistics
```bash
python crawler.py --stats
```

### Specify custom database
```bash
python crawler.py --db custom.db
```

### Crawl different user
```bash
python crawler.py --user different_archive_user
```

## Database Schema

The SQLite database contains two main tables:

### media
- `identifier`: Archive.org unique ID (primary key)
- `title`: Media title
- `description`: Full description
- `creator`: Creator/uploader
- `date`: Upload/creation date
- `mediatype`: Type of media (movies, audio, etc.)
- `collection`: Collection it belongs to
- `thumbnail_url`: URL to thumbnail image
- `download_url`: Direct download URL for the media
- `duration`: Length of media (for video/audio)
- `size`: File size in bytes
- `format`: File format
- `views`: View count
- `downloads`: Download count
- `subject`: Tags/subjects (JSON)
- `language`: Language code
- `licenseurl`: License URL
- `crawled_at`: When we crawled this item
- `raw_metadata`: Complete metadata JSON

### crawl_history
Tracks crawl runs for monitoring and debugging.

## Next Steps

After populating the database, a web interface will be built to:
- Browse the media library
- Search and filter content
- Plan channel programming
- Mark favorites and create playlists
- Preview thumbnails and metadata

## Notes for Future Development

- Database is stored as `media_library.db` by default
- Crawler includes rate limiting to be respectful to Archive.org
- All metadata is preserved in raw_metadata field for future needs
- Thumbnail URLs are extracted when available, with fallback to Archive.org's default
- Video files prioritize original uploads over derivatives