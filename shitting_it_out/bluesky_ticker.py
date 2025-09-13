#!/usr/bin/env python3
"""
Bluesky Ticker Integration for Bobby TV
Fetches posts from Bluesky to display in the channel ticker
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time

class BlueskyTicker:
    def __init__(self):
        self.config_file = Path('overlays/bluesky_config.json')
        self.posts_cache = Path('overlays/posts_cache.json')
        self.load_config()
        self.session = None

    def load_config(self):
        """Load Bluesky configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'handle': 'your-handle.bsky.social',
                'app_password': '',  # App-specific password from Settings
                'fetch_count': 20,
                'include_replies': False,
                'include_reposts': True,
                'cache_minutes': 5
            }
            self.save_config()
            print(f"Please edit {self.config_file} with your Bluesky credentials")

    def save_config(self):
        """Save configuration"""
        self.config_file.parent.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def authenticate(self):
        """Authenticate with Bluesky ATP"""
        if not self.config.get('app_password'):
            print("No app password configured. Using sample posts.")
            return False

        try:
            response = requests.post(
                'https://bsky.social/xrpc/com.atproto.server.createSession',
                json={
                    'identifier': self.config['handle'],
                    'password': self.config['app_password']
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.session = {
                    'accessJwt': data['accessJwt'],
                    'refreshJwt': data['refreshJwt'],
                    'did': data['did']
                }
                return True
            else:
                print(f"Authentication failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def fetch_posts(self):
        """Fetch recent posts from Bluesky"""
        # Check cache first
        if self.posts_cache.exists():
            with open(self.posts_cache, 'r') as f:
                cache = json.load(f)
                cache_time = datetime.fromisoformat(cache['timestamp'])
                if datetime.now() - cache_time < timedelta(minutes=self.config['cache_minutes']):
                    return cache['posts']

        # Authenticate if needed
        if not self.session and not self.authenticate():
            return self.get_sample_posts()

        try:
            # Fetch timeline posts
            headers = {'Authorization': f"Bearer {self.session['accessJwt']}"}
            response = requests.get(
                f'https://bsky.social/xrpc/app.bsky.feed.getAuthorFeed',
                params={
                    'actor': self.config['handle'],
                    'limit': self.config['fetch_count']
                },
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                posts = []

                for item in data.get('feed', []):
                    post = item.get('post', {})
                    record = post.get('record', {})

                    # Skip replies if configured
                    if not self.config['include_replies'] and record.get('reply'):
                        continue

                    # Extract text
                    text = record.get('text', '')
                    if text:
                        # Clean up text for ticker display
                        text = text.replace('\n', ' ').strip()
                        if len(text) > 200:
                            text = text[:197] + '...'
                        posts.append(text)

                # Cache posts
                cache_data = {
                    'timestamp': datetime.now().isoformat(),
                    'posts': posts
                }
                with open(self.posts_cache, 'w') as f:
                    json.dump(cache_data, f)

                return posts

            else:
                print(f"Failed to fetch posts: {response.status_code}")
                return self.get_sample_posts()

        except Exception as e:
            print(f"Error fetching posts: {e}")
            return self.get_sample_posts()

    def get_sample_posts(self):
        """Return sample posts for testing"""
        return [
            "🎬 Now streaming: Classic cartoons from the golden age of animation",
            "📺 The Bobbing Channel - Your 24/7 vintage entertainment destination",
            "🎭 Tonight's feature: Public domain sci-fi double feature starting at 8PM",
            "📻 Did you know? We have over 1,300 titles in our rotation",
            "🎪 Coming up: Educational films from the 1950s",
            "📼 Request your favorites by mentioning @bobby.tv",
            "🎯 Check out our catalog at http://localhost:5001",
            "🎨 All content courtesy of the Internet Archive",
            "📺 Stay tuned for more classic entertainment",
            "🎬 The Bobbing Channel - Preserving media history, one stream at a time"
        ]

    def format_for_ticker(self, posts):
        """Format posts for ticker display"""
        if not posts:
            posts = ["The Bobbing Channel - 24/7 Classic Entertainment"]

        # Add bullet points between posts
        formatted = []
        for post in posts:
            formatted.append(post)

        return formatted

    def generate_ticker_json(self):
        """Generate JSON file for ticker to consume"""
        posts = self.fetch_posts()
        formatted = self.format_for_ticker(posts)

        ticker_data = {
            'updated': datetime.now().isoformat(),
            'posts': formatted,
            'config': {
                'speed': 30,
                'separator': ' • '
            }
        }

        ticker_file = Path('overlays/ticker_data.json')
        with open(ticker_file, 'w') as f:
            json.dump(ticker_data, f, indent=2)

        print(f"Ticker data saved to: {ticker_file}")
        print(f"Found {len(formatted)} posts for ticker")
        return ticker_file

    def run_daemon(self, interval_seconds=60):
        """Run as daemon, updating ticker data periodically"""
        print(f"Starting Bluesky ticker daemon (updating every {interval_seconds}s)")

        while True:
            try:
                self.generate_ticker_json()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Ticker updated")
            except Exception as e:
                print(f"Error updating ticker: {e}")

            time.sleep(interval_seconds)


def main():
    """Main entry point"""
    import sys

    ticker = BlueskyTicker()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'fetch':
            posts = ticker.fetch_posts()
            for i, post in enumerate(posts, 1):
                print(f"{i}. {post}")

        elif command == 'generate':
            ticker.generate_ticker_json()

        elif command == 'daemon':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            ticker.run_daemon(interval)

        elif command == 'config':
            print(f"Edit config at: {ticker.config_file}")

        elif command == 'test':
            if ticker.authenticate():
                print("✓ Authentication successful")
                posts = ticker.fetch_posts()
                print(f"✓ Fetched {len(posts)} posts")
            else:
                print("✗ Authentication failed")

        else:
            print("Commands: fetch, generate, daemon [seconds], config, test")
    else:
        ticker.generate_ticker_json()


if __name__ == "__main__":
    main()