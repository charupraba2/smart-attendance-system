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

### Railway deployment

- Push your repo to GitHub.
- Connect your Railway project to the GitHub repository.
- Set the start command in Railway settings to:
  ```bash
  streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
  ```
- This binds Streamlit to Railway's dynamic `$PORT` and exposes it on `0.0.0.0` for public access.
- Use the mobile camera streaming option or provide a network camera URL (Streamlit Cloud cannot access local webcams).

### Streamlit Cloud deployment

- Keep `requirements.txt` in the repo root and add this repository to Streamlit Cloud.
- Streamlit Cloud will use the `streamlit.toml` file in the repo root.
- Note: `app.py` uses `cv2.VideoCapture(0)` for a local camera, so the built-in webcam mode will not work on Streamlit Cloud.
- Use the mobile camera streaming option or provide a network camera URL instead.

### Local deployment

- Install dependencies with `pip install -r requirements.txt`.
- Run the app with `streamlit run app.py`.

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
