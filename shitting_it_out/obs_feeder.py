#!/usr/bin/env python3
"""
OBS Feeder - Seamlessly rotates videos for OBS Media Source
Maintains a single file that OBS reads while swapping content behind the scenes
"""

import os
import shutil
import time
import subprocess
from pathlib import Path
import json
from datetime import datetime
import threading
from video_manager import VideoManager

class OBSFeeder:
    def __init__(self):
        self.video_dir = Path('streaming_videos')
        self.video_dir.mkdir(exist_ok=True)

        # The file OBS will read (always the same name)
        self.obs_file = self.video_dir / 'current_stream.mp4'
        self.next_file = self.video_dir / 'next_stream.mp4'

        # Video manager handles downloading and deletion
        self.video_manager = VideoManager()

        self.state_file = Path('obs_feeder_state.json')
        self.load_state()

    def load_state(self):
        """Load feeder state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {
                'current_video': None,
                'current_duration': 0,
                'started_at': None,
                'total_played': 0
            }

    def save_state(self):
        """Save feeder state"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get_video_duration(self, video_path):
        """Get video duration in seconds"""
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

    def prepare_next_video(self):
        """Prepare the next video in the background"""
        # Get next video from video manager
        next_video_info = self.video_manager.get_next_video()

        if not next_video_info:
            print("⚠️  No videos available! Downloading more...")
            # Trigger video download
            self.video_manager.maintain_library()
            next_video_info = self.video_manager.get_next_video()

        if next_video_info:
            next_video_path = Path(next_video_info['path'])
            print(f"📥 Preparing next: {next_video_info['title']}")

            # Copy to next_file (so it's ready to swap)
            shutil.copy2(next_video_path, self.next_file)

            # Store the identifier so we can mark it played later
            self.state['next_identifier'] = next_video_info['identifier']
            self.save_state()

            return self.next_file

        return None

    def swap_videos(self):
        """Atomically swap current video with next"""
        if not self.next_file.exists():
            print("❌ No next video prepared!")
            return False

        print(f"🔄 Swapping videos...")

        # Mark the current video as played (will delete it)
        if self.state.get('current_identifier'):
            self.video_manager.mark_video_played(self.state['current_identifier'])

        # Method 1: Atomic rename (least interruption)
        temp_file = self.video_dir / 'temp_stream.mp4'

        # Move current to temp
        if self.obs_file.exists():
            self.obs_file.rename(temp_file)

        # Move next to current
        self.next_file.rename(self.obs_file)

        # Clean up temp
        if temp_file.exists():
            temp_file.unlink()

        # Update current identifier
        self.state['current_identifier'] = self.state.get('next_identifier')
        self.state['next_identifier'] = None

        print(f"✅ Swap complete!")
        return True

    def monitor_playback(self):
        """Monitor current video and swap when needed"""
        if not self.state['current_video']:
            return False

        if not self.state['started_at']:
            return False

        # Calculate elapsed time
        started = datetime.fromisoformat(self.state['started_at'])
        elapsed = (datetime.now() - started).total_seconds()
        duration = self.state['current_duration']

        if duration > 0:
            remaining = duration - elapsed
            progress = (elapsed / duration) * 100

            print(f"▶️  Progress: {progress:.1f}% ({elapsed:.0f}s / {duration:.0f}s)")
            print(f"   Remaining: {remaining:.0f}s")

            # Start preparing next video when current is 75% done
            if progress > 75 and not self.next_file.exists():
                print("🎬 Preparing next video...")
                threading.Thread(target=self.prepare_next_video).start()

            # Swap when video is about to end (within 2 seconds)
            if remaining <= 2:
                print("⏰ Video ending, time to swap!")
                return True

        return False

    def initialize_stream(self):
        """Set up initial video for OBS"""
        print("\n🎬 Initializing OBS stream file...")

        # Make sure we have videos
        self.video_manager.maintain_library()

        # Get first video
        first_video_info = self.video_manager.get_next_video()

        if first_video_info:
            first_video_path = Path(first_video_info['path'])
            print(f"🎥 Setting up first video: {first_video_info['title']}")

            # Copy as current stream
            shutil.copy2(first_video_path, self.obs_file)

            # Update state
            self.state['current_video'] = first_video_info['title']
            self.state['current_identifier'] = first_video_info['identifier']
            self.state['current_duration'] = self.get_video_duration(self.obs_file)
            self.state['started_at'] = datetime.now().isoformat()
            self.save_state()

            print(f"✅ Stream file ready: {self.obs_file}")
            print(f"   Duration: {self.state['current_duration']:.0f}s")

            # Prepare next video
            self.prepare_next_video()

            return True

        return False

    def run_feeder(self):
        """Main feeder loop"""
        print("\n📺 OBS Feeder Starting...")
        print("="*50)

        # Initialize if needed
        if not self.obs_file.exists():
            if not self.initialize_stream():
                print("❌ Failed to initialize stream!")
                return

        print(f"\n✅ Configure OBS Media Source to read:")
        print(f"   {self.obs_file.absolute()}")
        print(f"\n   Make sure 'Loop' is CHECKED in Media Source!")
        print("\n" + "="*50)

        while True:
            try:
                # Check if we need to swap
                if self.monitor_playback():
                    if self.swap_videos():
                        # Update state for new video
                        self.state['current_duration'] = self.get_video_duration(self.obs_file)
                        self.state['started_at'] = datetime.now().isoformat()
                        self.state['total_played'] += 1
                        self.save_state()

                        # Prepare next video
                        threading.Thread(target=self.prepare_next_video).start()

                # Check storage and download more if needed
                storage = self.video_manager.get_storage_info()
                print(f"\n📊 Status: Videos: {storage['video_count']} | Storage: {storage['video_gb']:.1f}GB | Played: {self.state['total_played']}")

                # Maintain library (download more if space available)
                if storage['can_download']:
                    print("📥 Maintaining video library...")
                    self.video_manager.maintain_library()

                # Sleep for a bit
                time.sleep(10)  # Check every 10 seconds

            except KeyboardInterrupt:
                print("\n👋 Stopping OBS Feeder...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(5)

    def status(self):
        """Show current status"""
        print("\n📊 OBS Feeder Status")
        print("="*50)

        if self.obs_file.exists():
            print(f"✅ Stream file: {self.obs_file.name}")
            print(f"   Size: {self.obs_file.stat().st_size / (1024**2):.1f}MB")
        else:
            print("❌ No stream file")

        if self.next_file.exists():
            print(f"📥 Next ready: {self.next_file.name}")

        # Get storage info from video manager
        storage = self.video_manager.get_storage_info()
        print(f"\n📚 Library:")
        print(f"   Videos available: {storage['video_count']}")
        print(f"   Storage used: {storage['video_gb']:.1f}GB / 40GB")
        print(f"   Free space: {storage['free_gb']:.1f}GB")
        print(f"   Total streamed: {self.state.get('total_played', 0)} videos")

        if self.state.get('started_at'):
            started = datetime.fromisoformat(self.state['started_at'])
            elapsed = (datetime.now() - started).total_seconds()
            duration = self.state.get('current_duration', 0)
            if duration > 0:
                progress = (elapsed / duration) * 100
                remaining = duration - elapsed
                print(f"\n▶️  Current playback:")
                print(f"   Progress: {progress:.1f}%")
                print(f"   Remaining: {remaining:.0f}s")


def main():
    import sys

    feeder = OBSFeeder()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'run':
            feeder.run_feeder()
        elif command == 'init':
            feeder.initialize_stream()
        elif command == 'status':
            feeder.status()
        elif command == 'swap':
            feeder.swap_videos()
        else:
            print("Commands: run, init, status, swap")
    else:
        feeder.run_feeder()


if __name__ == "__main__":
    main()