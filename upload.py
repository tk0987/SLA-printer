from flask import request, redirect
from werkzeug.utils import secure_filename
import zipfile
import subprocess
from lcd_handler import *

UPLOAD_FOLDER = '/home/tk/Desktop/slicer'
ALLOWED_EXTENSIONS = {'sl1'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        sl1_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(sl1_path)

        # Extract archive
        extract_path = os.path.join(app.config['UPLOAD_FOLDER'], 'Unnamed-Sphere')
        with zipfile.ZipFile(sl1_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        # Launch the print script
        subprocess.Popen(['python3', 'lcd_handler.py'])

        return redirect('/')

    return "Invalid file format", 400
