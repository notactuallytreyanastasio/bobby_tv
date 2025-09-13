#!/usr/bin/env python3
"""Test to get full count from Archive.org"""

import requests

def test_full_search():
    base_url = "https://archive.org/advancedsearch.php"
    
    # Use the query that worked
    params = {
        'q': '@mark_pines_archive_project',
        'fl': 'identifier',
        'rows': 1,
        'output': 'json'
    }
    
    response = requests.get(base_url, params=params)
    data = response.json()
    
    if 'response' in data:
        print(f"Total items found: {data['response'].get('numFound', 0)}")
        
    # Now let's check what a specific item looks like
    print("\nTrying to get metadata for the collection itself...")
    meta_url = "https://archive.org/metadata/@mark_pines_archive_project"
    
    try:
        response = requests.get(meta_url)
        data = response.json()
        
        if 'metadata' in data:
            print("Collection metadata found:")
            print(f"  Type: {data['metadata'].get('mediatype')}")
            print(f"  Title: {data['metadata'].get('title')}")
            
            # Check if this is a collection
            if data['metadata'].get('mediatype') == 'collection':
                print("\nThis IS a collection! Searching for items in this collection...")
                
                # Search for items in this collection
                params = {
                    'q': 'collection:@mark_pines_archive_project OR collection:mark_pines_archive_project',
                    'fl': 'identifier,title,collection',
                    'rows': 10,
                    'output': 'json'
                }
                
                response = requests.get(base_url, params=params)
                search_data = response.json()
                
                if 'response' in search_data:
                    print(f"Items in collection: {search_data['response'].get('numFound', 0)}")
                    
                    if search_data['response'].get('docs'):
                        print("Sample items:")
                        for item in search_data['response']['docs'][:5]:
                            print(f"  - {item.get('identifier')}: {item.get('collection')}")
    except Exception as e:
        print(f"Error getting metadata: {e}")

if __name__ == "__main__":
    test_full_search()