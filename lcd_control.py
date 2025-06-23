# =======================++++++++++++++++++================
# 
#                           SLA printer preview code
#                                  lcd handling sketch
# 
# =======================++++++++++++++++++================


import os
import json
import time
from tkinter import Tk, Label
from PIL import Image, ImageTk
# =======================++++++++++++++++++================
# 
#                           config read, param extraction
# 
# =======================++++++++++++++++++================
path = "/home/tk/Desktop/slicer/Unnamed-Sphere"

# Load config parameters
with open(os.path.join(path, 'config.json'), 'r') as file:
    config = json.load(file)

expTime = config.get("expTime", 1)
expTimeFirst = config.get("expTimeFirst", expTime)
layerHeight = config.get("layerHeight", 0.05)
delay_before = config.get("delay_before_exposure_ms", 0) / 1000.0
delay_after = config.get("delay_after_exposure_ms", 0) / 1000.0
# =======================++++++++++++++++++================
# 
#                           images and display
# 
# =======================++++++++++++++++++================
image_files = sorted([f for f in os.listdir(path) if f.endswith('.png')])

root = Tk()
root.attributes('-fullscreen', True)
root.configure(background='black')
label = Label(root, bg='black')
label.pack(expand=False)


def exit_fullscreen(event):
    root.attributes('-fullscreen', False)
root.bind("<Escape>", exit_fullscreen)

# =======================++++++++++++++++++================
# 
#                           main loop
# 
# =======================++++++++++++++++++================
# Track current state
state = {"index": 0, "show_black": False}

def show_images():
    # If all layers are done, exit
    if state["index"] >= len(image_files):
        root.destroy()
        return

    if state["show_black"]:
        # Display black screen
        label.config(image='', bg='black')
        label.image = None
        state["show_black"] = False
        # Wait 10 seconds before next layer
        root.after(10000, show_images)
    else:
        # Show image
        img_path = os.path.join(path, image_files[state["index"]])
        img = Image.open(img_path).rotate(90, expand=False)
        photo = ImageTk.PhotoImage(img)
        label.config(image=photo, bg='black')
        label.image = photo

        current_exp = expTimeFirst if state["index"] == 0 else expTime
        total_delay = int((delay_before + current_exp + delay_after) * 1000)

        state["show_black"] = True
        state["index"] += 1
        root.after(total_delay, show_images)

# =======================++++++++++++++++++================
# 
#                           exe
# 
# =======================++++++++++++++++++================
show_images()
root.mainloop()
