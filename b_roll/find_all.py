#!/usr/bin/env python3
"""Find all items associated with mark_pines_archive_project"""

import requests

def find_all_items():
    base_url = "https://archive.org/advancedsearch.php"
    
    # Try different search strategies
    searches = [
        ('Direct @username', '@mark_pines_archive_project'),
        ('Uploader (no @)', 'uploader:mark_pines_archive_project'),
        ('Creator', 'creator:mark_pines_archive_project'),
        ('Description contains', 'description:mark_pines_archive_project'),
        ('Any field', 'mark_pines_archive_project'),
    ]
    
    print("Searching for all items...\n")
    
    for name, query in searches:
        params = {
            'q': query,
            'fl': 'identifier,uploader,creator,collection',
            'rows': 5,
            'output': 'json'
        }
        
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if 'response' in data:
            count = data['response'].get('numFound', 0)
            print(f"{name}: {count} items")
            
            if count > 0 and 'docs' in data['response']:
                print("  Sample items:")
                for item in data['response']['docs'][:3]:
                    uploader = item.get('uploader', 'N/A')
                    creator = item.get('creator', 'N/A')
                    collections = item.get('collection', [])
                    if isinstance(collections, str):
                        collections = [collections]
                    print(f"    - {item['identifier']}")
                    print(f"      Uploader: {uploader}, Creator: {creator}")
                    if collections:
                        print(f"      Collections: {', '.join(collections[:3])}")
            print()

if __name__ == "__main__":
    find_all_items()