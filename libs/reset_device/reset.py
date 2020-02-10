import RPi.GPIO as GPIO
import os
import time
import subprocess
import reset_lib

GPIO.setmode(GPIO.BCM)
GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP)

counter = 0
serial_last_four = subprocess.check_output(['cat', '/proc/cpuinfo'])[-5:-1].decode('utf-8')
config_hash = reset_lib.config_file_hash()
ssid_prefix = config_hash['ssid_prefix'] + " "
reboot_required = False


reboot_required = reset_lib.wpa_check_activate(config_hash['wpa_enabled'], config_hash['wpa_key'])

reboot_required = reset_lib.update_ssid(ssid_prefix, serial_last_four)

if reboot_required == True:
    os.system('reboot')

# This is the main logic loop waiting for a button to be pressed on GPIO 7 for 10 seconds.
# If that happens the device will reset to its AP Host mode allowing for reconfiguration on a new network.
while True:
    while GPIO.input(7) == 0:
        time.sleep(1)
        counter = counter + 1

        print(counter)

        if counter == 9:
            reset_lib.reset_to_host_mode()

        if GPIO.input(7) == 1:
            counter = 0
            break

    time.sleep(1)
# if gpio 6 button is pressed shutdown the AP kit
    while GPIO.input(6) == 0:
        time.sleep(1)
        counter = counter + 1

        print(counter)

        if counter == 9:
            os.system('shutdown')

        if GPIO.input(6) == 1:
            counter = 0
            break

    time.sleep(1)
