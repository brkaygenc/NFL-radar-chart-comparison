from flask import Flask, render_template, jsonify, send_from_directory
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
import os
import logging
from urllib.parse import urljoin
from lxml import etree

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Updated API URL to use the new API endpoint
API_BASE_URL = os.environ.get('NFL_API_URL', 'https://nfl-stats-api-2024-63a0f473cb46.herokuapp.com/api')

# Updated valid positions to include all available positions
VALID_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF', 'LB', 'DB', 'DL']

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
        
        # Stats fields - handle both offensive and defensive stats
        stats_fields = [
            # Offensive stats
            'passingyards', 'passingtds', 'interceptions', 'rushingyards',
            'rushingtds', 'receptions', 'receivingyards', 'receivingtds',
            'targets', 'yards_per_reception', 'fumbles', 'totalpoints',
            # Defensive stats
            'tackles', 'tackles_ast', 'sacks', 'tackles_tfl',
            'passes_defended', 'forced_fumbles', 'fumble_recoveries',
            'qb_hits'
        ]
        
        # Log the available fields in the player data
        logger.info(f"Available fields for player {player.get('name')}: {list(player.keys())}")
        
        for field in stats_fields:
            if field in player:
                elem = ET.SubElement(player_elem, field)
                value = player.get(field, '0')
                elem.text = str(value)
                logger.debug(f"Setting {field} = {value} for player {player.get('name')}")
    
    # Convert to string with proper formatting
    xml_str = ET.tostring(root, encoding='unicode')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    # Log a sample of the generated XML
    logger.info(f"Generated XML sample (first 500 chars): {pretty_xml[:500]}")
    
    # Validate XML against schema
    if not validate_xml(pretty_xml, 'static/player_stats.xsd'):
        logger.error("Generated XML does not validate against schema")
        return None
        
    return pretty_xml

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/players/<position>')
def get_players_by_position(position):
    try:
        # Validate position
        position = position.upper()
        if position not in VALID_POSITIONS:
            logger.warning(f"Invalid position requested: {position}")
            return jsonify({
                'error': 'Invalid position',
                'valid_positions': VALID_POSITIONS
            }), 400

        logger.info(f"Fetching players for position: {position}")
        api_url = f"{API_BASE_URL}/players/{position}"
        logger.info(f"API URL: {api_url}")
        
        # Add headers to request JSON response
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'NFL-Stats-Visualizer/1.0'
        }
        
        # Add timeout to prevent hanging
        response = requests.get(api_url, headers=headers, timeout=10)
        logger.info(f"API Response Status: {response.status_code}")
        
        # Handle different status codes
        if response.status_code == 404:
            logger.warning(f"No data found for position: {position}")
            return jsonify({'error': 'No data found for this position'}), 404
        elif response.status_code == 403:
            logger.error(f"API access forbidden for position: {position}")
            return jsonify({'error': 'API access forbidden. Please check authentication.'}), 403
        elif response.status_code != 200:
            logger.error(f"API Error {response.status_code} for position {position}: {response.text}")
            return jsonify({
                'error': f'API Error: {response.status_code}',
                'message': response.text
            }), 500
            
        try:
            players = response.json()
            if not isinstance(players, list):
                logger.error(f"Invalid API response format for position {position}. Got: {type(players)}")
                return jsonify({'error': 'Invalid API response format. Expected an array of players.'}), 500
                
            logger.info(f"Number of players found: {len(players)}")
            logger.debug(f"First player data: {players[0] if players else 'No players'}")
            
            # Convert to XML and validate
            xml_data = convert_to_xml(players)
            if xml_data is None:
                return jsonify({'error': 'Failed to generate valid XML'}), 500
                
            return xml_data, 200, {'Content-Type': 'application/xml; charset=utf-8'}
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error for position {position}: {str(e)}")
            logger.error(f"Raw response content: {response.text}")
            return jsonify({
                'error': 'Invalid JSON response from API',
                'message': str(e)
            }), 500
            
    except requests.Timeout:
        logger.error(f"API request timed out for position: {position}")
        return jsonify({
            'error': 'API request timed out',
            'message': 'The NFL stats API is not responding'
        }), 504
        
    except requests.ConnectionError:
        logger.error(f"Could not connect to API for position: {position}")
        return jsonify({
            'error': 'API connection error',
            'message': 'Could not connect to the NFL stats API'
        }), 503
        
    except Exception as e:
        logger.exception(f"Unexpected error for position {position}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 