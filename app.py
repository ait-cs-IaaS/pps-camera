from flask import Flask, render_template, Response, redirect, url_for, request ,jsonify,abort
from flask_socketio import SocketIO, emit
import cv2
import datetime
import time
import os
import json
import eventlet
import threading
import random
from threading import Thread

eventlet.monkey_patch()

# Initialize Flask app
app = Flask(__name__)
app.config['SERVER_NAME'] = '127.0.0.1:5001'
app.config['PREFERRED_URL_SCHEME'] = 'http'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', max_http_buffer_size=1000000)


def load_employee_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as config_file:
            config_data = json.load(config_file)
            return config_data.get("employees", [])
    except Exception as e:
        print(f"[ERROR] Failed to load employee configuration: {e}")
        return []

# Load employees from the configuration
employees = load_employee_config()
#vars

mp4_files = [
    "vid/door.mp4",
    "vid/max.mp4",
    "vid/klaus.mp4",
    "vid/stefania.mp4",
    "vid/breach.mp4",
    "vid/ghaith.mp4",
    "vid/gregor.mp4",
    "vid/irene.mp4",
    "vid/lenhard.mp4",
    "vid/mario.mp4",
    "vid/martin.mp4",
    "vid/michael.mp4",
    "vid/oliver.mp4",
    "vid/peter.mp4",
    "vid/petra.mp4",
    "vid/anna.mp4",
    "vid/tobi.mp4"
]

mp4_files_out = [
    
    "vid_out/door.mp4",
    "vid_out/max.mp4",
    "vid_out/klaus.mp4",
    "vid_out/stefania.mp4",
    "vid_out/breach.mp4",
    "vid_out/ghaith.mp4",
    "vid_out/gregor.mp4",
    "vid_out/irene.mp4",
    "vid_out/lenhard.mp4",
    "vid_out/mario.mp4",
    "vid_out/martin.mp4",
    "vid_out/michael.mp4",
    "vid_out/oliver.mp4",
    "vid_out/peter.mp4",
    "vid_out/petra.mp4",
    "vid_out/anna.mp4",
    "vid_out/tobi.mp4"
]
# vid_out_folder = 'vid_out'
# mp4_files_out = [os.path.join(vid_out_folder, file) 
#                  for file in os.listdir(vid_out_folder) 
#                  if file.endswith('.mp4')]

current_employee_name = "Unknown"
current_mp4 = mp4_files[0]
open_sesame = False
counter = 0
camera_freeze = False
last_frame = None
breach_mode = False
default_vid = "vid/door.mp4"
tmp_vid = None
lock = threading.Lock()
delay_seconds = 10


# Generate videos frames
def generate_frames():
    global tmp_vid

    while True:
        # Determine the video source
        with lock:
            video_source = tmp_vid if tmp_vid else default_vid

        cap = cv2.VideoCapture(video_source)

        print(f"Playing video: { video_source }")
        if video_source != default_vid:
            # manual_switch_sequence("image_filename", "test")
            print("Change back to play default loop")
            tmp_vid = None

        while True:
            success, frame = cap.read()

            if not success:
                break

            # Add timestamp to the frame
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(
                frame,
                timestamp,
                (10, 30),
                cv2.FONT_HERSHEY_COMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

            # Encode the frame in JPEG format
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame = buffer.tobytes()

            # Stream the frame as an HTTP multipart response
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            time.sleep(0.01)

        cap.release()

# Function to find employee video path by their first name
def find_video_by_name(name):
    for video_path in mp4_files:
        if name in video_path:
            return video_path
    return None

# Function to find employee video_out path by their first name
def find_video_by_name_out(name):
    for video_path in mp4_files_out:
        if name in video_path:
            return video_path
    return None

# Function to find employee details by their first name
def find_employee_by_first_name(first_name):
    for employee in employees:
        if employee["name"].lower().startswith(first_name.lower()):
            return employee
    return None

# Route to handle API calls using the first name in the URL
@app.route('/manual_switch/<name>', methods=['GET'])
def manual_switch_by_name(name):
    # Find the employee using the first name
    employee = find_employee_by_first_name(name)
    
    if employee:
        # Find the corresponding video path using the video name from the employee data
        video_path = find_video_by_name(employee['video'])

        if video_path:
            return handle_manual_switch(
                employee["id"],
                employee["picture"],
                "Access Granted - Log In",
                video_path
            )
        else:
            return abort(404, description="Video not found for the provided employee.")
    else:
        return abort(404, description="Employee not found.")
    

# Route to handle API calls using the first name in the URL for video out      
@app.route('/manual_switch_out/<name>', methods=['GET'])
def manual_switch_by_name_out(name):
    # Find the employee using the first name
    employee = find_employee_by_first_name(name)
    
    if employee:
        # Find the corresponding video path using the video name from the employee data
        video_path = find_video_by_name_out(employee['video'])

        if video_path:
            return handle_manual_switch_out(
                employee["id"],
                employee["picture"],
                "Log Out",
                video_path
            )
        else:
            return abort(404, description="Video not found for the provided employee.")
    else:
        return abort(404, description="Employee not found.")

# Main route to render HTML
@app.route('/')
def index():
    return render_template('index.html')  # Render the main HTML page

# Video Feed Route
@app.route("/feed")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

# Freeze Camera Route
@app.route("/frz")
def toggle_freeze():
    global camera_freeze
    camera_freeze = not camera_freeze
    return "Camera Frozen" if camera_freeze else "Camera Un-Frozen"

def handle_manual_switch(employee_id, image_filename, message, video_path,):
    global tmp_vid

    # Fetch employee name from the loaded employee list
    employee = next((emp for emp in employees if emp["id"] == employee_id), None)
    employee_name = employee["name"] if employee else "Unknown"

    # Step 1: Emit access logs
    access_log = {
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'employee_id': employee_id,
        'employee_name': employee_name,
        'status': message if employee_name != "Unknown" else None
    }
    socketio.emit('access_log', access_log)
    print(f"Access log emitted for {employee_id}")
    
    # Step 2: Call perform_switch with the provided video path
    # Pass the video path to ensure the desired video is used
    result = perform_switch(video_path=video_path)
    print(f"Switch feed called with video path: {video_path}, result: {result}")
    # Step 2: Write the log to a file in a fixed folder
    log_folder = 'logs'
    
    # Ensure the log folder exists
    os.makedirs(log_folder, exist_ok=True)
    
    # Define the log file path
    log_file_path = os.path.join(log_folder, 'access_logs.txt')

    # Format the log entry as a string
    log_entry = f"{access_log['timestamp']} - ID: {access_log['employee_id']} - Name: {access_log['employee_name']} - Status: {access_log['status']}\n"

    # Append the log entry to the file
    with open(log_file_path, 'a') as log_file:
        log_file.write(log_entry)

    print(f"Access log written to {log_file_path}")
    # Step 3: Emit facial recognition log after 1 second if an image is provided
    if image_filename:
        socketio.start_background_task(manual_switch_sequence, image_filename, access_log["status"])
        print(f"Started background task with image: {image_filename}")
    else:
        socketio.start_background_task(manual_switch_sequence, None, access_log["status"])
        print("Started background task without image")

    return redirect('/')


def handle_manual_switch_out(employee_id, image_filename, message, video_path,):
    global tmp_vid

    # Fetch employee name from the loaded employee list
    employee = next((emp for emp in employees if emp["id"] == employee_id), None)
    employee_name = employee["name"] if employee else "Unknown"

    # Step 1: Emit access logs
    access_log = {
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'employee_id': employee_id,
        'employee_name': employee_name,
        'status': message if employee_name != "Unknown" else None
    }
    socketio.emit('access_log', access_log)
    print(f"Access log emitted for {employee_id}")
    
    # Step 2: Call perform_switch with the provided video path
    # Pass the video path to ensure the desired video is used
    result = perform_switch(video_path=video_path)
    print(f"Switch feed called with video path: {video_path}, result: {result}")
    # Step 2: Write the log to a file in a fixed folder
    log_folder = 'logs'
    
    # Ensure the log folder exists
    os.makedirs(log_folder, exist_ok=True)
    
    # Define the log file path
    log_file_path = os.path.join(log_folder, 'access_logs.txt')

    # Format the log entry as a string
    log_entry = f"{access_log['timestamp']} - ID: {access_log['employee_id']} - Name: {access_log['employee_name']} - Status: {access_log['status']}\n"

    # Append the log entry to the file
    with open(log_file_path, 'a') as log_file:
        log_file.write(log_entry)

    print(f"Access log written to {log_file_path}")
    # Step 3: Emit facial recognition log after 1 second if an image is provided
    if image_filename:
        socketio.start_background_task(manual_switch_sequence, image_filename, access_log["status"])
        print(f"Started background task with image: {image_filename}")
    else:
        socketio.start_background_task(manual_switch_sequence, None, access_log["status"])
        print("Started background task without image")

    return redirect('/')



@app.route("/switch")
def switch_feed():
    return perform_switch()

# Manual Switch Sequence
def manual_switch_sequence(image_filename, message):
    with app.app_context():
        # Wait for 3 seconds before emitting facial recognition log
        socketio.sleep(3)
        if image_filename:
            facial_image_url = url_for('static', filename=image_filename, _external=True, _scheme='http')
            socketio.emit('facial_hello', {'image_url': facial_image_url, 'message': message})
            # Start a background task to remove the facial image after 5 seconds
            # socketio.sleep(3)
            socketio.start_background_task(remove_facial_image_after_delay)

        else:
            socketio.emit('facial_hello', {'image_url': None, 'message': message})
        

def perform_switch(video_path=None):
    global tmp_vid, open_sesame, counter, breach_mode

    # Check if we are in breach mode, if yes, do not change the feed
    if breach_mode:
        print(f'Breach mode active. Feed remains on {tmp_vid}')
        return "Breach mode active. Feed remains unchanged."

    # If a specific video path is provided, use it directly
    if video_path:
        with lock:
            tmp_vid = video_path
        print(f'Feed manually switched to {tmp_vid}')
        return f"Feed manually switched to {video_path}"

    # Toggle between default video and alternative video if no video path is provided
    if open_sesame:
        counter = 0
        open_sesame = False
        with lock:
            tmp_vid = default_vid
    else:
        open_sesame = True
        with lock:
            tmp_vid = mp4_files[1]

    print(f'Feed switched to {tmp_vid}')
    return "Feed Change Requested"


# Reset Video Feed to Default
def reset_to_default_feed():
    global tmp_vid, open_sesame, counter
    # Reset feed to the default closed door video
    with lock:
        tmp_vid = default_vid
    open_sesame = False  # Ensure that the automatic switch is disabled
    counter = 0  # Reset the counter to avoid unintended switches
    print(f"[DEBUG] Feed reset to default video: {default_vid}")
    # Emit an event to notify clients that the default video feed has been restored
    socketio.emit('video_changed', {'video_path': default_vid, 'message': 'Default feed restored'})
    
def remove_facial_image_after_delay():
    # Wait for 5 seconds before removing the facial image
    socketio.sleep(10)
    socketio.emit('facial_hello', {'image_url': None, 'message': ''})

def play_videos_randomly():
    global mp4_files_out, breach_mode

    # Create a copy of mp4_files so the original list remains unchanged
    remaining_videos = mp4_files_out.copy()

    while not breach_mode and remaining_videos:
        # Select a random video from the remaining list
        video_path = random.choice(remaining_videos)

        # Call the switch_feed function with the selected video
        perform_switch(video_path)

        # Remove the played video from the list to avoid repetition
        remaining_videos.remove(video_path)
        # delay_seconds  = random.uniform(2,10)
        # Wait for the specified delay before switching again
        time.sleep(delay_seconds)

    if breach_mode:
        print("Stopped switching due to breach mode being active.")
    else:
        print("All videos have been played.")


# Function to start the video switching process in a separate thread
def start_random_video_playback():
    Thread(target=play_videos_randomly, daemon=True).start()

@app.route("/switch2")
def switch_feed2():
    response_message = start_random_video_playback()
    return jsonify({"message": response_message})


# SocketIO connection handling
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('server_message', {'data': 'Welcome! You are connected to the Flask server.'})
    emit('hello_world', {'data': 'Hello World'})

# Example of a data emitting loop
@socketio.on('request_data')
def handle_message():
    while True:
        socketio.sleep(3)
        data = {'timestamp': time.time()}
        emit('update', data)

# Facial Recognition System Logs
@socketio.on('facial_logs')
def handle_facial_logs():
    print('Facial Logs Connected')
    facial_image_url = url_for('static', filename='Foto_Ashqar_Ghaith.jpg', _external=True, _scheme='http')
    emit('facial_hello', {'image_url': facial_image_url, 'message': 'Access Granted'})

# Central Access Control System Logs
@socketio.on('access_logs')
def handle_access_logs(data):
    print('Access Logs Connected')

    # Extract employee ID from the incoming data
    employee_id = data.get('employee_id', 'Unknown')

    # Fetch employee name from the configuration
    employee_name = ["employees"].get(employee_id, "Unknown")

    # Construct the access log
    access_log = {
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'employee_id': employee_id,
        'employee_name': employee_name,
        'status': data.get('status', 'Access Granted'),
        'key': data.get('key', 'N/A')
    }

    # Emit the access log
    emit('access_log', access_log)

# Disconnect event
@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# Run the application
if __name__ == "__main__":
    socketio.run(app, host='127.0.0.1', port=5001, debug=True)
