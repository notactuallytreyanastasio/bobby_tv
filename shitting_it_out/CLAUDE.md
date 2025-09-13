# Bobby TV Streaming System - Claude Context

## Project Overview

This is a 24/7 streaming TV channel system that broadcasts Archive.org content to stream.place. It's designed to run on limited hardware (like a Raspberry Pi) with intelligent storage management.

## Key Design Decisions

### Storage Management
- **2-video rotation**: Only keeps current + next video to minimize storage
- **40GB limit**: Configurable max storage with 10GB per video max
- **Just-in-time downloads**: Downloads next video while current plays
- **Auto-cleanup**: Deletes watched videos immediately after playback

### Streaming Architecture
- **OBS Studio**: Primary streaming engine (or FFmpeg as lightweight alternative)
- **RTMP Protocol**: Streams to stream.place/live
- **HTML Overlays**: Browser sources in OBS for dynamic content
- **Bluesky Integration**: Live ticker showing social media posts

## Important Context

### Database Location
The system expects the Archive.org catalog database at `../b_roll/media_library.db`. This contains metadata for 1,327 videos from Archive.org.

### Content Selection
Videos are selected randomly from the database, excluding recently played items. The system prioritizes variety and avoids repeating content within 100 plays.

### Network Considerations
- Requires stable internet for Archive.org downloads
- RTMP streaming needs consistent upload bandwidth
- Downloads happen during playback to avoid interruptions

## Code Organization

Each Python module is self-contained with a CLI interface:
- Run without arguments for default behavior
- Pass command names for specific actions
- All have `--help` or show commands when given invalid input

## Testing Approach

1. **Local Testing**: Test video downloads first with `video_manager.py`
2. **Overlay Testing**: Open HTML files directly in browser
3. **OBS Testing**: Use OBS recording instead of streaming initially
4. **Stream Testing**: Test with short videos first

## Common Issues & Solutions

### Issue: Videos not downloading
- Check database path exists
- Verify Archive.org is accessible
- Check disk space available

### Issue: OBS not playing videos
- Ensure VLC source is installed in OBS
- Set playlist to loop
- Check file paths are absolute

### Issue: Stream dropping
- Reduce bitrate in OBS settings
- Check network stability
- Consider using FFmpeg directly

## Performance Optimization

### For Raspberry Pi
- Use FFmpeg instead of OBS (`obs_controller.py ffmpeg`)
- Reduce video bitrate to 2000-3000 kbps
- Lower resolution to 720p
- Disable complex overlays

### For Limited Bandwidth
- Adjust `MAX_VIDEO_SIZE_GB` lower
- Increase download buffer time
- Pre-download during off-peak hours

## Extension Points

### Adding New Overlays
Create new HTML files in `overlays/` and add as Browser Sources in OBS.

### Custom Content Sources
Modify `video_manager.py` to pull from different sources beyond Archive.org.

### Social Media Integration
Extend `bluesky_ticker.py` to pull from multiple social platforms.

### Scheduling
Add time-based programming blocks (morning cartoons, evening movies, etc.)

## Architecture Decisions

### Why OBS?
- Industry standard for streaming
- Supports complex scenes and transitions
- Has VLC source for playlist playback
- Browser sources for dynamic overlays

### Why Archive.org?
- Massive public domain collection
- Reliable CDN for downloads
- Rich metadata for content discovery
- Free and legal content

### Why stream.place?
- Built on AT Protocol (decentralized)
- Integrates with Bluesky ecosystem
- Modern streaming platform
- Developer-friendly

## Future Enhancements

1. **Smart Scheduling**: Time-based content blocks
2. **Viewer Interaction**: Bluesky mentions trigger content changes
3. **Analytics**: Track what's popular, adjust rotation
4. **Multi-Channel**: Run several themed channels
5. **Local Cache**: Keep popular videos permanently

## Important Files

- `streaming_state.json`: Current playback state
- `playlist.json`: Download history and queue
- `streaming_config.json`: RTMP and video settings
- `bluesky_config.json`: Social media credentials
- `ticker_data.json`: Current ticker content

## Debug Commands

```bash
# Check current streaming state
python stream_coordinator.py status

# Force video rotation
python stream_coordinator.py rotate

# See storage usage
python video_manager.py status

# Test Bluesky connection
python bluesky_ticker.py test

# Generate FFmpeg command for debugging
python obs_controller.py ffmpeg
```

## Resource Usage

- **CPU**: Moderate (video transcoding if needed)
- **RAM**: ~500MB for Python scripts
- **Disk I/O**: Burst during downloads
- **Network**: Continuous upload (4-8 Mbps)
- **Storage**: 40GB for videos + overhead

## Security Notes

- Store Bluesky app password securely
- Don't commit credentials to git
- Use app-specific passwords, not main password
- RTMP stream key should be kept private

## Maintenance

- Clear old logs periodically
- Check `played_history` doesn't grow too large
- Monitor disk space trends
- Restart coordinator if memory grows
- Update Archive.org database occasionally