from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import csv
import os
from datetime import datetime
import json
<<<<<<< HEAD

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Load saved message if it exists
    message = ''
    if os.path.exists('saved_message.json'):
        with open('saved_message.json', 'r') as f:
            data = json.load(f)
            message = data.get('message', '')
=======
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
>>>>>>> 98fa4bca30b85932b8f33f40e5c86e021cc67b98
    return render_template('index.html', saved_message=message)

@app.route('/save_message', methods=['POST'])
def save_message():
    message = request.json.get('message', '')
<<<<<<< HEAD
    with open('saved_message.json', 'w') as f:
        json.dump({'message': message}, f)
=======
    saved_message = SavedMessage.query.first()
    
    if saved_message:
        saved_message.message = message
    else:
        saved_message = SavedMessage(message=message)
        db.session.add(saved_message)
    
    db.session.commit()
>>>>>>> 98fa4bca30b85932b8f33f40e5c86e021cc67b98
    return jsonify({'success': True})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
<<<<<<< HEAD
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read phone numbers from CSV
        phone_numbers = []
        with open(filepath, 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader, None)  # Skip header row
            for row in csv_reader:
                if row and row[0].strip():  # Check if row exists and has data
                    phone_numbers.append(row[0].strip())
        
        # Store in session
        session['phone_numbers'] = phone_numbers
=======
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
>>>>>>> 98fa4bca30b85932b8f33f40e5c86e021cc67b98
        session['current_index'] = 0
        session['total_numbers'] = len(phone_numbers)
        
        return jsonify({
            'success': True,
            'total': len(phone_numbers),
<<<<<<< HEAD
            'current_number': phone_numbers[0] if phone_numbers else None
=======
            'current_number': phone_numbers[0].number if phone_numbers else None
>>>>>>> 98fa4bca30b85932b8f33f40e5c86e021cc67b98
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/next', methods=['POST'])
def next_number():
<<<<<<< HEAD
    if 'phone_numbers' not in session:
        return jsonify({'error': 'No phone numbers loaded'}), 400
    
    action = request.json.get('action', 'send')  # 'send' or 'skip'
    message = request.json.get('message', '')  # Get the current message
    current_index = session.get('current_index', 0)
    phone_numbers = session['phone_numbers']
    
    # Log the action with the message
    if action == 'send':
        log_action(phone_numbers[current_index], 'sent', message)
    else:
        log_action(phone_numbers[current_index], 'skipped', message)
    
    # Move to next number
    current_index += 1
    session['current_index'] = current_index
    
    # Check if we've reached the end
=======
    if 'upload_id' not in session:
        return jsonify({'error': 'No phone numbers loaded'}), 400
    
    action = request.json.get('action', 'send')  # 'send' or 'skip'
    message = request.json.get('message', '')
    current_index = session.get('current_index', 0)
    
    # Get current phone number
    phone_numbers = PhoneNumber.query.filter_by(
        upload_id=session['upload_id']
    ).order_by(PhoneNumber.id).all()
    
>>>>>>> 98fa4bca30b85932b8f33f40e5c86e021cc67b98
    if current_index >= len(phone_numbers):
        return jsonify({
            'complete': True,
            'progress': 100
        })
    
<<<<<<< HEAD
=======
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
    
>>>>>>> 98fa4bca30b85932b8f33f40e5c86e021cc67b98
    # Calculate progress
    progress = (current_index / len(phone_numbers)) * 100
    
    return jsonify({
<<<<<<< HEAD
        'number': phone_numbers[current_index],
=======
        'number': phone_numbers[current_index].number if current_index < len(phone_numbers) else None,
>>>>>>> 98fa4bca30b85932b8f33f40e5c86e021cc67b98
        'progress': progress,
        'remaining': len(phone_numbers) - current_index
    })

<<<<<<< HEAD
def log_action(phone_number, action, message):
    with open('activity_log.csv', 'a', newline='') as logfile:
        writer = csv.writer(logfile)
        writer.writerow([datetime.now(), phone_number, action, message])

# Create the templates directory and index.html
os.makedirs('templates', exist_ok=True)
with open('templates/index.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>SMS Sender</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .container { max-width: 800px; margin-top: 50px; }
        #progressBar { margin: 20px 0; }
        #actionButtons { margin-top: 20px; }
        #messageArea { margin: 20px 0; }
        .autosave-status {
            color: #6c757d;
            font-size: 0.8em;
            margin-top: 5px;
        }
        .navbar {
            background-color: #1a73e8;
            padding: 1rem;
        }
        .navbar-brand {
            color: white !important;
            font-size: 1.5rem;
            font-weight: 500;
        }
        .progress {
            height: 0.5rem;
        }
        .card {
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .btn {
            padding: 0.5rem 2rem;
            font-weight: 500;
        }
        .form-control:focus {
            border-color: #1a73e8;
            box-shadow: 0 0 0 0.2rem rgba(26,115,232,0.25);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark">
        <div class="container">
            <span class="navbar-brand">SMS Sender</span>
        </div>
    </nav>

    <div class="container">
        <!-- Message Template -->
        <div id="messageArea" class="mb-4">
            <label for="messageTemplate" class="form-label">Message Template</label>
            <textarea class="form-control" id="messageTemplate" rows="4" placeholder="Type your SMS message here...">{{ saved_message }}</textarea>
            <div class="autosave-status" id="autosaveStatus"></div>
        </div>

        <!-- File Upload -->
        <div id="uploadSection">
            <div class="mb-3">
                <label for="csvFile" class="form-label">Upload Phone Numbers (CSV)</label>
                <input class="form-control" type="file" id="csvFile" accept=".csv">
            </div>
            <button class="btn btn-primary" onclick="uploadFile()">Upload List</button>
        </div>

        <!-- Progress Section -->
        <div id="progressSection" style="display: none;">
            <div class="progress" id="progressBar">
                <div class="progress-bar bg-primary" role="progressbar" style="width: 0%"></div>
            </div>
            
            <div class="card mt-4">
                <div class="card-body">
                    <h5 class="card-title">Current Number:</h5>
                    <p class="card-text" id="currentNumber"></p>
                </div>
            </div>

            <div id="actionButtons">
                <button class="btn btn-success me-2" onclick="processNumber('send')">Send SMS</button>
                <button class="btn btn-secondary" onclick="processNumber('skip')">Skip</button>
            </div>
        </div>
    </div>

    <script>
        let saveTimeout;
        const messageTemplate = document.getElementById('messageTemplate');
        const autosaveStatus = document.getElementById('autosaveStatus');

        // Save message with debouncing
        messageTemplate.addEventListener('input', () => {
            clearTimeout(saveTimeout);
            autosaveStatus.textContent = 'Saving...';
            
            saveTimeout = setTimeout(async () => {
                try {
                    const response = await fetch('/save_message', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ message: messageTemplate.value })
                    });
                    
                    if (response.ok) {
                        autosaveStatus.textContent = 'Saved';
                        setTimeout(() => {
                            autosaveStatus.textContent = '';
                        }, 2000);
                    }
                } catch (error) {
                    console.error('Error saving message:', error);
                    autosaveStatus.textContent = 'Error saving';
                }
            }, 1000);
        });

        async function uploadFile() {
            const fileInput = document.getElementById('csvFile');
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('uploadSection').style.display = 'none';
                    document.getElementById('progressSection').style.display = 'block';
                    document.getElementById('currentNumber').textContent = data.current_number;
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Upload failed');
            }
        }

        async function processNumber(action) {
            try {
                const response = await fetch('/next', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        action: action,
                        message: messageTemplate.value 
                    })
                });
                const data = await response.json();
                
                if (data.complete) {
                    alert('All messages processed!');
                    window.location.reload();
                    return;
                }
                
                document.getElementById('currentNumber').textContent = data.number;
                document.querySelector('.progress-bar').style.width = data.progress + '%';
            } catch (error) {
                console.error('Error:', error);
                alert('Operation failed');
            }
        }
    </script>
</body>
</html>
''')

if __name__ == '__main__':
    app.run(debug=True)
=======
# Initialize database
init_db()

if __name__ == '__main__':
    app.run(debug=True)

>>>>>>> 98fa4bca30b85932b8f33f40e5c86e021cc67b98
