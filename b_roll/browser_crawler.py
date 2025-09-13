#!/usr/bin/env python3
"""
Browser-based Archive.org crawler for The Bobbing Channel
Uses Selenium to scrape the actual webpage and get all 1,326 items
"""

import sqlite3
import json
import time
from datetime import datetime
from typing import Dict, List
import argparse
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

console = Console()

class BrowserCrawler:
    """Browser-based crawler for Archive.org collections"""
    
    def __init__(self, db_path: str = "media_library.db", headless: bool = True):
        self.db_path = db_path
        self.base_url = "https://archive.org"
        self.headless = headless
        self.driver = None
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with media metadata schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple schema focused on what we can scrape from the page
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media (
                identifier TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                creator TEXT,
                date TEXT,
                year INTEGER,
                mediatype TEXT,
                views TEXT,
                thumbnail_url TEXT,
                item_url TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                items_found INTEGER,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON media(title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_creator ON media(creator)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON media(year)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mediatype ON media(mediatype)')
        
        conn.commit()
        conn.close()
        console.print(f"[green]✓[/green] Database initialized at {self.db_path}")
    
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        import subprocess
        import os
        
        # First, try to find chromium-chromedriver on the system (for ARM/Raspberry Pi)
        chromedriver_paths = [
            '/usr/bin/chromedriver',
            '/usr/lib/chromium-browser/chromedriver',
            '/usr/lib/chromium/chromedriver',
            '/snap/bin/chromium.chromedriver'
        ]
        
        chromedriver_path = None
        for path in chromedriver_paths:
            if os.path.exists(path):
                chromedriver_path = path
                break
        
        if not chromedriver_path:
            # Check if chromium-chromedriver is installed
            try:
                result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
                if result.returncode == 0:
                    chromedriver_path = result.stdout.strip()
            except:
                pass
        
        options = ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless')
        
        # Common options for stability
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # For Raspberry Pi / ARM
        options.add_argument('--disable-software-rasterizer')
        
        # Try to use Chromium on Raspberry Pi
        options.binary_location = '/usr/bin/chromium-browser'
        
        if chromedriver_path:
            try:
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=options)
                console.print(f"[green]✓[/green] Using system ChromeDriver at {chromedriver_path}")
                return
            except Exception as e:
                console.print(f"[yellow]Failed with system chromedriver: {e}[/yellow]")
        
        # Try Firefox as fallback
        try:
            from selenium.webdriver.firefox.service import Service as FirefoxService
            firefox_options = FirefoxOptions()
            if self.headless:
                firefox_options.add_argument('--headless')
            firefox_options.add_argument('--width=1920')
            firefox_options.add_argument('--height=1080')
            
            self.driver = webdriver.Firefox(options=firefox_options)
            console.print("[green]✓[/green] Using Firefox as fallback")
            return
        except Exception as e:
            console.print(f"[yellow]Firefox also failed: {e}[/yellow]")
        
        raise Exception("Could not setup any browser driver. Please install chromium-chromedriver: sudo apt-get install chromium-chromedriver")
    
    def extract_item_data(self, item_element) -> Dict:
        """Extract metadata from an item element on the page"""
        data = {}
        
        try:
            # Get item identifier from the link
            link = item_element.find_element(By.CSS_SELECTOR, 'a[href^="/details/"]')
            href = link.get_attribute('href')
            data['identifier'] = href.split('/details/')[-1].split('?')[0]
            data['item_url'] = f"{self.base_url}/details/{data['identifier']}"
            
            # Get title
            try:
                title_elem = item_element.find_element(By.CSS_SELECTOR, '.item-ttl a, .ttl a, [class*="title"] a')
                data['title'] = title_elem.get_attribute('title') or title_elem.text.strip()
            except:
                data['title'] = data['identifier']
            
            # Get creator/author
            try:
                creator_elem = item_element.find_element(By.CSS_SELECTOR, '.by, .creator, [class*="byline"]')
                data['creator'] = creator_elem.text.strip().replace('by ', '')
            except:
                data['creator'] = None
            
            # Get date
            try:
                date_elem = item_element.find_element(By.CSS_SELECTOR, '.date, .pubdate, [class*="date"]')
                data['date'] = date_elem.text.strip()
                # Try to extract year
                if data['date']:
                    year_str = data['date'][:4]
                    if year_str.isdigit():
                        data['year'] = int(year_str)
                    else:
                        data['year'] = None
                else:
                    data['year'] = None
            except:
                data['date'] = None
                data['year'] = None
            
            # Get views
            try:
                views_elem = item_element.find_element(By.CSS_SELECTOR, '.views, .download-count, [class*="views"]')
                data['views'] = views_elem.text.strip()
            except:
                data['views'] = None
            
            # Get media type
            try:
                # Look for media type icon or text
                mediatype_elem = item_element.find_element(By.CSS_SELECTOR, '[data-mediatype], .mediatype, .format')
                data['mediatype'] = mediatype_elem.get_attribute('data-mediatype') or mediatype_elem.text.strip()
            except:
                data['mediatype'] = None
            
            # Get thumbnail
            try:
                img_elem = item_element.find_element(By.CSS_SELECTOR, 'img[src*="archive.org"]')
                data['thumbnail_url'] = img_elem.get_attribute('src')
            except:
                data['thumbnail_url'] = f"{self.base_url}/services/img/{data['identifier']}"
            
            # Get description (if available on the page)
            try:
                desc_elem = item_element.find_element(By.CSS_SELECTOR, '.description, .snippet, [class*="desc"]')
                data['description'] = desc_elem.text.strip()
            except:
                data['description'] = None
            
        except Exception as e:
            console.print(f"[yellow]Error extracting item data: {e}[/yellow]")
            return None
        
        return data
    
    def save_items(self, items: List[Dict]):
        """Save items to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item in items:
            if not item or not item.get('identifier'):
                continue
            
            cursor.execute('''
                INSERT OR REPLACE INTO media (
                    identifier, title, description, creator, date, year,
                    mediatype, views, thumbnail_url, item_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.get('identifier'),
                item.get('title'),
                item.get('description'),
                item.get('creator'),
                item.get('date'),
                item.get('year'),
                item.get('mediatype'),
                item.get('views'),
                item.get('thumbnail_url'),
                item.get('item_url')
            ))
        
        conn.commit()
        conn.close()
    
    def crawl_collection(self, collection_url: str):
        """Crawl all items from an Archive.org collection page"""
        console.print(f"\n[bold cyan]Starting browser crawl of: {collection_url}[/bold cyan]\n")
        
        # Record crawl session
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO crawl_sessions (url, started_at, status)
            VALUES (?, ?, ?)
        ''', (collection_url, datetime.now(), "in_progress"))
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Setup driver
        console.print("Setting up browser...")
        self.setup_driver()
        
        all_items = []
        page_num = 1
        items_found = 0  # Initialize here
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                
                task = progress.add_task("Loading collection page...", total=None)
                
                # Load the first page
                self.driver.get(collection_url)
                
                # Wait for page to load
                time.sleep(3)
                
                # Wait for items to load
                wait = WebDriverWait(self.driver, 20)
                
                # Wait for the results to appear - try different selectors
                item_found = False
                selectors_to_try = [
                    '.item-ia',
                    '.C234',
                    'div[data-id]',
                    '.results .item',
                    'article.item',
                    '.collection-items .item',
                    '[class*="item-tile"]'
                ]
                
                for selector in selectors_to_try:
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        console.print(f"[green]Found items with selector: {selector}[/green]")
                        item_found = True
                        break
                    except TimeoutException:
                        continue
                
                if not item_found:
                    console.print("[red]Timeout waiting for results to load[/red]")
                    console.print("Trying to find any items on page...")
                    # Debug: check what's on the page
                    possible_items = self.driver.find_elements(By.TAG_NAME, 'a')
                    archive_links = [a for a in possible_items if '/details/' in (a.get_attribute('href') or '')]
                    if archive_links:
                        console.print(f"[yellow]Found {len(archive_links)} archive links directly[/yellow]")
                    return
                
                # Check total number of items
                try:
                    # Look for results count
                    results_text = self.driver.find_element(By.CSS_SELECTOR, '.results_count, .num-results, [class*="results"]').text
                    console.print(f"[green]Results info: {results_text}[/green]")
                except:
                    pass
                
                # Scroll and load all items
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                no_change_count = 0
                
                while True:
                    # Find all item containers - use multiple selectors
                    item_elements = []
                    for selector in ['.item-ia', '.C234', 'div[data-id]', 'article.item']:
                        found = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if found:
                            item_elements = found
                            break
                    
                    # If still no items, look for any links to /details/
                    if not item_elements:
                        all_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/details/"]')
                        # Group links by their parent containers
                        containers = {}
                        for link in all_links:
                            try:
                                parent = link.find_element(By.XPATH, './ancestor::div[contains(@class, "C") or contains(@class, "item")]')
                                containers[parent] = parent
                            except:
                                pass
                        if containers:
                            item_elements = list(containers.values())
                    
                    progress.update(task, description=f"Found {len(item_elements)} items so far...")
                    
                    # Scroll down to load more
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    
                    # Check if new content loaded
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    
                    if new_height == last_height:
                        no_change_count += 1
                        if no_change_count >= 3:
                            # No more content loading
                            break
                    else:
                        no_change_count = 0
                        last_height = new_height
                    
                    # Check if we have enough items (around 1326)
                    if len(item_elements) >= 1300:
                        console.print(f"[yellow]Reached {len(item_elements)} items, checking for more...[/yellow]")
                        if no_change_count >= 2:
                            break
                
                # Extract data from all items
                console.print(f"\n[green]Processing {len(item_elements)} items...[/green]")
                
                task = progress.add_task("Extracting metadata...", total=len(item_elements))
                
                for item_elem in item_elements:
                    item_data = self.extract_item_data(item_elem)
                    if item_data:
                        all_items.append(item_data)
                    progress.update(task, advance=1)
                
                # Save to database
                console.print(f"\n[green]Saving {len(all_items)} items to database...[/green]")
                self.save_items(all_items)
                
        except Exception as e:
            console.print(f"[red]Error during crawl: {e}[/red]")
            status = "failed"
            items_found = len(all_items)
        else:
            status = "completed"
            items_found = len(all_items)
        finally:
            # Clean up
            if self.driver:
                self.driver.quit()
            
            # Update crawl session
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE crawl_sessions
                SET items_found = ?, completed_at = ?, status = ?
                WHERE id = ?
            ''', (items_found, datetime.now(), status, session_id))
            conn.commit()
            conn.close()
            
            console.print(f"\n[bold green]✓ Crawl {status}![/bold green]")
            console.print(f"  Found and saved: {items_found} items")
        
        return all_items
    
    def get_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total items
        cursor.execute("SELECT COUNT(*) FROM media")
        total = cursor.fetchone()[0]
        
        # By media type
        cursor.execute("""
            SELECT mediatype, COUNT(*) as count
            FROM media
            WHERE mediatype IS NOT NULL
            GROUP BY mediatype
            ORDER BY count DESC
        """)
        by_type = cursor.fetchall()
        
        # By year
        cursor.execute("""
            SELECT year, COUNT(*) as count
            FROM media
            WHERE year IS NOT NULL
            GROUP BY year
            ORDER BY year DESC
            LIMIT 10
        """)
        by_year = cursor.fetchall()
        
        # Recent crawls
        cursor.execute("""
            SELECT url, items_found, started_at, status
            FROM crawl_sessions
            ORDER BY started_at DESC
            LIMIT 5
        """)
        sessions = cursor.fetchall()
        
        conn.close()
        
        # Display stats
        console.print("\n[bold cyan]═══ Media Library Statistics ═══[/bold cyan]\n")
        console.print(f"Total items: [green]{total}[/green]")
        
        if by_type:
            console.print("\nBy media type:")
            for mtype, count in by_type:
                console.print(f"  {mtype}: {count}")
        
        if by_year:
            console.print("\nBy year:")
            for year, count in by_year:
                console.print(f"  {year}: {count}")
        
        if sessions:
            console.print("\nRecent crawl sessions:")
            for url, items, started, status in sessions:
                console.print(f"  {started[:19]} - {status} - {items} items")

def main():
    parser = argparse.ArgumentParser(
        description='Browser-based Archive.org crawler for The Bobbing Channel'
    )
    
    parser.add_argument('--url', default='https://archive.org/details/@mark_pines_archive_project',
                       help='Archive.org collection URL to crawl')
    parser.add_argument('--db', default='media_library.db',
                       help='SQLite database path')
    parser.add_argument('--stats', action='store_true',
                       help='Show library statistics')
    parser.add_argument('--visible', action='store_true',
                       help='Run browser in visible mode (not headless)')
    
    args = parser.parse_args()
    
    crawler = BrowserCrawler(db_path=args.db, headless=not args.visible)
    
    if args.stats:
        crawler.get_stats()
    else:
        try:
            crawler.crawl_collection(args.url)
            crawler.get_stats()
        except KeyboardInterrupt:
            console.print("\n[yellow]Crawl interrupted by user[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Crawl failed: {e}[/red]")

if __name__ == "__main__":
    main()