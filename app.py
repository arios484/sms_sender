from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import csv
import os
from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sms_sender.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class PhoneNumber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), nullable=False)
    upload_id = db.Column(db.Integer, db.ForeignKey('upload.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, sent, skipped
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    phone_numbers = db.relationship('PhoneNumber', backref='upload', lazy=True)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SavedMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    with app.app_context():
        db.create_all()

@app.route('/')
def index():
    # Load saved message from database
    saved_message = SavedMessage.query.first()
    message = saved_message.message if saved_message else ''
    return render_template('index.html', saved_message=message)

@app.route('/save_message', methods=['POST'])
def save_message():
    message = request.json.get('message', '')
    saved_message = SavedMessage.query.first()
    
    if saved_message:
        saved_message.message = message
    else:
        saved_message = SavedMessage(message=message)
        db.session.add(saved_message)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.csv'):
        # Create new upload record
        upload = Upload(filename=secure_filename(file.filename))
        db.session.add(upload)
        db.session.commit()
        
        # Read phone numbers from CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"))
        csv_reader = csv.reader(stream)
        next(csv_reader, None)  # Skip header row
        
        phone_numbers = []
        for row in csv_reader:
            if row and row[0].strip():
                phone_number = PhoneNumber(
                    number=row[0].strip(),
                    upload_id=upload.id
                )
                db.session.add(phone_number)
                phone_numbers.append(phone_number)
        
        db.session.commit()
        
        # Store upload ID in session
        session['upload_id'] = upload.id
        session['current_index'] = 0
        session['total_numbers'] = len(phone_numbers)
        
        return jsonify({
            'success': True,
            'total': len(phone_numbers),
            'current_number': phone_numbers[0].number if phone_numbers else None
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/next', methods=['POST'])
def next_number():
    if 'upload_id' not in session:
        return jsonify({'error': 'No phone numbers loaded'}), 400
    
    action = request.json.get('action', 'send')  # 'send' or 'skip'
    message = request.json.get('message', '')
    current_index = session.get('current_index', 0)
    
    # Get current phone number
    phone_numbers = PhoneNumber.query.filter_by(
        upload_id=session['upload_id']
    ).order_by(PhoneNumber.id).all()
    
    if current_index >= len(phone_numbers):
        return jsonify({
            'complete': True,
            'progress': 100
        })
    
    current_number = phone_numbers[current_index]
    
    # Update phone number status and log action
    current_number.status = 'sent' if action == 'send' else 'skipped'
    log_entry = ActivityLog(
        phone_number=current_number.number,
        action=action,
        message=message
    )
    db.session.add(log_entry)
    db.session.commit()
    
    # Move to next number
    current_index += 1
    session['current_index'] = current_index
    
    # Calculate progress
    progress = (current_index / len(phone_numbers)) * 100
    
    return jsonify({
        'number': phone_numbers[current_index].number if current_index < len(phone_numbers) else None,
        'progress': progress,
        'remaining': len(phone_numbers) - current_index
    })

# Initialize database
init_db()

if __name__ == '__main__':
    app.run(debug=True)

