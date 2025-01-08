from flask import Flask, render_template, jsonify
import requests
import xml.etree.ElementTree as ET
import json
import os
import logging
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Updated API URL to use the new API endpoint
API_BASE_URL = os.environ.get('NFL_API_URL', 'https://nfl-stats-api-2024-63a0f473cb46.herokuapp.com/api')

# Updated valid positions to include all available positions
VALID_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF', 'LB', 'DB', 'DL']

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
        logger.info(f"API Response Headers: {dict(response.headers)}")
        logger.info(f"API Response Content: {response.text[:500]}")  # Print first 500 chars for debugging
        
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
            
            # Convert to XML and return with proper content type
            xml_data = convert_to_xml(players)
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