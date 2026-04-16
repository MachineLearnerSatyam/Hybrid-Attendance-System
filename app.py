import streamlit as st
import cv2
import face_recognition
import mysql.connector
import numpy as np
from PIL import Image
import pickle
import io
import qrcode
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="Hybrid Attendance System", page_icon="🏫", layout="wide")

# DATABASE CONFIGURATION & INITIALIZATION
db_config_init = {
    "host": "localhost",
    "user": "root",
    "password": "patlu"
}

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "patlu",
    "database": "attendance_db"
}

def init_db():
    """Creates the MySQL database and tables if they do not exist."""
    try:
        # Create Database
        conn = mysql.connector.connect(**db_config_init)
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS attendance_db")
        conn.commit()
        conn.close()

        # Create Tables
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(100),
                face_encoding BLOB
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(50),
                name VARCHAR(100),
                date DATE,
                time_in TIME,
                time_out TIME
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        st.sidebar.error(f"Database Error: Ensure MySQL is running. {e}")

try:
    init_db()
except Exception as e:
    st.error(f"Failed to run database initialization: {e}")


# MAIN APP SETUP & NAVIGATION

st.sidebar.title("🏫 Attendance System")
st.sidebar.write("Choose a module:")
menu = ["📸 Register Student", "🟢 Live Scanner", "📊 Admin Dashboard"]
choice = st.sidebar.radio("Navigation", menu)


#  MODULE 1: REGISTER STUDENT

if choice == "📸 Register Student":
    st.title("📸 Advanced Student Registration")
    st.write("Register a new student by entering their details and capturing their face.")

    col1, col2 = st.columns(2)
    with col1:
        student_id = st.text_input("Enter Student ID (e.g., CS101)")
    with col2:
        student_name = st.text_input("Enter Full Name")

    st.write("### Capture Face")
    img_file_buffer = st.camera_input("Look straight into the camera")

    if st.button("Save & Generate QR Code"):
        if not student_id or not student_name:
            st.warning("⚠️ Please enter both Student ID and Name.")
        elif img_file_buffer is None:
            st.warning("⚠️ Please take a picture first.")
        else:
            with st.spinner("Processing face data..."):
                try:
                    # Process image and extract encoding
                    image = Image.open(img_file_buffer)
                    img_array = np.array(image)
                    face_encodings = face_recognition.face_encodings(img_array)
                    
                    if len(face_encodings) == 0:
                        st.error("🚨 No face detected! Please ensure you are well-lit and looking at the camera.")
                    else:
                        encoding = face_encodings[0]
                        encoding_bytes = pickle.dumps(encoding)
                        
                        # Save to MySQL
                        conn = mysql.connector.connect(**db_config)
                        cursor = conn.cursor()
                        cursor.execute('''
                            REPLACE INTO students (student_id, name, face_encoding)
                            VALUES (%s, %s, %s)
                        ''', (student_id, student_name, encoding_bytes))
                        conn.commit()
                        conn.close()
                        
                        # Generate QR Code
                        qr = qrcode.QRCode(box_size=10, border=4)
                        qr.add_data(student_id)
                        qr.make(fit=True)
                        qr_img = qr.make_image(fill_color="black", back_color="white")
                        
                        buf = io.BytesIO()
                        qr_img.save(buf, format="PNG")
                        byte_im = buf.getvalue()

                        st.success(f"✅ Successfully registered {student_name} in MySQL Database!")
                        st.image(byte_im, caption=f"QR for {student_id}", width=200)
                        st.download_button("Download QR Code", data=byte_im, file_name=f"{student_id}_QR.png", mime="image/png")
                        
                except Exception as e:
                    st.error(f"An error occurred: {e}")



# MODULE 2: LIVE SCANNER

elif choice == "🟢 Live Scanner":
    st.title("🟢 Live Hybrid Attendance Scanner")
    st.write("Scan a QR code or show your face to the camera to mark attendance.")

    # Helper function to load known faces from MySQL
    def load_student_data():
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT student_id, name, face_encoding FROM students")
            rows = cursor.fetchall()
        except mysql.connector.Error:
            rows = []
        
        known_ids, known_names, known_encodings = [], [], []
        for row in rows:
            known_ids.append(row[0])
            known_names.append(row[1])
            known_encodings.append(pickle.loads(row[2])) 
            
        conn.close()
        return known_ids, known_names, known_encodings

    # Helper function to calculate Eye Aspect Ratio (EAR)
    def calculate_ear(eye):
        # eye points: p1, p2, p3, p4, p5, p6
        # Vertical distances
        a = np.linalg.norm(np.array(eye[1]) - np.array(eye[5]))
        b = np.linalg.norm(np.array(eye[2]) - np.array(eye[4]))
        # Horizontal distance
        c = np.linalg.norm(np.array(eye[0]) - np.array(eye[3]))
        # EAR formula
        ear = (a + b) / (2.0 * c)
        return ear

    # Helper function to log attendance in MySQL
    def mark_attendance(std_id, name):
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        now = datetime.now()
        today_date = now.strftime("%Y-%m-%d")
        current_time_str = now.strftime("%H:%M:%S")
        
        # Check if student already marked IN today
        cursor.execute("SELECT id, time_in, time_out FROM attendance WHERE student_id = %s AND date = %s", (std_id, today_date))
        record = cursor.fetchone()
        
        if record is None:
        
            cursor.execute("INSERT INTO attendance (student_id, name, date, time_in) VALUES (%s, %s, %s, %s)", 
                           (std_id, name, today_date, current_time_str))
            conn.commit()
            st.toast(f"✅ {name} marked IN at {current_time_str}!") 
        else:
        
            att_id, time_in, time_out = record
            
            if time_out is None:

                if isinstance(time_in, timedelta):
                    # Create a dummy datetime for today with the time_in offset
                    today_start = datetime.combine(now.date(), datetime.min.time())
                    last_scan_time = today_start + time_in
                else:
                    # If it's already a time/datetime object
                    last_scan_time = datetime.combine(now.date(), time_in)

                if now - last_scan_time > timedelta(minutes=1):
                    cursor.execute("UPDATE attendance SET time_out = %s WHERE id = %s", (current_time_str, att_id))
                    conn.commit()
                    st.toast(f"🚪 {name} marked OUT at {current_time_str}!")
                else:
                    remaining = 60 - (now - last_scan_time).seconds
                    st.warning(f"⏳ {name} already marked IN! Please wait {remaining}s to mark OUT.")
            else:
                st.info(f"📁 {name} has already completed both IN and OUT for today.")

    known_ids, known_names, known_encodings = load_student_data()

    if len(known_encodings) == 0:
        st.warning("⚠️ No students found in the MySQL database. Please register students first.")
    else:
        run_camera = st.checkbox("Start Camera Scanner")
        FRAME_WINDOW = st.image([]) 

        if run_camera:
            camera = cv2.VideoCapture(0)
            detector = cv2.QRCodeDetector()
            while run_camera:
                ret, frame = camera.read()
                if not ret:
                    st.error("Failed to capture video.")
                    break
                    
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # QR CODE SCANNING
                qr_data, pts, _ = detector.detectAndDecode(frame)
                if qr_data:
                    if pts is not None:
                        pts = pts.astype(np.int32).reshape((-1, 1, 2))
                        cv2.polylines(rgb_frame, [pts], True, (0, 255, 0), 3)
                    
                    if qr_data in known_ids:
                        index = known_ids.index(qr_data)
                        name = known_names[index]
                        if pts is not None:
                            # Use top-left point for text positioning
                            pos = tuple(pts[0][0])
                            cv2.putText(rgb_frame, f"QR: {name}", (pos[0], pos[1] - 10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        mark_attendance(qr_data, name)

                # FACE RECOGNITION
                small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
                face_locations = face_recognition.face_locations(small_frame)
                face_encodings_in_frame = face_recognition.face_encodings(small_frame, face_locations)
                
                # Landmarks extraction (List of dictionaries)
                face_landmarks_list = face_recognition.face_landmarks(small_frame, face_locations)

                for (top, right, bottom, left), face_encoding, face_landmarks in zip(face_locations, face_encodings_in_frame, face_landmarks_list):
                    # Upscale coordinates
                    top *= 4; right *= 4; bottom *= 4; left *= 4
                    
                    matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
                    name = "Unknown"
                    color = (255, 0, 0) # Red
                    
                    if True in matches:
                        match_index = matches.index(True)
                        name = known_names[match_index]
                        student_id = known_ids[match_index]
                        
                        # --- BLINK DETECTION LOGIC START ---
                        left_eye = face_landmarks['left_eye']
                        right_eye = face_landmarks['right_eye']
                        
                        # Calculate EAR for both eyes and average
                        left_ear = calculate_ear(left_eye)
                        right_ear = calculate_ear(right_eye)
                        avg_ear = (left_ear + right_ear) / 2.0
                        
                        # EAR below 0.22 indicates a blink
                        if avg_ear < 0.22:
                            color = (0, 255, 0) # Green
                            cv2.putText(rgb_frame, "Real - Blink Detected!", (left, top - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                            
                            # Mark attendance only when blink detected
                            mark_attendance(student_id, name)
                        else:
                            # Face matched but no blink detected yet
                            color = (0, 165, 255) # Orange (OpenCV uses BGR)
                            cv2.putText(rgb_frame, "Please Blink to Verify!", (left, top - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    
                    
                    # Draw box and name
                    cv2.rectangle(rgb_frame, (left, top), (right, bottom), color, 2)
                    cv2.putText(rgb_frame, name, (left, bottom + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

                FRAME_WINDOW.image(rgb_frame)
            camera.release()



# MODULE 3: ADMIN DASHBOARD

elif choice == "📊 Admin Dashboard":
    st.title("📊 Attendance Admin Dashboard")
    st.write("View, filter, and export daily student attendance records.")

    def fetch_attendance(selected_date=None):
        try:
            conn = mysql.connector.connect(**db_config)
            if selected_date:
                query = "SELECT student_id, name, date, time_in, time_out FROM attendance WHERE date = %s ORDER BY time_in DESC"
                df = pd.read_sql(query, conn, params=(selected_date,))
            else:
                query = "SELECT student_id, name, date, time_in, time_out FROM attendance ORDER BY date DESC, time_in DESC"
                df = pd.read_sql(query, conn)
            conn.close()
            
            # Format time_in and time_out columns in Pandas to avoid SQL format strings
            if not df.empty:

                def format_time(val):
                    if pd.isnull(val):
                        return ""
                    
                    return str(val).split()[-1]
                
                df['time_in'] = df['time_in'].apply(format_time)
                df['time_out'] = df['time_out'].apply(format_time)
                
            return df
        except Exception as err:
            st.error(f"Database Error: {err}")
            return pd.DataFrame()

    col1, col2 = st.columns([1, 3])
    with col1:
        st.write("### Filter Records")
        filter_by_date = st.checkbox("Filter by Date")
        if filter_by_date:
            selected_date = st.date_input("Select Date", datetime.today())
            date_str = selected_date.strftime("%Y-%m-%d")
            df = fetch_attendance(date_str)
        else:
            date_str = "All Time"
            df = fetch_attendance()

    with col2:
        st.write(f"### Records: {date_str}")
        if df.empty:
            st.info("No attendance records found for this selection.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            filename = f"Attendance_{date_str}.csv" if filter_by_date else "Attendance_All_Records.csv"
            
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv,
                file_name=filename,
                mime="text/csv",
            )
            