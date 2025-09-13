#!/usr/bin/env python3
"""
OBS Controller for Bobby TV
Manages OBS scenes, sources, and streaming to stream.place
"""

import json
import os
from pathlib import Path
import subprocess
import time

class OBSController:
    def __init__(self):
        self.config_dir = Path('obs_config')
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / 'streaming_config.json'
        self.load_config()

    def load_config(self):
        """Load or create streaming configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'rtmp': {
                    'server': 'rtmp://stream.place/live',  # Will need actual URL
                    'stream_key': 'YOUR_STREAM_KEY_HERE'
                },
                'video': {
                    'resolution': '1920x1080',
                    'fps': 30,
                    'bitrate': 4000  # kbps
                },
                'audio': {
                    'bitrate': 128,  # kbps
                    'sample_rate': 44100
                },
                'scenes': {}
            }
            self.save_config()

    def save_config(self):
        """Save configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"Config saved to {self.config_file}")

    def generate_obs_scene_collection(self):
        """Generate OBS scene collection JSON"""
        scene_collection = {
            "name": "Bobby TV",
            "scenes": [
                {
                    "name": "Main Channel",
                    "sources": [
                        {
                            "name": "Video Playlist",
                            "type": "vlc_source",
                            "settings": {
                                "playlist": str(Path('streaming_videos/obs_playlist.m3u').absolute()),
                                "loop": True,
                                "shuffle": False,
                                "playback_behavior": "always_play"
                            }
                        },
                        {
                            "name": "Channel Logo",
                            "type": "image_source",
                            "settings": {
                                "file": str(Path('assets/bobby_tv_logo.png').absolute())
                            },
                            "position": {
                                "x": 20,
                                "y": 20
                            },
                            "scale": {
                                "x": 0.2,
                                "y": 0.2
                            }
                        },
                        {
                            "name": "Now Playing",
                            "type": "text_gdiplus",
                            "settings": {
                                "text": "The Bobbing Channel",
                                "font": {
                                    "face": "Arial",
                                    "size": 32
                                }
                            },
                            "position": {
                                "x": 20,
                                "y": 1020
                            }
                        }
                    ]
                },
                {
                    "name": "Intermission",
                    "sources": [
                        {
                            "name": "Intermission Card",
                            "type": "image_source",
                            "settings": {
                                "file": str(Path('assets/intermission.png').absolute())
                            }
                        },
                        {
                            "name": "Background Music",
                            "type": "ffmpeg_source",
                            "settings": {
                                "local_file": str(Path('assets/intermission_music.mp3').absolute()),
                                "looping": True
                            }
                        }
                    ]
                }
            ],
            "output": {
                "mode": "Advanced",
                "streaming": {
                    "type": "rtmp_custom",
                    "settings": {
                        "server": self.config['rtmp']['server'],
                        "key": self.config['rtmp']['stream_key'],
                        "use_auth": False
                    }
                },
                "recording": {
                    "path": str(Path('recordings').absolute()),
                    "format": "mp4",
                    "encoder": "x264"
                },
                "video": {
                    "base_resolution": self.config['video']['resolution'],
                    "output_resolution": self.config['video']['resolution'],
                    "fps": self.config['video']['fps'],
                    "encoder": "x264",
                    "rate_control": "CBR",
                    "bitrate": self.config['video']['bitrate'],
                    "keyframe_interval": 2,
                    "preset": "veryfast",
                    "profile": "main"
                },
                "audio": {
                    "sample_rate": self.config['audio']['sample_rate'],
                    "bitrate": self.config['audio']['bitrate']
                }
            }
        }

        scene_file = self.config_dir / 'bobby_tv_scenes.json'
        with open(scene_file, 'w') as f:
            json.dump(scene_collection, f, indent=2)

        print(f"OBS Scene Collection saved to: {scene_file}")
        return scene_file

    def generate_obs_profile(self):
        """Generate OBS profile settings"""
        profile = {
            "general": {
                "name": "Bobby TV Stream"
            },
            "stream": {
                "service": "Custom",
                "server": self.config['rtmp']['server'],
                "key": self.config['rtmp']['stream_key']
            },
            "output": {
                "mode": "Advanced",
                "encoder": "x264",
                "rate_control": "CBR",
                "bitrate": self.config['video']['bitrate'],
                "keyframe_interval": 2,
                "cpu_preset": "veryfast",
                "profile": "main",
                "audio_bitrate": self.config['audio']['bitrate']
            },
            "video": {
                "base_resolution": self.config['video']['resolution'],
                "output_resolution": self.config['video']['resolution'],
                "fps": self.config['video']['fps']
            },
            "audio": {
                "sample_rate": self.config['audio']['sample_rate']
            }
        }

        profile_file = self.config_dir / 'bobby_tv_profile.json'
        with open(profile_file, 'w') as f:
            json.dump(profile, f, indent=2)

        print(f"OBS Profile saved to: {profile_file}")
        return profile_file

    def generate_ffmpeg_stream_command(self):
        """Generate ffmpeg command for direct streaming (backup option)"""
        playlist_file = Path('streaming_videos/obs_playlist.m3u')

        command = [
            'ffmpeg',
            '-re',  # Read input at native frame rate
            '-f', 'concat',
            '-safe', '0',
            '-i', str(playlist_file),
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-maxrate', f'{self.config["video"]["bitrate"]}k',
            '-bufsize', f'{self.config["video"]["bitrate"]*2}k',
            '-vf', f'scale={self.config["video"]["resolution"]}',
            '-g', str(self.config['video']['fps'] * 2),  # Keyframe interval
            '-c:a', 'aac',
            '-b:a', f'{self.config["audio"]["bitrate"]}k',
            '-ar', str(self.config['audio']['sample_rate']),
            '-f', 'flv',
            f'{self.config["rtmp"]["server"]}/{self.config["rtmp"]["stream_key"]}'
        ]

        return ' '.join(command)

    def update_stream_key(self, stream_key):
        """Update the stream key"""
        self.config['rtmp']['stream_key'] = stream_key
        self.save_config()
        print(f"Stream key updated")

    def update_rtmp_server(self, server_url):
        """Update RTMP server URL"""
        self.config['rtmp']['server'] = server_url
        self.save_config()
        print(f"RTMP server updated to: {server_url}")

    def show_setup_instructions(self):
        """Display setup instructions for OBS"""
        print("\n" + "="*60)
        print("🎬 Bobby TV OBS Setup Instructions")
        print("="*60)
        print("\n1. INSTALL OBS Studio:")
        print("   - Download from: https://obsproject.com")
        print("   - On Raspberry Pi: sudo apt install obs-studio")

        print("\n2. CONFIGURE STREAMING:")
        print("   Settings → Stream")
        print(f"   - Service: Custom")
        print(f"   - Server: {self.config['rtmp']['server']}")
        print(f"   - Stream Key: {self.config['rtmp']['stream_key']}")

        print("\n3. VIDEO SETTINGS:")
        print("   Settings → Video")
        print(f"   - Base Resolution: {self.config['video']['resolution']}")
        print(f"   - Output Resolution: {self.config['video']['resolution']}")
        print(f"   - FPS: {self.config['video']['fps']}")

        print("\n4. OUTPUT SETTINGS:")
        print("   Settings → Output (Advanced Mode)")
        print(f"   - Video Bitrate: {self.config['video']['bitrate']} kbps")
        print(f"   - Keyframe Interval: 2")
        print(f"   - CPU Usage Preset: veryfast")
        print(f"   - Audio Bitrate: {self.config['audio']['bitrate']} kbps")

        print("\n5. ADD VIDEO SOURCE:")
        print("   Sources → Add → VLC Video Source")
        print(f"   - Playlist: {Path('streaming_videos/obs_playlist.m3u').absolute()}")
        print("   - Loop Playlist: ✓")
        print("   - Show Source When Playlist Ends: ✓")

        print("\n6. ALTERNATIVE (Direct FFmpeg streaming):")
        print("   If OBS is too heavy for Pi, use this command:")
        print(f"   {self.generate_ffmpeg_stream_command()}")

        print("\n" + "="*60)


def main():
    """Main entry point"""
    import sys

    controller = OBSController()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'setup':
            controller.show_setup_instructions()
        elif command == 'scenes':
            controller.generate_obs_scene_collection()
        elif command == 'profile':
            controller.generate_obs_profile()
        elif command == 'ffmpeg':
            print(controller.generate_ffmpeg_stream_command())
        elif command == 'set-key' and len(sys.argv) > 2:
            controller.update_stream_key(sys.argv[2])
        elif command == 'set-server' and len(sys.argv) > 2:
            controller.update_rtmp_server(sys.argv[2])
        else:
            print("Commands: setup, scenes, profile, ffmpeg, set-key <key>, set-server <url>")
    else:
        controller.show_setup_instructions()


if __name__ == "__main__":
    main()