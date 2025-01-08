from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_cors import CORS
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
import os
import logging
from urllib.parse import urljoin
from lxml import etree
from dotenv import load_dotenv
import pandas as pd
import numpy as np

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Configuration
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
app.config['DEBUG'] = DEBUG

# Updated API URL to use the new API endpoint with fallback
API_BASE_URL = os.getenv('NFL_API_URL', 'https://nfl-stats-api-2024-63a0f473cb46.herokuapp.com')

# Updated valid positions to include all available positions
VALID_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF', 'LB', 'DB', 'DL']

def make_api_request(endpoint):
    """Make a request to the NFL stats API"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'NFL-Stats-Visualizer/1.0'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return None

def validate_xml(xml_string, xsd_path):
    """Validate XML against XSD schema"""
    try:
        schema_doc = etree.parse(xsd_path)
        schema = etree.XMLSchema(schema_doc)
        xml_doc = etree.fromstring(xml_string.encode('utf-8'))
        schema.assertValid(xml_doc)
        return True
    except Exception as e:
        logger.error(f"XML validation error: {str(e)}")
        return False

def convert_to_xml(data):
    """Convert player data to XML format with proper schema"""
    root = ET.Element("players")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xsi:noNamespaceSchemaLocation", "static/player_stats.xsd")
    
    for player in data:
        player_elem = ET.SubElement(root, "player")
        player_elem.set("id", str(player.get('id', '')))
        
        # Required fields
        for field in ['name', 'position', 'team']:
            elem = ET.SubElement(player_elem, field)
            elem.text = str(player.get(field, ''))
        
        # Map API fields to XML fields based on position
        position = player.get('position', '').upper()
        
        # Position-specific stats mapping
        stats_mapping = {
            'QB': ['passing_yards', 'passing_touchdowns', 'interceptions'],
            'RB': ['rushing_yards', 'rushing_touchdowns', 'receptions'],
            'WR': ['receiving_yards', 'receptions', 'targets', 'receiving_touchdowns'],
            'TE': ['receiving_yards', 'receptions', 'targets', 'receiving_touchdowns'],
            'K': ['field_goals_made', 'field_goals_attempted', 'extra_points_made'],
            'LB': ['tackles', 'sacks', 'interceptions'],
            'DB': ['tackles', 'interceptions', 'passes_defended'],
            'DL': ['tackles', 'sacks', 'tackles_for_loss']
        }
        
        # Add stats based on position
        if position in stats_mapping:
            for stat in stats_mapping[position]:
                if stat in player:
                    elem = ET.SubElement(player_elem, stat)
                    elem.text = str(player.get(stat, '0'))
    
    xml_str = ET.tostring(root, encoding='unicode')
    return minidom.parseString(xml_str).toprettyxml(indent="  ")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/players/<position>')
def get_players_by_position(position):
    try:
        position = position.upper()
        if position not in VALID_POSITIONS:
            return jsonify({'error': 'Invalid position', 'valid_positions': VALID_POSITIONS}), 400

        players = make_api_request(f'/api/players/{position}')
        if players is None:
            return jsonify({'error': 'Failed to fetch player data'}), 503

        xml_data = convert_to_xml(players)
        if not validate_xml(xml_data, 'static/player_stats.xsd'):
            return jsonify({'error': 'Generated XML failed validation'}), 500

        return xml_data, 200, {'Content-Type': 'application/xml; charset=utf-8'}

    except Exception as e:
        logger.exception(f"Error processing request for position {position}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/teams')
def get_teams():
    """Get all teams with their codes and divisions"""
    teams = make_api_request('/api/teams')
    if teams is None:
        return jsonify({'error': 'Failed to fetch team data'}), 503
    return jsonify(teams)

@app.route('/api/team/<team_code>/players')
def get_team_players(team_code):
    """Get all players for a specific team"""
    players = make_api_request(f'/api/team/{team_code}/players')
    if players is None:
        return jsonify({'error': 'Failed to fetch team players'}), 503
    return jsonify(players)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 