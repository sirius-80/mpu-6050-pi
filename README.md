# Robot
Building a smart robot using a raspberrypi and cheap components.

# Prerequisites
## For I2C (APDS-9960, MPU-6050)
sudo apt-get install i2c-tools python-smbus

## For scheduling tasks at fixed rate
pip3 install apscheduler

## For MQTT pub/sub
sudo apt-get install mosquitto
sudo apt-get install mosquitto-clients

## For wii-mote
sudo apt-get install bluetooth 
sudo apt-get install python-cwiid 
sudo apt-get install wminput 
sudo cat > /etc/udev/rules.d/wiimote.rules
KERNEL=="uinput", MODE="0666"
EOF
