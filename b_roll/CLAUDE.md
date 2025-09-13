# Claude Context for B-Roll Media Library

## Project Overview
This is the media library crawler for The Bobbing Channel - a personal TV channel project that streams content from Archive.org to stream.place.

## Current State
- ✅ **Database populated**: 1,327 items from the markpines collection
- ✅ **Crawler working**: Simple, clean implementation in `crawler.py`
- 📊 **Collection stats**: 1,321 movies, 5 collections, 1 audio item (27TB total)

## Key Information

### Archive.org Collection
- **URL**: https://archive.org/details/markpines
- **API Query**: `collection:markpines`
- **Public collection** - no authentication needed
- **Total items**: 1,327 (as of 2025-09-13)

### Database Schema
The SQLite database (`media_library.db`) has these columns:
- `identifier` (TEXT PRIMARY KEY) - Archive.org item ID
- `title` (TEXT)
- `creator` (TEXT)
- `date` (TEXT)
- `year` (INTEGER)
- `mediatype` (TEXT) - movies/audio/collection
- `description` (TEXT)
- `collection` (TEXT)
- `downloads` (INTEGER)
- `item_size` (INTEGER) - in bytes
- `item_url` (TEXT) - Full Archive.org URL
- `thumbnail_url` (TEXT) - Thumbnail service URL
- `crawled_at` (TIMESTAMP)

### Important Commands
```bash
# Always use virtual environment
source tv/bin/activate

# Re-crawl collection (updates database)
python crawler.py

# View statistics
python crawler.py --stats

# Query database directly
python -c "import sqlite3; conn = sqlite3.connect('media_library.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM media'); print(f'Total items: {cursor.fetchone()[0]}')"
```

## Next Steps & Ideas

### Immediate Next Steps
1. **Web Interface**: Build a local web app to browse the 1,327 items
   - Filter by mediatype, year, creator
   - Search functionality
   - Thumbnail grid view
   - Item details page

2. **Playlist Builder**: Create programming schedules
   - Group items into "shows"
   - Time-based scheduling
   - Random selection modes
   - Themed collections

3. **Streaming Pipeline**: Connect to stream.place
   - Download items on-demand from Archive.org
   - Local cache management (SD card space)
   - FFmpeg transcoding if needed
   - Stream scheduling

### Technical Considerations
- **Raspberry Pi constraints**: Limited CPU/RAM, use lightweight solutions
- **SD card space**: Can't store all 27TB, need smart caching
- **Network bandwidth**: Stream from Archive.org, cache popular items
- **Archive.org rate limits**: Be respectful, add delays between requests

### Potential Issues & Solutions
- **Issue**: Some items might be restricted/removed
  - **Solution**: Handle 404s gracefully, mark items as unavailable
  
- **Issue**: Database might get out of sync
  - **Solution**: Regular re-crawls, track last_checked timestamps
  
- **Issue**: Stream.place API changes
  - **Solution**: Abstract streaming layer, make it adaptable

## Context from Development

### Why This Approach
1. **Started complex**: Tried Selenium, browser automation, API discovery
2. **Found simple solution**: The collection URL was actually `markpines` not `@mark_pines_archive_project`
3. **Learned**: Archive.org has straightforward API, no auth needed for public data
4. **Final result**: 247-line Python script that just works

### Lessons Learned
- Archive.org Search API is well-documented and reliable
- The `collection:` query parameter is key for getting collection items
- Pagination with `page` and `rows` parameters (max 500 rows/page)
- Always check actual URLs - sometimes the obvious path is right

## For Future Claude Sessions

When continuing this project:
1. **Check database first**: `python crawler.py --stats` to see current state
2. **Preserve the database**: Don't recreate tables, they have 1,327 items already
3. **Test in virtual env**: Always `source tv/bin/activate` first
4. **Keep it simple**: This runs on a Raspberry Pi, avoid heavy dependencies

The goal is to create a unique, personal TV channel with curated content. Think public-access TV meets modern streaming, with a focus on interesting/obscure media from the Archive.org collection.