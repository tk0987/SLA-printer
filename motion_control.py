#====================++++++++++++++++++++++++++++++++++==========================
#                      basic sketch. do not copy without brain
#
#====================++++++++++++++++++++++++++++++++++==========================
from flask import Flask, render_template, request, redirect
import os
import RPi.GPIO as GPIO
from time import sleep

app = Flask(__name__)
#====================++++++++++++++++++++++++++++++++++==========================
#
#                            gpios - to change
#
#====================++++++++++++++++++++++++++++++++++==========================
GPIO.setmode(GPIO.BCM)
MOTOR_IN1 = 17  # Step pin
MOTOR_IN2 = 18  # Direction pin
GPIO.setup(MOTOR_IN1, GPIO.OUT)
GPIO.setup(MOTOR_IN2, GPIO.OUT)
#====================++++++++++++++++++++++++++++++++++==========================
#
#                            steps/mm, frequency
#
#====================++++++++++++++++++++++++++++++++++==========================
STEPS_PER_MM = 100  # Adjust this for your motor and leadscrew
STEP_DELAY = 0.05  # Seconds between steps
#====================++++++++++++++++++++++++++++++++++==========================
#
#                            motion - to add autoencoder from driver
#
#====================++++++++++++++++++++++++++++++++++==========================
def step_motor(steps):
    direction = GPIO.HIGH if steps > 0 else GPIO.LOW
    GPIO.output(MOTOR_IN2, direction)
    for _ in range(abs(steps)):
        GPIO.output(MOTOR_IN1, GPIO.HIGH)
        sleep(STEP_DELAY)
        GPIO.output(MOTOR_IN1, GPIO.LOW)
        sleep(STEP_DELAY)

def move_z_axis(mm):
    steps = int(mm * STEPS_PER_MM)
    step_motor(steps)

def go_home():
    print("Executing homing routine...")
    # Replace with limit switch logic if available
    step_motor(-200)

def set_zero():
    print("Zero point set. (In real hardware, store position in variable or file.)")
#====================++++++++++++++++++++++++++++++++++==========================
#
#                            flask
#
#====================++++++++++++++++++++++++++++++++++==========================
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
#====================++++++++++++++++++++++++++++++++++==========================
#
#                            run
#
#====================++++++++++++++++++++++++++++++++++==========================
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=80)
    finally:
        GPIO.cleanup()
