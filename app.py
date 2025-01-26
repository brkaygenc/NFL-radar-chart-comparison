from flask import Flask, render_template, jsonify, send_from_directory, request, Response
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

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
DEBUG = True  # Enable debug mode for more detailed error messages
app.config['DEBUG'] = DEBUG

# URLs for frontend and API
FRONTEND_URL = 'https://nfl-stats-visualizer-eu-c5e58c1a5426.herokuapp.com'
API_BASE_URL = os.getenv('NFL_API_URL', 'https://nfl-stats-api-2024-b3f5cb494117.herokuapp.com')

logger.info(f"Using API base URL: {API_BASE_URL}")

# Updated valid positions to include all available positions
VALID_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF', 'LB', 'DB', 'DL']

def make_api_request(endpoint):
    """Make a request to the NFL stats API"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        logger.info(f"Making API request to: {url}")
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'NFL-Stats-Visualizer/1.0'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        logger.info(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"API request failed with status {response.status_code}: {url}")
            logger.error(f"Response content: {response.text}")
            return None
            
        try:
            data = response.json()
            return data
        except ValueError as e:
            logger.error(f"Error parsing JSON response: {str(e)}")
            logger.error(f"Invalid JSON response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in make_api_request: {str(e)}")
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
        player_id = str(player.get('playerid', ''))
        player_elem.set("id", player_id)
        
        # Required fields
        for field in ['name', 'position', 'team']:
            elem = ET.SubElement(player_elem, field)
            value = player.get(field, '')
            elem.text = str(value) if value else ''

        # Add stats based on position
        position = player.get('position', '').upper()
        
        # Initialize all possible stats with default values
        default_stats = {
            # Offensive Stats
            'passing_yards': '0',
            'passing_touchdowns': '0',
            'interceptions': '0',
            'rushing_yards': '0',
            'rushing_touchdowns': '0',
            'receptions': '0',
            'receiving_yards': '0',
            'receiving_touchdowns': '0',
            'targets': '0',
            'yards_per_reception': '0.0',
            # Defensive Stats
            'tackles': '0',
            'sacks': '0.0',
            'tackles_for_loss': '0',
            'passes_defended': '0',
            'forced_fumbles': '0',
            'fumble_recoveries': '0',
            # Kicker Stats
            'fieldgoals': '0',
            'fieldgoal_attempts': '0',
            'extrapoints': '0',
            'extrapoint_attempts': '0',
            # Fantasy Points
            'total_points': '0.0'
        }
        
        # Add all stats with proper type handling
        for xml_field, default_value in default_stats.items():
            elem = ET.SubElement(player_elem, xml_field)
            value = None
            
            # Map API fields to XML fields
            if xml_field == 'tackles':
                value = player.get('tackles')
            elif xml_field == 'sacks':
                value = player.get('sacks')
            elif xml_field == 'tackles_for_loss':
                value = player.get('tackles_for_loss')
            elif xml_field == 'passes_defended':
                value = player.get('passes_defended')
            elif xml_field == 'forced_fumbles':
                value = player.get('forced_fumbles')
            elif xml_field == 'fumble_recoveries':
                value = player.get('fumble_recoveries', 0)
            # Kicker stats mapping
            elif xml_field == 'fieldgoals':
                value = player.get('field_goals')
            elif xml_field == 'fieldgoal_attempts':
                value = player.get('field_goals_attempted')
            elif xml_field == 'extrapoints':
                value = player.get('extra_points')
            elif xml_field == 'extrapoint_attempts':
                value = player.get('extra_points_attempted')
            elif xml_field == 'total_points':
                value = player.get('total_points')
            else:
                value = player.get(xml_field)
            
            try:
                if value is None:
                    elem.text = default_value
                elif isinstance(value, (int, float)):
                    # Handle decimal fields
                    if xml_field in ['sacks', 'yards_per_reception', 'total_points']:
                        elem.text = f"{float(value):.1f}"
                    else:
                        elem.text = str(int(float(value)))
                else:
                    # Try to convert string values
                    if xml_field in ['sacks', 'yards_per_reception', 'total_points']:
                        elem.text = f"{float(value):.1f}"
                    else:
                        elem.text = str(int(float(value)))
            except (ValueError, TypeError):
                logger.warning(f"Invalid value for {xml_field}: {value}, using default")
                elem.text = default_value
    
    xml_str = ET.tostring(root, encoding='unicode')
    return minidom.parseString(xml_str).toprettyxml(indent="  ")

import os
from lxml import etree

# Load XSD schema
XSD_PATH = os.path.join(os.path.dirname(__file__), 'static', 'player_stats.xsd')
try:
    with open(XSD_PATH, 'rb') as f:
        xsd_doc = etree.parse(f)
        xsd_schema = etree.XMLSchema(xsd_doc)
    logger.info("XSD schema loaded successfully")
except Exception as e:
    logger.error(f"Error loading XSD schema: {str(e)}")
    xsd_schema = None

def json_to_xml(player_data):
    """Convert player stats from JSON to XML format"""
    # Create root element
    players = ET.Element('players')
    
    # Create player element
    player = ET.SubElement(players, 'player', {'id': str(player_data.get('playerid', ''))})
    
    # Add basic info
    ET.SubElement(player, 'name').text = player_data.get('playername', '')
    ET.SubElement(player, 'position').text = player_data.get('position', '')
    ET.SubElement(player, 'team').text = player_data.get('team', '')
    
    # Add stats
    stats = [
        'passing_yards', 'passing_touchdowns', 'interceptions',
        'rushing_yards', 'rushing_touchdowns',
        'receptions', 'receiving_yards', 'receiving_touchdowns', 'targets',
        'tackles', 'sacks', 'tackles_for_loss', 'passes_defended', 'forced_fumbles',
        'fieldgoals', 'fieldgoal_attempts', 'extrapoints', 'extrapoint_attempts',
        'total_points'
    ]
    
    for stat in stats:
        value = player_data.get(stat, '0')
        ET.SubElement(player, stat).text = str(value)
    
    return ET.tostring(players, encoding='unicode', method='xml')

def validate_xml(xml_string):
    """Validate XML against XSD schema"""
    if not xsd_schema:
        logger.warning("XSD schema not loaded, skipping validation")
        return True
        
    try:
        xml_doc = etree.fromstring(xml_string.encode())
        xsd_schema.assertValid(xml_doc)
        return True
    except etree.DocumentInvalid as e:
        logger.error(f"XML validation failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error during XML validation: {str(e)}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/search')
def search_players():
    try:
        name = request.args.get('name', '').strip()
        position = request.args.get('position', '').strip().upper()
        
        if not name:
            return jsonify({'error': 'Name parameter is required'}), 400
            
        # If position is specified, get players for that position
        if position:
            url = f"{API_BASE_URL}/api/players/{position}"
            players = requests.get(url).json()
            # Filter by name
            players = [p for p in players if name.lower() in p['playername'].lower()]
        else:
            # Get all positions and search through each
            positions_url = f"{API_BASE_URL}/api/players/positions"
            positions = requests.get(positions_url).json()
            players = []
            for pos in positions:
                url = f"{API_BASE_URL}/api/players/{pos}"
                pos_players = requests.get(url).json()
                players.extend([p for p in pos_players if name.lower() in p['playername'].lower()])
        
        # Sort by total points
        players.sort(key=lambda x: float(x['totalpoints']), reverse=True)
        return jsonify(players)
        
    except Exception as e:
        logger.error(f"Error in search_players: {str(e)}")
        return jsonify({'error': 'Failed to search players', 'message': str(e)}), 500

@app.route('/api/players/<position>')
def get_players(position):
    """Get all players for a specific position"""
    position = position.upper()
    if position not in VALID_POSITIONS:
        return jsonify({'error': f'Invalid position. Valid positions are: {", ".join(VALID_POSITIONS)}'}), 400
    
    try:
        players = make_api_request(f'/api/players/{position}')
        if players is None:
            return jsonify({'error': 'Failed to fetch players data'}), 500
        return jsonify(players)
    except Exception as e:
        logger.error(f"Error in get_players: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/teams')
def get_teams():
    """Get all teams with their codes and divisions"""
    try:
        teams = make_api_request('/api/teams')
        if teams is None:
            return jsonify({'error': 'Failed to fetch teams data'}), 500
        return jsonify(teams)
    except Exception as e:
        logger.error(f"Error in get_teams: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/teams/<team_code>/players')
def get_team_players(team_code):
    """Get all players for a specific team"""
    team_code = team_code.upper()
    try:
        players = make_api_request(f'/api/teams/{team_code}/players')
        if players is None:
            return jsonify({'error': 'Failed to fetch team players data'}), 500
        return jsonify(players)
    except Exception as e:
        logger.error(f"Error in get_team_players: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/players/<playerid>/stats')
def get_player_stats(playerid):
    """Get stats for a specific player"""
    try:
        logger.info(f"Fetching stats for player ID: {playerid}")
        
        # First try to get the player's position
        search_response = make_api_request(f'/api/search?name={playerid}')
        if not search_response or not isinstance(search_response, list) or len(search_response) == 0:
            logger.warning(f"No player found with ID {playerid}")
            return jsonify({'error': 'Player not found'}), 404

        player = search_response[0]
        position = player.get('position')
        
        if not position:
            logger.warning(f"No position found for player {playerid}")
            return jsonify({'error': 'Player position not found'}), 404

        # Get player stats based on position
        all_players = make_api_request(f'/api/players/{position}')
        if not all_players:
            logger.warning(f"No players found for position {position}")
            return jsonify({'error': 'No players found for position'}), 404

        # Find this player's stats
        player_stats = next((p for p in all_players if str(p.get('playerid')) == str(playerid)), None)
        if not player_stats:
            logger.warning(f"Stats not found for player {playerid} in position {position}")
            return jsonify({'error': 'Player stats not found'}), 404

        # Convert to XML
        xml_data = json_to_xml(player_stats)
        
        # Validate XML
        if not validate_xml(xml_data):
            logger.error("XML validation failed")
            return jsonify({'error': 'Invalid player data format'}), 500

        # Set XML response headers
        response = app.response_class(
            response=xml_data,
            status=200,
            mimetype='application/xml'
        )
        return response

    except Exception as e:
        logger.error(f"Error in get_player_stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def json_to_xml(player_data):
    """Convert JSON player stats to XML format"""
    root = etree.Element("player")
    
    # Add basic player info
    name = etree.SubElement(root, "name")
    name.text = player_data.get('playername', '')
    
    position = etree.SubElement(root, "position")
    position.text = player_data.get('position', '')
    
    team = etree.SubElement(root, "team")
    team.text = player_data.get('team', '')
    
    # Add all stats
    for key, value in player_data.items():
        if key not in ['playername', 'position', 'team', 'playerid']:
            stat = etree.SubElement(root, key)
            stat.text = str(value)
    
    # Validate against schema
    try:
        xsd_path = os.path.join(os.path.dirname(__file__), 'static', 'player_stats.xsd')
        with open(xsd_path, 'rb') as f:
            xsd_doc = etree.parse(f)
            schema = etree.XMLSchema(xsd_doc)
        schema.assertValid(root)
    except etree.DocumentInvalid as e:
        logger.error(f"XML validation error: {e}")
        return None
    
    return etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 