#!/usr/bin/env python3
"""
Video Manager for Bobby TV - Smart rotation system for limited disk space
Manages downloading, playing, and deleting videos to stay within storage limits
"""

import sqlite3
import os
import requests
import json
from pathlib import Path
import time
import shutil
from datetime import datetime

# Configuration
DB_PATH = '../b_roll/media_library.db'
VIDEO_DIR = Path('streaming_videos')
MAX_STORAGE_GB = 40  # Maximum storage to use
MIN_FREE_SPACE_GB = 10  # Always keep this much free space
MAX_VIDEO_SIZE_GB = 10  # Max size per video
VIDEOS_TO_MAINTAIN = 2  # Keep only current + next video ready

class VideoManager:
    def __init__(self):
        self.video_dir = VIDEO_DIR
        self.video_dir.mkdir(exist_ok=True)
        self.playlist_file = self.video_dir / 'playlist.json'
        self.load_playlist()

    def load_playlist(self):
        """Load or create playlist tracking"""
        if self.playlist_file.exists():
            with open(self.playlist_file, 'r') as f:
                self.playlist = json.load(f)
        else:
            self.playlist = {
                'current': None,
                'queue': [],
                'played': [],
                'downloaded': {}
            }

    def save_playlist(self):
        """Save playlist state"""
        with open(self.playlist_file, 'w') as f:
            json.dump(self.playlist, f, indent=2)

    def get_storage_info(self):
        """Get current storage statistics"""
        # Get disk usage
        stat = shutil.disk_usage(self.video_dir)
        free_gb = stat.free / (1024**3)

        # Calculate video directory size
        video_size = sum(f.stat().st_size for f in self.video_dir.glob('*.mp4'))
        video_gb = video_size / (1024**3)

        return {
            'free_gb': free_gb,
            'video_gb': video_gb,
            'video_count': len(list(self.video_dir.glob('*.mp4'))),
            'can_download': free_gb > MIN_FREE_SPACE_GB and video_gb < MAX_STORAGE_GB
        }

    def get_db(self):
        """Get database connection"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def find_next_videos(self, count=5):
        """Find videos to download that haven't been played recently"""
        conn = self.get_db()
        cursor = conn.cursor()

        # Get played identifiers to exclude
        played_ids = self.playlist.get('played', [])[-100:]  # Last 100 played

        # Build exclusion clause
        if played_ids:
            placeholders = ','.join(['?' for _ in played_ids])
            exclude_clause = f"AND identifier NOT IN ({placeholders})"
            params = played_ids
        else:
            exclude_clause = ""
            params = []

        # Query for videos
        query = f"""
            SELECT identifier, title, item_size, downloads, creator, year
            FROM media
            WHERE mediatype = 'movies'
            AND item_size > 0
            AND item_size < ?
            {exclude_clause}
            ORDER BY RANDOM()
            LIMIT ?
        """

        params = [MAX_VIDEO_SIZE_GB * 1024 * 1024 * 1024] + params + [count]
        cursor.execute(query, params)

        items = cursor.fetchall()
        conn.close()
        return items

    def get_archive_metadata(self, identifier):
        """Get metadata from Archive.org"""
        url = f"https://archive.org/metadata/{identifier}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"  Error fetching metadata: {e}")
        return None

    def download_video(self, item):
        """Download a video if space available"""
        storage = self.get_storage_info()

        if not storage['can_download']:
            print(f"  ⚠ Cannot download: Storage limit reached or low disk space")
            return None

        metadata = self.get_archive_metadata(item['identifier'])
        if not metadata:
            return None

        # Find smallest MP4
        mp4_files = []
        if 'files' in metadata:
            for file_info in metadata['files']:
                if file_info.get('name', '').lower().endswith('.mp4'):
                    size_gb = int(file_info.get('size', 0)) / (1024**3)
                    if size_gb <= MAX_VIDEO_SIZE_GB:
                        mp4_files.append(file_info)

        if not mp4_files:
            print(f"  No suitable MP4 files found")
            return None

        # Get smallest file
        mp4_files.sort(key=lambda x: int(x.get('size', 0)))
        selected = mp4_files[0]

        # Prepare download
        file_name = selected['name']
        file_size_gb = int(selected.get('size', 0)) / (1024**3)
        download_url = f"https://archive.org/download/{item['identifier']}/{file_name}"

        # Create safe filename
        safe_title = "".join(c for c in item['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()[:40]
        output_file = self.video_dir / f"{item['identifier']}_{safe_title}.mp4"

        print(f"  Downloading: {item['title']} ({file_size_gb:.2f}GB)")

        try:
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            with open(output_file, 'wb') as f:
                downloaded = 0
                total = int(selected.get('size', 0))
                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = (downloaded / total) * 100 if total > 0 else 0
                        print(f"\r    Progress: {percent:.1f}% ({downloaded/(1024**3):.2f}GB / {file_size_gb:.2f}GB)", end='')

            print(f"\n  ✓ Downloaded successfully")

            # Update playlist
            self.playlist['downloaded'][item['identifier']] = {
                'file': str(output_file.name),
                'title': item['title'],
                'size_gb': file_size_gb,
                'downloaded_at': datetime.now().isoformat()
            }
            self.save_playlist()

            return output_file

        except Exception as e:
            print(f"\n  ✗ Download failed: {e}")
            if output_file.exists():
                output_file.unlink()
            return None

    def cleanup_old_videos(self, keep_current=True):
        """Remove played videos to free space"""
        storage = self.get_storage_info()

        if storage['free_gb'] > MIN_FREE_SPACE_GB and storage['video_gb'] < MAX_STORAGE_GB:
            return  # No cleanup needed

        print("\n🧹 Cleaning up old videos...")

        # Get list of videos sorted by modification time (oldest first)
        videos = sorted(self.video_dir.glob('*.mp4'), key=lambda x: x.stat().st_mtime)

        # Keep current playing video if specified
        current_file = None
        if keep_current and self.playlist.get('current'):
            current_info = self.playlist['downloaded'].get(self.playlist['current'])
            if current_info:
                current_file = self.video_dir / current_info['file']

        deleted_count = 0
        deleted_gb = 0

        for video in videos:
            # Don't delete current video
            if current_file and video == current_file:
                continue

            # Check if we still need to free space
            storage = self.get_storage_info()
            if storage['free_gb'] > MIN_FREE_SPACE_GB and storage['video_gb'] < MAX_STORAGE_GB:
                break

            # Delete video
            size_gb = video.stat().st_size / (1024**3)
            video.unlink()
            deleted_count += 1
            deleted_gb += size_gb

            # Update playlist
            for identifier, info in list(self.playlist['downloaded'].items()):
                if info['file'] == video.name:
                    del self.playlist['downloaded'][identifier]
                    break

            print(f"  Deleted: {video.name} ({size_gb:.2f}GB)")

        if deleted_count > 0:
            print(f"  Freed {deleted_gb:.2f}GB by deleting {deleted_count} videos")
            self.save_playlist()

    def maintain_library(self):
        """Main maintenance cycle - download new videos, cleanup old ones"""
        print("\n📚 Bobby TV Video Library Maintenance")
        print("=" * 50)

        # Show current status
        storage = self.get_storage_info()
        print(f"Storage Status:")
        print(f"  Videos: {storage['video_count']} files using {storage['video_gb']:.2f}GB")
        print(f"  Free Space: {storage['free_gb']:.2f}GB")
        print(f"  Limits: {MAX_STORAGE_GB}GB max, {MIN_FREE_SPACE_GB}GB min free")

        # Cleanup if needed
        self.cleanup_old_videos()

        # Calculate how many videos we need
        current_count = storage['video_count']
        needed = max(0, VIDEOS_TO_MAINTAIN - current_count)

        if needed == 0:
            print(f"\n✓ Library is full with {current_count} videos")
            return

        print(f"\n🎬 Downloading {needed} new videos...")

        # Find and download videos
        candidates = self.find_next_videos(needed * 2)  # Get extra candidates
        downloaded = 0

        for item in candidates:
            if downloaded >= needed:
                break

            print(f"\n[{downloaded+1}/{needed}] {item['title']}")
            print(f"  Year: {item['year']}, Downloads: {item['downloads']:,}")

            result = self.download_video(item)
            if result:
                downloaded += 1
                self.playlist['queue'].append(item['identifier'])
                time.sleep(2)  # Be nice to Archive.org

            # Check storage after each download
            storage = self.get_storage_info()
            if not storage['can_download']:
                print("\n⚠ Storage limit reached, stopping downloads")
                break

        self.save_playlist()

        # Final status
        storage = self.get_storage_info()
        print(f"\n{'=' * 50}")
        print(f"✓ Maintenance complete")
        print(f"  Videos ready: {storage['video_count']}")
        print(f"  Storage used: {storage['video_gb']:.2f}GB / {MAX_STORAGE_GB}GB")
        print(f"  Free space: {storage['free_gb']:.2f}GB")

    def get_next_video(self):
        """Get next video to play from queue"""
        if not self.playlist['queue']:
            # Refill queue from downloaded videos
            downloaded_ids = list(self.playlist['downloaded'].keys())
            if downloaded_ids:
                import random
                random.shuffle(downloaded_ids)
                self.playlist['queue'] = downloaded_ids

        if self.playlist['queue']:
            next_id = self.playlist['queue'].pop(0)
            self.playlist['current'] = next_id
            self.playlist['played'].append(next_id)

            # Keep played list from growing too large
            if len(self.playlist['played']) > 200:
                self.playlist['played'] = self.playlist['played'][-100:]

            self.save_playlist()

            video_info = self.playlist['downloaded'].get(next_id)
            if video_info:
                video_path = self.video_dir / video_info['file']
                if video_path.exists():
                    return {
                        'identifier': next_id,
                        'path': str(video_path),
                        'title': video_info['title']
                    }

        return None

    def generate_obs_playlist(self):
        """Generate playlist file for OBS VLC source"""
        playlist_m3u = self.video_dir / 'obs_playlist.m3u'

        with open(playlist_m3u, 'w') as f:
            f.write("#EXTM3U\n")

            # Add all downloaded videos
            for identifier, info in self.playlist['downloaded'].items():
                video_path = self.video_dir / info['file']
                if video_path.exists():
                    f.write(f"#EXTINF:-1,{info['title']}\n")
                    f.write(f"{video_path.absolute()}\n")

        print(f"Generated OBS playlist: {playlist_m3u}")
        return playlist_m3u


def main():
    """Main entry point"""
    import sys

    manager = VideoManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'maintain':
            manager.maintain_library()
        elif command == 'cleanup':
            manager.cleanup_old_videos()
        elif command == 'status':
            storage = manager.get_storage_info()
            print(f"Storage: {storage['video_count']} videos, {storage['video_gb']:.2f}GB used, {storage['free_gb']:.2f}GB free")
        elif command == 'playlist':
            manager.generate_obs_playlist()
        elif command == 'next':
            video = manager.get_next_video()
            if video:
                print(f"Next: {video['title']}\nPath: {video['path']}")
            else:
                print("No videos available")
        else:
            print(f"Unknown command: {command}")
    else:
        # Default: maintain library
        manager.maintain_library()


if __name__ == "__main__":
    main()