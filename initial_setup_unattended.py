import setup_lib

if __name__ == "__main__":
    ssid = "AstroPlant Setup"
    wpa_enabled = "N" 
    wpa_entered_key = "NO PASSWORD"
    auto_config = "N"
    auto_config_delay = "300"
    server_port = "80"
    ssl_enabled = "N"

    setup_lib.install_prereqs()
    setup_lib.copy_configs(wpa_enabled)
    setup_lib.update_main_config_file(ssid, auto_config, auto_config_delay, ssl_enabled, server_port, wpa_enabled, wpa_entered_key)
