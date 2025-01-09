from flask import Flask, jsonify, render_template
from lxml import etree
import xml.etree.ElementTree as ET
import requests
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VALID_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'LB', 'DB', 'DL']
NFL_API_BASE_URL = "https://nfl-stats-api-2024-63a0f473cb46.herokuapp.com"

def make_api_request(endpoint):
    try:
        response = requests.get(f"{NFL_API_BASE_URL}{endpoint}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"API request failed: {str(e)}")
        raise

def convert_to_xml(data):
    root = ET.Element("players")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xsi:noNamespaceSchemaLocation", "static/player_stats.xsd")
    
    for player in data:
        player_elem = ET.SubElement(root, "player")
        player_id = str(player.get('playerid', ''))
        player_elem.set("id", player_id)
        
        # Common fields
        name_elem = ET.SubElement(player_elem, "name")
        name_elem.text = player.get('name', '')
        
        position_elem = ET.SubElement(player_elem, "position")
        position_elem.text = player.get('position', '')
        
        team_elem = ET.SubElement(player_elem, "team")
        team_elem.text = player.get('team', '')

        # Position-specific stats
        position = player.get('position', '').upper()
        
        if position == 'QB':
            for stat in ['passing_yards', 'passing_touchdowns', 'rushing_yards', 'interceptions']:
                stat_elem = ET.SubElement(player_elem, stat)
                stat_elem.text = str(player.get(stat, 0))
        
        elif position == 'RB':
            for stat in ['rushing_yards', 'rushing_touchdowns', 'receiving_yards', 'receptions']:
                stat_elem = ET.SubElement(player_elem, stat)
                stat_elem.text = str(player.get(stat, 0))
        
        elif position in ['WR', 'TE']:
            for stat in ['receiving_yards', 'receiving_touchdowns', 'receptions', 'targets']:
                stat_elem = ET.SubElement(player_elem, stat)
                stat_elem.text = str(player.get(stat, 0))
        
        elif position in ['LB', 'DL']:
            for stat in ['tackles', 'sacks', 'tackles_for_loss', 'forced_fumbles']:
                stat_elem = ET.SubElement(player_elem, stat)
                stat_elem.text = str(player.get(stat, 0))
        
        elif position == 'DB':
            for stat in ['tackles', 'interceptions', 'passes_defended', 'forced_fumbles']:
                stat_elem = ET.SubElement(player_elem, stat)
                stat_elem.text = str(player.get(stat, 0))
        
        elif position == 'K':
            for stat in ['fieldgoals', 'fieldgoal_attempts', 'extrapoints', 'extrapoint_attempts']:
                stat_elem = ET.SubElement(player_elem, stat)
                stat_elem.text = str(player.get(stat, 0))

        # Total points for all positions
        total_points_elem = ET.SubElement(player_elem, "total_points")
        total_points_elem.text = str(player.get('total_points', 0))

    return ET.tostring(root, encoding='unicode', xml_declaration=True)

def validate_xml(xml_string, xsd_path):
    try:
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), xsd_path)
        schema_doc = etree.parse(schema_path)
        schema = etree.XMLSchema(schema_doc)
        xml_doc = etree.fromstring(xml_string.encode('utf-8'))
        schema.assertValid(xml_doc)
        return True
    except Exception as e:
        logger.error(f"XML validation error: {str(e)}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/players/<position>')
def get_players_by_position(position):
    try:
        position = position.upper()
        if position not in VALID_POSITIONS:
            return jsonify({'error': 'Invalid position'}), 400

        players = make_api_request(f'/api/players/{position}')
        xml_data = convert_to_xml(players)
        
        if not validate_xml(xml_data, 'static/player_stats.xsd'):
            return jsonify({'error': 'Generated XML failed validation'}), 500

        return xml_data, 200, {'Content-Type': 'application/xml; charset=utf-8'}
    except Exception as e:
        logger.error(f"Error in get_players_by_position: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/teams')
def get_teams():
    try:
        teams = make_api_request('/api/teams')
        return jsonify(teams)
    except Exception as e:
        logger.error(f"Error in get_teams: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/team/<team_code>/players')
def get_team_players(team_code):
    try:
        players = make_api_request(f'/api/team/{team_code}/players')
        xml_data = convert_to_xml(players)
        
        if not validate_xml(xml_data, 'static/player_stats.xsd'):
            return jsonify({'error': 'Generated XML failed validation'}), 500

        return xml_data, 200, {'Content-Type': 'application/xml; charset=utf-8'}
    except Exception as e:
        logger.error(f"Error in get_team_players: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True) 