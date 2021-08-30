from machine import UART
import network
import time
from UartDsmrMqtt import UartDsmrMqtt


uart0 = UART(0)
uart0.init(baudrate=115200, bits=8, parity=None, stop=1, rxbuf=4096)
uart1 = UART(1)
uart1.init(baudrate=115200, bits=8, parity=None, stop=1)

uos.dupterm(None, 1)
uos.dupterm(uart1, 1)

#
# Main app configuration
#
# if ["uart"]["enabled"] is True, then uos.dupterm(None, 1) is set
#
# lastObis: The obis code which should be processed. Any other line after this line
# will be still read (readline), but ignored
#
configuration = {
    "server": "192.168.222.61",
    "port": 1883,
    "user": "MQTT USER HERE",
    "password": "MQTT USER PASSWORD HERE",
    "baseTopic": "home/basement/smartmeter",
    "lastObis": "1-0:8.7.0"
}
udm = UartDsmrMqtt(configuration)


#
# Connect to WIFI
#
sta_if = network.WLAN(network.STA_IF)
ap_if = network.WLAN(network.AP_IF)
sta_if.scan()
sta_if.connect("SSID HERE", "WIFI PASS HERE")
while (not sta_if.isconnected()):
    print("Connecting... " + str(sta_if.ifconfig()))
    time.sleep(1)
ap_if.active(False)
sta_if.active(True)
print("ifconfig: " + str(sta_if.ifconfig()))

print("sleep for 5 sec")
time.sleep(5)

#
# RUN MAIN LOOP
#
print("Running UartDsmrMqtt loop")
udm.loop()




