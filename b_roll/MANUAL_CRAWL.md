# Manual Crawling Instructions

Since the Archive.org page at https://archive.org/details/@mark_pines_archive_project uses heavy JavaScript rendering that's not working well with our automated tools on the Raspberry Pi, here's how to manually get the data:

## Option 1: Browser Developer Tools

1. Open the page in a desktop browser: https://archive.org/details/@mark_pines_archive_project
2. Open Developer Tools (F12)
3. Go to the Network tab
4. Refresh the page
5. Look for XHR/Fetch requests that return JSON data with the items
6. The API endpoint will likely be one of:
   - `/services/search/v1/scrape`
   - `/advancedsearch.php`
   - `/services/users/mark_pines_archive_project/`

## Option 2: Browser Console Extraction

1. Open the page in a browser
2. Wait for all 1,326 items to load (scroll down if needed)
3. Open the browser console (F12 → Console)
4. Run this JavaScript to extract all items:

```javascript
// Extract all item links and titles
let items = [];
document.querySelectorAll('a[href*="/details/"]').forEach(link => {
    let href = link.getAttribute('href');
    if (href && !href.includes('@mark_pines')) {
        let id = href.split('/details/')[1].split('?')[0];
        let title = link.getAttribute('title') || link.textContent.trim();
        if (id) {
            items.push({
                identifier: id,
                title: title,
                url: 'https://archive.org' + href
            });
        }
    }
});

// Remove duplicates
let unique = {};
items.forEach(item => {
    unique[item.identifier] = item;
});

// Convert to JSON
console.log(JSON.stringify(Object.values(unique), null, 2));
console.log('Total items:', Object.keys(unique).length);
```

5. Copy the JSON output and save to a file called `items.json`

## Option 3: Export Browser HAR File

1. Open Developer Tools → Network tab
2. Load the page
3. Right-click in the Network tab → Save all as HAR
4. We can then parse the HAR file to find the API requests

## Import Script

Once you have the data, use this script to import it:

```python
#!/usr/bin/env python3
import json
import sqlite3

# Load the JSON data
with open('items.json', 'r') as f:
    items = json.load(f)

# Save to database
conn = sqlite3.connect('media_library.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS media (
        identifier TEXT PRIMARY KEY,
        title TEXT,
        item_url TEXT
    )
''')

for item in items:
    cursor.execute('''
        INSERT OR REPLACE INTO media VALUES (?, ?, ?)
    ''', (
        item.get('identifier'),
        item.get('title'),
        item.get('url', f"https://archive.org/details/{item.get('identifier')}")
    ))

conn.commit()
conn.close()

print(f"Imported {len(items)} items")
```

## Why This Is Happening

The Archive.org member page uses React or similar JavaScript framework that:
1. Loads initial HTML with no content
2. Makes API calls to fetch the data
3. Renders the items client-side

The Chromium headless browser on Raspberry Pi seems to have issues with:
- JavaScript execution timing
- Modern React/Vue rendering
- Possible memory constraints

## Next Steps

Once we identify the actual API endpoint from the browser tools, we can update our crawler to use it directly without needing browser automation.