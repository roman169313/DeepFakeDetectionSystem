# 🧠 Deep Fake Detection of Videos and Audio using Digital Forensics

### 🎯 Project Overview
The **Deep Fake Detection System** is a deep learning–based web application designed to detect manipulated or AI-generated media content in **videos and audio files**.  
Using advanced **digital forensic** and **machine learning** techniques, it identifies signs of tampering such as facial inconsistencies, unnatural movement, and synthetic audio signatures.

This system provides an intuitive **web-based platform** where users can upload media files and receive a real-time authenticity analysis.

---

### ⚙️ Core Features
- 🔍 Detects deepfakes in both **video and audio**
- ⚡ Real-time analysis and report generation
- 🧑‍💻 Facial expression and motion consistency analysis
- 🔊 Audio spectrogram–based fake voice detection
- 🧱 Scalable **Django REST API** backend
- 🐳 Dockerized for easy deployment
- 🧠 Built with TensorFlow, PyTorch, and Keras

---

### 🧩 Tech Stack

| Layer | Technologies |
|-------|---------------|
| **Frontend** | HTML, CSS, JavaScript |
| **Backend** | Python (Django, Django REST Framework) |
| **AI/ML** | TensorFlow, Keras |
| **Data Processing** | OpenCV (video), Librosa (audio) |
| **Database** | MySQL |

---

### 🏗️ System Architecture
1. **User Interface** — Web form for uploading audio/video files.  
2. **Backend API** — Django handles requests, manages database entries, and interfaces with ML models.  
3. **AI Engine** — Deep learning models trained to detect manipulated faces, voice inconsistencies, and frame anomalies.  
4. **Results Module** — Returns authenticity probability and confidence score.

---

### 🚀 Installation Guide

#### 1. Clone the Repository
```bash
git clone <repository_url>
cd deepfake-detection



python -m venv venv
source venv/bin/activate     # for Linux/Mac
venv\Scripts\activate        # for Windows


pip install -r requirements.txt

# Optional — live reload / tailwind dev tools (not for production VPS):
# pip install -r requirements-dev.txt

# Optional — copy environment template:
# cp .env.example .env

python manage.py migrate
python manage.py collectstatic --noinput

python manage.py runserver
```

---

### 🖥️ VPS deployment (with Node/PM2 on same server)

Uses **Gunicorn + systemd + Nginx** on port `8000` — does not use or change PM2.

See **[deploy/README.md](deploy/README.md)** for full steps.

```bash
chmod +x deploy/deploy.sh
export NGINX_SERVER_NAME=deepfake.yourdomain.com
cp .env.example .env   # set DJANGO_DEBUG=False and DB credentials
./deploy/deploy.sh --full
```
