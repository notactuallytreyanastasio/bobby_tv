#!/usr/bin/env python3
"""
Capture network requests to find the actual API endpoint
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json
import time
from rich.console import Console

console = Console()

def capture_network_requests():
    """Use Selenium to capture network requests"""
    
    # Enable network logging
    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.binary_location = '/usr/bin/chromium-browser'
    
    # Enable logging
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    
    console.print("[yellow]Loading page and capturing network requests...[/yellow]")
    
    try:
        # Navigate to the page
        driver.get("https://archive.org/details/@mark_pines_archive_project")
        
        # Wait for page to load
        time.sleep(5)
        
        # Get network logs
        logs = driver.get_log('performance')
        
        # Find API requests
        api_requests = []
        for entry in logs:
            log = json.loads(entry['message'])['message']
            if 'Network.requestWillBeSent' in log['method']:
                request = log['params']['request']
                url = request['url']
                
                # Look for API endpoints
                if any(x in url for x in ['/services/', 'search', 'metadata', '.json', 'scrape']):
                    if '@mark_pines' not in url or 'search' in url:
                        api_requests.append(url)
                        console.print(f"[green]Found API request:[/green] {url[:100]}...")
        
        # Also check page source for data
        page_source = driver.page_source
        
        # Look for JSON data embedded in page
        if 'window.__INITIAL_DATA__' in page_source:
            console.print("[green]Found embedded data in page![/green]")
        
        # Count items in page
        item_count = page_source.count('/details/')
        console.print(f"[cyan]Found {item_count} '/details/' links in page source[/cyan]")
        
        return api_requests
        
    finally:
        driver.quit()

if __name__ == "__main__":
    console.print("[bold cyan]Network Request Capture[/bold cyan]\n")
    
    requests = capture_network_requests()
    
    if requests:
        console.print(f"\n[bold]Found {len(requests)} API requests:[/bold]")
        for req in requests[:10]:
            console.print(f"  {req}")
    else:
        console.print("[red]No API requests found[/red]")
        console.print("\n[yellow]The page might be using:[/yellow]")
        console.print("  1. Server-side rendering (data embedded in HTML)")
        console.print("  2. A different domain for API")
        console.print("  3. WebSocket connections")
        console.print("  4. GraphQL with POST requests")