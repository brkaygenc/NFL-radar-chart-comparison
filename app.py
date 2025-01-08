from flask import Flask, render_template, jsonify
import requests
import xml.etree.ElementTree as ET
import json
import os

app = Flask(__name__)

# Database URL from environment variable for security
DATABASE_URL = os.environ.get('DATABASE_URL')

def convert_to_xml(data):
    """Convert player data to XML format"""
    root = ET.Element("players")
    for player in data:
        player_elem = ET.SubElement(root, "player")
        for key, value in player.items():
            elem = ET.SubElement(player_elem, key)
            elem.text = str(value)
    return ET.tostring(root, encoding='unicode')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/players/<position>')
def get_players_by_position(position):
    try:
        # Connect to your PostgreSQL database directly
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Query based on position
        cur.execute("SELECT * FROM players WHERE position = %s", (position,))
        columns = [desc[0] for desc in cur.description]
        results = cur.fetchall()
        
        # Convert to list of dictionaries
        players = [dict(zip(columns, row)) for row in results]
        
        cur.close()
        conn.close()
        
        # Convert to XML for processing
        xml_data = convert_to_xml(players)
        return xml_data, 200, {'Content-Type': 'application/xml'}
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 