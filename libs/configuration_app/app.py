from flask import Flask, render_template, request
import subprocess
import os
import time
from threading import Thread

app = Flask(__name__)
app.debug = True


@app.route('/')
def index():
    wifi_ap_array = scan_wifi_networks()
    info = ""
    return render_template('app.html', wifi_ap_array = wifi_ap_array, info=info)


@app.route('/manual_ssid_entry')
def manual_ssid_entry():
    return render_template('manual_ssid_entry.html')


@app.route('/save_credentials', methods = ['GET', 'POST'])
def save_credentials():
    ssid = request.form.get('ssid', None)
    wifi_key = request.form.get('wifi_key', None)
    api_url = request.form.get('api_url', None)
    ws_url = request.form.get('ws_url', None)
    auth_serial = request.form.get('auth_serial', None)
    auth_token = request.form.get('auth_secret', None)
    if if_empty(ssid, wifi_key, api_url, ws_url, auth_token, auth_serial):
        wifi_ap_array = scan_wifi_networks()
        info = "Some input fields where empty!"
        return render_template('app.html', wifi_ap_array=wifi_ap_array, info=info)
    checked = request.form.get('i2c_check', None)

    create_wpa_supplicant(ssid, wifi_key)
    if checked:
        i2c_address = request.form.get('lcd_address', None)
        if i2c_address:
            create_kit_config_with_lcd(api_url, ws_url, auth_serial, auth_token, i2c_address)
        else:
            wifi_ap_array = scan_wifi_networks()
            info = "If you checked the LCD screen, fill in the i2c address"
            return render_template('app.html', wifi_ap_array=wifi_ap_array, info=info)
    else:
        create_kit_config(api_url, ws_url, auth_serial, auth_token)

    # Call set_ap_client_mode() in a thread otherwise the reboot will prevent
    # the response from getting to the browser
    def sleep_and_start_ap():
        time.sleep(2)
        set_ap_client_mode()
    t = Thread(target=sleep_and_start_ap)
    t.start()

    return render_template('save_credentials.html', ssid = ssid)




######## FUNCTIONS ##########

def scan_wifi_networks():
    iwlist_raw = subprocess.Popen(['iwlist', 'scan'], stdout=subprocess.PIPE)
    ap_list, err = iwlist_raw.communicate()
    ap_array = []

    for line in ap_list.decode('utf-8').rsplit('\n'):
        if 'ESSID' in line:
            ap_ssid = line[27:-1]
            if ap_ssid != '':
                ap_array.append(ap_ssid)

    return ap_array

def create_wpa_supplicant(ssid, wifi_key):
    temp_conf_file = open('wpa_supplicant.conf.tmp', 'w')

    temp_conf_file.write('ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n')
    temp_conf_file.write('update_config=1\n')
    temp_conf_file.write('\n')
    temp_conf_file.write('network={\n')
    temp_conf_file.write('	ssid="' + ssid + '"\n')

    if wifi_key == '':
        temp_conf_file.write('	key_mgmt=NONE\n')
    else:
        temp_conf_file.write('	psk="' + wifi_key + '"\n')

    temp_conf_file.write('	}')

    temp_conf_file.close

    os.system('mv wpa_supplicant.conf.tmp /etc/wpa_supplicant/wpa_supplicant.conf')

def create_kit_config_with_lcd(api_url, ws_url, auth_serial, auth_token, i2c_address):
    kit_conf_file = open('kit_config.json.tmp', 'w')

    kit_conf_file.write('{\n')
    kit_conf_file.write('    "api": {\n')
    kit_conf_file.write('        "root": "' + api_url + '"\n')
    kit_conf_file.write('    },\n')
    kit_conf_file.write('    "websockets": {\n')
    kit_conf_file.write('        "url": "' + ws_url + '"\n')
    kit_conf_file.write('    },\n')
    kit_conf_file.write('    "auth": {\n')
    kit_conf_file.write('        "serial": "' + auth_serial + '",\n')
    kit_conf_file.write('        "secret": "' + auth_token + '"\n')
    kit_conf_file.write('    },\n')
    kit_conf_file.write('    "debug": {\n')
    kit_conf_file.write('        "level": "INFO",\n')
    kit_conf_file.write('        "peripheral_display": {\n')
    kit_conf_file.write('            "module_name": "astroplant_peripheral_device_library.lcd",\n')
    kit_conf_file.write('            "class_name": "LCD",\n')
    kit_conf_file.write('            "parameters": {\n')
    kit_conf_file.write('                "i2c_address": "'+i2c_address+'"\n')
    kit_conf_file.write('            }\n')
    kit_conf_file.write('        }\n')
    kit_conf_file.write('    }\n')
    kit_conf_file.write('}\n')
    kit_conf_file.close

    os.system('mv kit_config.json.tmp /home/pi/astroplant-kit/astroplant_kit/kit_config.json')
    os.system('(crontab -l 2>/home/pi/log_pigpiod.txt; echo \'@reboot sudo pigpiod\'; ) |  sort - | uniq - | crontab -')
    os.system('(crontab -u pi -l 2>/home/pi/logcron.txt; echo \'@reboot sleep 30; cd /home/pi/astroplant-kit/astroplant_kit && python3 core.py >> /home/pi/core.log \'; ) |  sort - | uniq - | crontab -u pi - -')

def create_kit_config(api_url, ws_url, auth_serial, auth_token):
    kit_conf_file = open('kit_config.json.tmp', 'w')

    kit_conf_file.write('{\n')
    kit_conf_file.write('    "api": {\n')
    kit_conf_file.write('        "root": "' + api_url + '"\n')
    kit_conf_file.write('    },\n')
    kit_conf_file.write('    "websockets": {\n')
    kit_conf_file.write('        "url": "' + ws_url + '"\n')
    kit_conf_file.write('    },\n')
    kit_conf_file.write('    "auth": {\n')
    kit_conf_file.write('        "serial": "' + auth_serial + '",\n')
    kit_conf_file.write('        "secret": "' + auth_token + '"\n')
    kit_conf_file.write('    },\n')
    kit_conf_file.write('    "debug": {\n')
    kit_conf_file.write('        "level": "INFO",\n')
    kit_conf_file.write('        "peripheral_display": {\n')
    kit_conf_file.write('            "module_name": "peripheral",\n')
    kit_conf_file.write('            "class_name": "BlackHoleDisplay"\n')
    kit_conf_file.write('        }\n')
    kit_conf_file.write('    }\n')
    kit_conf_file.write('}\n')
    kit_conf_file.close

    os.system('mv kit_config.json.tmp /home/pi/astroplant-kit/astroplant_kit/kit_config.json')
    os.system('(crontab -l 2>/home/pi/log_pigpiod.txt; echo \'@reboot sudo pigpiod\'; ) |  sort - | uniq - | crontab -')
    os.system('(crontab -u pi -l 2>/home/pi/logcron.txt; echo \'@reboot sleep 30; cd /home/pi/astroplant-kit/astroplant_kit && python3 core.py >> /home/pi/core.log \'; ) |  sort - | uniq - | crontab -u pi - -')

def if_empty(ssid, wifi_key, api_url,ws_url,auth_token,auth_serial):
    if ssid and wifi_key and api_url and ws_url and auth_token and auth_serial is not None:
        return False
    else:
        return True

def set_ap_client_mode():
    os.system('rm -f /etc/raspiwifi/host_mode')
    os.system('rm /etc/cron.raspiwifi/aphost_bootstrapper')
    os.system('cp /usr/lib/raspiwifi/reset_device/static_files/apclient_bootstrapper /etc/cron.raspiwifi/')
    os.system('chmod +x /etc/cron.raspiwifi/apclient_bootstrapper')
    os.system('mv /etc/dnsmasq.conf.original /etc/dnsmasq.conf')
    os.system('mv /etc/dhcpcd.conf.original /etc/dhcpcd.conf')
    os.system('cp /usr/lib/raspiwifi/reset_device/static_files/isc-dhcp-server.apclient /etc/default/isc-dhcp-server')
    os.system('reboot')

def config_file_hash():
    config_file = open('/etc/raspiwifi/raspiwifi.conf')

    config_hash = {}

    for line in config_file:
        line_key = line.split("=")[0]
        line_value = line.split("=")[1].rstrip()
        config_hash[line_key] = line_value

    return config_hash


if __name__ == '__main__':
    config_hash = config_file_hash()

    if config_hash['ssl_enabled'] == "1":
        app.run(host = '0.0.0.0', port = int(config_hash['server_port']), ssl_context='adhoc')
    else:
        app.run(host = '0.0.0.0', port = int(config_hash['server_port']))
