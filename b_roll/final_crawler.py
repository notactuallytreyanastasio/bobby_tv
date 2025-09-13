#!/usr/bin/env python3
"""
Final working Archive.org crawler for the markpines collection
"""

import requests
import sqlite3
import json
import time
from datetime import datetime
from rich.console import Console
from rich.progress import track

console = Console()

class MarkPinesCrawler:
    def __init__(self, db_path="media_library.db"):
        self.db_path = db_path
        self.base_url = "https://archive.org"
        self.session = requests.Session()
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Drop old table if it exists (to fix schema issues)
        cursor.execute("DROP TABLE IF EXISTS media")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media (
                identifier TEXT PRIMARY KEY,
                title TEXT,
                creator TEXT,
                date TEXT,
                year INTEGER,
                mediatype TEXT,
                description TEXT,
                collection TEXT,
                downloads INTEGER,
                item_size INTEGER,
                item_url TEXT,
                thumbnail_url TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        console.print("[green]✓[/green] Database initialized")
    
    def crawl_collection(self, collection_id="markpines"):
        """
        Crawl items from the markpines collection
        https://archive.org/details/markpines
        """
        
        console.print(f"[bold cyan]Crawling collection: {collection_id}[/bold cyan]\n")
        
        all_items = []
        page = 1
        rows_per_page = 500
        
        while True:
            # Search for items in the markpines collection
            url = f"{self.base_url}/advancedsearch.php"
            
            params = {
                'q': f'collection:{collection_id}',  # Search in the markpines collection
                'fl': 'identifier,title,creator,date,year,mediatype,description,collection,downloads,item_size',
                'rows': rows_per_page,
                'page': page,
                'output': 'json',
                'sort': 'addeddate desc'
            }
            
            console.print(f"Fetching page {page}...")
            
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                console.print(f"[red]Error fetching page {page}: {e}[/red]")
                break
            
            if 'response' not in data:
                console.print("[red]No response in data[/red]")
                break
            
            response_data = data['response']
            num_found = response_data.get('numFound', 0)
            docs = response_data.get('docs', [])
            
            if page == 1:
                console.print(f"[green]Found {num_found} total items in collection![/green]\n")
            
            if not docs:
                console.print("No more items")
                break
            
            all_items.extend(docs)
            console.print(f"  Retrieved {len(docs)} items (total: {len(all_items)}/{num_found})")
            
            # Check if we have all items
            if len(all_items) >= num_found:
                break
            
            page += 1
            time.sleep(0.5)  # Be nice to the server
        
        return all_items
    
    def save_items(self, items):
        """Save items to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved = 0
        for item in track(items, description="Saving to database..."):
            try:
                # Extract year if not present
                year = item.get('year')
                if not year and item.get('date'):
                    try:
                        year = int(item['date'][:4])
                    except:
                        year = None
                
                # Handle collection field (can be string or list)
                collection = item.get('collection', '')
                if isinstance(collection, list):
                    collection = ', '.join(collection)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO media (
                        identifier, title, creator, date, year, mediatype,
                        description, collection, downloads, item_size,
                        item_url, thumbnail_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.get('identifier'),
                    item.get('title', ''),
                    item.get('creator', ''),
                    item.get('date', ''),
                    year,
                    item.get('mediatype', ''),
                    item.get('description', ''),
                    collection,
                    item.get('downloads', 0),
                    item.get('item_size', 0),
                    f"https://archive.org/details/{item.get('identifier')}",
                    f"https://archive.org/services/img/{item.get('identifier')}"
                ))
                saved += 1
            except Exception as e:
                console.print(f"[yellow]Error saving {item.get('identifier')}: {e}[/yellow]")
        
        conn.commit()
        conn.close()
        
        console.print(f"\n[green]✓ Saved {saved} items to database[/green]")
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
            SELECT year, COUNT(*) as count
            FROM media
            WHERE year IS NOT NULL
            GROUP BY year
            ORDER BY year DESC
            LIMIT 10
        """)
        by_year = cursor.fetchall()
        
        cursor.execute("""
            SELECT identifier, title, downloads
            FROM media
            WHERE downloads > 0
            ORDER BY downloads DESC
            LIMIT 10
        """)
        top_items = cursor.fetchall()
        
        conn.close()
        
        console.print(f"\n[bold cyan]═══ Collection Statistics ═══[/bold cyan]")
        console.print(f"Total items: [green]{total}[/green]")
        
        if by_type:
            console.print("\nBy media type:")
            for mtype, count in by_type:
                console.print(f"  {mtype}: {count}")
        
        if by_year:
            console.print("\nBy year:")
            for year, count in by_year[:5]:
                console.print(f"  {year}: {count}")
        
        if top_items:
            console.print("\nMost downloaded:")
            for identifier, title, downloads in top_items[:5]:
                title_short = title[:50] + "..." if len(title) > 50 else title
                console.print(f"  {downloads:,} - {title_short}")

def main():
    console.print("[bold cyan]Archive.org markpines Collection Crawler[/bold cyan]\n")
    console.print("Collection URL: https://archive.org/details/markpines\n")
    
    crawler = MarkPinesCrawler()
    
    # Crawl the markpines collection
    items = crawler.crawl_collection("markpines")
    
    if items:
        console.print(f"\n[bold]Retrieved {len(items)} items total[/bold]")
        
        # Save to database
        saved = crawler.save_items(items)
        
        # Show statistics
        crawler.get_stats()
        
        console.print(f"\n[bold green]✓ Complete! Database saved as media_library.db[/bold green]")
    else:
        console.print("\n[red]No items found[/red]")
        console.print("Please check if the collection exists at:")
        console.print("https://archive.org/details/markpines")

if __name__ == "__main__":
    main()