from machine import Pin
import utime
import sys
# 🔌 Pin configuration
MOTOR_IN1 = Pin(2, Pin.OUT)     # Step trigger
MOTOR_IN2 = Pin(3, Pin.OUT)     # Direction
HOME = Pin(4, Pin.IN, Pin.PULL_UP)  # Home position sensor (digital input)
UV_IN = Pin(5, Pin.OUT)
UV_IN.value(0)
# Global state
STEPS_PER_MM = 400  # Tune this based on your motor and lead screw - mine has 2 mm/rotation, with 1/4 microstepping (fast and smooth enough)
posi_z = 0
zero_home = None
print_mode = False  # Flag: True after initial zeroing when init zero used, currently just true unles you wanna print



def step_motor(steps):
    global posi_z, zero_home, print_mode

    if steps == 0:
        return

    direction = -1 if steps < 0 else 1

    MOTOR_IN2.value(1 if direction > 0 else 0)
    utime.sleep_us(10)
    # print(f"Direction: {'UP' if direction > 0 else 'DOWN'}")


    index = 0

    for _ in range(abs(steps)):
        MOTOR_IN1.value(1)
        utime.sleep(1e-3)
        MOTOR_IN1.value(0)
        utime.sleep(1e-3)

        index += 1
        posi_z += direction

# 📏 Move by millimeters
def move_z_axis(mm):
    step_motor(int(mm * STEPS_PER_MM))

# Homing routine
# def go_home():
#     global posi_z, zero_home
#     print("Homing...")
#     offset = step_motor(-300 * STEPS_PER_MM)
#     posi_z = 0

def uv_on():
    UV_IN.value(1)
    print("🔆 UV turned ON")

def uv_off():
    UV_IN.value(0)
    print("UV turned OFF")

# 📍 Set current position as software zero
def set_zero():
    global zero_home, posi_z
    zero_home = posi_z
    print(f"Zero point set at position: {posi_z}")

def usb_command_listener():
    global print_mode

    print("USB command listener active. Type 'help' for options.")
    while True:
        try:
            line = sys.stdin.readline().strip().lower()

            if line == "home":
                # go_home()
                pass
            elif line == "printmode":
                print_mode = True
                print("Print mode activated. Home sensor disabled for future moves.")
            elif line == "resetmode":
                print_mode = False
                print("Print mode deactivated. Home sensor logic restored.")
            elif line.startswith("move"):
                try:
                    # mm = float(line.split(" ")[1])
                    mm = float(line.split(" ")[1])
                    move_z_axis(mm)
                except Exception as e:
                    print("Invalid 'move' command. Usage: move 12.5")
            elif line == "uv_on":
                uv_on()
            elif line == "uv_off":
                uv_off()

            elif line == "zero":
#                 set_zero()
#                 print("Zero point set.")
                pass
            elif line == "pos":
                print(f"Current Z position: {posi_z}")
            elif line == "exit":
                print("Exiting USB listener.")
                break
            elif line == "help":
                print("Commands: move <mm>, home, zero, pos, uv_on, uv_off, printmode, resetmode, help, exit")
            else:
                print("Unknown command. Type 'help'.")

        except KeyboardInterrupt:
            print("\nInterrupted.\n")
            break

def load_zero_offset():
    global zero_home, print_mode
    try:
        with open("home.posiz", "r", encoding="utf-8") as f:
            zero_home = int(f.read().strip())
            print_mode = True
            print(f"Loaded saved zero offset: {zero_home}. Print mode enabled.")
    except Exception:
        print("No saved offset found. Machine not calibrated.")
        zero_home = None
        print_mode = False
load_zero_offset()
usb_command_listener()
'''
yeah - additional, currently not used, but will be further refined
        # Auto-zeroing logic
#         if not HOME.value() and direction < 0 and not print_mode:
#             print(" HOME triggered during initial zeroing.")
#             MOTOR_IN1.value(0)
#             utime.sleep(0.002)
# 
#             print("Continuing slowly to zero position...")
#             while HOME.value():  # While still not fully at home
#                 MOTOR_IN1.value(1)
#                 utime.sleep(1e-3)
#                 MOTOR_IN1.value(0)
#                 utime.sleep(1e-3)
#                 index += 1
#                 posi_z -= 1
# 
#             zero_home = -index
#             posi_z = 0
#             print_mode = True
#             print(f"Zero reached. Offset: {zero_home}. Entering print mode.")
#             return zero_home
'''
