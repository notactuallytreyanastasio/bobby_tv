#!/usr/bin/env python3
"""Test getting member uploads from Archive.org"""

import requests
import json

def test_member_uploads():
    # Try the member search endpoint
    base_url = "https://archive.org/services/search/v1/scrape"
    
    params = {
        'q': '@mark_pines_archive_project',
        'fields': 'identifier,title,mediatype,collection,creator,uploader,publicdate',
        'count': 10000,
        'sorts': 'publicdate desc'
    }
    
    print("Testing Archive.org scrape API...")
    
    try:
        response = requests.get(base_url, params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'items' in data:
                print(f"Found {len(data['items'])} items")
                print(f"Total available: {data.get('total', 'unknown')}")
                
                if data['items']:
                    print("\nFirst 5 items:")
                    for item in data['items'][:5]:
                        print(f"  - {item.get('identifier')}: {item.get('title')}")
                        print(f"    Type: {item.get('mediatype')}, Uploader: {item.get('uploader')}")
            else:
                print("Response:", json.dumps(data, indent=2))
        else:
            print("Error response:", response.text[:500])
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Also try a different query format
    print("\n\nTrying member uploads query...")
    
    params = {
        'q': 'uploader:(mark_pines_archive_project) OR creator:(mark_pines_archive_project)',
        'fields': 'identifier,title,uploader,creator',
        'count': 10
    }
    
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data.get('total', 0)} items with uploader/creator query")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_member_uploads()