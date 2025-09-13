#!/usr/bin/env python3
"""
Find what collections/uploads are associated with mark_pines_archive_project
"""

import requests
import json
from rich.console import Console

console = Console()

def search_archive():
    """Try different search approaches"""
    
    searches = [
        # User's uploads
        ("Uploads by user", "https://archive.org/advancedsearch.php?q=uploader%3Amark_pines_archive_project&fl=identifier,title&rows=10&output=json"),
        
        # User's reviews
        ("Reviews by user", "https://archive.org/advancedsearch.php?q=reviewer%3Amark_pines_archive_project&fl=identifier,title&rows=10&output=json"),
        
        # Collections by user
        ("Collections by user", "https://archive.org/advancedsearch.php?q=creator%3Amark_pines_archive_project%20AND%20mediatype%3Acollection&fl=identifier,title&rows=10&output=json"),
        
        # Member's favorites (the 1,326 items are likely favorites!)
        ("Favorited items", "https://archive.org/advancedsearch.php?q=favoriteBy%3Amark_pines_archive_project&fl=identifier,title&rows=10&output=json"),
        
        # Items in member's library
        ("Member library", "https://archive.org/advancedsearch.php?q=loans__status__status%3A*%20AND%20loans__status__userid%3Amark_pines_archive_project&fl=identifier,title&rows=10&output=json"),
    ]
    
    for name, url in searches:
        console.print(f"\n[yellow]Checking: {name}[/yellow]")
        try:
            resp = requests.get(url)
            data = resp.json()
            
            if 'response' in data:
                count = data['response'].get('numFound', 0)
                console.print(f"[green]Found: {count} items![/green]")
                
                if count > 0 and count == 1326:
                    console.print(f"[bold green]✓ This matches the 1,326 items![/bold green]")
                    return url.replace("&rows=10", "&rows=2000"), name
                
                if count > 0:
                    console.print("Sample items:")
                    for doc in data['response'].get('docs', [])[:3]:
                        console.print(f"  - {doc.get('identifier')}: {doc.get('title')}")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    return None, None

def get_all_favorites():
    """Get all favorited items"""
    console.print("\n[bold cyan]Fetching all favorited items...[/bold cyan]")
    
    all_items = []
    page = 1
    rows = 1000
    
    while True:
        url = f"https://archive.org/advancedsearch.php?q=favoriteBy%3Amark_pines_archive_project&fl=identifier,title,creator,date,mediatype&rows={rows}&page={page}&output=json"
        
        console.print(f"Fetching page {page}...")
        resp = requests.get(url)
        data = resp.json()
        
        if 'response' in data:
            docs = data['response'].get('docs', [])
            if not docs:
                break
            
            all_items.extend(docs)
            console.print(f"  Got {len(docs)} items (total so far: {len(all_items)})")
            
            if len(docs) < rows:
                break
            
            page += 1
        else:
            break
    
    return all_items

def save_items(items):
    """Save to database"""
    import sqlite3
    
    conn = sqlite3.connect("media_library.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media (
            identifier TEXT PRIMARY KEY,
            title TEXT,
            creator TEXT,
            date TEXT,
            mediatype TEXT,
            item_url TEXT
        )
    ''')
    
    for item in items:
        cursor.execute('''
            INSERT OR REPLACE INTO media VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            item.get('identifier'),
            item.get('title'),
            item.get('creator'),
            item.get('date'),
            item.get('mediatype'),
            f"https://archive.org/details/{item.get('identifier')}"
        ))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # First, find what type of collection this is
    url, collection_type = search_archive()
    
    if collection_type and "Favorited" in collection_type:
        # Get all favorites
        items = get_all_favorites()
        
        if items:
            console.print(f"\n[bold green]✓ Found {len(items)} favorited items![/bold green]")
            save_items(items)
            console.print(f"[green]✓ Saved to database[/green]")
            
            # Show stats
            types = {}
            for item in items:
                t = item.get('mediatype', 'unknown')
                types[t] = types.get(t, 0) + 1
            
            console.print("\nMedia types:")
            for t, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
                console.print(f"  {t}: {count}")
    else:
        console.print("\n[red]Could not determine collection type[/red]")