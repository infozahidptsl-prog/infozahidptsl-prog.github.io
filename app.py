import os
import json
import uuid
import cv2
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Needed for flash messages

UPLOAD_FOLDER = 'uploads'
DATA_FILE = 'data/videos.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)

# Default data state
DEFAULT_DATA = {
    "300x600": {"url": "", "description": "300x600 Video"},
    "300x250": {"url": "", "description": "300x250 Video"}
}

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump(DEFAULT_DATA, f)
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            # Merge with default ensuring all keys exist
            for k in DEFAULT_DATA:
                if k not in data:
                    data[k] = DEFAULT_DATA[k]
            return data
    except:
        return DEFAULT_DATA

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def get_video_dimensions(file_path):
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        return None, None
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return width, height

@app.route('/')
def index():
    data = load_data()
    return render_template('index.html', data=data)

@app.route('/admin')
def admin():
    data = load_data()
    return render_template('admin.html', data=data)

@app.route('/upload/<slot>', methods=['POST'])
def upload(slot):
    if slot not in ["300x600", "300x250"]:
        flash("Invalid slot", "error")
        return redirect(url_for('admin'))
        
    description = request.form.get('description', '')
    
    data = load_data()
    data[slot]["description"] = description

    if 'video' in request.files and request.files['video'].filename != '':
        video_file = request.files['video']
        ext = os.path.splitext(video_file.filename)[1] or '.mp4'
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        video_file.save(filepath)
        
        # Verify dimensions
        expected_w, expected_h = map(int, slot.split('x'))
        actual_w, actual_h = get_video_dimensions(filepath)
        
        if actual_w != expected_w or actual_h != expected_h:
            os.remove(filepath)
            flash(f"Invalid dimensions! Expected {expected_w}x{expected_h}, got {actual_w}x{actual_h} for {slot}", "error")
            return redirect(url_for('admin'))
        
        # Remove old video if exists to save space
        if data[slot].get("url", "").startswith("/uploads/"):
            old_file = os.path.join(UPLOAD_FOLDER, os.path.basename(data[slot]["url"]))
            if os.path.exists(old_file):
                try:
                    os.remove(old_file)
                except:
                    pass
                
        data[slot]["url"] = f"/uploads/{filename}"
        data[slot]["filename"] = video_file.filename

    save_data(data)
    flash(f"Updated {slot} successfully!", "success")
    return redirect(url_for('admin'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
