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
API_BASE_URL = os.environ.get('NFL_API_URL', 'https://nfl-stats-api-2024-63a0f473cb46.herokuapp.com')

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
        
        # Map API fields to our XML fields based on position
        position = player.get('position', '').upper()
        
        # Common fields for all positions
        field_mapping = {
            # Offensive stats
            'passing_yards': 'passingyards',
            'passing_touchdowns': 'passingtds',
            'rushing_yards': 'rushingyards',
            'rushing_touchdowns': 'rushingtds',
            'receiving_yards': 'receivingyards',
            'receiving_touchdowns': 'receivingtds',
            'receptions': 'receptions',
            'targets': 'targets',
            'total_points': 'totalpoints',
            'interceptions': 'interceptions',
            # Defensive stats
            'tackles': 'tackles',
            'sacks': 'sacks',
            'passes_defended': 'passes_defended',
            'forced_fumbles': 'forced_fumbles',
            'tackles_for_loss': 'tackles_tfl',
            'qb_hits': 'qb_hits'
        }
        
        # Log the available fields in the player data
        logger.info(f"Available fields for player {player.get('name')}: {list(player.keys())}")
        
        # Map and convert fields
        for api_field, xml_field in field_mapping.items():
            if api_field in player:
                elem = ET.SubElement(player_elem, xml_field)
                value = player.get(api_field, '0')
                elem.text = str(value)
                logger.debug(f"Mapping {api_field} -> {xml_field} = {value} for player {player.get('name')}")
    
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
        
        # Try different API URL patterns
        api_urls = [
            f"{API_BASE_URL}/api/players/{position}",
            f"{API_BASE_URL}/players/{position}",
            f"{API_BASE_URL}/api/v1/players/{position}",
            f"{API_BASE_URL}/v1/players/{position}"
        ]
        
        # Add headers to request JSON response
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'NFL-Stats-Visualizer/1.0'
        }
        
        response = None
        working_url = None
        
        # Try each URL pattern until we get a successful response
        for url in api_urls:
            logger.info(f"Trying API URL: {url}")
            try:
                response = requests.get(url, headers=headers, timeout=10)
                logger.info(f"Response from {url}: Status={response.status_code}, Content-Type={response.headers.get('Content-Type')}")
                
                if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
                    working_url = url
                    break
            except Exception as e:
                logger.warning(f"Failed to fetch from {url}: {str(e)}")
                continue
        
        if not working_url:
            logger.error("No working API URL found")
            return jsonify({
                'error': 'API endpoint not found',
                'message': 'Could not find a working API endpoint'
            }), 404
            
        logger.info(f"Using working API URL: {working_url}")
        
        try:
            players = response.json()
            logger.info(f"Successfully parsed JSON response. Type: {type(players)}")
            logger.info(f"First player data: {players[0] if players else 'No players'}")
            
            if not isinstance(players, list):
                logger.error(f"Invalid API response format. Got: {type(players)}")
                return jsonify({'error': 'Invalid API response format. Expected an array of players.'}), 500
                
            logger.info(f"Number of players found: {len(players)}")
            
            # Convert to XML and validate
            xml_data = convert_to_xml(players)
            if xml_data is None:
                return jsonify({'error': 'Failed to generate valid XML'}), 500
                
            logger.info("Successfully generated and validated XML")
            return xml_data, 200, {'Content-Type': 'application/xml; charset=utf-8'}
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {str(e)}")
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