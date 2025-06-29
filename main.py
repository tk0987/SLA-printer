
# Unified SLA Printer Controller for Raspberry Pi Zero W

import os
import json
import time
import threading
import subprocess
import zipfile
from flask import Flask, render_template, request, redirect, jsonify
from werkzeug.utils import secure_filename
from tkinter import Tk, Label
from PIL import Image, ImageTk
import RPi.GPIO as GPIO
#os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# -----------------------------
# Configuration
# -----------------------------
UPLOAD_FOLDER = '/home/threedeprinter/Documents/3dPrinter/dwnld'
ALLOWED_EXTENSIONS = {'sl1'}
CONFIG_PATH = os.path.join(UPLOAD_FOLDER, 'config.json')
IMAGE_DIR = os.path.join(UPLOAD_FOLDER,'img')
STEPS_PER_MM = 100

# -----------------------------
# App + GPIO Setup
# -----------------------------
images = []
state = {"index": 0}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

MOTOR_IN1 = 23
MOTOR_IN2 = 24
DOOR_IN = 5
HOME = 6
UV_BCKG=23
GPIO.setmode(GPIO.BCM)
GPIO.setup(UV_BCKG, GPIO.OUT)
GPIO.setup(MOTOR_IN1, GPIO.OUT)
GPIO.setup(MOTOR_IN2, GPIO.OUT)
GPIO.setup(DOOR_IN, GPIO.IN)
GPIO.setup(HOME, GPIO.IN)

posi_z = 0
try:
    with open("global_zero.zero", "r+", encoding="utf-8") as f:
        zero_home = int(f.readline())
except:
    zero_home = 0
# -----------------------------
# UV Control
# -----------------------------
def uv_on():
    GPIO.output(UV_BCKG, GPIO.HIGH)

def uv_off():
    GPIO.output(UV_BCKG, GPIO.LOW)
# -----------------------------
# turn uv off - shall be BLACK!!!
# -----------------------------
uv_off()

# -----------------------------
# Motor Control
# -----------------------------
def accel(steps, index):
    x0 = steps // 2
    return 10 * (index - x0)**2 / 1000 + 0.025

def step_motor(steps):
    global posi_z, zero_home
    GPIO.output(MOTOR_IN2, GPIO.HIGH if steps > 0 else GPIO.LOW)
    index = 0
    for _ in range(abs(steps)):
        if GPIO.input(HOME) > 0:
            if zero_home:
                for _ in range(zero_home):
                    GPIO.output(MOTOR_IN1, GPIO.HIGH)
                    time.sleep(0.1)
                    GPIO.output(MOTOR_IN1, GPIO.LOW)
                    time.sleep(0.1)
            posi_z = 0
            break
        if posi_z >= 245:
            break
        GPIO.output(MOTOR_IN1, GPIO.HIGH)
        time.sleep(accel(steps, index))
        GPIO.output(MOTOR_IN1, GPIO.LOW)
        time.sleep(accel(steps, index))
        index += 1
    posi_z += steps

def move_z_axis(mm): step_motor(int(mm * STEPS_PER_MM))
def go_home():
    print("Homing...")
    step_motor(-300 * STEPS_PER_MM)
    global posi_z
    posi_z = 0

def set_zero():
    global zero_home, posi_z
    zero_home = posi_z

# -----------------------------
# Image Preview Thread
# -----------------------------
def start_preview(path):
    global images, state
    try:
        config_path = os.path.join(path, 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Failed to load config.json: {e}")
        return

    expTime = config.get("expTime", 1)
    expTimeFirst = config.get("expTimeFirst", expTime)
    layerHeight = config.get("layerHeight", 0.05)
    delay_before = config.get("delay_before_exposure_ms", 0) / 1000.0
    delay_after = config.get("delay_after_exposure_ms", 0) / 1000.0

    images = sorted(f for f in os.listdir(path) if f.endswith('.png'))
    if not images:
        print(f"No images found in {path}")
        return

    state["index"] = 0
    state["show_black"] = False

    root = Tk()
    root.attributes('-fullscreen', True)
    root.configure(background='black')
    label = Label(root, bg='black')
    label.pack(expand=False)
    root.bind("<Escape>", lambda e: root.attributes('-fullscreen', False))

    def show_images():
        if state["index"] >= len(images):
            uv_off()
            root.destroy()
            move_z_axis(100)
            return
        if state["show_black"]:
            uv_off()
            label.config(image='', bg='black')
            move_z_axis(10)
            time.sleep(0.5)
            move_z_axis(-(10 - layerHeight))
            label.image = None
            state["show_black"] = False
            root.after(10000, show_images)
        else:
            uv_on()
            img_file = os.path.join(path, images[state["index"]])
            img = Image.open(img_file).rotate(90)
            photo = ImageTk.PhotoImage(img)
            label.config(image=photo, bg='black')
            label.image = photo
            exposure = expTimeFirst if state["index"] == 0 else expTime
            total_delay = int((delay_before + exposure + delay_after) * 1000)
            state["index"] += 1
            state["show_black"] = True
            root.after(total_delay, show_images)

    show_images()
    root.mainloop()

def show_uv_pattern(pattern_file, duration=10):
    def display():
        root = Tk()
        root.attributes('-fullscreen', True)
        root.configure(background='black')
        label = Label(root, bg='black')
        label.pack(expand=True)

        try:
            uv_on()
            img = Image.open(pattern_file)
            photo = ImageTk.PhotoImage(img)
            label.config(image=photo)
            label.image = photo
        except Exception as e:
            print(f"Failed to display {pattern_file}: {e}")
        finally:
            root.after(duration * 1000, lambda: [uv_off(), root.destroy()])
            root.mainloop()

    threading.Thread(target=display, daemon=True).start()

# -----------------------------
# Wi-Fi Auto Connect
# -----------------------------
def is_connected():
    result = subprocess.run(['iwgetid', '-r'], stdout=subprocess.PIPE)
    return bool(result.stdout.decode().strip())

def start_hotspot():
    subprocess.run(['sudo', 'systemctl', 'stop', 'wpa_supplicant.service'])
    subprocess.run(['sudo', 'systemctl', 'stop', 'dhcpcd.service'])
    subprocess.run(['sudo', 'systemctl', 'start', 'hostapd.service'])
    subprocess.run(['sudo', 'systemctl', 'start', 'dnsmasq.service'])

def connect_wifi():
    cred_path = '/home/pi/wificonf.fill'
    if not os.path.exists(cred_path): return False
    with open(cred_path, 'r') as f:
        lines = f.readlines()
    creds = dict(line.strip().split("=", 1) for line in lines if "=" in line)
    if not creds.get("SSID") or not creds.get("PASSWORD"): return False

    try:
        with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'w') as f:
            f.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
            f.write("update_config=1\ncountry=US\n\n")
            f.write("network={\n")
            f.write(f'    ssid="{creds["SSID"]}"\n')
            f.write(f'    psk="{creds["PASSWORD"]}"\n}}\n')
        os.chmod('/etc/wpa_supplicant/wpa_supplicant.conf', 0o600)
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'reconfigure'])
        time.sleep(10)
        return is_connected()
    except Exception as e:
        print(f"Wi-Fi error: {e}")
        return False

# -----------------------------
# Flask Routes
# -----------------------------
@app.route('/')
def index():
    folders = []
    upload_folder = app.config['UPLOAD_FOLDER']

    if os.path.exists(upload_folder):
        folders = [name for name in os.listdir(upload_folder)
                    if os.path.isdir(os.path.join(upload_folder, name))]

    return render_template('index.html', folders=folders)

@app.route('/move', methods=['POST'])
def move():
    direction = request.form.get('direction')
    mm = int(request.form.get('z_steps', 0))
    if direction == 'up': move_z_axis(abs(mm))
    elif direction == 'down': move_z_axis(-abs(mm))
    elif direction == 'home': go_home()
    elif direction == 'set_zero': set_zero()
    return redirect('/')
@app.route('/uv', methods=['POST'])
def uv_pattern():
    pattern = request.form.get('pattern')

    if pattern == 'black':
        uv_off()  # Just turn off UV, no need to show image
    elif pattern == 'white':
        show_uv_pattern('white.jpg')
    elif pattern == 'chessboard':
        show_uv_pattern('black.jpg')  # Replace with actual chessboard image if different
    else:
        print(f"Unknown pattern: {pattern}")

    return redirect('/')


@app.route('/upload', methods=['POST'])
def upload_file():
    from werkzeug.utils import secure_filename
    import zipfile

    upload_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    if 'file' not in request.files:
        print("❌ No file part in request.")
        return "No file uploaded", 400

    file = request.files['file']
    if file.filename == '':
        print("⚠️ Empty filename.")
        return "No file selected", 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(upload_folder, filename)

    try:
        file.save(save_path)
        print(f"✅ File '{filename}' uploaded to {save_path}")
    except Exception as e:
        print(f"❌ Failed to save file: {e}")
        return "Failed to save", 500

    # Unzip if it's a .sl1 file (usually a ZIP archive)
    if filename.lower().endswith('.sl1') and zipfile.is_zipfile(save_path):
        extract_dir = os.path.join(upload_folder, os.path.splitext(filename)[0] + '_extracted')
        try:
            with zipfile.ZipFile(save_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            print(f"📦 Extracted SL1 contents to: {extract_dir}")
            
            # Start preview as a daemon thread
            threading.Thread(target=start_preview, args=(extract_dir,), daemon=True).start()

        except Exception as e:
            print(f"❌ Failed to extract or preview: {e}")
            return "SL1 unzip error", 500
    else:
        print("ℹ️ Uploaded file is not an SL1 (ZIP) — skipping extraction.")

    return redirect('/')


@app.route('/add', methods=['POST'])
def add_wifi():
    ssid = request.form.get('ssid', '').strip()
    password = request.form.get('password', '').strip()
    if ssid and password:
        try:
            with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'w') as f:
                f.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
                f.write("update_config=1\ncountry=US\n\n")
                f.write("network={\n")
                f.write(f'    ssid="{ssid}"\n    psk="{password}"\n\n')
            os.chmod('/etc/wpa_supplicant/wpa_supplicant.conf', 0o600)
            subprocess.run(['wpa_cli', '-i', 'wlan0', 'reconfigure'])
            subprocess.run(['sudo', 'reboot'])
        except Exception as e:
            return f"Wi-Fi config error: {e}", 500
        return redirect('/')
    return "SSID and password are required.", 400

@app.route('/progress')
def progress():
    if not images or "index" not in state:
        return jsonify(current_layer=0, total_layers=0, percent=0)
    total = len(images)
    current = min(state.get("index", 0), total)
    return jsonify(
        current_layer=current,
        total_layers=total,
        percent=int((current / total) * 100)
    )
@app.route('/print', methods=['POST'])
def start_print():
    folder_name = request.form.get('folder')
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)

    if not os.path.isdir(full_path):
        return f"❌ Folder not found: {folder_name}", 400

    print(f"🖨️ Starting print from: {full_path}")
    try:
        threading.Thread(target=start_preview, args=(full_path,), daemon=True).start()
        return redirect('/')
    except Exception as e:
        return f"Error starting print: {e}", 500



# -----------------------------
# Run the App
# -----------------------------
if __name__ == '__main__':
    try:
        if not is_connected():
            print("Wi-Fi not connected. Attempting to connect...")
            if not connect_wifi():
                print("Wi-Fi connection failed. Starting hotspot...")
                start_hotspot()
        else:
            print("Already connected to Wi-Fi.")

        print("Starting Flask server...")
        app.run(host='0.0.0.0', port=8080)

    finally:
        print("Cleaning up GPIO pins...")
        GPIO.cleanup()
