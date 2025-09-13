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

class OBSFeeder:
    def __init__(self):
        self.video_dir = Path('streaming_videos')
        self.video_dir.mkdir(exist_ok=True)

        # The file OBS will read (always the same name)
        self.obs_file = self.video_dir / 'current_stream.mp4'
        self.next_file = self.video_dir / 'next_stream.mp4'

        # Queue management
        self.queue_dir = self.video_dir / 'queue'
        self.queue_dir.mkdir(exist_ok=True)
        self.played_dir = self.video_dir / 'played'
        self.played_dir.mkdir(exist_ok=True)

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
        # Get all videos in queue
        queue_videos = sorted(self.queue_dir.glob('*.mp4'))

        if not queue_videos:
            print("⚠️  No videos in queue! Downloading more...")
            # Trigger video download
            subprocess.run(['python', 'video_manager.py', 'maintain'])
            queue_videos = sorted(self.queue_dir.glob('*.mp4'))

        if queue_videos:
            next_video = queue_videos[0]
            print(f"📥 Preparing next: {next_video.name}")

            # Copy to next_file (so it's ready to swap)
            shutil.copy2(next_video, self.next_file)

            # Move original to played
            shutil.move(str(next_video), self.played_dir / next_video.name)

            return self.next_file

        return None

    def swap_videos(self):
        """Atomically swap current video with next"""
        if not self.next_file.exists():
            print("❌ No next video prepared!")
            return False

        print(f"🔄 Swapping videos...")

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

        # Move any existing videos to queue
        for video in self.video_dir.glob('*.mp4'):
            if video.name not in ['current_stream.mp4', 'next_stream.mp4']:
                print(f"  Moving {video.name} to queue")
                shutil.move(str(video), self.queue_dir / video.name)

        # Get first video
        queue_videos = sorted(self.queue_dir.glob('*.mp4'))

        if not queue_videos:
            print("📥 No videos found, downloading...")
            subprocess.run(['python', 'video_manager.py', 'maintain'])
            queue_videos = sorted(self.queue_dir.glob('*.mp4'))

        if queue_videos:
            first_video = queue_videos[0]
            print(f"🎥 Setting up first video: {first_video.name}")

            # Copy as current stream
            shutil.copy2(first_video, self.obs_file)

            # Move original to played
            shutil.move(str(first_video), self.played_dir / first_video.name)

            # Update state
            self.state['current_video'] = first_video.name
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

                # Clean up played directory if too full
                played_videos = list(self.played_dir.glob('*.mp4'))
                if len(played_videos) > 10:
                    print("🧹 Cleaning old played videos...")
                    for video in played_videos[:-5]:  # Keep last 5
                        video.unlink()

                # Check queue health
                queue_count = len(list(self.queue_dir.glob('*.mp4')))
                print(f"\n📊 Status: Queue: {queue_count} | Played: {self.state['total_played']}")

                # Download more if queue is low
                if queue_count < 2:
                    print("📥 Queue low, downloading more videos...")
                    subprocess.run(['python', 'video_manager.py', 'maintain'])

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

        queue_count = len(list(self.queue_dir.glob('*.mp4')))
        played_count = len(list(self.played_dir.glob('*.mp4')))

        print(f"\n📚 Library:")
        print(f"   Queue: {queue_count} videos")
        print(f"   Played: {played_count} videos")
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