RaspiWiFi

Forked from jasbur/RaspiWifi for setting up Wifi, AstroPlant credentials. To be used later for a dedicated AstroPlant image.

RaspiWiFi is a program to headlessly configure a Raspberry Pi's WiFi
connection using using any other WiFi-enabled device (much like the way
a Chromecast or similar device can be configured). RaspiWiFi has been
tested with the Raspberry Pi B+, Raspberry Pi 3, and Raspberry Pi Zero W.

DEPENDENCIES:
AstroPlant astroplant-kit, astroplant-api-python-client, 
astroplant-peripheral-device-library need to be installed. 
Current configuration expects astroplant-kit under /home/pi/.
A push button connected to GPIO7 (example:http://razzpisampler.oreilly.com/ch07.html).

KEY FILES ADJUSTED:
	- Configuration App/app/models/main.rb adjusted to create JSON file and crontab conf.
	- Configuration App/app/views/main/index.html.erb view adjusted to enter credentials.
	- Configuration App/app/controllers/main_controller.rb additional functions added.
	- /Reset Device/reset.py.template adjusted for cron job removal and GPIO 7 push button. 
	
 SCRIPT-BASED INSTALLATION INSTRUCTIONS:

== Navigate to the directory you downloaded or cloned RaspiWiFi

== Run:

sudo python3 initial_setup.py

== This script will install all necessary prerequisites, copy configuration
files, and reboot. When it finishes booting it should present itself in
"Configuration Mode" as a WiFi access point with the name "RaspiWiFi Setup".



USAGE:

== Connect to the "RaspiWiFi Setup" access point using any other WiFi enabled
device.

== Navigate to http://10.0.0.1:9191 using any web browser on the device you
connected with.

== Select the WiFi connection you'd like your Raspberry Pi to connect to from
the drop down list and enter its wireless password on the page provided. If no
encryption is enabled, leave the password box blank.

== Click the "Connect" button.

== At this point your Raspberry Pi will reboot and connect to the access point
specified.



RESETTING THE DEVICE:

== This install expects GPIO.input 7 to be 1 (default). If the button is pressed 
for 10 seconds (GPIO.input(7) == 0) or more the Raspberry Pi will reset all 
settings, reboot, and enter "Configuration Mode" again. Just press and hold for
10 seconds or longer. Before installing this package make sure a button is 
connected on GPIO7.

== You can also reset the device by running the manual_reset.py in the
"Reset Device" directory



