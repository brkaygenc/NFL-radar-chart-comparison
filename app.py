from flask import Flask, render_template, jsonify
import requests
import xml.etree.ElementTree as ET
import json
import os

app = Flask(__name__)

API_BASE_URL = "https://nfl-website-db-8d1f1be10618.herokuapp.com/api"

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
        # Fetch data from the NFL stats API
        response = requests.get(f"{API_BASE_URL}/players/{position}")
        if response.status_code != 200:
            return f"API Error: {response.status_code}", 500
            
        players = response.json()
        
        # Convert to XML for processing
        xml_data = convert_to_xml(players)
        return xml_data, 200, {'Content-Type': 'application/xml'}
    except Exception as e:
        print(f"API error: {str(e)}")  # Add logging
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 