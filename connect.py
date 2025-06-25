# basic draw for wifi connection managing automatisation
# wifi config and connect file
import os
import subprocess
from flask import Flask, request, redirect
import time

def is_connected():
    result = subprocess.run(['iwgetid', '-r'], stdout=subprocess.PIPE)
    ssid = result.stdout.decode().strip()
    return bool(ssid)

def start_hotspot():
    subprocess.run(['sudo', 'systemctl', 'stop', 'wpa_supplicant.service'])
    subprocess.run(['sudo', 'systemctl', 'stop', 'dhcpcd.service'])
    subprocess.run(['sudo', 'systemctl', 'start', 'hostapd.service'])
    subprocess.run(['sudo', 'systemctl', 'start', 'dnsmasq.service'])


def connect():
    cred_path = '/home/pi/wificonf.fill'  # Or wherever you save the file

    if not os.path.exists(cred_path):
        print("Credential file not found.")
        return False

    ssid, password = None, None

    with open(cred_path, 'r') as f:
        for line in f:
            if line.startswith("SSID="):
                ssid = line.strip().split("=", 1)[1]
            elif line.startswith("PASSWORD="):
                password = line.strip().split("=", 1)[1]

    if not ssid or not password:
        print("Missing SSID or password in credential file.")
        return False

    try:
        # Apply credentials to wpa_supplicant
        with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'w') as f:
            f.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
            f.write("update_config=1\n")
            f.write("country=US\n\n")  # Replace with your region
            f.write("network={\n")
            f.write(f'    ssid="{ssid}"\n')
            f.write(f'    psk="{password}"\n')
            f.write("}\n")

        os.chmod('/etc/wpa_supplicant/wpa_supplicant.conf', 0o600)

        # Trigger connection attempt
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'reconfigure'])
        time.sleep(10)

        return is_connected()

    except Exception as e:
        print(f"Connection error: {e}")
        return False

app = Flask(__name__)

@app.route('/add', methods=['POST'])
def add_wifi():
    ssid = request.form.get('ssid', '').strip()
    password = request.form.get('password', '').strip()

    if ssid and password:
        try:
            # 1. Write config in wpa_supplicant format
            conf_path = '/etc/wpa_supplicant/wpa_supplicant.conf'
            with open(conf_path, 'w') as f:
                f.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
                f.write("update_config=1\n")
                f.write("country=US\n\n")  # Adjust your country code
                f.write("network={\n")
                f.write(f'    ssid="{ssid}"\n')
                f.write(f'    psk="{password}"\n')
                f.write("}\n")

            os.chmod(conf_path, 0o600)  # Secure the file

            # 2. Restart networking
            subprocess.run(['wpa_cli', '-i', 'wlan0', 'reconfigure'])

            # 3. Optional: Reboot to be extra safe
            subprocess.run(['sudo', 'reboot'])

        except Exception as e:
            return f"Error saving config: {e}", 500

        return redirect('/')
    else:
        return "SSID and password are required.", 400



if __name__ == '__main__':
    if not is_connected():
        success = connect()
        if not success:
            print("WiFi connection failed. Starting hotspot...")
            start_hotspot()
        else:
            print("Connected to WiFi.")
            app.run(host='0.0.0.0', port=8080)
    else:
        print("Already connected to WiFi.")
        app.run(host='0.0.0.0', port=8080)

