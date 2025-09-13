#!/usr/bin/env python3
"""
Bobby TV Overlay Generator
Creates HTML overlays for OBS with Bluesky posts ticker, channel branding, etc.
"""

import json
import requests
from pathlib import Path
from datetime import datetime
import time

class OverlayGenerator:
    def __init__(self):
        self.overlay_dir = Path('overlays')
        self.overlay_dir.mkdir(exist_ok=True)
        self.config_file = self.overlay_dir / 'overlay_config.json'
        self.load_config()

    def load_config(self):
        """Load or create overlay configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'bluesky': {
                    'handle': 'your-handle.bsky.social',
                    'app_password': '',  # Need to set this
                    'refresh_minutes': 5
                },
                'ticker': {
                    'speed': 30,  # Seconds for full scroll
                    'background_color': 'rgba(0, 0, 0, 0.8)',
                    'text_color': '#ffffff',
                    'font_size': '24px',
                    'font_family': 'Arial, sans-serif'
                },
                'branding': {
                    'channel_name': 'The Bobbing Channel',
                    'tagline': '24/7 Archive.org Classics',
                    'logo_position': 'top-right'
                }
            }
            self.save_config()

    def save_config(self):
        """Save configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def fetch_bluesky_posts(self):
        """Fetch recent posts from Bluesky"""
        posts = []

        # This is a simplified example - you'll need proper ATP authentication
        # For now, returning sample posts
        sample_posts = [
            "🎬 Now playing: Classic cartoons from the 1940s",
            "📺 Coming up next: Vintage educational films",
            "🎭 Tonight at 8PM: Public domain feature films",
            "📻 Remember to check out our catalog at bobby.tv",
            "🎪 The Bobbing Channel - Your 24/7 vintage entertainment",
            "🎨 Featuring content from Archive.org's vast collection",
            "📼 Over 1,300 titles in rotation",
            "🎯 Submit requests via Bluesky mentions",
        ]

        return sample_posts

    def generate_ticker_html(self):
        """Generate HTML for news ticker overlay"""
        posts = self.fetch_bluesky_posts()

        # Double the posts for seamless looping
        ticker_text = " • ".join(posts * 2)

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Bobby TV Ticker</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: {self.config['ticker']['font_family']};
            overflow: hidden;
            background: transparent;
        }}

        .ticker-container {{
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 60px;
            background: {self.config['ticker']['background_color']};
            display: flex;
            align-items: center;
            border-top: 3px solid #ff6b6b;
        }}

        .ticker-label {{
            background: linear-gradient(90deg, #ff6b6b, #ff8787);
            color: white;
            padding: 0 20px;
            height: 100%;
            display: flex;
            align-items: center;
            font-weight: bold;
            font-size: 18px;
            text-transform: uppercase;
            letter-spacing: 1px;
            min-width: 150px;
            justify-content: center;
            box-shadow: 2px 0 10px rgba(0,0,0,0.3);
        }}

        .ticker-content {{
            flex: 1;
            overflow: hidden;
            position: relative;
            height: 100%;
        }}

        .ticker-text {{
            position: absolute;
            white-space: nowrap;
            color: {self.config['ticker']['text_color']};
            font-size: {self.config['ticker']['font_size']};
            line-height: 60px;
            animation: scroll {self.config['ticker']['speed']}s linear infinite;
            padding-left: 100%;
        }}

        @keyframes scroll {{
            0% {{
                transform: translateX(0);
            }}
            100% {{
                transform: translateX(-50%);
            }}
        }}

        .flash {{
            animation: flash 1s ease-in-out;
        }}

        @keyframes flash {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.3; }}
        }}
    </style>
</head>
<body>
    <div class="ticker-container">
        <div class="ticker-label">BOBBY TV</div>
        <div class="ticker-content">
            <div class="ticker-text">{ticker_text}</div>
        </div>
    </div>

    <script>
        // Auto-refresh posts every few minutes
        setTimeout(() => {{
            location.reload();
        }}, {self.config['ticker']['refresh_minutes'] * 60 * 1000});
    </script>
</body>
</html>"""

        ticker_file = self.overlay_dir / 'ticker.html'
        with open(ticker_file, 'w') as f:
            f.write(html_content)

        print(f"Ticker overlay saved to: {ticker_file}")
        return ticker_file

    def generate_full_overlay_html(self):
        """Generate complete overlay with all elements"""
        posts = self.fetch_bluesky_posts()
        ticker_text = " • ".join(posts * 2)

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Bobby TV Full Overlay</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: {self.config['ticker']['font_family']};
            overflow: hidden;
            background: transparent;
            width: 1920px;
            height: 1080px;
            position: relative;
        }}

        /* Channel Bug / Logo */
        .channel-bug {{
            position: absolute;
            top: 30px;
            right: 30px;
            background: rgba(0, 0, 0, 0.7);
            padding: 15px 20px;
            border-radius: 10px;
            border: 2px solid #ff6b6b;
            color: white;
            backdrop-filter: blur(10px);
        }}

        .channel-name {{
            font-size: 24px;
            font-weight: bold;
            color: #ff6b6b;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }}

        .channel-tagline {{
            font-size: 14px;
            color: #ffffff;
            opacity: 0.9;
            margin-top: 5px;
        }}

        /* Now Playing */
        .now-playing {{
            position: absolute;
            bottom: 80px;
            left: 30px;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px 25px;
            border-radius: 10px;
            border-left: 4px solid #ff6b6b;
            max-width: 500px;
            backdrop-filter: blur(10px);
            display: none;  /* Will be shown via JavaScript */
        }}

        .now-playing-label {{
            color: #ff6b6b;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 8px;
        }}

        .now-playing-title {{
            color: white;
            font-size: 20px;
            font-weight: bold;
        }}

        .now-playing-info {{
            color: #cccccc;
            font-size: 14px;
            margin-top: 5px;
        }}

        /* News Ticker */
        .ticker-container {{
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 60px;
            background: linear-gradient(to right, rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.8));
            display: flex;
            align-items: center;
            border-top: 3px solid #ff6b6b;
        }}

        .ticker-label {{
            background: linear-gradient(90deg, #ff6b6b, #ff8787);
            color: white;
            padding: 0 20px;
            height: 100%;
            display: flex;
            align-items: center;
            font-weight: bold;
            font-size: 18px;
            text-transform: uppercase;
            letter-spacing: 1px;
            min-width: 150px;
            justify-content: center;
            box-shadow: 2px 0 10px rgba(0,0,0,0.3);
            position: relative;
        }}

        .ticker-label::after {{
            content: '';
            position: absolute;
            right: -20px;
            top: 0;
            width: 0;
            height: 0;
            border-style: solid;
            border-width: 30px 0 30px 20px;
            border-color: transparent transparent transparent #ff8787;
        }}

        .ticker-content {{
            flex: 1;
            overflow: hidden;
            position: relative;
            height: 100%;
            padding-left: 30px;
        }}

        .ticker-text {{
            position: absolute;
            white-space: nowrap;
            color: {self.config['ticker']['text_color']};
            font-size: {self.config['ticker']['font_size']};
            line-height: 60px;
            animation: scroll {self.config['ticker']['speed']}s linear infinite;
            padding-left: 100%;
        }}

        @keyframes scroll {{
            0% {{
                transform: translateX(0);
            }}
            100% {{
                transform: translateX(-50%);
            }}
        }}

        /* Time Display */
        .time-display {{
            position: absolute;
            top: 30px;
            left: 30px;
            background: rgba(0, 0, 0, 0.7);
            padding: 10px 20px;
            border-radius: 10px;
            color: white;
            font-size: 20px;
            font-weight: bold;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 107, 107, 0.5);
        }}

        /* Intermission Screen */
        .intermission {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: none;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
        }}

        .intermission-title {{
            font-size: 72px;
            font-weight: bold;
            text-shadow: 4px 4px 8px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }}

        .intermission-message {{
            font-size: 32px;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <!-- Channel Bug -->
    <div class="channel-bug">
        <div class="channel-name">{self.config['branding']['channel_name']}</div>
        <div class="channel-tagline">{self.config['branding']['tagline']}</div>
    </div>

    <!-- Time Display -->
    <div class="time-display" id="time"></div>

    <!-- Now Playing -->
    <div class="now-playing" id="nowPlaying">
        <div class="now-playing-label">Now Playing</div>
        <div class="now-playing-title" id="nowPlayingTitle">Loading...</div>
        <div class="now-playing-info" id="nowPlayingInfo"></div>
    </div>

    <!-- News Ticker -->
    <div class="ticker-container">
        <div class="ticker-label">LIVE</div>
        <div class="ticker-content">
            <div class="ticker-text">{ticker_text}</div>
        </div>
    </div>

    <!-- Intermission Screen (hidden by default) -->
    <div class="intermission" id="intermission">
        <div class="intermission-title">We'll Be Right Back</div>
        <div class="intermission-message">The Bobbing Channel</div>
    </div>

    <script>
        // Update time
        function updateTime() {{
            const now = new Date();
            const timeStr = now.toLocaleTimeString('en-US', {{
                hour: '2-digit',
                minute: '2-digit',
                hour12: true
            }});
            document.getElementById('time').textContent = timeStr;
        }}
        setInterval(updateTime, 1000);
        updateTime();

        // Show/hide now playing periodically
        let showNowPlaying = false;
        setInterval(() => {{
            const nowPlayingEl = document.getElementById('nowPlaying');
            if (showNowPlaying) {{
                nowPlayingEl.style.display = 'block';
                setTimeout(() => {{
                    nowPlayingEl.style.display = 'none';
                }}, 10000);  // Show for 10 seconds
            }}
            showNowPlaying = !showNowPlaying;
        }}, 30000);  // Every 30 seconds

        // Auto-refresh
        setTimeout(() => {{
            location.reload();
        }}, {self.config['ticker']['refresh_minutes'] * 60 * 1000});
    </script>
</body>
</html>"""

        overlay_file = self.overlay_dir / 'full_overlay.html'
        with open(overlay_file, 'w') as f:
            f.write(html_content)

        print(f"Full overlay saved to: {overlay_file}")
        return overlay_file

    def generate_obs_instructions(self):
        """Generate instructions for adding overlays to OBS"""
        print("\n" + "="*60)
        print("📺 Adding Overlays to OBS")
        print("="*60)

        print("\n1. ADD BROWSER SOURCE:")
        print("   Sources → Add → Browser")
        print(f"   - URL: file://{(self.overlay_dir / 'full_overlay.html').absolute()}")
        print("   - Width: 1920")
        print("   - Height: 1080")
        print("   - FPS: 30")
        print("   - Custom CSS: (leave empty)")

        print("\n2. POSITION IN SCENE:")
        print("   - Make sure Browser source is ABOVE video source")
        print("   - Right-click → Order → Move to Top")

        print("\n3. TICKER ONLY OPTION:")
        print("   For just the ticker without other elements:")
        print(f"   - URL: file://{(self.overlay_dir / 'ticker.html').absolute()}")
        print("   - Width: 1920")
        print("   - Height: 60")
        print("   - Position at bottom of screen")

        print("\n4. CUSTOMIZE:")
        print(f"   Edit {self.config_file} to change:")
        print("   - Ticker speed and colors")
        print("   - Channel branding")
        print("   - Bluesky handle for real posts")

        print("\n" + "="*60)


def main():
    """Main entry point"""
    import sys

    generator = OverlayGenerator()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'ticker':
            generator.generate_ticker_html()
        elif command == 'full':
            generator.generate_full_overlay_html()
        elif command == 'instructions':
            generator.generate_obs_instructions()
        elif command == 'config':
            print(f"Edit config at: {generator.config_file}")
        else:
            print("Commands: ticker, full, instructions, config")
    else:
        # Generate both by default
        generator.generate_ticker_html()
        generator.generate_full_overlay_html()
        generator.generate_obs_instructions()


if __name__ == "__main__":
    main()