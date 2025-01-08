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
    logger.info(f"Making API request to: {url}")
    
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'NFL-Stats-Visualizer/1.0'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Received {len(data)} records from API")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        logger.error(f"Response content: {response.text if response else 'No response'}")
        return None

def validate_xml(xml_string, xsd_path):
    """Validate XML against XSD schema"""
    try:
        # Get absolute path to schema file
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), xsd_path)
        schema_doc = etree.parse(schema_path)
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
        # Use playerid if available, otherwise use a fallback
        player_id = str(player.get('playerid', player.get('id', '')))
        player_elem.set("id", player_id)
        
        # Required fields with validation
        for field in ['name', 'position', 'team']:
            elem = ET.SubElement(player_elem, field)
            value = player.get(field, '')
            elem.text = str(value) if value else ''
        
        # Position-specific stats mapping
        position = player.get('position', '').upper()
        
        # Common stats mapping for all positions
        stats_mapping = {
            'QB': {
                'passing_yards': 'passing_yards',
                'passing_touchdowns': 'passing_touchdowns',
                'interceptions': 'interceptions',
                'rushing_yards': 'rushing_yards',
                'total_points': 'total_points'
            },
            'RB': {
                'rushing_yards': 'rushing_yards',
                'rushing_touchdowns': 'rushing_touchdowns',
                'receptions': 'receptions',
                'receiving_yards': 'receiving_yards',
                'total_points': 'total_points'
            },
            'WR': {
                'receiving_yards': 'receiving_yards',
                'receiving_touchdowns': 'receiving_touchdowns',
                'receptions': 'receptions',
                'targets': 'targets',
                'total_points': 'total_points'
            },
            'TE': {
                'receiving_yards': 'receiving_yards',
                'receiving_touchdowns': 'receiving_touchdowns',
                'receptions': 'receptions',
                'targets': 'targets',
                'total_points': 'total_points'
            },
            'LB': {
                'tackles': 'tackles',
                'sacks': 'sacks',
                'interceptions': 'interceptions',
                'tackles_for_loss': 'tackles_for_loss',
                'total_points': 'total_points'
            },
            'DB': {
                'tackles': 'tackles',
                'interceptions': 'interceptions',
                'passes_defended': 'passes_defended',
                'forced_fumbles': 'forced_fumbles',
                'total_points': 'total_points'
            },
            'DL': {
                'tackles': 'tackles',
                'sacks': 'sacks',
                'tackles_for_loss': 'tackles_for_loss',
                'forced_fumbles': 'forced_fumbles',
                'total_points': 'total_points'
            }
        }
        
        # Add stats based on position
        if position in stats_mapping:
            position_stats = stats_mapping[position]
            for api_field, xml_field in position_stats.items():
                elem = ET.SubElement(player_elem, xml_field)
                value = player.get(api_field, 0)
                # Ensure numeric values
                try:
                    if isinstance(value, (int, float)):
                        elem.text = str(value)
                    else:
                        elem.text = str(float(value)) if value else '0'
                except (ValueError, TypeError):
                    elem.text = '0'
                    logger.warning(f"Invalid value for {api_field}: {value}, defaulting to 0")
    
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
            logger.warning(f"Invalid position requested: {position}")
            return jsonify({'error': 'Invalid position', 'valid_positions': VALID_POSITIONS}), 400

        logger.info(f"Fetching players for position: {position}")
        players = make_api_request(f'/api/players/{position}')
        
        if players is None:
            logger.error("Failed to fetch player data from API")
            return jsonify({'error': 'Failed to fetch player data'}), 503

        logger.info(f"Converting {len(players)} players to XML")
        try:
            xml_data = convert_to_xml(players)
            logger.info("XML conversion successful")
            logger.debug(f"Generated XML: {xml_data[:500]}...")  # Log first 500 chars
        except Exception as xml_error:
            logger.error(f"Failed to convert data to XML: {str(xml_error)}")
            return jsonify({'error': 'Failed to convert data to XML'}), 500
        
        logger.info("Validating XML against schema")
        if not validate_xml(xml_data, 'static/player_stats.xsd'):
            logger.error("Generated XML failed validation")
            return jsonify({'error': 'Generated XML failed validation'}), 500

        logger.info("Successfully generated and validated XML")
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