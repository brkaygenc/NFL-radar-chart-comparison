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
API_BASE_URL = os.getenv('NFL_API_URL', 'https://nfl-stats-bd003f70104a.herokuapp.com')

# Sample player data (fallback when API is not available)
SAMPLE_PLAYERS = {
    'QB': [
        {'name': 'Patrick Mahomes', 'position': 'QB', 'team': 'KC', 'passing_yards': 4183, 'passing_touchdowns': 27, 'interceptions': 14, 'rushing_yards': 358},
        {'name': 'Lamar Jackson', 'position': 'QB', 'team': 'BAL', 'passing_yards': 3678, 'passing_touchdowns': 24, 'interceptions': 7, 'rushing_yards': 821},
        {'name': 'Josh Allen', 'position': 'QB', 'team': 'BUF', 'passing_yards': 4306, 'passing_touchdowns': 29, 'interceptions': 18, 'rushing_yards': 524},
    ],
    'RB': [
        {'name': 'Christian McCaffrey', 'position': 'RB', 'team': 'SF', 'rushing_yards': 1459, 'rushing_touchdowns': 14, 'receiving_yards': 564, 'receptions': 67},
        {'name': 'Raheem Mostert', 'position': 'RB', 'team': 'MIA', 'rushing_yards': 1012, 'rushing_touchdowns': 11, 'receiving_yards': 175, 'receptions': 25},
    ],
    'WR': [
        {'name': 'CeeDee Lamb', 'position': 'WR', 'team': 'DAL', 'receiving_yards': 1749, 'receiving_touchdowns': 12, 'receptions': 135, 'targets': 181},
        {'name': 'Tyreek Hill', 'position': 'WR', 'team': 'MIA', 'receiving_yards': 1799, 'receiving_touchdowns': 13, 'receptions': 119, 'targets': 171},
    ]
}

# Updated valid positions to include all available positions
VALID_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF', 'LB', 'DB', 'DL']

def make_api_request(endpoint):
    """Make a request to the NFL stats API"""
    try:
        # First try to get data from the external API
        if endpoint.startswith('/api/search'):
            url = f"{API_BASE_URL}{endpoint}"
        else:
            position = endpoint.split('/')[-1]
            url = f"{API_BASE_URL}/api/players/{position}"
        
        logger.info(f"Making API request to: {url}")
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'NFL-Stats-Visualizer/1.0'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"API request failed, using sample data: {str(e)}")
        # If API fails, fall back to sample data
        if endpoint.startswith('/api/players/'):
            position = endpoint.split('/')[-1]
            return SAMPLE_PLAYERS.get(position, [])
        return []

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/search')
def search_players():
    """Search for players by name and optionally position"""
    name = request.args.get('name', '').strip()
    position = request.args.get('position', '').strip().upper()
    
    if not name:
        return jsonify({'error': 'Name parameter is required'}), 400
        
    if position and position not in VALID_POSITIONS:
        return jsonify({'error': f'Invalid position. Valid positions are: {", ".join(VALID_POSITIONS)}'}), 400
    
    try:
        players = []
        # If position is specified, search only in that position
        if position:
            # Try to get players from API, fall back to sample data if API fails
            api_players = make_api_request(f'/api/players/{position}')
            if not api_players:  # If API request failed
                api_players = SAMPLE_PLAYERS.get(position, [])
            players = [p for p in api_players if name.lower() in p.get('name', '').lower()]
        else:
            # Search across all positions
            for pos in VALID_POSITIONS:
                api_players = make_api_request(f'/api/players/{pos}')
                if not api_players:  # If API request failed
                    api_players = SAMPLE_PLAYERS.get(pos, [])
                players.extend([p for p in api_players if name.lower() in p.get('name', '').lower()])
        
        logger.info(f"Found {len(players)} players matching '{name}' for position {position or 'any'}")
        return jsonify(players)
    except Exception as e:
        logger.error(f"Error in search_players: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

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
        teams = [
            {"code": "ARI", "name": "Arizona Cardinals", "division": "NFC West"},
            {"code": "ATL", "name": "Atlanta Falcons", "division": "NFC South"},
            {"code": "BAL", "name": "Baltimore Ravens", "division": "AFC North"},
            {"code": "BUF", "name": "Buffalo Bills", "division": "AFC East"},
            {"code": "CAR", "name": "Carolina Panthers", "division": "NFC South"},
            {"code": "CHI", "name": "Chicago Bears", "division": "NFC North"},
            {"code": "CIN", "name": "Cincinnati Bengals", "division": "AFC North"},
            {"code": "CLE", "name": "Cleveland Browns", "division": "AFC North"},
            {"code": "DAL", "name": "Dallas Cowboys", "division": "NFC East"},
            {"code": "DEN", "name": "Denver Broncos", "division": "AFC West"},
            {"code": "DET", "name": "Detroit Lions", "division": "NFC North"},
            {"code": "GB", "name": "Green Bay Packers", "division": "NFC North"},
            {"code": "HOU", "name": "Houston Texans", "division": "AFC South"},
            {"code": "IND", "name": "Indianapolis Colts", "division": "AFC South"},
            {"code": "JAX", "name": "Jacksonville Jaguars", "division": "AFC South"},
            {"code": "KC", "name": "Kansas City Chiefs", "division": "AFC West"},
            {"code": "LV", "name": "Las Vegas Raiders", "division": "AFC West"},
            {"code": "LAC", "name": "Los Angeles Chargers", "division": "AFC West"},
            {"code": "LAR", "name": "Los Angeles Rams", "division": "NFC West"},
            {"code": "MIA", "name": "Miami Dolphins", "division": "AFC East"},
            {"code": "MIN", "name": "Minnesota Vikings", "division": "NFC North"},
            {"code": "NE", "name": "New England Patriots", "division": "AFC East"},
            {"code": "NO", "name": "New Orleans Saints", "division": "NFC South"},
            {"code": "NYG", "name": "New York Giants", "division": "NFC East"},
            {"code": "NYJ", "name": "New York Jets", "division": "AFC East"},
            {"code": "PHI", "name": "Philadelphia Eagles", "division": "NFC East"},
            {"code": "PIT", "name": "Pittsburgh Steelers", "division": "AFC North"},
            {"code": "SF", "name": "San Francisco 49ers", "division": "NFC West"},
            {"code": "SEA", "name": "Seattle Seahawks", "division": "NFC West"},
            {"code": "TB", "name": "Tampa Bay Buccaneers", "division": "NFC South"},
            {"code": "TEN", "name": "Tennessee Titans", "division": "AFC South"},
            {"code": "WAS", "name": "Washington Commanders", "division": "NFC East"}
        ]
        return jsonify(teams)
    except Exception as e:
        logger.error(f"Error in get_teams: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/teams/<team_code>/players')
def get_team_players(team_code):
    """Get all players for a specific team"""
    team_code = team_code.upper()
    try:
        all_players = []
        for position in VALID_POSITIONS:
            players = make_api_request(f'/api/players/{position}')
            if players:
                team_players = [p for p in players if p.get('team', '').upper() == team_code]
                all_players.extend(team_players)
        return jsonify(all_players)
    except Exception as e:
        logger.error(f"Error in get_team_players: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 