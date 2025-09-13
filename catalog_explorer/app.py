#!/usr/bin/env python3
"""
Catalog Explorer - Browse The Bobbing Channel media library
A fun, intuitive interface for exploring 1,327 items from Archive.org
"""

from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import json
from datetime import datetime
import random
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bobbing-channel-2025'

# Database path
DB_PATH = '../b_roll/media_library.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def format_number(num):
    """Format number with commas"""
    if num is None:
        return "0"
    return f"{int(num):,}"

def format_size(bytes):
    """Format bytes to human readable"""
    if not bytes:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"

@app.route('/')
def index():
    """Main catalog view"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get filter parameters
    mediatype = request.args.get('type', 'all')
    sort = request.args.get('sort', 'random')
    search = request.args.get('search', '')
    year = request.args.get('year', '')
    page = int(request.args.get('page', 1))
    per_page = 48  # Grid of 48 items
    
    # Build query
    query = "SELECT * FROM media WHERE 1=1"
    params = []
    
    if mediatype != 'all':
        query += " AND mediatype = ?"
        params.append(mediatype)
    
    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR creator LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    
    if year:
        query += " AND year = ?"
        params.append(int(year))
    
    # Get total count
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    cursor.execute(count_query, params)
    total_items = cursor.fetchone()[0]
    
    # Add sorting
    if sort == 'downloads':
        query += " ORDER BY downloads DESC"
    elif sort == 'date':
        query += " ORDER BY date DESC"
    elif sort == 'title':
        query += " ORDER BY title ASC"
    elif sort == 'size':
        query += " ORDER BY item_size DESC"
    else:  # random
        query += " ORDER BY RANDOM()"
    
    # Add pagination
    offset = (page - 1) * per_page
    query += f" LIMIT {per_page} OFFSET {offset}"
    
    cursor.execute(query, params)
    items = cursor.fetchall()
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) FROM media")
    total_in_db = cursor.fetchone()[0]
    
    cursor.execute("SELECT mediatype, COUNT(*) as count FROM media GROUP BY mediatype")
    type_counts = {row['mediatype']: row['count'] for row in cursor.fetchall()}
    
    cursor.execute("SELECT DISTINCT year FROM media WHERE year IS NOT NULL ORDER BY year DESC")
    years = [row['year'] for row in cursor.fetchall()]
    
    # Get random programming ideas
    programming_ideas = get_programming_ideas(cursor)
    
    conn.close()
    
    # Calculate pagination
    total_pages = (total_items + per_page - 1) // per_page
    
    return render_template('index.html',
                         items=items,
                         total_items=total_items,
                         total_in_db=total_in_db,
                         type_counts=type_counts,
                         years=years,
                         current_type=mediatype,
                         current_sort=sort,
                         current_search=search,
                         current_year=year,
                         current_page=page,
                         total_pages=total_pages,
                         format_number=format_number,
                         format_size=format_size,
                         programming_ideas=programming_ideas)

@app.route('/item/<identifier>')
def item_detail(identifier):
    """Detailed view of a single item"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM media WHERE identifier = ?", (identifier,))
    item = cursor.fetchone()
    
    if not item:
        return "Item not found", 404
    
    # Get similar items (same creator or random from same type)
    similar_query = """
        SELECT * FROM media 
        WHERE identifier != ? 
        AND (creator = ? OR mediatype = ?)
        ORDER BY RANDOM() 
        LIMIT 12
    """
    cursor.execute(similar_query, (identifier, item['creator'], item['mediatype']))
    similar = cursor.fetchall()
    
    conn.close()
    
    return render_template('detail.html',
                         item=item,
                         similar=similar,
                         format_number=format_number,
                         format_size=format_size)

@app.route('/random')
def random_item():
    """Get a random item"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT identifier FROM media ORDER BY RANDOM() LIMIT 1")
    item = cursor.fetchone()
    
    conn.close()
    
    if item:
        return jsonify({'identifier': item['identifier']})
    return jsonify({'error': 'No items found'}), 404


def get_programming_ideas(cursor):
    """Generate programming block ideas"""
    ideas = []
    
    # Late Night Obscura
    cursor.execute("""
        SELECT title, identifier FROM media 
        WHERE downloads < 50 
        ORDER BY RANDOM() LIMIT 3
    """)
    obscure = cursor.fetchall()
    if obscure:
        ideas.append({
            'block': 'Late Night Obscura',
            'description': 'Deep cuts nobody watches',
            'items': obscure
        })
    
    # Popular Hour
    cursor.execute("""
        SELECT title, identifier FROM media 
        ORDER BY downloads DESC LIMIT 3
    """)
    popular = cursor.fetchall()
    if popular:
        ideas.append({
            'block': 'Prime Time Favorites',
            'description': 'Most downloaded content',
            'items': popular
        })
    
    # Vintage Vault
    cursor.execute("""
        SELECT title, identifier FROM media 
        WHERE year < 1990 AND year IS NOT NULL
        ORDER BY RANDOM() LIMIT 3
    """)
    vintage = cursor.fetchall()
    if vintage:
        ideas.append({
            'block': 'Vintage Vault',
            'description': 'Pre-1990 classics',
            'items': vintage
        })
    
    return ideas

@app.route('/api/stats')
def api_stats():
    """Get collection statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    stats = {}
    
    # Basic counts
    cursor.execute("SELECT COUNT(*) FROM media")
    stats['total'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT mediatype, COUNT(*) as count FROM media GROUP BY mediatype")
    stats['by_type'] = {row['mediatype']: row['count'] for row in cursor.fetchall()}
    
    cursor.execute("SELECT SUM(item_size) FROM media")
    stats['total_size'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(downloads) FROM media")
    stats['total_downloads'] = cursor.fetchone()[0]
    
    # Year distribution
    cursor.execute("""
        SELECT year, COUNT(*) as count 
        FROM media 
        WHERE year IS NOT NULL 
        GROUP BY year 
        ORDER BY year
    """)
    stats['by_year'] = {row['year']: row['count'] for row in cursor.fetchall()}
    
    conn.close()
    
    return jsonify(stats)

if __name__ == '__main__':
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        print("Make sure you run this from the catalog_explorer directory")
        exit(1)
    
    print("Starting Catalog Explorer...")
    print("Open http://localhost:5001 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5001)