from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from werkzeug.security import generate_password_hash, check_password_hash
import json
import csv
import gpxpy
import gpxpy.gpx
from io import StringIO, BytesIO

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))

# Configuration de la base de données
if os.environ.get('DATABASE_URL'):
    # Pour Render.com
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
else:
    # Pour le développement local
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///map.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Création des tables au démarrage
with app.app_context():
    db.create_all()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    markers = db.relationship('Marker', backref='user', lazy=True)

class Marker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    color = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/api/markers', methods=['GET'])
@login_required
def get_markers():
    markers = Marker.query.filter_by(user_id=current_user.id).all()
    markers_list = []
    for marker in markers:
        markers_list.append({
            'id': marker.id,
            'lat': marker.lat,
            'lon': marker.lon,
            'name': marker.name,
            'description': marker.description,
            'color': marker.color
        })
    return jsonify(markers_list)

@app.route('/api/markers', methods=['POST'])
@login_required
def add_marker():
    data = request.get_json()
    new_marker = Marker(
        lat=data['lat'],
        lon=data['lon'],
        name=data['name'],
        description=data.get('description', ''),
        color=data.get('color', 'red'),
        user_id=current_user.id
    )
    db.session.add(new_marker)
    db.session.commit()
    return jsonify({
        'id': new_marker.id,
        'lat': new_marker.lat,
        'lon': new_marker.lon,
        'name': new_marker.name,
        'description': new_marker.description,
        'color': new_marker.color
    })

@app.route('/api/markers/<int:marker_id>', methods=['PUT'])
@login_required
def update_marker(marker_id):
    marker = Marker.query.get_or_404(marker_id)
    if marker.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    marker.lat = data.get('lat', marker.lat)
    marker.lon = data.get('lon', marker.lon)
    marker.name = data.get('name', marker.name)
    marker.description = data.get('description', marker.description)
    marker.color = data.get('color', marker.color)
    
    db.session.commit()
    return jsonify({
        'id': marker.id,
        'lat': marker.lat,
        'lon': marker.lon,
        'name': marker.name,
        'description': marker.description,
        'color': marker.color
    })

@app.route('/api/markers/<int:marker_id>', methods=['DELETE'])
@login_required
def delete_marker(marker_id):
    marker = Marker.query.get_or_404(marker_id)
    if marker.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(marker)
    db.session.commit()
    return '', 204

@app.route('/api/export', methods=['POST'])
@login_required
def export_markers():
    data = request.get_json()
    format_type = data.get('format', 'json')
    marker_ids = data.get('markers', [])
    
    if marker_ids:
        markers = Marker.query.filter(Marker.id.in_(marker_ids), Marker.user_id == current_user.id).all()
    else:
        markers = Marker.query.filter_by(user_id=current_user.id).all()

    if format_type == 'json':
        markers_list = [{
            'lat': marker.lat,
            'lon': marker.lon,
            'name': marker.name,
            'description': marker.description,
            'color': marker.color
        } for marker in markers]
        
        return jsonify(markers_list)
    
    elif format_type == 'csv':
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Latitude', 'Longitude', 'Name', 'Description', 'Color'])
        
        for marker in markers:
            writer.writerow([marker.lat, marker.lon, marker.name, marker.description, marker.color])
        
        output.seek(0)
        return send_file(
            BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='markers.csv'
        )
    
    elif format_type == 'gpx':
        gpx = gpxpy.gpx.GPX()
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(gpx_track)
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        
        for marker in markers:
            point = gpxpy.gpx.GPXTrackPoint(marker.lat, marker.lon, name=marker.name)
            gpx_segment.points.append(point)
        
        return send_file(
            BytesIO(gpx.to_xml().encode('utf-8')),
            mimetype='application/gpx+xml',
            as_attachment=True,
            download_name='markers.gpx'
        )
    
    return jsonify({'error': 'Invalid format'}), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
