#!/usr/bin/env python3
"""
Archive.org Media Crawler for The Bobbing Channel
Crawls and catalogs metadata for all media from a specified Archive.org user collection
"""

import requests
import sqlite3
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

class ArchiveCrawler:
    """Crawler for Archive.org media collections - metadata only"""
    
    def __init__(self, db_path: str = "media_library.db"):
        self.db_path = db_path
        self.base_url = "https://archive.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BobbyTV-Crawler/1.0 (https://github.com/yourusername/bobby_tv)'
        })
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with media metadata schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media (
                identifier TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                creator TEXT,
                date TEXT,
                year INTEGER,
                mediatype TEXT,
                collection TEXT,
                thumbnail_url TEXT,
                duration TEXT,
                file_count INTEGER,
                total_size INTEGER,
                primary_format TEXT,
                views INTEGER,
                downloads INTEGER,
                subject TEXT,
                language TEXT,
                licenseurl TEXT,
                archive_url TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection TEXT,
                items_found INTEGER,
                items_processed INTEGER,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT,
                error_message TEXT
            )
        ''')
        
        # Create indexes for better query performance (only for columns that exist)
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mediatype ON media(mediatype)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_collection ON media(collection)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON media(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON media(year)')
            # Only create subject index if column exists
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='media'")
            table_schema = cursor.fetchone()[0]
            if 'subject' in table_schema:
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_subject ON media(subject)')
        except sqlite3.OperationalError as e:
            # Ignore index creation errors for missing columns
            pass
        
        conn.commit()
        conn.close()
        console.print(f"[green]✓[/green] Database initialized at {self.db_path}")
    
    def fetch_user_items(self, username: str, rows: int = 100, page: int = 1) -> Dict:
        """Fetch items from a user's collection"""
        # For Archive.org member pages, use @username directly in the query
        # This searches for items that reference this member account
        if not username.startswith('@'):
            username = f'@{username}'
        
        params = {
            'q': username,
            'fl': 'identifier,title,description,creator,date,year,mediatype,collection,subject,language,licenseurl,downloads,item_size',
            'rows': rows,
            'page': page,
            'output': 'json',
            'sort': 'addeddate desc'
        }
        
        url = f"{self.base_url}/advancedsearch.php"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Error fetching page {page}: {e}[/red]")
            return {}
    
    def fetch_item_metadata(self, identifier: str) -> Dict:
        """Fetch detailed metadata for a specific item"""
        url = f"{self.base_url}/metadata/{identifier}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Error fetching metadata for {identifier}: {e}[/red]")
            return {}
    
    def extract_thumbnail_url(self, identifier: str, metadata: Dict) -> Optional[str]:
        """Extract thumbnail URL from metadata"""
        # Use Archive.org's thumbnail service
        return f"{self.base_url}/services/img/{identifier}"
    
    def analyze_files_metadata(self, metadata: Dict) -> Dict:
        """Analyze files to extract summary information without storing file details"""
        file_info = {
            'duration': None,
            'total_size': 0,
            'file_count': 0,
            'primary_format': None
        }
        
        if 'files' not in metadata:
            return file_info
        
        files = metadata.get('files', [])
        file_info['file_count'] = len(files)
        
        # Video format priority
        video_formats = ['.mp4', '.webm', '.avi', '.mkv', '.mov', '.mpeg', '.mpg', '.ogv']
        audio_formats = ['.mp3', '.ogg', '.wav', '.flac', '.m4a']
        
        formats_found = set()
        
        for file in files:
            # Sum up total size
            size = file.get('size')
            if size and isinstance(size, (int, float)):
                file_info['total_size'] += int(size)
            
            # Look for duration in original files
            if file.get('source') == 'original' and not file_info['duration']:
                file_info['duration'] = file.get('length')
            
            # Track formats
            filename = file.get('name', '').lower()
            for fmt in video_formats + audio_formats:
                if filename.endswith(fmt):
                    formats_found.add(fmt[1:])
                    break
        
        # Determine primary format
        for fmt in video_formats:
            if fmt[1:] in formats_found:
                file_info['primary_format'] = fmt[1:]
                break
        
        if not file_info['primary_format']:
            for fmt in audio_formats:
                if fmt[1:] in formats_found:
                    file_info['primary_format'] = fmt[1:]
                    break
        
        if not file_info['primary_format'] and formats_found:
            file_info['primary_format'] = list(formats_found)[0]
        
        return file_info
    
    def save_media_metadata(self, item_data: Dict, detailed_metadata: Dict):
        """Save media metadata to database (no file details)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata = detailed_metadata.get('metadata', {})
        identifier = metadata.get('identifier', item_data.get('identifier'))
        
        # Analyze files for summary info only
        file_info = self.analyze_files_metadata(detailed_metadata)
        
        # Extract year from date if available
        date_str = metadata.get('date', item_data.get('date', ''))
        year = None
        if date_str:
            try:
                year = int(date_str[:4])
            except (ValueError, IndexError):
                pass
        
        # Build Archive.org URL
        archive_url = f"{self.base_url}/details/{identifier}"
        
        # Prepare metadata for storage
        media_data = (
            identifier,
            metadata.get('title', item_data.get('title')),
            metadata.get('description', item_data.get('description')),
            metadata.get('creator', item_data.get('creator')),
            date_str,
            year,
            metadata.get('mediatype', item_data.get('mediatype')),
            ','.join(metadata.get('collection', [])) if isinstance(metadata.get('collection'), list) else metadata.get('collection'),
            self.extract_thumbnail_url(identifier, detailed_metadata),
            file_info['duration'],
            file_info['file_count'],
            file_info['total_size'],
            file_info['primary_format'],
            metadata.get('downloads', item_data.get('downloads')),
            metadata.get('downloads', item_data.get('downloads')),  # Using downloads as views
            json.dumps(metadata.get('subject', item_data.get('subject', []))),
            metadata.get('language', item_data.get('language')),
            metadata.get('licenseurl', item_data.get('licenseurl')),
            archive_url,
            json.dumps(metadata, indent=2)
        )
        
        cursor.execute('''
            INSERT OR REPLACE INTO media (
                identifier, title, description, creator, date, year, mediatype, collection,
                thumbnail_url, duration, file_count, total_size, primary_format,
                views, downloads, subject, language, licenseurl, archive_url, raw_metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', media_data)
        
        conn.commit()
        conn.close()
    
    def crawl_user_uploads(self, username: str = "mark_pines_archive_project"):
        """Crawl all uploads from a specific user"""
        console.print(f"\n[bold cyan]Starting metadata crawl for user: @{username}[/bold cyan]\n")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create crawl history entry
        cursor.execute('''
            INSERT INTO crawl_history (collection, started_at, status)
            VALUES (?, ?, ?)
        ''', (f"@{username}", datetime.now(), "in_progress"))
        crawl_id = cursor.lastrowid
        conn.commit()
        
        page = 1
        total_items = 0
        processed_items = 0
        failed_items = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            # First, get total count
            console.print("Fetching total item count...")
            initial_data = self.fetch_user_items(username, rows=1, page=1)
            
            if 'response' in initial_data:
                total_items = initial_data['response'].get('numFound', 0)
                console.print(f"[green]Found {total_items} total items[/green]\n")
            else:
                console.print("[red]Failed to fetch initial data[/red]")
                cursor.execute('''
                    UPDATE crawl_history
                    SET completed_at = ?, status = ?, error_message = ?
                    WHERE id = ?
                ''', (datetime.now(), "failed", "Could not fetch initial data", crawl_id))
                conn.commit()
                conn.close()
                return 0
            
            task = progress.add_task(f"Processing {total_items} items...", total=total_items)
            
            while True:
                # Fetch page of results
                data = self.fetch_user_items(username, rows=100, page=page)
                
                if 'response' not in data or 'docs' not in data['response']:
                    break
                
                items = data['response']['docs']
                if not items:
                    break
                
                for item in items:
                    identifier = item.get('identifier')
                    if not identifier:
                        continue
                    
                    title = item.get('title', 'Untitled')
                    progress.update(task, description=f"Processing: {title[:50]}...")
                    
                    # Fetch detailed metadata
                    detailed_metadata = self.fetch_item_metadata(identifier)
                    
                    if detailed_metadata:
                        try:
                            self.save_media_metadata(item, detailed_metadata)
                            processed_items += 1
                        except Exception as e:
                            console.print(f"[yellow]Failed to save {identifier}: {e}[/yellow]")
                            failed_items.append(identifier)
                    else:
                        failed_items.append(identifier)
                    
                    progress.update(task, advance=1)
                    
                    # Rate limiting
                    time.sleep(0.3)
                
                if len(items) < 100:
                    break
                
                page += 1
        
        # Update crawl history
        status = "completed" if not failed_items else "completed_with_errors"
        error_msg = f"Failed items: {', '.join(failed_items[:10])}" if failed_items else None
        
        cursor.execute('''
            UPDATE crawl_history
            SET items_found = ?, items_processed = ?, completed_at = ?, status = ?, error_message = ?
            WHERE id = ?
        ''', (total_items, processed_items, datetime.now(), status, error_msg, crawl_id))
        conn.commit()
        conn.close()
        
        # Print summary
        console.print(f"\n[bold green]✓ Crawl completed![/bold green]")
        console.print(f"  Processed: {processed_items}/{total_items} items")
        if failed_items:
            console.print(f"  [yellow]Failed: {len(failed_items)} items[/yellow]")
        
        return processed_items
    
    def get_library_stats(self) -> Dict:
        """Get comprehensive statistics about the media library"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total items
        cursor.execute("SELECT COUNT(*) FROM media")
        stats['total_items'] = cursor.fetchone()[0]
        
        # By media type
        cursor.execute("""
            SELECT mediatype, COUNT(*) as count
            FROM media
            WHERE mediatype IS NOT NULL
            GROUP BY mediatype
            ORDER BY count DESC
        """)
        stats['by_mediatype'] = cursor.fetchall()
        
        # By year
        cursor.execute("""
            SELECT year, COUNT(*) as count
            FROM media
            WHERE year IS NOT NULL
            GROUP BY year
            ORDER BY year DESC
            LIMIT 20
        """)
        stats['by_year'] = cursor.fetchall()
        
        # Total size and file counts
        cursor.execute("""
            SELECT 
                SUM(item_size) as total_size,
                COUNT(*) as total_files,
                COUNT(CASE WHEN item_size IS NOT NULL AND item_size > 0 THEN 1 END) as items_with_size
            FROM media
        """)
        result = cursor.fetchone()
        stats['total_size_bytes'] = result[0] or 0
        stats['total_files'] = result[1] or 0
        stats['items_with_duration'] = result[2] or 0
        
        # Calculate total size in human-readable format
        size_gb = stats['total_size_bytes'] / (1024**3) if stats['total_size_bytes'] else 0
        stats['total_size_gb'] = round(size_gb, 2)
        
        # Format distribution (using mediatype since we don't have primary_format)
        cursor.execute("""
            SELECT mediatype, COUNT(*) as count
            FROM media
            WHERE mediatype IS NOT NULL
            GROUP BY mediatype
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['top_formats'] = cursor.fetchall()
        
        # Recent crawls
        cursor.execute("""
            SELECT collection, items_found, items_processed, started_at, completed_at, status
            FROM crawl_history
            ORDER BY started_at DESC
            LIMIT 5
        """)
        stats['recent_crawls'] = cursor.fetchall()
        
        # Top collections
        cursor.execute("""
            SELECT collection, COUNT(*) as count
            FROM media
            WHERE collection IS NOT NULL AND collection != ''
            GROUP BY collection
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['top_collections'] = cursor.fetchall()
        
        conn.close()
        return stats
    
    def display_stats(self):
        """Display library statistics in a formatted table"""
        stats = self.get_library_stats()
        
        console.print("\n[bold cyan]═══ Media Library Statistics ═══[/bold cyan]\n")
        
        # Overview
        overview_table = Table(title="Overview", show_header=False)
        overview_table.add_column("Metric", style="cyan")
        overview_table.add_column("Value", style="green")
        
        overview_table.add_row("Total Items", str(stats['total_items']))
        overview_table.add_row("Total Size", f"{stats['total_size_gb']} GB")
        overview_table.add_row("Items with Size Info", str(stats.get('items_with_duration', 0)))
        
        console.print(overview_table)
        console.print()
        
        # Media types
        if stats['by_mediatype']:
            type_table = Table(title="Media Types")
            type_table.add_column("Type", style="cyan")
            type_table.add_column("Count", justify="right", style="green")
            
            for mediatype, count in stats['by_mediatype']:
                type_table.add_row(mediatype or "Unknown", str(count))
            
            console.print(type_table)
            console.print()
        
        # Top formats
        if stats['top_formats']:
            format_table = Table(title="Top File Formats")
            format_table.add_column("Format", style="cyan")
            format_table.add_column("Count", justify="right", style="green")
            
            for format_type, count in stats['top_formats'][:5]:
                format_table.add_row(format_type, str(count))
            
            console.print(format_table)
            console.print()
        
        # Recent crawls
        if stats['recent_crawls']:
            crawl_table = Table(title="Recent Crawls")
            crawl_table.add_column("Collection", style="cyan")
            crawl_table.add_column("Processed", justify="right", style="green")
            crawl_table.add_column("Status", style="yellow")
            crawl_table.add_column("Date", style="blue")
            
            for crawl in stats['recent_crawls']:
                date = crawl[3][:10] if crawl[3] else "Unknown"
                processed = f"{crawl[2]}/{crawl[1]}" if crawl[1] else "0/0"
                crawl_table.add_row(crawl[0], processed, crawl[5], date)
            
            console.print(crawl_table)

def main():
    parser = argparse.ArgumentParser(
        description='Crawl Archive.org media metadata for The Bobbing Channel',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                    # Crawl default user's uploads
  %(prog)s --stats            # Show library statistics
  %(prog)s --user other_user  # Crawl different user
  %(prog)s --db custom.db     # Use custom database file
        '''
    )
    
    parser.add_argument('--user', default='mark_pines_archive_project',
                       help='Archive.org username to crawl (default: mark_pines_archive_project)')
    parser.add_argument('--db', default='media_library.db',
                       help='SQLite database path (default: media_library.db)')
    parser.add_argument('--stats', action='store_true',
                       help='Show library statistics instead of crawling')
    
    args = parser.parse_args()
    
    # Create crawler instance
    crawler = ArchiveCrawler(db_path=args.db)
    
    if args.stats:
        # Display statistics
        crawler.display_stats()
    else:
        # Run crawler
        try:
            items_processed = crawler.crawl_user_uploads(args.user)
            
            # Show stats after crawl
            if items_processed > 0:
                console.print("\n[bold]Post-crawl statistics:[/bold]")
                crawler.display_stats()
        except KeyboardInterrupt:
            console.print("\n[yellow]Crawl interrupted by user[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]Crawl failed: {e}[/red]")
            sys.exit(1)

if __name__ == "__main__":
    main()