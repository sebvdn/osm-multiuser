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
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///map.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

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
def index():
    return render_template('index.html')

@app.route('/api/markers', methods=['GET'])
def get_markers():
    markers = Marker.query.all()
    return jsonify([{
        'id': marker.id,
        'lat': marker.lat,
        'lon': marker.lon,
        'name': marker.name,
        'description': marker.description,
        'color': marker.color,
        'user': marker.user.username
    } for marker in markers])

@app.route('/api/markers', methods=['POST'])
@login_required
def add_marker():
    data = request.json
    new_marker = Marker(
        lat=data['lat'],
        lon=data['lon'],
        name=data['name'],
        description=data.get('description', ''),
        color=data['color'],
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
        'color': new_marker.color,
        'user': current_user.username
    })

@app.route('/api/markers/<int:marker_id>', methods=['PUT'])
@login_required
def update_marker(marker_id):
    marker = Marker.query.get_or_404(marker_id)
    if marker.user_id != current_user.id:
        return jsonify({'error': 'Non autorisé'}), 403
    
    data = request.json
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
        'color': marker.color,
        'user': current_user.username
    })

@app.route('/api/markers/<int:marker_id>', methods=['DELETE'])
@login_required
def delete_marker(marker_id):
    marker = Marker.query.get_or_404(marker_id)
    if marker.user_id != current_user.id:
        return jsonify({'error': 'Non autorisé'}), 403
    
    db.session.delete(marker)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/export', methods=['POST'])
@login_required
def export_markers():
    data = request.json
    marker_ids = data.get('markers', [])
    format_type = data.get('format', 'json')
    
    if not marker_ids:
        return jsonify({'error': 'No markers selected'}), 400
        
    markers = Marker.query.filter(Marker.id.in_(marker_ids)).all()
    
    if format_type == 'json':
        output = [{
            'name': m.name,
            'description': m.description,
            'latitude': m.lat,
            'longitude': m.lon,
            'color': m.color
        } for m in markers]
        return jsonify(output)
        
    elif format_type == 'csv':
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Name', 'Description', 'Latitude', 'Longitude', 'Color'])
        
        for m in markers:
            writer.writerow([
                m.name,
                m.description,
                m.lat,
                m.lon,
                m.color
            ])
            
        output.seek(0)
        return send_file(
            BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name='markers.csv'
        )
        
    elif format_type == 'gpx':
        gpx = gpxpy.gpx.GPX()
        
        for m in markers:
            point = gpxpy.gpx.GPXWaypoint(
                latitude=m.lat,
                longitude=m.lon,
                name=m.name,
                description=m.description
            )
            gpx.waypoints.append(point)
            
        return send_file(
            BytesIO(gpx.to_xml().encode()),
            mimetype='application/gpx+xml',
            as_attachment=True,
            download_name='markers.gpx'
        )
        
    return jsonify({'error': 'Unsupported format'}), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Identifiants invalides')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Nom d\'utilisateur déjà pris')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('index'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
