#!/usr/bin/env python3
"""
Import items from manually extracted JSON
"""

import json
import sqlite3
import sys
from pathlib import Path
from rich.console import Console

console = Console()

def import_items(json_file='items.json'):
    """Import items from JSON file to database"""
    
    if not Path(json_file).exists():
        console.print(f"[red]File {json_file} not found![/red]")
        console.print("\n[yellow]Please follow the instructions in MANUAL_CRAWL.md to extract the data[/yellow]")
        return
    
    # Load JSON
    with open(json_file, 'r') as f:
        items = json.load(f)
    
    console.print(f"[green]Loaded {len(items)} items from {json_file}[/green]")
    
    # Create database
    conn = sqlite3.connect('media_library.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media (
            identifier TEXT PRIMARY KEY,
            title TEXT,
            creator TEXT,
            date TEXT,
            mediatype TEXT,
            item_url TEXT,
            thumbnail_url TEXT
        )
    ''')
    
    # Import items
    imported = 0
    for item in items:
        if isinstance(item, dict):
            identifier = item.get('identifier')
            if identifier:
                cursor.execute('''
                    INSERT OR REPLACE INTO media (
                        identifier, title, creator, date, mediatype, item_url, thumbnail_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    identifier,
                    item.get('title', ''),
                    item.get('creator', ''),
                    item.get('date', ''),
                    item.get('mediatype', ''),
                    item.get('url', f"https://archive.org/details/{identifier}"),
                    item.get('thumbnail_url', f"https://archive.org/services/img/{identifier}")
                ))
                imported += 1
    
    conn.commit()
    
    # Show stats
    cursor.execute("SELECT COUNT(*) FROM media")
    total = cursor.fetchone()[0]
    
    conn.close()
    
    console.print(f"\n[bold green]✓ Import complete![/bold green]")
    console.print(f"  Imported: {imported} items")
    console.print(f"  Total in database: {total} items")
    
    # Show sample
    conn = sqlite3.connect('media_library.db')
    cursor = conn.cursor()
    cursor.execute("SELECT identifier, title FROM media LIMIT 5")
    samples = cursor.fetchall()
    
    if samples:
        console.print("\nSample items:")
        for id, title in samples:
            console.print(f"  - {id}: {title[:60]}...")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        import_items(sys.argv[1])
    else:
        import_items()