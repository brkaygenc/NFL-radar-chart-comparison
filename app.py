from flask import Flask, render_template, jsonify
import requests
import xml.etree.ElementTree as ET
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Database URL from environment variable for security
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

def convert_to_xml(data):
    """Convert player data to XML format"""
    root = ET.Element("players")
    for player in data:
        player_elem = ET.SubElement(root, "player")
        for key, value in player.items():
            elem = ET.SubElement(player_elem, key)
            elem.text = str(value) if value is not None else ""
    return ET.tostring(root, encoding='unicode')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/players/<position>')
def get_players_by_position(position):
    try:
        # Connect to your PostgreSQL database directly
        conn = psycopg2.connect(DATABASE_URL)
        
        # Use RealDictCursor to get results as dictionaries
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query based on position
        if position == 'all':
            cur.execute("SELECT * FROM players")
        else:
            cur.execute("SELECT * FROM players WHERE position = %s", (position,))
        
        players = cur.fetchall()
        
        # Convert players to list of dictionaries
        players_list = [dict(player) for player in players]
        
        cur.close()
        conn.close()
        
        # Convert to XML for processing
        xml_data = convert_to_xml(players_list)
        return xml_data, 200, {'Content-Type': 'application/xml'}
    except Exception as e:
        print(f"Database error: {str(e)}")  # Add logging
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 