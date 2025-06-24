from flask import Flask, render_template, request, redirect
import os
import RPi.GPIO as GPIO
from time import sleep
global posi_z
posi_z=0
app = Flask(__name__)
global zero_home

f=open("global_zero.zero","r+",encoding="utf-8")
zero_home=int(f.readline())
# ----- GPIO Setup -----
GPIO.setmode(GPIO.BCM)
MOTOR_IN1 = 23  # Step pin
MOTOR_IN2 = 24  # Direction pin
GPIO.setup(MOTOR_IN1, GPIO.OUT)
GPIO.setup(MOTOR_IN2, GPIO.OUT)
door_in=5
home=6
GPIO.setup(door_in, GPIO.IN)
GPIO.setup(home, GPIO.IN)
# Constants
STEPS_PER_MM = 100  # Adjust this for your motor and leadscrew
# STEP_DELAY = 0.05  # Seconds between steps

# ----- Movement Functions -----
def accel(steps,index):
    x0=steps//2
    
    delay=10*(index-x0)**2/1000 + 0.025 # in ms
    return delay
    
    
def step_motor(steps):
    global zero_home
    global posi_z
    direction = GPIO.HIGH if steps > 0 else GPIO.LOW
    GPIO.output(MOTOR_IN2, direction)
    index=0
    for _ in range(abs(steps)):
        if GPIO.input(home)>0:
            if zero_home:
                for _ in range(zero_home):
                    GPIO.output(MOTOR_IN1, GPIO.HIGH)
                    sleep(0.1)
                    GPIO.output(MOTOR_IN1, GPIO.LOW)
                    sleep(0.1)
            posi_z=0
            break
        if posi_z>=245:
            break  
                
        GPIO.output(MOTOR_IN1, GPIO.HIGH)
        delay=accel(steps=steps,index=index)
        sleep(delay)
        GPIO.output(MOTOR_IN1, GPIO.LOW)
        delay=accel(steps=steps,index=index)
        sleep(delay)
        index+=1
    posi_z+=steps

def move_z_axis(mm):
    steps = int(mm * STEPS_PER_MM)
    step_motor(steps)

def go_home():
    global posi_z
    print("Executing homing routine...")
    # Replace with limit switch logic if available
    # while GPIO.input(home)<=0:
    step_motor(-300*STEPS_PER_MM)
    posi_z=0

def set_zero():
    global posi_z
    global zero_home
    zero_home=posi_z
    
    
        

# ----- Flask Routes -----
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/move', methods=['POST'])
def move():
    direction = request.form.get('direction')
    try:
        mm = int(request.form.get('z_steps', 0))
    except ValueError:
        mm = 0

    if direction == 'up':
        move_z_axis(abs(mm))
    elif direction == 'down':
        move_z_axis(-abs(mm))
    elif direction == 'home':
        go_home()
    elif direction == 'set_zero':
        set_zero()

    return redirect('/')

# ----- Run the app -----
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=8080)
    finally:
        GPIO.cleanup()
