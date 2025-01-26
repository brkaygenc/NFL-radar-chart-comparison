# NFL Stats Visualizer

A modern web application for visualizing and comparing NFL player statistics using interactive radar charts. Compare your favorite NFL players side by side with an intuitive and beautiful interface.

 [Live Demo](https://nfl-stats-visualizer-eu-c5e58c1a5426.herokuapp.com/)

![NFL Stats Visualizer Demo](static/demo.png)

## Features

- **Player Search**: 
  - Quick search for NFL players by name
  - Filter by position (QB, RB, WR, TE, K, DEF, LB, DB, DL)
  - Real-time search results
  
- **Multi-Player Comparison**: 
  - Compare up to 5 players simultaneously
  - Each player represented by a unique color
  - Easy-to-read overlapping radar charts

- **Interactive Visualization**:
  - Dynamic radar charts using Chart.js
  - Hover over data points for exact values
  - Smooth animations when updating data
  - Position-specific statistical categories

- **Position-Specific Stats**: 
  - QB: Passing Yards, Passing TDs, Rushing Yards, Interceptions, Total Points
  - RB: Rushing Yards, Rushing TDs, Receiving Yards, Receptions, Total Points
  - WR/TE: Receiving Yards, Receiving TDs, Receptions, Targets, Total Points
  - K: Field Goals, FG Attempts, Extra Points, XP Attempts, Total Points
  - LB/DL: Tackles, Sacks, Tackles for Loss, Forced Fumbles, Total Points
  - DB: Tackles, Interceptions, Passes Defended, Forced Fumbles, Total Points

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/nfl-stats-visualizer.git
   cd nfl-stats-visualizer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Visit the application**
   ```
   http://localhost:5000
   ```

## Technology Stack

### Backend
- **Python Flask**: RESTful web service framework
- **XML Processing**: 
  - `lxml` for schema validation
  - `xml.etree.ElementTree` for XML handling
- **API Integration**: Custom NFL Stats API

### Frontend
- **HTML5 & CSS3**: Modern, responsive interface
- **JavaScript**: 
  - Dynamic DOM manipulation
  - Chart.js for radar charts
- **Design**: Glass-morphism UI with modern aesthetics

### Deployment
- **Heroku**: Cloud hosting platform
- **Git**: Version control and deployment

## Usage Examples

1. **Search for Players**
   - Enter player name in the search box
   - Select position from dropdown (optional)
   - Click "Search" or press Enter

2. **Compare Players**
   - Click "Add to Compare" for each player
   - View the radar chart update in real-time
   - Remove players using the "×" button in their tag

3. **View Statistics**
   - Hover over chart points for exact values
   - Compare multiple players' stats simultaneously
   - Stats automatically adjust based on position

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Future Enhancements

- [ ] Add historical player statistics
- [ ] Implement team comparison features
- [ ] Add more statistical categories
- [ ] Include player photos and additional information
- [ ] Add season selection functionality
- [ ] Implement data export functionality
- [ ] Add player career progression visualization

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- NFL Stats API for providing the data
- Chart.js for the visualization library
- Flask community for the excellent web framework
- All contributors who have helped improve this project

## Contact

Berkay Genc - [@brkaygenc](https://github.com/brkaygenc)

Project Link: [https://github.com/brkaygenc/NFL-radar-chart-comparison](https://github.com/brkaygenc/NFL-radar-chart-comparison)

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