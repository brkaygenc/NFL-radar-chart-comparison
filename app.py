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
        print(f"Fetching players for position: {position}")
        api_url = f"{API_BASE_URL}/players/{position}"
        print(f"API URL: {api_url}")
        
        # Fetch data from the NFL stats API
        response = requests.get(api_url)
        print(f"API Response Status: {response.status_code}")
        print(f"API Response Content: {response.text[:500]}")  # Print first 500 chars of response
        
        if response.status_code != 200:
            return f"API Error: {response.status_code} - {response.text}", 500
            
        try:
            players = response.json()
            print(f"Number of players found: {len(players)}")
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {str(e)}")
            return f"Invalid JSON response from API: {str(e)}", 500
        
        # Convert to XML for processing
        xml_data = convert_to_xml(players)
        return xml_data, 200, {'Content-Type': 'application/xml'}
    except requests.RequestException as e:
        print(f"Request error: {str(e)}")
        return f"API Request Error: {str(e)}", 500
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 