# Hybrid Student Attendance System 🎓

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg)](https://streamlit.io/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green.svg)](https://opencv.org/)
[![MySQL](https://img.shields.io/badge/MySQL-Database-orange.svg)](https://www.mysql.com/)

## 📝 Abstract
The **Hybrid Student Attendance System** is an automated, real-time application designed to modernize academic attendance tracking. By integrating both **Facial Recognition** and **QR Code scanning**, this system eliminates the inefficiencies of manual roll calls and effectively prevents proxy logging. Built with Python, Streamlit, OpenCV, and MySQL, it provides a secure, hardware-agnostic, and user-friendly administrative tool.

## ✨ Key Features
* **Dual-Method Scanning:** Processes both live facial data and unique QR codes simultaneously via a standard webcam.
* **Anti-Spam Temporal Logic:** Includes a 1-minute programmatic cooldown to accurately distinguish between "IN" and "OUT" states, preventing accidental duplicate scans.
* **Advanced Student Registration:** Seamlessly pairs student credentials with 128-dimensional facial encodings and generates downloadable 2D QR barcodes.
* **Admin Dashboard:** A real-time, interactive UI for data visualization, filtering, and instant CSV exportation of attendance records.

## 🛠️ Technology Stack
* **Frontend/UI:** [Streamlit](https://streamlit.io/)
* **Computer Vision:** [OpenCV](https://opencv.org/) (`cv2`), `face_recognition`
* **Backend Logic:** Python (`datetime`, `qrcode`, `pandas`)
* **Database:** MySQL

## ⚙️ System Architecture

### 1. Database Configuration
A localized MySQL database featuring two primary tables:
* `students`: Stores static registration data (Student ID, Name, Binary Face Encodings).
* `attendance`: Records dynamic, time-stamped logs (Date, Time In, Time Out).

### 2. Module Workflow
* **Module 1 (Registration):** Captures high-quality snapshots, extracts facial encoding arrays, generates a unique QR code, and pushes the profile to the database.
* **Module 2 (Live Hybrid Scanner):** Runs parallel algorithms on real-time webcam frames to decode QR codes and match facial encodings (0.5 tolerance threshold). Applies chronological logic to manage IN/OUT states.
* **Module 3 (Visualization):** Queries the MySQL database to render an interactive dataframe for institutional record-keeping.

## 🚀 Future Scope
* **Agentic AI for Proactive Truancy Management:** Autonomous AI voice agents to call guardians regarding consecutive absences and transcribe responses using STT models.
* **Liveness Detection:** Upgrading the facial recognition module to require a blink or head movement to prevent spoofing via printed photographs.
* **Advanced Data Visualization:** Mining historical data to uncover deeper behavioral insights and chronic absenteeism trends.
* **Cloud Migration & Real-Time Alerts:** Moving the database to AWS/GCP and enabling automated SMS/email alerts to parents upon campus entry.

## 👨‍💻 Author
**Satyam Pandey** * **Email:** satyampandey6069@gmail.com  
* **Phone:** +91 6388400030

---
*If you find this repository helpful, please consider leaving a star! ⭐*
