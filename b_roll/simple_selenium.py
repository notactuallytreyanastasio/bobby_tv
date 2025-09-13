#!/usr/bin/env python3
"""
Simple Selenium scraper - just get the rendered page and find items
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import sqlite3
from rich.console import Console

console = Console()

def scrape_page():
    """Simple page scrape"""
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.binary_location = '/usr/bin/chromium-browser'
    
    service = Service('/usr/bin/chromedriver')
    
    console.print("[yellow]Starting browser...[/yellow]")
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        console.print("[yellow]Loading page...[/yellow]")
        driver.get("https://archive.org/details/@mark_pines_archive_project")
        
        # Wait for page to load
        console.print("[yellow]Waiting for content...[/yellow]")
        time.sleep(10)
        
        # Find all links to /details/
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/details/"]')
        console.print(f"[green]Found {len(links)} detail links[/green]")
        
        # Extract unique items
        items = {}
        for link in links:
            href = link.get_attribute('href')
            if href and '/details/' in href and '@mark_pines' not in href:
                identifier = href.split('/details/')[-1].split('?')[0].split('#')[0]
                if identifier and identifier not in items:
                    title = link.get_attribute('title') or link.text or identifier
                    items[identifier] = {
                        'identifier': identifier,
                        'title': title.strip() if title else identifier,
                        'url': f"https://archive.org/details/{identifier}"
                    }
        
        console.print(f"[green]Found {len(items)} unique items![/green]")
        
        # Save to database
        if items:
            conn = sqlite3.connect("media_library.db")
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS media (
                    identifier TEXT PRIMARY KEY,
                    title TEXT,
                    item_url TEXT
                )
            ''')
            
            for item in items.values():
                cursor.execute('''
                    INSERT OR REPLACE INTO media (identifier, title, item_url)
                    VALUES (?, ?, ?)
                ''', (item['identifier'], item['title'], item['url']))
            
            conn.commit()
            conn.close()
            
            console.print(f"[green]✓ Saved {len(items)} items to database![/green]")
            
            # Show first 10
            console.print("\nFirst 10 items:")
            for i, (id, item) in enumerate(list(items.items())[:10]):
                console.print(f"  {i+1}. {item['title']}")
        
        return items
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return {}
    finally:
        driver.quit()

if __name__ == "__main__":
    console.print("[bold cyan]Simple Archive.org Scraper[/bold cyan]\n")
    items = scrape_page()
    
    if not items:
        console.print("\n[red]No items found. The page might need more time to load or different selectors.[/red]")