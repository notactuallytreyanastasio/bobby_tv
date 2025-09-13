#!/usr/bin/env python3
"""
Stream Coordinator for Bobby TV
Manages the continuous streaming flow with minimal storage footprint
Keeps only current + next video, downloads new content just-in-time
"""

import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
import threading
import os

class StreamCoordinator:
    def __init__(self):
        self.state_file = Path('streaming_state.json')
        self.video_dir = Path('streaming_videos')
        self.video_dir.mkdir(exist_ok=True)
        self.load_state()
        self.download_lock = threading.Lock()

    def load_state(self):
        """Load streaming state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {
                'now_playing': None,
                'up_next': None,
                'played_history': [],
                'start_time': None,
                'status': 'idle'
            }
            self.save_state()

    def save_state(self):
        """Save streaming state"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get_video_duration(self, video_path):
        """Get video duration in seconds using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception as e:
            print(f"Error getting duration: {e}")
        return 0

    def get_storage_status(self):
        """Get current storage usage"""
        videos = list(self.video_dir.glob('*.mp4'))
        total_size = sum(v.stat().st_size for v in videos) / (1024**3)

        return {
            'video_count': len(videos),
            'total_gb': total_size,
            'videos': [v.name for v in videos]
        }

    def download_next_video(self):
        """Download the next video from catalog"""
        with self.download_lock:
            # Use video_manager to download one video
            result = subprocess.run(
                ['python', 'video_manager.py', 'maintain'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print("✓ Downloaded next video")
                return True
            else:
                print(f"✗ Download failed: {result.stderr}")
                return False

    def cleanup_old_video(self, keep_files=None):
        """Remove videos that are no longer needed"""
        if keep_files is None:
            keep_files = []

        videos = list(self.video_dir.glob('*.mp4'))
        for video in videos:
            if video.name not in keep_files:
                print(f"🗑 Removing: {video.name}")
                video.unlink()

    def rotate_videos(self):
        """Rotate videos: current becomes old, next becomes current"""
        # Move up_next to now_playing
        if self.state['up_next']:
            # Clean up the previously playing video
            if self.state['now_playing']:
                old_file = self.video_dir / self.state['now_playing']['file']
                if old_file.exists():
                    print(f"🗑 Removing finished: {old_file.name}")
                    old_file.unlink()

                # Add to history
                self.state['played_history'].append({
                    'identifier': self.state['now_playing'].get('identifier'),
                    'played_at': datetime.now().isoformat()
                })

                # Keep history limited
                if len(self.state['played_history']) > 100:
                    self.state['played_history'] = self.state['played_history'][-50:]

            # Promote next to current
            self.state['now_playing'] = self.state['up_next']
            self.state['up_next'] = None
            self.state['start_time'] = datetime.now().isoformat()

            print(f"▶️ Now playing: {self.state['now_playing']['title']}")

            # Start downloading next video in background
            download_thread = threading.Thread(target=self.prepare_next_video)
            download_thread.daemon = True
            download_thread.start()

    def prepare_next_video(self):
        """Download and prepare the next video"""
        print("📥 Preparing next video...")

        # Download a new video
        if self.download_next_video():
            # Find the newest video that's not currently playing
            videos = sorted(
                self.video_dir.glob('*.mp4'),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )

            current_file = self.state['now_playing']['file'] if self.state['now_playing'] else None

            for video in videos:
                if video.name != current_file:
                    # This is our next video
                    duration = self.get_video_duration(video)

                    self.state['up_next'] = {
                        'file': video.name,
                        'title': video.stem,
                        'duration': duration,
                        'ready_at': datetime.now().isoformat()
                    }

                    print(f"✓ Up next: {video.name}")
                    self.save_state()
                    break

    def generate_active_playlist(self):
        """Generate playlist with only current and next video"""
        playlist_file = self.video_dir / 'active_playlist.m3u'

        with open(playlist_file, 'w') as f:
            f.write("#EXTM3U\n")

            # Add current video
            if self.state['now_playing']:
                current_path = self.video_dir / self.state['now_playing']['file']
                if current_path.exists():
                    f.write(f"#EXTINF:-1,{self.state['now_playing']['title']}\n")
                    f.write(f"{current_path.absolute()}\n")

            # Add next video
            if self.state['up_next']:
                next_path = self.video_dir / self.state['up_next']['file']
                if next_path.exists():
                    f.write(f"#EXTINF:-1,{self.state['up_next']['title']}\n")
                    f.write(f"{next_path.absolute()}\n")

        return playlist_file

    def monitor_playback(self):
        """Monitor current playback and rotate when needed"""
        if not self.state['now_playing']:
            print("No video currently playing")
            return False

        if not self.state['start_time']:
            return False

        # Calculate elapsed time
        start = datetime.fromisoformat(self.state['start_time'])
        elapsed = (datetime.now() - start).total_seconds()
        duration = self.state['now_playing'].get('duration', 0)

        if duration > 0:
            remaining = duration - elapsed
            progress = (elapsed / duration) * 100

            print(f"⏱ Progress: {progress:.1f}% ({elapsed:.0f}s / {duration:.0f}s)")
            print(f"  Remaining: {remaining:.0f}s")

            # Check if video is almost done (within 10 seconds)
            if remaining <= 10:
                if self.state['up_next']:
                    print("🔄 Video ending soon, preparing rotation...")
                    return True
                else:
                    print("⚠️ No next video ready!")
                    self.prepare_next_video()

        return False

    def run_coordinator(self):
        """Main coordination loop"""
        print("\n🎬 Bobby TV Stream Coordinator")
        print("=" * 50)

        # Initial setup
        if not self.state['now_playing']:
            print("📥 Initial setup - downloading first videos...")
            self.download_next_video()
            time.sleep(2)
            self.download_next_video()

            # Set up initial state
            videos = sorted(
                self.video_dir.glob('*.mp4'),
                key=lambda x: x.stat().st_mtime
            )

            if len(videos) >= 2:
                self.state['now_playing'] = {
                    'file': videos[0].name,
                    'title': videos[0].stem,
                    'duration': self.get_video_duration(videos[0])
                }
                self.state['up_next'] = {
                    'file': videos[1].name,
                    'title': videos[1].stem,
                    'duration': self.get_video_duration(videos[1])
                }
                self.state['start_time'] = datetime.now().isoformat()
                self.save_state()

        print("\n📺 Streaming started!")
        print(f"Now playing: {self.state['now_playing']['title']}")
        print(f"Up next: {self.state['up_next']['title'] if self.state['up_next'] else 'Loading...'}")

        # Main monitoring loop
        while True:
            try:
                # Update playlist
                self.generate_active_playlist()

                # Check if we need to rotate
                if self.monitor_playback():
                    self.rotate_videos()

                # Show storage status
                storage = self.get_storage_status()
                print(f"\n💾 Storage: {storage['video_count']} videos, {storage['total_gb']:.2f}GB")

                self.save_state()

                # Check every 30 seconds
                time.sleep(30)

            except KeyboardInterrupt:
                print("\n👋 Stopping coordinator...")
                break
            except Exception as e:
                print(f"Error in coordinator: {e}")
                time.sleep(5)

    def status(self):
        """Show current streaming status"""
        print("\n📊 Bobby TV Stream Status")
        print("=" * 50)

        if self.state['now_playing']:
            print(f"▶️ Now Playing: {self.state['now_playing']['title']}")
            if self.state['start_time']:
                start = datetime.fromisoformat(self.state['start_time'])
                elapsed = (datetime.now() - start).total_seconds()
                duration = self.state['now_playing'].get('duration', 0)
                if duration > 0:
                    progress = (elapsed / duration) * 100
                    print(f"   Progress: {progress:.1f}% ({elapsed:.0f}s / {duration:.0f}s)")
        else:
            print("⏸ Not playing")

        if self.state['up_next']:
            print(f"⏭ Up Next: {self.state['up_next']['title']}")
        else:
            print("⏭ Up Next: Preparing...")

        storage = self.get_storage_status()
        print(f"\n💾 Storage: {storage['video_count']} videos, {storage['total_gb']:.2f}GB")
        print(f"   Files: {', '.join(storage['videos'])}")

        print(f"\n📜 History: {len(self.state['played_history'])} videos played")


def main():
    """Main entry point"""
    import sys

    coordinator = StreamCoordinator()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'run':
            coordinator.run_coordinator()
        elif command == 'status':
            coordinator.status()
        elif command == 'rotate':
            coordinator.rotate_videos()
        elif command == 'playlist':
            playlist = coordinator.generate_active_playlist()
            print(f"Playlist generated: {playlist}")
        elif command == 'cleanup':
            coordinator.cleanup_old_video()
        else:
            print("Commands: run, status, rotate, playlist, cleanup")
    else:
        coordinator.run_coordinator()


if __name__ == "__main__":
    main()