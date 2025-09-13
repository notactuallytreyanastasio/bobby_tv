#!/usr/bin/env python3
"""Check for items in mark_pines_archive_project collection"""

import requests

def check_collection():
    base_url = "https://archive.org/advancedsearch.php"
    
    # Search for items that have mark_pines_archive_project in their collection field
    queries = [
        'collection:(mark_pines_archive_project)',
        'collection:(mark pines archive project)',
        'collection:*mark_pines*',
        'collection:markmilligan',  # Maybe different username?
        'uploader:markmilligan',
    ]
    
    print("Checking collection searches...\n")
    
    for query in queries:
        params = {
            'q': query,
            'fl': 'identifier,title,collection,uploader',
            'rows': 1000,  # Get more items to see the full count
            'output': 'json'
        }
        
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if 'response' in data:
            count = data['response'].get('numFound', 0)
            if count > 0:
                print(f"Query: {query}")
                print(f"  Found: {count} items")
                
                # Show unique collections found
                if 'docs' in data['response']:
                    collections = set()
                    uploaders = set()
                    for item in data['response']['docs']:
                        if 'collection' in item:
                            coll = item['collection']
                            if isinstance(coll, list):
                                collections.update(coll)
                            else:
                                collections.add(coll)
                        if 'uploader' in item:
                            uploaders.add(item['uploader'])
                    
                    if collections:
                        print(f"  Unique collections: {list(collections)[:10]}")
                    if uploaders:
                        print(f"  Unique uploaders: {list(uploaders)[:10]}")
                print()

if __name__ == "__main__":
    check_collection()