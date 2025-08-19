#works with pi pico / pi pico w v2 or v1 - all via usb, second display is must-be
# This class defines a GUI application in Python using PySide6 for controlling a device named Pico,
# with various buttons and functionalities implemented for interacting with the device.
# -*- coding: utf-8 -*-
import sys
import serial
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (QApplication, QWidget, QMainWindow, QGridLayout,
    QLineEdit, QLabel, QPushButton, QProgressBar, QFrame,
    QMenuBar, QMenu, QStatusBar, QFileDialog)
import json, os, time
from tkinter import Tk, Label
from PIL import Image, ImageTk
from screeninfo import get_monitors
import serial.tools.list_ports

class Ui_MainWindow(object):
    def find_pico_port(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "Pico" in port.description or "ACM" in port.device or "USB Serial" in port.description:
                return port.device
        return None
    def blackout_second_monitor(self):
        monitors = get_monitors()
        if len(monitors) < 2:
            print("⚠️ Second monitor not detected.")
            return

        second = monitors[1]
        x, y = second.x, second.y
        width, height = second.width, second.height

        self.blackout_root = Tk()
        self.blackout_root.geometry(f"{width}x{height}+{x}+{y}")
        self.blackout_root.configure(background='black')
        self.blackout_root.overrideredirect(True)
        self.blackout_root.lift()
        self.blackout_root.attributes("-topmost", True)
        self.blackout_root.resizable(False, False)

        label = Label(self.blackout_root, bg='black', borderwidth=0, highlightthickness=0)
        label.place(x=0, y=0, width=width, height=height)

        self.blackout_root.update()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(856, 610)
        MainWindow.setStyleSheet("background-color: rgb(61, 56, 70);")




        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.gridLayout_2 = QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")

        # 🧠 All buttons and widgets
        self.pushButton_2 = QPushButton("Home", self.centralwidget)
        self.pushButton_2.clicked.connect(self.home)

        self.pushButton_4 = QPushButton("Set zero\n(calibrate)", self.centralwidget)
        self.pushButton_4.clicked.connect(self.set_zero)

        self.pushButton_3 = QPushButton("Reset", self.centralwidget)
        self.pushButton_3.clicked.connect(self.reset_mode)

        self.pushButton_6 = QPushButton("Exit", self.centralwidget)
        self.pushButton_6.clicked.connect(self.exit_session)

        self.pushButton = QPushButton("Set to print\nmode", self.centralwidget)
        self.pushButton.clicked.connect(self.activate_print_mode)

        self.pushButton_7 = QPushButton("Print current\nposition", self.centralwidget)
        self.pushButton_7.clicked.connect(self.get_position)

        self.pushButton_5 = QPushButton("Help", self.centralwidget)
        self.pushButton_5.clicked.connect(self.get_help)

        self.pushButton_8 = QPushButton("Move Z [mm]", self.centralwidget)
        self.pushButton_8.clicked.connect(self.send_move_command)
        self.pushButton_confirm = QPushButton("Confirm Zero", self.centralwidget)
        self.pushButton_confirm.clicked.connect(self.send_zero_confirm)
        self.gridLayout_2.addWidget(self.pushButton_confirm, 6, 0)


        self.lineEdit = QLineEdit(self.centralwidget)
        self.lineEdit.setPlaceholderText("Move... [mm]")
        self.lineEdit.setStyleSheet("color: rgb(255, 255, 255);")

        self.label_2 = QLabel("Status", self.centralwidget)
        self.label_2.setStyleSheet("color: rgb(255, 255, 255);")

        self.progressBar = QProgressBar(self.centralwidget)
        self.progressBar.setValue(0)
        self.progressBar.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(38, 162, 105);")

        self.line = QFrame(self.centralwidget)
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.line_2 = QFrame(self.centralwidget)
        self.line_2.setFrameShape(QFrame.VLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.gridLayout = QGridLayout()
        self.gridLayout.addWidget(self.label_2, 0, 0)
        self.gridLayout.addWidget(self.line, 3, 0)
        self.gridLayout.addWidget(self.progressBar, 4, 0)

        self.gridLayout_2.addLayout(self.gridLayout, 1, 0)
        self.gridLayout_2.addWidget(self.lineEdit, 2, 0)
        self.gridLayout_2.addWidget(self.line_2, 1, 1)
        self.gridLayout_2.addWidget(self.pushButton_2, 1, 3)
        self.gridLayout_2.addWidget(self.pushButton_4, 5, 3)
        self.gridLayout_2.addWidget(self.pushButton_3, 3, 3)
        self.gridLayout_2.addWidget(self.pushButton_6, 6, 3)
        self.gridLayout_2.addWidget(self.pushButton, 2, 3)
        self.gridLayout_2.addWidget(self.pushButton_7, 4, 3)
        self.gridLayout_2.addWidget(self.pushButton_5, 0, 3)
        self.gridLayout_2.addWidget(self.pushButton_8, 3, 0)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menuNothing = QMenu("Nothing", self.menubar)
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)
        self.menubar.addAction(self.menuNothing.menuAction())
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.blackout_second_monitor()
        port = self.find_pico_port()
        if port:
            self.pico = serial.Serial(port, 115200, timeout=1)
            self.label_2.setText(f"🔌 Connected to Pico on {port}")
        else:
            self.label_2.setText("❌ Pico not found.")
            self.pico = None


    # 🔧 Serial Command Methods Inside Class
    def send_command(self, cmd: str):
        self.pico.write((cmd + '\n').encode('utf-8'))

    def home(self):
        self.send_command('home')

    def move_z(self, mm: float):
        self.send_command(f'move {mm}')
        
    def get_position(self):
        self.send_command('pos')
        
    def set_zero(self):
        pass
        # self.send_command('zero')
        # pos=self.get_position()
        # f=open('zero.posiz','w',encoding='asci')
        # f.writelines(pos)
        # f.close()


    def send_zero_confirm(self):
        pass
        # self.send_command("zero_confirm")
        # self.label_2.setText("✅ Zero confirmed sent to Pico.")

    def activate_print_mode(self):
    # Send Pico command
        image_dir = QFileDialog.getExistingDirectory(self.centralwidget, "Select Image Folder")
        self.send_command('printmode')

        # Detect second monitor
        monitors = get_monitors()
        for i, m in enumerate(monitors):
            print(f"Monitor {i}: {m.width}x{m.height} at ({m.x},{m.y})")
        if len(monitors) < 2:
            self.label_2.setText("⚠️ Second monitor not detected.")
            return
        second = monitors[1]
        x, y = second.x, second.y
        width, height = second.width, second.height
        


    
        


        # Select image folder
        
        if not image_dir:
            self.label_2.setText("❌ No folder selected.")
            return
        self.label_2.setText(f"🖨️ Selected folder: {image_dir}")

        # Load config
        try:
            with open(os.path.join(image_dir,"config.json"), "r") as f:
                config = json.load(f)
        except Exception as e:
            self.label_2.setText(f"⚠️ Failed to load config.json: {e}")
            return
        expTime =10 # config.get("expTime", 5)
        expTimeFirst = 50#config.get("expTimeFirst", expTime+20)
        layerHeight = 0.05#config.get("layerHeight", 0.05)
        delay_before = 2#config.get("delay_before_exposure_ms", 2) / 1000.0 
        delay_after = 2#config.get("delay_after_exposure_ms", 2) / 1000.0

        images = sorted(f for f in os.listdir(image_dir) if f.lower().endswith('.png'))
        index = 0
        show_black = False

        # Create pixel-perfect window on second monitor
        if hasattr(self, 'blackout_root'):
            self.blackout_root.destroy()
        root = Tk()
        root.geometry(f"{width}x{height}+{1920}+{0}")
        root.configure(background='black')
        root.overrideredirect(True)  # Removes window borders
        root.lift()                  # Brings window to front
        root.attributes("-topmost", True)  # Keeps it on top


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
                self.label_2.setText("✅ Printing completed.")
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
                img = Image.open(img_path)#.rotate(-90)
                photo = ImageTk.PhotoImage(img)
                label.config(image=photo, bg='black')
                label.image = photo
                exposure = expTimeFirst if index == 0 else expTime
                delay_ms = int((delay_before + exposure + delay_after) * 1000)+10000
                index += 1
                show_black = True
                root.after(delay_ms, show_images)
                
        show_images()
        root.mainloop()
    def reset_mode(self):
        self.send_command('resetmode')

    def exit_session(self):
        self.send_command('exit')

    def get_help(self):
        self.send_command('help')

    def send_move_command(self):
        try:
            mm = float(self.lineEdit.text())
            self.move_z(mm)
        except ValueError:
            self.label_2.setText("⚠️ Invalid move value.")
    





# 🖼️ Launching the App
if __name__ == "__main__":
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())

