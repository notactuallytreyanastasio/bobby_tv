#!/usr/bin/env python3
"""Test script to debug Archive.org API queries"""

import requests
import json

def test_queries():
    base_url = "https://archive.org/advancedsearch.php"
    
    # Test different query formats
    queries = [
        'uploader:"mark_pines_archive_project"',
        'uploader:mark_pines_archive_project',
        'creator:"mark_pines_archive_project"',
        'creator:mark_pines_archive_project',
        '@mark_pines_archive_project',
        'collection:mark_pines_archive_project',
        'collection:"mark_pines_archive_project"',
        'collection:@mark_pines_archive_project',
        'collection:"@mark_pines_archive_project"',
    ]
    
    print("Testing Archive.org API queries...\n")
    
    for query in queries:
        params = {
            'q': query,
            'fl': 'identifier,title',
            'rows': 5,
            'page': 1,
            'output': 'json'
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'response' in data:
                num_found = data['response'].get('numFound', 0)
                print(f"Query: {query}")
                print(f"  Found: {num_found} items")
                
                if num_found > 0 and 'docs' in data['response']:
                    print("  First few items:")
                    for item in data['response']['docs'][:3]:
                        print(f"    - {item.get('identifier')}: {item.get('title', 'No title')}")
                print()
        except Exception as e:
            print(f"Query: {query}")
            print(f"  Error: {e}\n")

if __name__ == "__main__":
    test_queries()