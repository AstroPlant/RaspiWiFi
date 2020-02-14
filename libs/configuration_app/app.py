from flask import Flask, render_template, request
import subprocess
import os
import time
from threading import Thread
import fileinput

app = Flask(__name__)
app.debug = True


@app.route('/')
def index():
    wifi_ap_array = scan_wifi_networks()
    info = ""
    config_hash = config_file_hash()

    return render_template('app.html',
                           wifi_ap_array=wifi_ap_array,
                           config_hash=config_hash,
                           info=info)


@app.route('/manual_ssid_entry')
def manual_ssid_entry():
    return render_template('manual_ssid_entry.html')


@app.route('/enterprise_entry')
def enterprise_entry():
    return render_template('enterprise_entry.html')


@app.route('/wpa_settings')
def wpa_settings():
    config_hash = config_file_hash()
    return render_template('wpa_settings.html',
                           wpa_enabled=config_hash['wpa_enabled'],
                           wpa_key=config_hash['wpa_key'])


@app.route('/astroplant')
def astroplant():
    return render_template('astroplant.html')


@app.route('/save_credentials', methods=['GET', 'POST'])
def save_credentials():
    ssid = request.form.get('ssid', None)
    wifi_key = request.form.get('wifi_key', None)
    enterprise_id = request.form.get('identity', None)
    enterprise_pwd = request.form.get('password', None)
    enterprise_check = request.form.get('checker', None)

    if enterprise_check == "1":
        create_enterprise_wpa_supplicant(ssid, enterprise_id, enterprise_pwd)
    else:
        create_wpa_supplicant(ssid, wifi_key)

    return render_template('save_credentials.html', ssid=ssid)


@app.route('/save_astroplant', methods=['GET', 'POST'])
def save_astroplant():
    mqtt_host = request.form.get('mqtt_host', None)
    mqtt_port = request.form.get('mqtt_port', None)
    auth_serial = request.form.get('auth_serial', None)
    auth_secret = request.form.get('auth_secret', None)
    lcd_address = None
    lcd_connected = request.form.get('lcd_connected', None)
    if lcd_connected:
        lcd_address = request.form.get('lcd_address', None)
        if not lcd_address:
            info = "Please enter the I2C address of the LCD screen"
            return render_template('astroplant.html', info=info)
    create_kit_config(mqtt_host,
                      mqtt_port,
                      auth_serial,
                      auth_secret,
                      lcd_address=lcd_address)

    # Call set_ap_client_mode() in a thread otherwise the reboot will prevent
    # the response from getting to the browser
    def sleep_and_start_ap():
        time.sleep(2)
        set_ap_client_mode()

    t = Thread(target=sleep_and_start_ap)
    t.start()

    return render_template('completed.html')


@app.route('/save_wpa_credentials', methods=['GET', 'POST'])
def save_wpa_credentials():
    config_hash = config_file_hash()
    wpa_enabled = request.form.get('wpa_enabled')
    wpa_key = request.form['wpa_key']

    if str(wpa_enabled) == '1':
        update_wpa(1, wpa_key)
    else:
        update_wpa(0, wpa_key)

    def sleep_and_reboot_for_wpa():
        time.sleep(2)
        os.system('reboot')

    t = Thread(target=sleep_and_reboot_for_wpa)
    t.start()

    config_hash = config_file_hash()
    return render_template('save_wpa_credentials.html',
                           wpa_enabled=config_hash['wpa_enabled'],
                           wpa_key=config_hash['wpa_key'])


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

    temp_conf_file.write(
        'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n')
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

    os.system(
        'mv wpa_supplicant.conf.tmp /etc/wpa_supplicant/wpa_supplicant.conf')


def create_enterprise_wpa_supplicant(ssid, identity, password):
    temp_conf_file = open('wpa_supplicant.conf.tmp', 'w')

    temp_conf_file.write(
        'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n')
    temp_conf_file.write('update_config=1\n')
    temp_conf_file.write('\n')
    temp_conf_file.write('network={\n')
    temp_conf_file.write('	ssid="' + ssid + '"\n')
    temp_conf_file.write('	scan_ssid=1\n')
    temp_conf_file.write('	key_mgmt=WPA-EAP\n')
    temp_conf_file.write('	eap=PEAP\n')
    temp_conf_file.write('	identity="' + identity + '"\n')
    temp_conf_file.write('	password="' + password + '"\n')
    temp_conf_file.write('	phase1="peaplabel=0"\n')
    temp_conf_file.write('	phase2="auth=MSCHAPV2"\n')

    temp_conf_file.write('	}')

    temp_conf_file.close

    os.system(
        'mv wpa_supplicant.conf.tmp /etc/wpa_supplicant/wpa_supplicant.conf')


def create_kit_config(mqtt_host,
                      mqtt_port,
                      auth_serial,
                      auth_secret,
                      lcd_address=None):
    config = (f"[message_broker]\n"
              f"host = \"{mqtt_host}\"\n"
              f"port = {mqtt_port}\n"
              f"\n"
              f"[message_broker.auth]\n"
              f"serial = \"{auth_serial}\"\n"
              f"secret = \"{auth_secret}\"\n"
              f"\n"
              f"[debug]\n"
              f"level = \"INFO\"\n")
    if lcd_address is not None:
        config += (
            f"\n"
            f"[debug.peripheral_display]\n"
            f"module_name = \"astroplant_peripheral_device_library.lcd\"\n"
            f"class_name = \"LCD\"\n"
            f"\n"
            f"[debug.peripheral_display.configuration]\n"
            f"i2cAddress = \"{lcd_address}\"\n")
    with open('kit_config.toml.tmp', 'w') as kit_conf_file:
        kit_conf_file.write(config)

    os.system('chown pi:pi kit_config.toml.tmp')
    os.system('mv kit_config.toml.tmp /home/pi/kit_config.toml')


def set_ap_client_mode():
    os.system('rm -f /etc/raspiwifi/host_mode')
    os.system('rm /etc/cron.raspiwifi/aphost_bootstrapper')
    os.system(
        'cp /usr/lib/raspiwifi/reset_device/static_files/apclient_bootstrapper /etc/cron.raspiwifi/'
    )
    os.system('chmod +x /etc/cron.raspiwifi/apclient_bootstrapper')
    os.system('mv /etc/dnsmasq.conf.original /etc/dnsmasq.conf')
    os.system('mv /etc/dhcpcd.conf.original /etc/dhcpcd.conf')
    os.system('reboot')


def update_wpa(wpa_enabled, wpa_key):
    with fileinput.FileInput('/etc/raspiwifi/raspiwifi.conf',
                             inplace=True) as raspiwifi_conf:
        for line in raspiwifi_conf:
            if 'wpa_enabled=' in line:
                line_array = line.split('=')
                line_array[1] = wpa_enabled
                print(line_array[0] + '=' + str(line_array[1]))

            if 'wpa_key=' in line:
                line_array = line.split('=')
                line_array[1] = wpa_key
                print(line_array[0] + '=' + line_array[1])

            if 'wpa_enabled=' not in line and 'wpa_key=' not in line:
                print(line, end='')


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
        app.run(host='0.0.0.0',
                port=int(config_hash['server_port']),
                ssl_context='adhoc')
    else:
        app.run(host='0.0.0.0', port=int(config_hash['server_port']))
