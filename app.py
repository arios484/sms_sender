from flask import Flask, render_template, request, jsonify, session, send_file
from werkzeug.utils import secure_filename
import csv
import os
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Create results directory if it doesn't exist
os.makedirs('results', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_results_csv(phone_numbers, statuses):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_filename = f'results/results_{timestamp}.csv'
    
    with open(results_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['phone_number', 'status'])  # Header row
        for number, status in zip(phone_numbers, statuses):
            writer.writerow([number, status])
    
    return results_filename

@app.route('/')
def index():
    # Load saved message if it exists
    message = ''
    if os.path.exists('saved_message.json'):
        with open('saved_message.json', 'r') as f:
            data = json.load(f)
            message = data.get('message', '')
    return render_template('index.html', saved_message=message)

@app.route('/save_message', methods=['POST'])
def save_message():
    message = request.json.get('message', '')
    with open('saved_message.json', 'w') as f:
        json.dump({'message': message}, f)
    return jsonify({'success': True})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
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
        session['statuses'] = ['pending'] * len(phone_numbers)  # Initialize status list
        session['current_index'] = 0
        session['total_numbers'] = len(phone_numbers)
        
        return jsonify({
            'success': True,
            'total': len(phone_numbers),
            'current_number': phone_numbers[0] if phone_numbers else None
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/next', methods=['POST'])
def next_number():
    if 'phone_numbers' not in session:
        return jsonify({'error': 'No phone numbers loaded'}), 400
    
    action = request.json.get('action', 'send')  # 'send' or 'skip'
    message = request.json.get('message', '')  # Get the current message
    current_index = session.get('current_index', 0)
    phone_numbers = session['phone_numbers']
    statuses = session['statuses']
    
    # Update status for current number based on action
    if action == 'send':
        statuses[current_index] = 'sent'
        log_action(phone_numbers[current_index], 'sent', message)
    else:
        statuses[current_index] = 'skipped'
        log_action(phone_numbers[current_index], 'skipped', message)
    
    session['statuses'] = statuses  # Update session with new statuses
    
    # Move to next number
    current_index += 1
    session['current_index'] = current_index
    
    # Check if we've reached the end
    if current_index >= len(phone_numbers):
        # Create results CSV when finished with actual statuses
        results_file = create_results_csv(phone_numbers, statuses)
        return jsonify({
            'complete': True,
            'progress': 100,
            'results_file': results_file
        })
    
    # Calculate progress
    progress = (current_index / len(phone_numbers)) * 100
    
    return jsonify({
        'number': phone_numbers[current_index],
        'progress': progress,
        'remaining': len(phone_numbers) - current_index
    })

@app.route('/download_results/<path:filename>')
def download_results(filename):
    return send_file(filename, as_attachment=True)

def log_action(phone_number, action, message):
    with open('activity_log.csv', 'a', newline='') as logfile:
        writer = csv.writer(logfile)
        writer.writerow([datetime.now(), phone_number, action, message])

# [Rest of the HTML template code remains the same as before]

if __name__ == '__main__':
    app.run(debug=True)