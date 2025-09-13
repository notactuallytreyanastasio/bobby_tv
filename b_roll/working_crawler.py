#!/usr/bin/env python3
"""
Working Archive.org crawler using the correct Search API
Based on https://archive.org/developers/index.html
"""

import requests
import sqlite3
import json
import time
from rich.console import Console
from rich.progress import track

console = Console()

class ArchiveSearchCrawler:
    def __init__(self, db_path="media_library.db"):
        self.db_path = db_path
        self.base_url = "https://archive.org"
        self.session = requests.Session()
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
                description TEXT,
                item_url TEXT,
                thumbnail_url TEXT,
                downloads INTEGER,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        console.print("[green]✓[/green] Database initialized")
    
    def search_archive(self, query, page=1, rows=100):
        """
        Use the Archive.org Search API
        Documentation: https://archive.org/developers/item-apis.html#searching-items
        """
        
        # The Search API endpoint
        url = f"{self.base_url}/advancedsearch.php"
        
        params = {
            'q': query,
            'fl': 'identifier,title,creator,date,mediatype,description,downloads',  # fields to return
            'rows': rows,
            'page': page,
            'output': 'json',
            'sort': 'addeddate desc'  # or 'downloads desc' for most popular
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return None
    
    def crawl_member_favorites(self, username="mark_pines_archive_project"):
        """
        Search for items favorited by a user
        The @username page typically shows favorites
        """
        
        # Try different query patterns
        queries = [
            f'favoriteBy:{username}',  # Items favorited by user
            f'@{username}',  # Direct member reference
            f'uploader:{username}',  # Items uploaded by user
        ]
        
        all_items = []
        
        for query in queries:
            console.print(f"\n[yellow]Trying query: {query}[/yellow]")
            
            page = 1
            total_found = 0
            
            while True:
                data = self.search_archive(query, page=page, rows=500)
                
                if not data or 'response' not in data:
                    break
                
                response = data['response']
                num_found = response.get('numFound', 0)
                docs = response.get('docs', [])
                
                if page == 1:
                    console.print(f"[green]Found {num_found} total items[/green]")
                    total_found = num_found
                
                if not docs:
                    break
                
                all_items.extend(docs)
                console.print(f"  Page {page}: Retrieved {len(docs)} items (total so far: {len(all_items)})")
                
                # Check if we have all items
                if len(all_items) >= num_found:
                    break
                
                page += 1
                time.sleep(0.5)  # Be nice to the server
            
            # If we found the right collection (1326 items), stop
            if total_found >= 1300 and total_found <= 1400:
                console.print(f"[bold green]✓ Found the collection with {total_found} items![/bold green]")
                break
        
        return all_items
    
    def save_items(self, items):
        """Save items to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved = 0
        for item in items:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO media (
                        identifier, title, creator, date, mediatype,
                        description, item_url, thumbnail_url, downloads
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.get('identifier'),
                    item.get('title'),
                    item.get('creator'),
                    item.get('date'),
                    item.get('mediatype'),
                    item.get('description'),
                    f"https://archive.org/details/{item.get('identifier')}",
                    f"https://archive.org/services/img/{item.get('identifier')}",
                    item.get('downloads', 0)
                ))
                saved += 1
            except Exception as e:
                console.print(f"[yellow]Error saving {item.get('identifier')}: {e}[/yellow]")
        
        conn.commit()
        conn.close()
        
        console.print(f"[green]✓ Saved {saved} items to database[/green]")
        return saved
    
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
        
        cursor.execute("""
            SELECT identifier, title, downloads
            FROM media
            ORDER BY downloads DESC
            LIMIT 10
        """)
        top_items = cursor.fetchall()
        
        conn.close()
        
        console.print(f"\n[bold cyan]Database Statistics[/bold cyan]")
        console.print(f"Total items: {total}")
        
        if by_type:
            console.print("\nBy media type:")
            for mtype, count in by_type:
                console.print(f"  {mtype}: {count}")
        
        if top_items:
            console.print("\nMost downloaded:")
            for identifier, title, downloads in top_items:
                console.print(f"  {downloads:,} - {title[:50]}...")

def main():
    console.print("[bold cyan]Archive.org Search API Crawler[/bold cyan]\n")
    
    crawler = ArchiveSearchCrawler()
    
    # Try to find the collection
    items = crawler.crawl_member_favorites()
    
    if items:
        console.print(f"\n[bold]Retrieved {len(items)} items total[/bold]")
        
        # Save to database
        saved = crawler.save_items(items)
        
        # Show statistics
        crawler.get_stats()
    else:
        console.print("\n[red]No items found[/red]")
        console.print("\n[yellow]The collection might be:[/yellow]")
        console.print("1. A private collection")
        console.print("2. Using a different identifier")
        console.print("3. Loaded dynamically with JavaScript")
        
        console.print("\n[yellow]Try manually extracting from the browser:[/yellow]")
        console.print("1. Open https://archive.org/details/@mark_pines_archive_project")
        console.print("2. Open browser console (F12)")
        console.print("3. Run the extraction script from MANUAL_CRAWL.md")

if __name__ == "__main__":
    main()