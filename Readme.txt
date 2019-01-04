RaspiWiFi

Forked from jasbur/RaspiWifi for setting up Wifi, AstroPlant credentials. To be used for a dedicated AstroPlant image.

NOTES:
    - This is a modified RaspiWifi version for pilot users of AstroPlant. At this point the implementation is not generic for actuator control.
      Future developments will be focused on cloud support for actuator control for arbitrary GPIO pins. Hence this fork is only of temporary nature.
    - If you wish to use the standard RaspiWifi only for internet configurations, please use the master branch.


DEPENDENCIES:
	- AstroPlant astroplant-kit, astroplant-api-python-client,
	  astroplant-peripheral-device-library need to be installed.
	- Optionally astrogeeks-actuator-control for actuator control
	- Current configuration expects all astroplant libraries under /home/pi/.
	- A push button connected to GPIO7 (example:http://razzpisampler.oreilly.com/ch07.html).
	- A push button connected to GPIO6
	- pigpio library (sudo apt-get install pigpio python-pigpio python3-pigpio)
	- cryptography packages (sudo apt-get install build-essential libssl-dev libffi-dev python3-dev)
	- pyopenssl (pip3 install pyopenssl)

RaspiWifi can also be used as a method to connect wirelessly point-to-point with your
Pi when a network is not available or you do not want to connect to one. Just
leave it in Configuration Mode, connect to the "RaspiWiFi[xxxx] Setup" access
point. The Pi will be addressable at 10.0.0.1 or astroplantsetup.com using all the normal methods you
might use while connected through a network.

RaspiWiFi has been
tested with the Raspberry Pi B+, Raspberry Pi 3, and Raspberry Pi Zero W.


SCRIPT-BASED INSTALLATION INSTRUCTIONS:

== Navigate to the directory where you downloaded or cloned RaspiWiFi

== Run:

sudo python3 initial_setup.py

== This script will install all necessary prerequisites and copy all necessary
config and library files, then reboot. When it finishes booting it should
present itself in "Configuration Mode" as a WiFi access point with the
name "AstroPlant[xxxx] Setup".

== The original RaspiWiFi directory that you ran the Initial Setup is no longer
needed after installation and can be safely deleted. All necessary files are
copied to /usr/lib/raspiwifi/ on setup.


CONFIGURATION:

== You will be prompted to set 3 variables during the Initial Setup Script:

==== "SSID Prefix" [default: "RaspiWiFi Setup"]: This is the prefix of the SSID
      that your Pi will broadcast for you to connect to during
      Configuration Mode (Host Mode). The last four of you Pi's serial number
      will be appended to whatever you enter here.

==== "Auto-Config mode" [default: n]: If you choose to enable this mode your Pi
      will check for an active connection while in normal operation mode (Client Mode).
      If an active connection has been determined to be lost, the Pi will reboot
      back into Configuration Mode (Host Mode) automatically.

==== "Auto-Config delay" [default: 300 seconds]: This is the time in consecutive
      seconds to wait with an inactive connection before triggering a reset into
      Configuration Mode (Host Mode). This is only applicable if the
      "Auto-Config mode" mentioned above is set to active.

==== "Server port" [default: 80]: This is the server port that the web server
      hosting the Configuration App page will be listening on. If you change
      this port make sure to add it to the end of the address when you're
      connecting to it. For example, if you speficiy 12345 as the port number
      you would navigate to the page like this: http://10.0.0.1:12345 If you
      leave the port at the default setting [80] there is no need to specify the
      port when navigating to the page.

==== "SSL Mode" [default: n]: With this option enabled your RaspiWifi
      configuration page will be sent over an SSL encrypted connection (don't
      forget the "s" when navigating to https://10.0.0.1:9191 when using
      this mode). You will get a certificate error from your web browser when
      connecting. The error is just a warning that the certificate has not been
      verified by a third party but everything will be properly encrypted anyway.

== All of these variables can be set at any time after the Initial Setup has
been running by editing the /etc/raspiwifi/raspiwifi.conf


USAGE:

== Connect to the "RaspiWiFi[xxxx] Setup" access point using any other WiFi enabled
device.

== Navigate to [10.0.0.1], [raspiwifisetup.com], or
[astroplantwifisetup.com] using any web browser on the device you
connected with. (don't forget to manually start with [https://] when using SSL mode)

== Select the WiFi connection you'd like your Raspberry Pi to connect to from
the drop down list and enter its wireless password on the page provided. If no
encryption is enabled, leave the password box blank. You may also manually
specify your network information by clicking on the "manual SSID entry ->" link.

== Click the "Connect" button.

== At this point your Raspberry Pi will reboot and connect to the access point
specified.

== You can also use the Pi in a point-to-point connection mode by leaving it in
Configuration Mode. All services will be addresible in their normal way at
10.0.0.1 while connected to the "AstroPlant[xxxx] Setup" AP.



RESETTING THE DEVICE:

== This install expects GPIO.input 7 to be 1 when the RPI is running, when the button
is pressed the GPIO.input 7 will be 0. If the button is 
pressed for 10 seconds or more the Raspberry Pi will reset all 
settings, reboot, and enter "Configuration Mode" again. Just press and hold for
10 seconds or longer. Before installing this package make sure a button is 
connected on GPIO7.

== You can also reset the device by running the manual_reset.py in the "Reset Device" directory
/usr/lib/raspiwifi/reset_device directory as root or with sudo.

