from flask import Flask, render_template, jsonify
import requests
import xml.etree.ElementTree as ET
import json
import os

app = Flask(__name__)

# Database URL from environment variable for security
DATABASE_URL = "postgres://u4frfq8rphkr89:pb906d5963e4ac1f17db49d71c8ff2cfddd55faa1f12a6f63aa9a1d1ac938b9a9@clhtb6lu92mj2.cluster-czz5s0kz4scl.eu-west-1.rds.amazonaws.com:5432/d1imqo8lepvt22"

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
    # Here you would fetch data from your Heroku API
    # For now, we'll return a sample response
    response = requests.get(f'YOUR_API_URL/players/{position}')
    players = response.json()
    
    # Convert to XML for processing
    xml_data = convert_to_xml(players)
    return xml_data, 200, {'Content-Type': 'application/xml'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 