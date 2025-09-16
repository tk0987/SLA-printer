import serial
import serial.tools.list_ports
import os, json, time
from tkinter import Tk, Label
from screeninfo import get_monitors
from PIL import Image, ImageTk

class PrinterController:
    def __init__(self):
        self.port = self.find_pico_port()
        self.pico = serial.Serial(self.port, 115200, timeout=1) if self.port else None

    def find_pico_port(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "Pico" in port.description or "ACM" in port.device or "USB Serial" in port.description:
                return port.device
        return None

    def send_command(self, cmd: str):
        if self.pico:
            self.pico.write((cmd + '\n').encode('utf-8'))
        print(f"Sent command: {cmd}")

    def move_z(self, mm: float):
        self.send_command(f"move {mm}")

    def home(self):
        self.send_command("home")

    def reset_mode(self):
        self.send_command("resetmode")

    def exit_session(self):
        self.send_command("exit")

    def get_help(self):
        self.send_command("help")

    def activate_print_mode(self, image_dir):
        self.send_command("printmode")
        monitors = get_monitors()
        if not monitors:
            print("Monitor not detected.")
            return

        second = monitors[0]
        width, height = second.width, second.height

        try:
            with open(os.path.join(image_dir, "config.json"), "r") as f:
                config = json.load(f)
        except Exception as e:
            print(f"Failed to load config.json: {e}")
            return

        expTime = 10
        expTimeFirst = 5
        layerHeight = 0.05
        delay_before = 2
        delay_after = 2

        images = sorted(f for f in os.listdir(image_dir) if f.lower().endswith('.png'))
        index = 0
        show_black = False

        root = Tk()
        root.geometry(f"{width}x{height}+0+0")
        root.configure(background='black')
        root.overrideredirect(True)
        root.lift()
        root.attributes("-topmost", True)
        root.resizable(False, False)

        label = Label(root, bg='black', borderwidth=0, highlightthickness=0)
        label.place(x=0, y=0, width=width, height=height)

        def exit_view(event):
            root.destroy()
        root.bind("<Escape>", exit_view)

        def show_images():
            nonlocal index, show_black
            if index >= len(images):
                self.send_command("uv_off")
                root.destroy()
                self.move_z(100)
                print("Printing completed.")
                return

            if show_black:
                self.send_command("uv_off")
                label.config(image='', bg='black')
                self.move_z(2)
                time.sleep(0.5)
                self.move_z(-(2 - layerHeight))
                label.image = None
                show_black = False
                root.after(15000, show_images)
            else:
                self.send_command("uv_on")
                img_path = os.path.join(image_dir, images[index])
                print(f"Displaying image: {img_path}")
                img = Image.open(img_path)
                photo = ImageTk.PhotoImage(img)
                label.config(image=photo, bg='black')
                label.image = photo
                exposure = expTimeFirst if index == 0 else expTime
                delay_ms = int((delay_before + exposure + delay_after) * 1000) + 10000
                index += 1
                show_black = True
                root.after(delay_ms, show_images)

        show_images()
        root.mainloop()



# ================+++++++++++++++++++++++=======================   
#
#                        funny part
#
# ================+++++++++++++++++++++++=======================        
from fastapi import FastAPI, Request, Form, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi import Body
from typing import List
from fastapi import File
import zipfile
import uuid
from pydantic import BaseModel

class PrintRequest(BaseModel):
    path: str
UPLOAD_DIR = "/home/tk/Desktop/printer_control/sl1_files"

app = FastAPI()
templates = Jinja2Templates(directory="templates")
printer = PrinterController()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/move")
async def move(z_steps: float = Form(...), direction: str = Form(...)):
    if direction == "up":
        printer.move_z(z_steps)
    elif direction == "down":
        printer.move_z(-z_steps)
    elif direction == "set_zero":
        printer.set_zero()
    elif direction == "home":
        printer.home()
    return RedirectResponse(url="/", status_code=303)

@app.post("/uv")
async def uv(pattern: str = Form(...)):
    # printer.send_command(f"display_{pattern}")
    return RedirectResponse(url="/", status_code=303)





@app.post("/upload")
async def upload(files: List[UploadFile] = File(...)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    for file in files:
        if not file.filename.lower().endswith(".sl1"):
            continue  # Skip non-SL1 files

        # Create a unique folder for extraction
        folder_name = os.path.splitext(file.filename)[0] + "_" + str(uuid.uuid4())[:8]
        extract_path = os.path.join(UPLOAD_DIR, folder_name)
        os.makedirs(extract_path, exist_ok=True)

        # Save the uploaded SL1 file temporarily
        temp_path = os.path.join(extract_path, file.filename)
        with open(temp_path, "wb") as f:
            contents = await file.read()
            f.write(contents)

        # Extract contents
        try:
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            print(f"Extracted {file.filename} to {extract_path}")
        except zipfile.BadZipFile:
            print(f"Failed to extract {file.filename}: Not a valid ZIP archive")

        # Optionally delete the original .sl1 file
        os.remove(temp_path)

    return RedirectResponse(url="/", status_code=303)

# @app.get("/sl1_list")
# async def sl1_list():
#     files = [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(".sl1")]
#     return JSONResponse(content={"files": files})
# @app.post("/print")
# async def start_print(path: str):
#     full_path = os.path.join(UPLOAD_DIR, path)
#     # error=full_path
#     if full_path:
#         return templates.TemplateResponse("index.html", {
#                 "request": "/print",
#                 "error": full_path
#             })

#     # if os.path.isdir(full_path):
#     printer.activate_print_mode(full_path)
#     #     print(f"Printing started for: {full_path}")
#     # else:
#     #     print(f"Invalid print path: {full_path}")
#     return RedirectResponse(url="/", status_code=303)

# from fastapi.responses import JSONResponse
@app.post("/print")
async def start_print(request: PrintRequest):
    full_path = os.path.join(UPLOAD_DIR, request.path)

    if not os.path.isdir(full_path):
        return JSONResponse(content={"error": f"Invalid path: {full_path}"}, status_code=400)

    printer.activate_print_mode(full_path)
    return JSONResponse(content={"message": f"Printing started for: {full_path}"})

@app.get("/print_jobs")
async def list_print_jobs():
    subdirs = [
        name for name in os.listdir(UPLOAD_DIR)
        if os.path.isdir(os.path.join(UPLOAD_DIR, name))
    ]
    return JSONResponse(content={"jobs": subdirs})


@app.post("/add")
async def add_wifi(ssid: str = Form(...), password: str = Form(...)):
    print(f"WiFi SSID: {ssid}, Password: {password}")
    return RedirectResponse(url="/", status_code=303)
'''
sudo systemctl restart printercontrol.service
'''
