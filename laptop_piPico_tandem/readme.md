So - as in dir name - I'm building currently SLA printer on my oldest laptop.

Yeah, my oldest laptop. I wrote bachelor on it, commuting in buses and trams. This Monte Carlo simulation was badass, but data processing and visualization even better... Ah. Now this thing has honor to serve as working 3D SLA printer.
  
    # ====================================++++++++++++++++++++++++++++++++++++++===================================
  
    #                                                   Hardware
  
    # ====================================++++++++++++++++++++++++++++++++++++++===================================
OK. To construct such a printer software provided is not enough - you have to carefully dismantle the LCD laptop have.
You will need to take off all display back, optics inside, as well as led lights. Then you will need to secure pixel matrix - I used original display frame (aluminium, as I believe), some sponges to keep distance between matrix and frame, some glue - I used both T-7000 and B-7000 - to keep it in place, and some tape for securing matrix edges.

I did it carefully, and everything is OK. And if I did it, then everybody can.

When you have display LCD matrix, then you 'll need a case for it. Mine is not ready yet, I'm printing using Anycubic Photon Mono X 6k case. When building, consider adding normal light for debugging - LCD still works, as well as laptop, but without light coding on it would be difficult.

You 'll need also stepper motor, proper controller for it, raspberry pi pico and usb cable.

    # ====================================++++++++++++++++++++++++++++++++++++++===================================
  
    #                                            Software (this repo)
  
    # ====================================++++++++++++++++++++++++++++++++++++++===================================

A machine uPython code is provided - here for rpi pico. But the laptop does the most important things - serving web page over your wifi.
Main app serves a web page using FastAPI (basic control only - for now). When connected to the router, everybody in network can access the printer, everybody can control it - unless it is in printmode.

Ah, printmode. Screen control is realized using tkinter - the code runs just a single windowed app, with only one label - the image to print. 

After you make the printer and add this code to autostart consider small change using printmode code - when the service starts, it should turn screen black. I didn't do it because it is still in debugging phase - I simply add resin later.

Along with those two parts, I provide here (./templates directory) an index.html webpage, designed for controlling whole stuff. Yes, it could be more shiny, I believe - and maybe it will be someday.

Currently I'm glad it works, and I prefer simplicity and practicality over fashion and shiny things.

    # ====================================++++++++++++++++++++++++++++++++++++++===================================
  
    #                                            Future of this project
  
    # ====================================++++++++++++++++++++++++++++++++++++++===================================

I think, as it is a laptop, that it can be also a sftp server, like private & free cloud. Why not? Those HDD >1 TB drives are quite cheap now.

Even currently this /upload part of main laptop app can be used for sending things over WiFi using different devices - via python (like pydroid or termux on android) or maybe even binaries.

Also, index.html will be quite a more shiny, and zeroing (+ homing) will be added, with uPython code refined. Currently I found it unnecessary, as I need to keep an eye on this printer anyway.
