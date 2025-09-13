#!/usr/bin/env python3
"""
Direct API crawler - finds the actual API endpoint Archive.org uses
"""

import requests
import json
import sqlite3
from rich.console import Console

console = Console()

def find_api_endpoint():
    """
    When you visit https://archive.org/details/@mark_pines_archive_project
    the page loads data from somewhere. Let's find it.
    """
    
    # The page likely uses one of these patterns
    test_urls = [
        # Try the scrape API with correct collection format
        "https://archive.org/services/search/v1/scrape?q=collection:(@mark_pines_archive_project)&fields=identifier,title,creator,date,mediatype&count=10000",
        
        # Try member uploads
        "https://archive.org/services/search/v1/scrape?q=uploader:(mark_pines_archive_project)&fields=identifier,title,creator,date,mediatype&count=10000",
        
        # Try the member's favorites/uploads
        "https://archive.org/services/search/v1/scrape?q=@mark_pines_archive_project&fields=identifier,title,creator,date,mediatype&count=10000",
        
        # Try the PHP search endpoint
        "https://archive.org/advancedsearch.php?q=@mark_pines_archive_project&rows=10000&output=json",
        
        # Try getting member info first
        "https://archive.org/metadata/@mark_pines_archive_project"
    ]
    
    for url in test_urls:
        console.print(f"\n[yellow]Testing: {url[:80]}...[/yellow]")
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check what we got
                if 'items' in data:
                    console.print(f"[green]✓ Found {len(data['items'])} items![/green]")
                    return url, data
                elif 'response' in data and 'docs' in data['response']:
                    count = len(data['response']['docs'])
                    total = data['response'].get('numFound', count)
                    console.print(f"[green]✓ Found {count} items (total: {total})![/green]")
                    return url, data
                elif 'metadata' in data:
                    console.print(f"[cyan]This is metadata for: {data['metadata'].get('title')}[/cyan]")
                    # If this is a collection, try to get its items
                    if data.get('is_collection'):
                        collection_url = f"https://archive.org/services/search/v1/scrape?q=collection:({data['metadata']['identifier']})&fields=identifier,title,creator,date,mediatype&count=10000"
                        console.print(f"[yellow]Trying collection query...[/yellow]")
                        coll_response = requests.get(collection_url)
                        if coll_response.status_code == 200:
                            coll_data = coll_response.json()
                            if 'items' in coll_data:
                                console.print(f"[green]✓ Found {len(coll_data['items'])} items in collection![/green]")
                                return collection_url, coll_data
                else:
                    console.print(f"[red]Unexpected response structure[/red]")
            else:
                console.print(f"[red]Status code: {response.status_code}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    return None, None

def save_to_db(items, db_path="media_library.db"):
    """Save items to SQLite database"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create simple table
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
    
    # Save items
    saved = 0
    for item in items:
        # Handle different response formats
        if isinstance(item, dict):
            identifier = item.get('identifier')
            if identifier:
                cursor.execute('''
                    INSERT OR REPLACE INTO media (identifier, title, creator, date, mediatype, item_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    identifier,
                    item.get('title', ''),
                    item.get('creator', ''),
                    item.get('date', item.get('publicdate', '')),
                    item.get('mediatype', ''),
                    f"https://archive.org/details/{identifier}"
                ))
                saved += 1
    
    conn.commit()
    conn.close()
    
    console.print(f"[green]✓ Saved {saved} items to database[/green]")
    return saved

def main():
    console.print("[bold cyan]Archive.org API Explorer[/bold cyan]\n")
    
    # Find working endpoint
    url, data = find_api_endpoint()
    
    if not data:
        console.print("\n[red]Could not find a working API endpoint[/red]")
        console.print("\nLet's try examining what the webpage actually does...")
        
        # Try to see what JavaScript loads
        console.print("\n[yellow]The webpage shows 1,326 items, so they must be loaded somehow.[/yellow]")
        console.print("[yellow]Try opening the page in a browser with Developer Tools (F12)[/yellow]")
        console.print("[yellow]and look at the Network tab to see what API calls are made.[/yellow]")
        return
    
    # Extract items based on response format
    items = []
    if 'items' in data:
        items = data['items']
    elif 'response' in data and 'docs' in data['response']:
        items = data['response']['docs']
        
        # Check if we need to paginate
        total = data['response'].get('numFound', 0)
        if total > len(items):
            console.print(f"\n[yellow]Note: Found {total} total items but only got {len(items)}[/yellow]")
            console.print("[yellow]Need to implement pagination to get all items[/yellow]")
    
    if items:
        console.print(f"\n[bold]Found {len(items)} items![/bold]")
        
        # Show sample
        console.print("\nFirst 5 items:")
        for item in items[:5]:
            if isinstance(item, dict):
                console.print(f"  - {item.get('identifier', 'unknown')}: {item.get('title', 'No title')}")
        
        # Save to database
        saved = save_to_db(items)
        
        console.print(f"\n[bold green]✓ Complete! Saved {saved} items to media_library.db[/bold green]")
    else:
        console.print("\n[red]No items found in response[/red]")

if __name__ == "__main__":
    main()