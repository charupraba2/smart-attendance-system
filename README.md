# Face Recognition Attendance System

A Streamlit-based web application for tracking attendance using face recognition.

## Features
- **Real-time Face Recognition**: Detects and identifies faces from webcam feed.
- **Automated Attendance**: Logs name, date, and time into a SQLite database.
- **Attendance Log**: View and download attendance history as CSV.

## Project Structure
- `app.py`: Main Streamlit application.
- `database.py`: Handles database connections and queries.
- `utils.py`: Contains face recognition logic and face encoding loading.
- `data/`:
    - `student_faces/`: Store images of known individuals here.
    - `attendance.db`: SQLite database (generated automatically).
- `requirements.txt`: Python dependencies.

## Setup

1.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Add Faces**
    - Create the folder `data/student_faces` if it doesn't exist.
    - Add clear images of people you want to recognize. Name the files `Name.jpg`.

3.  **Run the App**
    ```bash
    streamlit run app.py
    ```

## Deployment

This project can be deployed locally or as a container.

### Local deployment

- Install dependencies with `pip install -r requirements.txt`.
- Run the app with `streamlit run app.py`.
- Note: `app.py` uses `cv2.VideoCapture(0)` for a local camera, so a remote cloud deployment may not support live webcam access from the browser.

### Docker deployment

1. Build the image:
    ```bash
    docker build -t attendance-system .
    ```
2. Run the container:
    ```bash
    docker run -p 8501:8501 attendance-system
    ```
3. Open `http://localhost:8501` in your browser.

> If you deploy to a cloud host, use the mobile camera streaming option in the app or provide an accessible RTSP/HTTP camera URL instead of relying on a local USB webcam.
