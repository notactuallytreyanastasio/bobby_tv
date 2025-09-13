#!/usr/bin/env python3
"""
Simplified Archive.org crawler using requests and HTML parsing
"""

import requests
import sqlite3
import json
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import track

console = Console()

class SimpleCrawler:
    def __init__(self, db_path: str = "media_library.db"):
        self.db_path = db_path
        self.base_url = "https://archive.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media (
                identifier TEXT PRIMARY KEY,
                title TEXT,
                creator TEXT,
                date TEXT,
                mediatype TEXT,
                item_url TEXT,
                thumbnail_url TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        console.print(f"[green]✓[/green] Database initialized")
    
    def crawl_page(self, page_num: int = 1):
        """Crawl a single page of results"""
        # Use the search API endpoint that the web interface uses
        url = f"{self.base_url}/details/@mark_pines_archive_project"
        
        params = {
            'page': page_num,
            'sort': '-week'
        }
        
        console.print(f"Fetching page {page_num}...")
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            items = []
            
            # Find all item tiles/cards on the page
            # Archive.org uses different class names, let's try multiple
            item_selectors = [
                'div.item-ia',
                'div.C234',
                'div[data-id]',
                'article.tile',
                'div.tile-ia'
            ]
            
            item_elements = []
            for selector in item_selectors:
                found = soup.select(selector)
                if found:
                    item_elements = found
                    console.print(f"[green]Found {len(found)} items with selector: {selector}[/green]")
                    break
            
            # If no items found with class selectors, look for links
            if not item_elements:
                # Find all links to /details/
                links = soup.find_all('a', href=re.compile(r'/details/[^/]+$'))
                console.print(f"[yellow]Found {len(links)} detail links[/yellow]")
                
                # Group by unique identifiers
                unique_items = {}
                for link in links:
                    href = link.get('href', '')
                    if '/details/' in href:
                        identifier = href.split('/details/')[-1]
                        if identifier and identifier not in unique_items:
                            unique_items[identifier] = {
                                'identifier': identifier,
                                'title': link.get('title') or link.text.strip() or identifier,
                                'item_url': f"{self.base_url}{href}"
                            }
                
                items = list(unique_items.values())
            else:
                # Extract from found elements
                for elem in item_elements:
                    item = self.extract_item_data(elem)
                    if item:
                        items.append(item)
            
            return items
            
        except Exception as e:
            console.print(f"[red]Error fetching page {page_num}: {e}[/red]")
            return []
    
    def extract_item_data(self, element):
        """Extract item data from HTML element"""
        item = {}
        
        # Find the main link
        link = element.find('a', href=re.compile(r'/details/'))
        if not link:
            return None
        
        href = link.get('href', '')
        item['identifier'] = href.split('/details/')[-1]
        item['item_url'] = f"{self.base_url}{href}"
        item['title'] = link.get('title') or link.text.strip() or item['identifier']
        
        # Try to find creator
        creator_elem = element.find(class_=re.compile(r'by|creator|author'))
        if creator_elem:
            item['creator'] = creator_elem.text.strip()
        
        # Try to find date
        date_elem = element.find(class_=re.compile(r'date|pubdate'))
        if date_elem:
            item['date'] = date_elem.text.strip()
        
        # Try to find mediatype
        mediatype_elem = element.find(attrs={'data-mediatype': True})
        if mediatype_elem:
            item['mediatype'] = mediatype_elem.get('data-mediatype')
        
        # Thumbnail
        item['thumbnail_url'] = f"{self.base_url}/services/img/{item['identifier']}"
        
        return item
    
    def save_items(self, items):
        """Save items to database"""
        if not items:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item in items:
            cursor.execute('''
                INSERT OR REPLACE INTO media (
                    identifier, title, creator, date, mediatype, item_url, thumbnail_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.get('identifier'),
                item.get('title'),
                item.get('creator'),
                item.get('date'),
                item.get('mediatype'),
                item.get('item_url'),
                item.get('thumbnail_url')
            ))
        
        conn.commit()
        conn.close()
        console.print(f"[green]Saved {len(items)} items[/green]")
    
    def crawl_all(self):
        """Crawl all pages"""
        console.print("\n[bold cyan]Starting crawl of @mark_pines_archive_project[/bold cyan]\n")
        
        all_items = []
        page = 1
        empty_pages = 0
        
        # First, let's see how many pages there might be
        # Archive.org typically shows 50-75 items per page
        # If there are 1326 items, that's about 18-27 pages
        
        while page <= 50:  # Safety limit
            items = self.crawl_page(page)
            
            if not items:
                empty_pages += 1
                if empty_pages >= 3:
                    console.print("[yellow]No more items found[/yellow]")
                    break
            else:
                empty_pages = 0
                all_items.extend(items)
                self.save_items(items)
                console.print(f"Total so far: {len(all_items)} items")
            
            page += 1
            time.sleep(1)  # Be nice to the server
        
        console.print(f"\n[bold green]✓ Crawl completed![/bold green]")
        console.print(f"Total items saved: {len(all_items)}")
        
        return all_items
    
    def get_stats(self):
        """Show database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM media")
        total = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT mediatype, COUNT(*) as count
            FROM media
            WHERE mediatype IS NOT NULL
            GROUP BY mediatype
            ORDER BY count DESC
        """)
        by_type = cursor.fetchall()
        
        conn.close()
        
        console.print(f"\n[bold cyan]Database Statistics[/bold cyan]")
        console.print(f"Total items: {total}")
        
        if by_type:
            console.print("\nBy type:")
            for mtype, count in by_type:
                console.print(f"  {mtype}: {count}")

if __name__ == "__main__":
    import sys
    
    crawler = SimpleCrawler()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--stats':
        crawler.get_stats()
    else:
        crawler.crawl_all()
        crawler.get_stats()