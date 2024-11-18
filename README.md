# Flask Video Streaming & Access Control System

This repository contains a Flask-based video streaming and access control system designed for employee management and logging purposes. The application allows users to stream video feeds, manually switch between access videos for employees, and supports real-time updates using SocketIO. It is an ideal solution for secure environments where access control and event logging are crucial.

## Key Features
- **Live Video Streaming**: Streams video content using OpenCV and Flask.
- **Access Control with Employee Management**: Manages employee access using pre-configured data stored in JSON format.
- **Real-time Notifications via SocketIO**: Provides real-time client-server communication for status updates and logging.
- **Video Feed Switching**: Allows manual switching between default and specific employee videos for access and logout.
- **Access Logging**: Logs all access and logout attempts with timestamps.

## Table of Contents
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Endpoints](#endpoints)
- [SocketIO Events](#socketio-events)
- [License](#license)

## Installation
To run this application, you need to have Python installed along with some dependencies. Follow the instructions below:

### Prerequisites
- Python 3.7+
- [pip](https://pip.pypa.io/en/stable/installation/)

### Setup
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ait-cs-IaaS/pps-camera.git
   cd pps-camera
   git checkout dev2

   ```

2. **Install Dependencies**:
   Install the necessary Python packages listed in `requirements.txt`.
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   python app.py
   ```
   By default, the server will run on `http://127.0.0.1:5001`.

4. **Run Using SocketIO**:
   The application uses SocketIO with Eventlet for real-time data handling. It is recommended to run it using the following command to ensure all socket features work properly:
   ```bash
   python -m flask run --host=127.0.0.1 --port=5001
   ```

## Configuration
The application requires a configuration JSON file (`config.json`) to manage employees and their details.

### Employee Configuration (test.json)
The configuration file should contain the list of employees with their unique details. An example structure is:

```json
{
  "employees": [
    {
      "id": "1",
      "name": "John Doe",
      "video": "john.mp4",
      "picture": "john_picture.jpg"
    },
    {
      "id": "2",
      "name": "Jane Smith",
      "video": "jane.mp4",
      "picture": "jane_picture.jpg"
    }
  ]
}
```
- **id**: Unique identifier for the employee.
- **name**: Employee's name.
- **video**: Corresponding video file for the employee.
- **picture**: Picture of the employee for logging purposes.

## Usage
### Running the Application
Once the server is up and running, you can access the main HTML page on `http://127.0.0.1:5001/`. Here, you will see the default video feed being streamed.

### Video Switching
- **Manual Switch**: You can manually switch the feed by accessing `/manual_switch/<name>` where `<name>` matches the first name of an employee in `config.json`.
- **Logout Video**: Use `/manual_switch_out/<name>` to play an employee's logout video.

### Random Video Playback
- Use `/switch2` to start random playback of all employee videos from the `vid_out` folder.

## Endpoints
### Main Routes
- `/` - Renders the main page with live video streaming.
- `/feed` - Streams the video feed.
- `/manual_switch/<name>` - Switches video to the corresponding employee's access video.
- `/manual_switch_out/<name>` - Switches video to the corresponding employee's logout video.
- `/frz` - Freezes or unfreezes the current video feed.
- `/switch2` - Starts random playback of logout videos.

### Video Streaming Endpoint
- `/feed` - Streams the current video using MJPEG format. This endpoint is primarily used for live feed rendering on the main page.

## SocketIO Events
- **connect**: Sends a welcome message when a client connects.
- **request_data**: Emits real-time timestamps every 3 seconds.
- **access_logs**: Handles logging for employee access.
- **facial_logs**: Manages facial recognition logging and image broadcasting.
- **disconnect**: Handles client disconnections.

## Logging
All access attempts are logged in a text file named `access_logs.txt` under the `logs` folder.
- **Log Structure**: `timestamp - ID: <employee_id> - Name: <employee_name> - Status: <status>`
- **Log Example**: `2023-08-01 12:45:23 - ID: 1 - Name: John Doe - Status: Access Granted`
The log file provides a comprehensive history of all employee activities, including when they logged in or out.

## Video Configuration
- **Default Video**: The default video is set to `vid/door.mp4`. This plays when no specific access is granted.
- **Employee Videos**: Videos for employees are stored in the `vid/` and `vid_out/` directories for access and logout, respectively.


