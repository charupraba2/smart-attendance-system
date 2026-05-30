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
