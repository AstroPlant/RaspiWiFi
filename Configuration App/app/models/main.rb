
class Main < ActiveRecord::Base

	def self.scan_wifi_networks
    ap_list = %x{sudo iwlist scan}.split('Cell')
    ap_array = Array.new

    ap_list.each{|ap_grouping|
        ap_hash = Hash.new
        encryption_found = false
        ssid = ''
        encryption_type = ''

        ap_grouping.split("\n").each{|line|
          if line.include?('ESSID')
              ssid = line[27..-2]
          end

          if line.include?('WEP')
              encryption_found = true
              encryption_type = 'wep'
          elsif line.include?('WPA Version 1')
              encryption_found = true
              encryption_type = 'WPA'
          elsif line.include?('IEEE 802.11i/WPA2')
              encryption_found = true
              encryption_type = 'WPA2'
          end
        }

        if encryption_found == false
          encryption_type = 'open'
        end

        unless ssid == ''
          ap_hash = {:ssid => ssid, :encryption_type => encryption_type}
          ap_array << ap_hash
        end
    }

    ap_array
	end

	def self.get_current_config_values
    current_values = Array.new

    if File.exist?('/etc/wpa_supplicant/wpa_supplicant.conf')
      wpa_supplicant_file = File.open('/etc/wpa_supplicant/wpa_supplicant.conf', 'r')

      wpa_supplicant_file.each{|line|
        if line.include?('ssid=')
            current_values << line.split('=')[1].chomp[1..-2]
        elsif line.include?('psk=')
            current_values << line.split('=')[1].chomp[1..-2]
        end
      }

      wpa_supplicant_file.close
    else
      current_values << ''
    end

    current_values
	end

  def self.create_wpa_supplicant(user_ssid, encryption_type, user_wifi_key)
		temp_conf_file = File.new('../tmp/wpa_supplicant.conf.tmp', 'w')
                 
    if encryption_type == 'WPA2'
      temp_conf_file.puts 'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev'
      temp_conf_file.puts 'update_config=1'
      temp_conf_file.puts
      temp_conf_file.puts 'network={'
      temp_conf_file.puts '	ssid="' + user_ssid + '"'
      temp_conf_file.puts '	psk="' + user_wifi_key + '"'
      temp_conf_file.puts '	proto=WPA2'
      temp_conf_file.puts '	key_mgmt=WPA-PSK'
      temp_conf_file.puts '}'
    elsif encryption_type == 'WPA'
      temp_conf_file.puts 'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev'
      temp_conf_file.puts 'update_config=1'
      temp_conf_file.puts
      temp_conf_file.puts 'network={'
      temp_conf_file.puts '	ssid="' + user_ssid + '"'
      temp_conf_file.puts '	proto=WPA RSN'
      temp_conf_file.puts '	key_mgmt=WPA-PSK'
      temp_conf_file.puts '	psk="' + user_wifi_key + '"'
      temp_conf_file.puts '}'
    elsif encryption_type == 'open'
	  temp_conf_file.puts 'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev'
      temp_conf_file.puts 'update_config=1'
      temp_conf_file.puts
      temp_conf_file.puts 'network={'
      temp_conf_file.puts '	ssid="' + user_ssid + '"'
      temp_conf_file.puts '}'
    end

		temp_conf_file.close
              
		system('sudo cp -r ../tmp/wpa_supplicant.conf.tmp /etc/wpa_supplicant/wpa_supplicant.conf')
              
		system('rm ../tmp/wpa_supplicant.conf.tmp')


	end

  def self.create_astroplant_config(user_api_url, user_ws_url, user_auth_serial ,user_auth_secret)
		kit_temp_conf_file = File.new('/home/pi/astroplant-kit/astroplant_kit/kit_config.json', 'w')

    
    kit_temp_conf_file.puts '{'
    kit_temp_conf_file.puts '    "api": {'
    kit_temp_conf_file.puts '        "root": "'+user_api_url+'"'
    kit_temp_conf_file.puts '    },'
    kit_temp_conf_file.puts '    "websockets": {'
    kit_temp_conf_file.puts '        "url": "'+user_ws_url+'"'
    kit_temp_conf_file.puts '    },'
    kit_temp_conf_file.puts '    "auth": {'
    kit_temp_conf_file.puts '        "serial": "'+user_auth_serial+'",'
    kit_temp_conf_file.puts '        "secret": "'+user_auth_secret+'"'
    kit_temp_conf_file.puts '    },'
    kit_temp_conf_file.puts '    "debug": {'
    kit_temp_conf_file.puts '        "level": "INFO",'
    kit_temp_conf_file.puts '        "peripheral_display": {'
    kit_temp_conf_file.puts '            "module_name": "peripheral",'
    kit_temp_conf_file.puts '            "class_name": "BlackHoleDisplay",'
    kit_temp_conf_file.puts '        }'
    kit_temp_conf_file.puts '    }'
    kit_temp_conf_file.puts '}'
		

		kit_temp_conf_file.close
		system('(crontab -l 2>/home/pi/log_pigpiod.txt; echo \'@reboot sudo pigpiod\'; ) |  sort - | uniq - | crontab -')
		system('(crontab -u pi -l 2>/home/pi/logcron.txt; echo \'@reboot sleep 30; cd /home/pi/astroplant-kit/astroplant_kit && python3 core.py >> /home/pi/core.log \'; ) |  sort - | uniq - | crontab -u pi - -')
	
	end


  def self.set_ap_client_mode
	raspiwifi_path = find_raspiwifi_path()
	lsb_release_string = %x{lsb_release -a}
	
	if lsb_release_string.include?('jessie')
		system ('sudo cp -r ' + raspiwifi_path + '/Reset\ Device/static_files/interfaces.apclient /etc/network/interfaces')
	elsif lsb_release_string.include?('stretch')
		system ('sudo rm /etc/network/interfaces')
	end
	
    system ('rm /etc/cron.raspiwifi/aphost_bootstrapper')
    system ('sudo cp -r ' + raspiwifi_path + '/Reset\ Device/static_files/apclient_bootstrapper /etc/cron.raspiwifi/')
    system ('sudo cp -r ' + raspiwifi_path + '/Reset\ Device/static_files/isc-dhcp-server.apclient /etc/default/isc-dhcp-server')
    system ('sudo reboot')
  end

  def self.reset_all
    raspiwifi_path = find_raspiwifi_path()
    
    system ('sudo rm -f /etc/wpa_supplicant/wpa_supplicant.conf')
    system ('rm -f ' + raspiwifi_path + '/tmp/*')
    system ('sudo cp -r ' + raspiwifi_path + '/Reset\ Device/static_files/interfaces.aphost /etc/network/interfaces')
    system ('sudo cp -r ' + raspiwifi_path + '/Reset\ Device/static_files/rc.local.aphost /etc/rc.local')
    system ('sudo reboot')
  end
  
  def self.find_raspiwifi_path
	raspiwifi_path = File.dirname(__FILE__)[0..-30]
	
	raspiwifi_path
  end

end
