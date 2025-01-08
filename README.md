# NFL Stats Visualizer

A modern web application for visualizing and comparing NFL player statistics using interactive radar charts. The application implements a RESTful architecture with XML-based data exchange, demonstrating modern web service principles and data transformation techniques.

## Features

- **Player Search**: Search for NFL players by name and position
- **Multi-Player Comparison**: Compare up to 5 players simultaneously
- **Interactive Radar Charts**: Visualize player statistics in an intuitive radar chart format
- **XML Data Processing**: 
  - XML Schema validation using XSD
  - XML data transformation and parsing
  - Client-side XML to JSON conversion
- **RESTful Web Services**:
  - XML-based API responses
  - Position-based player filtering
  - Team-based data retrieval
- **Position-Specific Stats**: Different statistical categories for each position:
  - QB: Passing Yards, Passing TDs, Rushing Yards, Interceptions, Total Points
  - RB: Rushing Yards, Rushing TDs, Receiving Yards, Receptions, Total Points
  - WR/TE: Receiving Yards, Receiving TDs, Receptions, Targets, Total Points
  - K: Field Goals, FG Attempts, Extra Points, XP Attempts, Total Points
  - LB/DL: Tackles, Sacks, Tackles for Loss, Forced Fumbles, Total Points
  - DB: Tackles, Interceptions, Passes Defended, Forced Fumbles, Total Points

## Technology Stack

### Backend
- **Python Flask**: RESTful web service framework
- **XML Processing**:
  - `lxml`: XML schema validation and processing
  - `xml.etree.ElementTree`: XML generation and manipulation
  - Custom XSD schema for data validation
- **API Integration**: Custom NFL Stats API with XML response format

### Frontend
- **HTML5 & CSS3**: Modern, responsive interface
- **JavaScript**:
  - XML parsing using DOMParser
  - Chart.js for data visualization
  - Dynamic DOM manipulation
- **Styling**: Modern CSS with Glass-morphism design
- **Data Visualization**: Interactive radar charts with Chart.js

### Deployment
- **Heroku**: Cloud platform hosting
- **Git**: Version control and deployment

## Web Service Architecture

### XML Data Flow
1. Client sends HTTP request for player data
2. Server retrieves data from NFL Stats API
3. Data is transformed into XML format
4. XML is validated against XSD schema
5. Valid XML is sent to client
6. Client parses XML and updates UI

### API Endpoints
- `/api/players/<position>`: Get players by position (XML response)
- `/api/teams`: Get all teams (JSON response)
- `/api/team/<team_code>/players`: Get team players (JSON response)

### XML Schema
The application uses a custom XSD schema (`player_stats.xsd`) to validate player statistics:
```xml
<xs:schema>
  <xs:element name="players">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="player" maxOccurs="unbounded">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="name" type="xs:string"/>
              <xs:element name="position" type="xs:string"/>
              <xs:element name="team" type="xs:string"/>
              <!-- Position-specific stats elements -->
            </xs:sequence>
            <xs:attribute name="id" type="xs:string"/>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
```

## Design Features

- Responsive design that works on both desktop and mobile devices
- Modern glass-morphism UI with gradient backgrounds
- Interactive elements with smooth animations
- Color-coded player comparisons
- Clean and intuitive user interface

## Live Demo

The application is deployed and can be accessed at: [NFL Stats Visualizer](https://nfl-stats-visualizer-eu-c5e58c1a5426.herokuapp.com/)

## Development

### Prerequisites
- Python 3.8+
- Flask and required packages (see requirements.txt)
- Modern web browser with JavaScript enabled
- Understanding of XML and RESTful web services

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/nfl-stats-visualizer.git
cd nfl-stats-visualizer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Project Structure

```
nfl-stats-visualizer/
├── app.py              # Flask application and XML processing
├── requirements.txt    # Python dependencies
├── static/
│   ├── styles.css     # CSS styles
│   └── player_stats.xsd # XML schema for data validation
├── templates/
│   └── index.html     # Main HTML template with JavaScript
└── README.md          # Project documentation
```

## Error Handling

- XML validation errors are caught and logged
- API connection issues are handled gracefully
- Client-side error messages for failed requests
- Proper HTTP status codes for different scenarios

## Future Enhancements

- Add historical player statistics
- Implement team comparison features
- Add more statistical categories
- Include player photos and additional information
- Add season selection functionality
- Implement caching for XML responses
- Add SOAP web service support
- Enhance XML schema with more validation rules

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 