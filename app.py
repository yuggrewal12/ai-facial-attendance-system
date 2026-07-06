import sys
import os
user_site = r'C:\Users\user\AppData\Roaming\Python\Python314\site-packages'
if user_site not in sys.path:
    sys.path.insert(0, user_site)
import cv2
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
blink_tracker = {}
import sqlite3
import base64
from datetime import datetime
from functools import wraps
import numpy as np
import cv2
import face_recognition
import face_recognition_models
sys.modules['face_recognition_models'] = face_recognition_models
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)
UPLOAD_FOLDER = 'static/profiles/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------------------------------------------
# DATABASE INITIALIZATION
# -------------------------------------------------------------
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            photo_path TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            timestamp TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()
# -------------------------------------------------------------
# FACIAL LOGIC ENGINE
# -------------------------------------------------------------
def load_registered_faces():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, photo_path FROM students")
    rows = cursor.fetchall()
    conn.close()

    known_encodings = []
    known_names = []
    known_ids = []
    print(f"[DEBUG LOG] Found {len(rows)} student records in SQL database.")
    for row in rows:
        student_id, name, photo_path = row
        if os.path.exists(photo_path):
            image = face_recognition.load_image_file(photo_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(name)
                known_ids.append(student_id)
                print(f"[DEBUG LOG] Loaded facial embedding matrix for: {name}")
            else:
                print(f"[DEBUG LOG] WARNING: Could not extract facial features from file: {photo_path}")
        else:
            print(f"[DEBUG LOG] WARNING: Photo file missing on hard drive: {photo_path}")
                
    return known_encodings, known_names, known_ids

GLOBAL_KNOWN_ENCODINGS = []
GLOBAL_KNOWN_NAMES = []
GLOBAL_KNOWN_IDS = []

def update_face_cache():
    """Loads all student profiles into active server RAM."""
    global GLOBAL_KNOWN_ENCODINGS, GLOBAL_KNOWN_NAMES, GLOBAL_KNOWN_IDS
    print("[SYSTEM] Rebuilding facial matrix cache into RAM...")
    GLOBAL_KNOWN_ENCODINGS, GLOBAL_KNOWN_NAMES, GLOBAL_KNOWN_IDS = load_registered_faces()

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == 'admin' and auth.password == 'admin123'):
            return Response(
                'Verification failed.', 401,
                {'WWW-Authenticate': 'Basic realm="Admin Login Required"'}
            )
        return f(*args, **kwargs)
    return decorated

# -------------------------------------------------------------
# SYSTEM PATH ROUTING CONTROLLERS
# -------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register_page')
def register_page():
    return render_template('register.html')
@app.route('/register', methods=['POST'])
def register_student():
    name = request.form.get('name')
    file = request.files.get('image')
    if not name or not file:
        return jsonify({"status": "error", "message": "Missing arguments."}), 400

    filename = f"{name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}.jpg"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        # Load image via OpenCV
        img_bgr = cv2.imread(filepath)
        if img_bgr is None:
            os.remove(filepath)
            return jsonify({"status": "error", "message": "Invalid image format."}), 400
            
        # INSTANT SPEED BOOST: Resize heavy smartphone photos before processing math
        max_dimension = 800
        height, width = img_bgr.shape[:2]
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img_bgr = cv2.resize(img_bgr, (new_width, new_height), interpolation=cv2.INTER_AREA)
            # Overwrite with the downscaled lightweight image
            cv2.imwrite(filepath, img_bgr)

        # Convert image color profile safely for processing
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        # Detect face locations first
        face_locations = face_recognition.face_locations(img_rgb)
        if len(face_locations) == 0:
            os.remove(filepath)
            return jsonify({"status": "error", "message": "No clear face found. Try again."}), 400
            
    except Exception as e:
        if os.path.exists(filepath): os.remove(filepath)
        return jsonify({"status": "error", "message": f"Processing error: {str(e)}"}), 500

    # Save lightweight path details into SQLite Database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO students (name, photo_path) VALUES (?, ?)", (name, filepath))
    conn.commit()
    conn.close()
    update_face_cache()
    return jsonify({"status": "success", "message": "Registered successfully!"})

# -------------------------------------------------------------
# SECURE ADMIN PORTAL WITH PROFILE REMOVAL
# -------------------------------------------------------------
@app.route('/admin_list')
@requires_auth
def admin_list():
    """Renders a password-protected directory of registered profiles with actions."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, photo_path FROM students ORDER BY name ASC")
    students = cursor.fetchall()
    conn.close()
    
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Student Directory</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
<!-- Replace the navbar block inside the admin_list function in app.py -->
<div class="navbar">
    <h1>📋 Master Student Profile Directory</h1>
    <div style="display: flex; gap: 12px;">
        <!-- New Session Lock Button -->
        <button onclick="lockAdminPortal()" class="nav-btn" style="background-color: #ef4444; border:none; cursor:pointer;">🔒 Lock Admin Portal</button>
        <a href="/" class="nav-btn">🔙 Back to Terminal</a>
    </div>
</div>
        <div class="container" style="display:block; max-width:900px; margin:40px auto;">
            <div class="card">
                <h2>Total Profiles Linked: {len(students)}</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Database ID</th>
                            <th>Student Profile Name</th>
                            <th>Internal File Path</th>
                            <th style="text-align:center;">Action</th>
                        </tr>
                    </thead>
                    <tbody>
    '''
    # Locate this section inside the @app.route('/admin_list') function
    # Replace the existing 'for row in students:' loop with this index counter loop:
    
    for index, row in enumerate(students, start=1):
        student_id, name, path = row
        html_content += f'''
        <tr>
            <td>{index}</td> <!-- This displays a clean sequential index: 1, 2, 3... -->
            <td><b>{name}</b></td>
            <td><code>{path}</code> (DB ID: {student_id})</td> <!-- Keeps database reference for transparency -->
            <td style="text-align:center;">
                <button onclick="deleteStudent({student_id})" class="nav-btn" style="background-color: #ef4444; padding: 6px 12px; font-size: 14px; border:none; cursor:pointer;">🗑️ Delete</button>
            </td>
        </tr>
        '''

        
    html_content += '''
                    </tbody>
                </table>
            </div>
        </div>
        <script>
// Add this inside the script tag block in the admin_list HTML inside app.py
function lockAdminPortal() {
    // Making an intentional invalid request tricks the browser into wiping its credentials cache
    fetch('/admin_list', {
        headers: { 'Authorization': 'Basic ' + btoa('logout:wrongpassword') }
    }).then(() => {
        alert("Admin portal session locked successfully!");
        window.location.href = "/"; // Redirects back to the public terminal screen
    });
}
            function deleteStudent(id) {
                if (confirm("Are you sure you want to permanently delete this student profile and file records?")) {
                    fetch('/delete_student/' + id, { method: 'POST' })
                    .then(res => res.json())
                    .then(data => {
                        alert(data.message);
                        if(data.status === 'success') location.reload();
                    });
                }
            }
        </script>
    </body>
    </html>
    '''
    return html_content

@app.route('/delete_student/<int:student_id>', methods=['POST'])
@requires_auth
def delete_student(student_id):
    """Deletes a student profile from SQL database and removes their stored file payload."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 1. Fetch the file path string to clean up server disk space
    cursor.execute("SELECT photo_path FROM students WHERE id = ?", (student_id,))
    row = cursor.fetchone()
    
    if row:
        photo_path = row[0]
        # Delete file safely if it exists on disk
        if os.path.exists(photo_path):
            os.remove(photo_path)
            
        # 2. Clear out cascading records across both SQL tables
        cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        conn.close()
        update_face_cache()
        return jsonify({"status": "success", "message": "Student profile successfully deleted."})
        
    conn.close()
    return jsonify({"status": "error", "message": "Record item reference lookup failed."}), 404

@app.route('/scan', methods=['POST'])
def scan_face():
    data = request.json.get('image')
    if not data: return jsonify({"status": "error"}), 400

    header, encoded = data.split(",", 1)
    data_bytes = base64.b64decode(encoded)
    nparr = np.frombuffer(data_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
# Inside def scan_face():
# Find the lines where known_encodings are loaded and replace them with:

    global GLOBAL_KNOWN_ENCODINGS, GLOBAL_KNOWN_NAMES, GLOBAL_KNOWN_IDS

    if not GLOBAL_KNOWN_ENCODINGS:
        print("[DEBUG LOG] Verification skipped: No encodings in RAM cache.")
        return jsonify({"status": "unknown"})

    for face_encoding, face_location in zip(face_encodings, face_locations):
        # Update these variables to use the GLOBAL lists
        matches = face_recognition.compare_faces(GLOBAL_KNOWN_ENCODINGS, face_encoding, tolerance=0.7)
        face_distances = face_recognition.face_distance(GLOBAL_KNOWN_ENCODINGS, face_encoding)
        
        if True in matches:
            best_match_idx = np.argmin(face_distances)
            student_id = GLOBAL_KNOWN_IDS[best_match_idx]
            student_name = GLOBAL_KNOWN_NAMES[best_match_idx]
            # ... rest of the logic remains exactly the same
            print(f"[DEBUG LOG] MATCH CONFIRMED: Found student {student_name} (ID: {student_id})")

            # -------------------------------------------------------------
            # ADVANCED PHOTO/SCREEN REJECTION (LAPLACIAN VARIANCE)
            # -------------------------------------------------------------
            top, right, bottom, left = face_location
            roi_bgr = frame[top:bottom, left:right]
            
            # Convert facial region to gray for structural sharpness analysis
            roi_gray_analysis = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
            
            # Calculate the Laplacian variance (Measures the edge sharpness of the face)
            # Real faces are sharp and crisp. Phone screen photos are slightly blurred or flat.
            laplacian_var = cv2.Laplacian(roi_gray_analysis, cv2.CV_64F).var()
            print(f"[DEBUG LOG] Sharpness Analysis Value for {student_name}: {laplacian_var}")

            # SECURITY THRESHOLD RULE:
            # If the sharpness value falls below 120, it means it is a flat, re-photographed screen image
            if laplacian_var < 120.0:
                print(f"[SECURITY ALERT] SPOOF ATTEMPT CAUGHT FOR {student_name}! REJECTED.")
                return jsonify({"status": "spoof_warning", "name": student_name})

            # -------------------------------------------------------------
            # DATA COMMIT & ALERT DISPATCH
            # -------------------------------------------------------------
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            current_date = datetime.now().strftime('%Y-%m-%d')           
          
            # Check if this student already has a log entry for TODAY
            cursor.execute("SELECT id FROM attendance WHERE student_id = ? AND timestamp LIKE ?", (student_id, f"{current_date}%"))           
            already_checked_in = cursor.fetchone()

            if already_checked_in:
                conn.close()
                print(f"[DEBUG LOG] Student {student_name} already has a record log entries for today.")
                # Changed status flag to 'already_logged' for frontend isolation
                return jsonify({"status": "already_logged", "name": student_name})


            # If no entry exists for today, insert a fresh attendance log row
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO attendance (student_id, timestamp) VALUES (?, ?)", (student_id, current_time))
            conn.commit()
            conn.close()

            print(f"[DEBUG LOG] ATTENDANCE SUCCESSFULLY LOGGED: {student_name} committed to SQL.")
            return jsonify({"status": "success", "name": student_name})

    return jsonify({"status": "unknown"})


@app.route('/logs', methods=['GET'])
def get_logs():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT students.name, attendance.timestamp FROM attendance 
        JOIN students ON attendance.student_id = students.id ORDER BY attendance.id DESC
    ''')
    logs = cursor.fetchall()
    conn.close()
    return jsonify([{"name": row[0], "timestamp": row[1]} for row in logs])

import csv
from io import StringIO
@app.route('/export_csv')
def export_csv():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT students.name, attendance.timestamp FROM attendance JOIN students ON attendance.student_id = students.id')
    rows = cursor.fetchall()
    conn.close()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Student Name', 'Timestamp'])
    cw.writerows(rows)
    return Response(si.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=logs.csv'})
# Add this code block inside app.py
@app.route('/clear_logs', methods=['POST'])
@requires_auth
def clear_logs():
    """Wipes all rows inside the attendance ledger while preserving registered student profiles."""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Delete all records from the attendance table
        cursor.execute("DELETE FROM attendance")
        
        # Reset the autoincrement counter for attendance table only
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='attendance'")
        
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "All attendance logs cleared successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Database error: {str(e)}"}), 500

if __name__ == '__main__':
    init_db()
    update_face_cache()
    app.run(debug=True, port=5000, threaded=True)
