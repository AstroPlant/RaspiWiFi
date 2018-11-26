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

@app.route('/enterprise_entry')
def enterprise_entry():
    return render_template('enterprise_entry.html')

@app.route('/save_credentials', methods = ['GET', 'POST'])
def save_credentials():
    ssid = request.form.get('ssid', None)
    wifi_key = request.form.get('wifi_key', None)
    api_url = request.form.get('api_url', None)
    ws_url = request.form.get('ws_url', None)
    auth_serial = request.form.get('auth_serial', None)
    auth_token = request.form.get('auth_secret', None)
    enterprise_id = request.form.get('identity', None)
    enterprise_pwd = request.form.get('password', None)
    enterprise_check = request.form.get('checker', None)
    if enterprise_check == "1":
            create_enterprise_wpa_supplicant(ssid, enterprise_id, enterprise_pwd)
    else:
            create_wpa_supplicant(ssid, wifi_key)
    checked = request.form.get('i2c_check', None)
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

    return render_template('save_credentials.html', ssid = ssid)

@app.route('/actuator_control', methods = ['GET', 'POST'])
def actuator_control():
    act_chck = request.form.get('chkControl', None)
    if act_chck is not None:
        area = request.form.get('area', None)
        location = request.form.get('location', None)
        fans_gpio = request.form.get('fans_gpio', None)
        fans_time_on = request.form.get('fans_time_on', None)
        fans_time_off = request.form.get('fans_time_off', None)
        red_gpio = request.form.get('red_gpio', None)
        red_time_on = request.form.get('red_time_on', None)
        red_time_off = request.form.get('red_time_off', None)
        blue_gpio = request.form.get('blue_gpio', None)
        blue_time_on = request.form.get('blue_time_on', None)
        blue_time_off = request.form.get('blue_time_off', None)
        farred_gpio = request.form.get('farred_gpio', None)
        farred_time_on = request.form.get('farred_time_on', None)
        farred_time_off= request.form.get('farred_time_off', None)
        int_farred = request.form.get('int_farred', None)
        int_blue = request.form.get('int_blue', None)
        int_red = request.form.get('int_red', None)
        # quick (dirty) fix for the following
        if area == 'base' or location == 'Please choose from above' or area == '' or location == '':
            info = "You have to select the area and location."
            return render_template('save_credentials.html', info=info)
        if if_schedule_empty(fans_gpio,fans_time_on,fans_time_off,red_gpio,red_time_off,red_time_on,blue_gpio,
                             blue_time_off,blue_time_on,farred_gpio,farred_time_off,farred_time_on, int_blue, int_red,
                             int_farred):
            info = "You have to fill in all schedule details."
            return render_template('save_credentials.html', info=info)
        set_gpio_config(fans_gpio, red_gpio, blue_gpio, farred_gpio)
        # configure cron
        os.system('(crontab -u pi -l 2>/home/pi/logcron.txt; echo \'@reboot cd /home/pi/astrogeeks-actuator-control && ./controld \'; ) |  sort - | uniq - | crontab -u pi -')
        cron_time(fans_time_on, fans_time_off, "Fan", "1")
        cron_time(red_time_on, red_time_off, "Led.Red", int_red)
        cron_time(blue_time_on, blue_time_off, "Led.Blue", int_blue)
        cron_time(farred_time_on, farred_time_off, "Led.FarRed", int_farred)

        os.system('timedatectl set-timezone ' + location )

    # Call set_ap_client_mode() in a thread otherwise the reboot will prevent
    # the response from getting to the browser
    def sleep_and_start_ap():
        time.sleep(2)
        set_ap_client_mode()
    t = Thread(target=sleep_and_start_ap)
    t.start()
    return render_template('completed.html')

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

def create_enterprise_wpa_supplicant(ssid, identity, password):
    temp_conf_file = open('wpa_supplicant.conf.tmp', 'w')

    temp_conf_file.write('ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n')
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

def if_schedule_empty(fans_gpio,fans_time_on,fans_time_off,red_gpio,red_time_off,red_time_on,blue_gpio,
                             blue_time_off,blue_time_on,farred_gpio,farred_time_off,farred_time_on,int_blue, int_red,
                             int_farred):
    if fans_gpio and fans_time_on and fans_time_off and red_gpio and red_time_off and red_time_on and blue_gpio and \
            blue_time_off and blue_time_on and farred_gpio and farred_time_off and farred_time_on and int_blue and int_red and int_farred:
        return False
    else:
        return True

def set_gpio_config(fans_gpio, red_gpio, blue_gpio, farred_gpio):
    config = open('config.json.tmp', 'w')

    if fans_gpio == 'old':
        base_str = '    { "className": "Fan", "name": "Fan", "pin": 20 },\n' \
                   '    { "className": "Fan", "name": "Fan", "pin": 21 }\n'
    else:
        base_str = '     { "className": "Fan", "name": "Fan", "pin": '+fans_gpio+' }\n'
    config.write('{\n')
    config.write(' "actuators": [\n')
    config.write('     { "className": "Led", "name": "Led.Blue", "pin": '+blue_gpio+' },\n')
    config.write('     { "className": "Led", "name": "Led.Red", "pin": '+red_gpio+' },\n')
    config.write('     { "className": "Led", "name": "Led.FarRed", "pin": '+farred_gpio+' },\n')
    config.write(base_str)
    config.write(' ]\n')
    config.write('}')

    os.system('mv config.json.tmp /home/pi/astrogeeks-actuator-control/config.json')

def cron_time(on ,off, name, parameter):
    on = int(on.split(':', 1)[0])
    off = int(off.split(':', 1)[0])

    if on < off:
        if on  == off - 1:
            cmd_on = str(on)
        else:
            # for start time the "on" stays the same and "off" is -1
            cmd_on = str(on) + "-" + str(off-1)
        if on - 1 <= 0:
            if off != 23:
            # edge case
                cmd_off = str(off) + "-" + "23"
            else:
                cmd_off = str(off)
        else:
            # for stop time the "start to stop" is the same as original off and the "stop" is on -1
            cmd_off = str(off) + "-" + "23" + ",0" + "-" + str(on - 1)
    elif on > off:
        if off -1 == 0:
            #edge case
            cmd_on = str(on) + "-" + "23" + "," + str(off - 1)
        elif off -1 < 0:
            cmd_on = str(on)
        else:
            cmd_on = str(on) + "-" + "23" + ",0" + "-" + str(off -1)

        cmd_off = str(off) + "-" + str(on-1)
    else:
        # the start time is the same as stop time, the assumption is that it should run continuously
        cmd_on = str(on)
        cmd_off = None

    if cmd_off is not None:
        os.system('(crontab -u pi -l 2>/home/pi/logschedule.txt; echo \'* '+ cmd_on + ' * * * '
                  'cd /home/pi/astrogeeks-actuator-control && ./control "'+name+'" '+parameter+' \'; ) '
                  '|  sort - | uniq - | crontab -u pi - ')
        if name != "Fan":
            os.system('(crontab -u pi -l 2>/home/pi/logschedule.txt; echo \'* '+ cmd_off + ' * * * '
                      'cd /home/pi/astrogeeks-actuator-control && ./control "'+name+'" 0.0 \'; ) '
                      '|  sort - | uniq - | crontab -u pi - ')
        else:
            os.system('(crontab -u pi -l 2>/home/pi/logschedule.txt; echo \'* '+ cmd_off + ' * * * '
                      'cd /home/pi/astrogeeks-actuator-control && ./control "'+name+'" 0 \'; ) '
                      '|  sort - | uniq - | crontab -u pi - ')
    else:
        os.system('(crontab -u pi -l 2>/home/pi/logschedule.txt; echo \'* '+ cmd_on + ' * * * '
                  'cd /home/pi/astrogeeks-actuator-control && ./control "'+name+'" '+parameter+' \'; ) '
                  '|  sort - | uniq - | crontab -u pi - ')
    
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
