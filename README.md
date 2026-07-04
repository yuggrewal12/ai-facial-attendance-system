## Documentation
# 🎓 AI-Powered Facial Recognition Attendance System
A contactless, automated biometric attendance tracking system built with Python, Flask, and OpenCV. This project eliminates manual roll calls and prevents proxy attendance by utilizing real-time deep learning facial encodings. It features an integrated liveness detection module (anti-spoofing) to reject fraudulent check-in attempts using photographs or digital screens.

# ✨ Key Features
1. Real-Time Verification: Instantly identifies registered students via a live webcam feed.

2. Anti-Spoofing Security: Calculates Laplacian variance to detect image sharpness, actively blocking flat 2D images or smartphone screens from tricking the scanner.

3. High-Performance RAM Caching: Loads facial embedding matrices directly into active memory on server startup, resulting in zero-latency matching.

4. Duplicate Prevention: Automatically isolates and flags duplicate check-ins for the same day.

5. Secure Admin Dashboard: A protected portal to register high-res student vectors, manage database profiles, and clear terminal history.

6. CSV Ledger Export: Download today's attendance logs directly into an Excel-ready CSV sheet.

7. Responsive UI: A clean, dark-mode terminal interface with interactive loading spinners and smart success-throttling.

# 🛠️ Tech Stack
Backend: Python, Flask

Database: SQLite (Built-in)

Computer Vision & AI: OpenCV (cv2), face_recognition, NumPy

Frontend: HTML5, CSS3, Vanilla JavaScript

# 📁 Project Structure
```bash
Plaintext
├── app.py                 # Core Flask server and facial logic engine
├── database.db            # SQLite database (auto-generates on first run)
├── static/
│   ├── css/
│   │   └── style.css      # Dark-mode dashboard styling and animations
│   └── profiles/          # Secure directory for downscaled student reference photos
└── templates/
    ├── index.html         # Live camera scanner and dynamic log table
    ├── register.html      # Secure onboarding portal for new biometric vectors
    └── admin_list.html    # Internal directory to view/delete records (generated in app.py)
```
#🚀 Installation & Setup
1. Clone the repository:
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```
2. Install required dependencies:

Make sure you have Python installed. Then, install the required libraries:
```bash
pip install flask opencv-python face-recognition numpy
```
(Note: face-recognition requires dlib and CMake to be installed on your system).

3. Run the application:
```bash
python app.py 
```
4. Access the Terminal:

Open your web browser and navigate to:
http://localhost:5000

# 💻 How to Use
1. Register a Student: Click "Register Student Profile" on the dashboard. Enter a name, upload a clear portrait photo, and click compile. The server will compress the image and extract the facial vector.

2. Scan Face: Return to the live dashboard. Look into the webcam. The system will detect your face, verify liveness, log the timestamp, and display a green success badge!

3. Admin Controls: Click "View Registered Students".

Default Credentials: Username: admin | Password: admin123 (Be sure to change this in app.py for production!)

# 🔮 Future Enhancements
1. SMS/Email notifications for daily absentees.

2. Cloud-based database synchronization.

3. Detailed graphical analytics for university administration.

4. Created as an academic mini-project.

Created as an academic mini-project.
