# OpenStreetMap Multi-User Collaborative Platform

An interactive web-based mapping platform that allows multiple users to collaborate on creating, managing, and exporting geographic markers.

## Features

- **User Authentication**
  - User registration and login
  - Session management
  - Role-based access control

- **Interactive Map**
  - OpenStreetMap base layer
  - Satellite imagery overlay
  - Opacity control for map layers
  - Geocoder for location search

- **Marker Management**
  - Create markers with custom attributes
  - 4 marker colors (red, blue, green, yellow)
  - Add/edit marker name and description
  - Delete personal markers

- **Export Capabilities**
  - Export markers in multiple formats:
    - JSON
    - GPX (compatible with GPS devices)
    - CSV (latitude/longitude coordinates)
  - Bulk export functionality
  - Marker selection mode

## Technical Stack

- **Backend**
  - Python Flask
  - Flask-SQLAlchemy
  - Flask-Login
  - SQLite database

- **Frontend**
  - JavaScript
  - Leaflet.js
  - Bootstrap 5
  - OpenStreetMap tiles
  - ArcGIS satellite imagery

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/osm-multiuser.git
cd osm-multiuser
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Access the application at `http://localhost:5000`

## Usage

1. Register a new account or login
2. Use the map controls to:
   - Add markers
   - Change marker colors
   - Edit marker information
   - Delete markers
3. Export your markers in various formats

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
