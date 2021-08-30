from machine import UART
import uasyncio as asyncio
from queue import Queue
from mqtt_as import MQTTClient
from mqtt_as import config as mqttConfigDefault
import ure
import uos
import time

class UartDsmrMqtt:

    # Mqtt default config
    _mqttClient = object()
    _baseTopic = "na"

    #
    # Queue: Adjust your queue size if needed
    # Sanxing smart meter sends burst of data every 10sec
    # That filtered data should fit into this queue
    # A good size is: ((obisItems * 2) + 3)
    # Items will be removed from this queue by "task_queueToMqtt()"
    #
    _q = Queue(100)

    #
    # We use regular expressions to parse the raw data,
    # from UART, "task_fakeDataToQueue()" and in "task_queueToMqtt()" too
    #
    _regexObisValue = ure.compile('(^\d+-\d+:(?:[0-9]|[0-8][0-9])\.\d+\.\d+)\((\S+)\)')
    _regex_float = ure.compile('^(\d+\.\d+)$')
    _regex_floatUnit = ure.compile('^(\d+\.\d+)\*\w+$')
    _regex_integerUnit = ure.compile('^(\d+)\*\w+$')

    # The last obis id which will be processed.
    # Anything after this obis will be ignored
    _lastObis = ""

    #
    # Constructor
    # Override MQTTClient default config options and set mqtt baseTopic
    #
    def __init__(self, cfg):

        # MQTT Client config override
        mcfg = mqttConfigDefault
        mcfg["clean"] = True
        mcfg["server"] = cfg["server"]
        mcfg["port"] = cfg["port"]
        mcfg["user"] = cfg["user"]
        mcfg["password"] = cfg["password"]

        # Instantiate MQTTClient
        self._mqttClient = MQTTClient(mcfg)
        self._baseTopic = cfg["baseTopic"]
        
        # The last obis id which will be processed.
        # Anything after this obis will be ignored
        self._lastObis = cfg["lastObis"]



    #
    # Generate 1 burst of fake data, every 5 seconds
    # This way you can still have your REPL attached to UART0 so you can debug code (dupterm)
    # Notice, these are "bytestrings"
    #
    #async def task_fakeDataToQueue(self):
    #    fakeData = [
    #        b'1-0:1.8.0(001682.364*kWh)',
    #        b'1-0:1.8.1(000606.248*kWh)',
    #        b'1-0:1.8.2(001076.116*kWh)',
    #        b'1-0:1.8.3(000000.000*kWh)',
    #        b'1-0:1.8.4(000000.000*kWh)',
    #        b'1-0:2.8.0(007766.555*kWh)',
    #        b'1-0:2.8.1(005411.785*kWh)',
    #        b'1-0:2.8.2(002354.770*kWh)',
    #        b'1-0:2.8.3(000000.000*kWh)',
    #        b'1-0:2.8.4(000000.000*kWh)',
    #        b'1-0:3.8.0(000706.322*kvarh)',
    #        b'1-0:4.8.0(000949.300*kvarh)',
    #        b'1-0:5.8.0(000376.335*kvarh)',
    #        b'1-0:6.8.0(000329.987*kvarh)',
    #        b'1-0:7.8.0(000396.286*kvarh)',
    #        b'1-0:8.8.0(000553.014*kvarh)',
    #        b'1-0:15.8.0(009448.932*kWh)',
    #        b'1-0:32.7.0(240.2*V)',
    #        b'1-0:52.7.0(239.5*V)',
    #        b'1-0:72.7.0(241.4*V)',
    #        b'1-0:31.7.0(001*A)',
    #        b'1-0:51.7.0(000*A)',
    #        b'1-0:71.7.0(000*A)',
    #        b'1-0:13.7.0(0.993)',
    #        b'1-0:33.7.0(0.998)',
    #        b'1-0:53.7.0(0.827)',
    #        b'1-0:73.7.0(0.660)',
    #        b'1-0:14.7.0(49.99*Hz)',
    #        b'1-0:1.7.0(00.565*kW)',
    #        b'1-0:2.7.0(00.000*kW)',
    #        b'1-0:5.7.0(00.170*kvar)',
    #        b'1-0:6.7.0(00.000*kvar)',
    #        b'1-0:7.7.0(00.000*kvar)',
    #        b'1-0:8.7.0(00.106*kvar)'
    #    ]
    #    while True:
    #        for item in fakeData:
    #            if (match := self._regexObisValue.match(item.decode('ascii'))):
    #                name = self.getObisName(match.group(1))
    #                # myArray = [ "obis", "rawValue", "name from getObisName(obis)" ]
    #                myArray = [ match.group(1), match.group(2), name ]
    #                if (not self._q.full()):
    #                    await self._q.put(myArray)
    #        await asyncio.sleep_ms(10000)


    #
    # UART to Queue 
    # if _uartParsingEnabled then try to readline data from uart
    #
    async def task_uartDataToQueue(self):
        lastObis = self._lastObis
        lastObisReached = False
        
        uart0 = UART(0)
        uart0.init(baudrate=115200, bits=8, parity=None, stop=1, rxbuf=4096)
        #uart1 = UART(1)
        #uart1.init(baudrate=115200, bits=8, parity=None, stop=1)
        
        uos.dupterm(None, 1)
        #uos.dupterm(uart1, 1)


        time.sleep(1)
        sreader = asyncio.StreamReader(uart0)
        #swriter = asyncio.StreamWriter(uart1, {})
        #swriter.write('asyncio stremwriter works\n')
        while True:
            lastObisReached = False
            while (uart0.any() > 0):
                line = await sreader.readline()
                #swriter.write("lastObisReaches: " + str(lastObisReached) + "    ")
                if (lastObisReached == False):
                    lineString = line.decode("ascii", "ignore")
                    if (match := self._regexObisValue.match(lineString)):
                        obis = match.group(1)
                        name = self.getObisName(obis)
                        rawValue = match.group(2)
                        #swriter.write(lineString)
                        myArray = [ obis, rawValue, name ]
                        if (not self._q.full()):
                            await self._q.put(myArray)
                        if (obis == lastObis):
                            #swriter.write("last obis true\n")
                            lastObisReached = True
                #swriter.write("queue size: " + str(self._q.qsize()))    
                #await swriter.drain()
            #await swriter.drain()
            await asyncio.sleep_ms(100)

    # 
    # Map your OBIS ids to a usable key
    #
    def getObisName(self, obis : str):
        if obis == "0-0:17.0.0": return "power_limiter_limit"
        if obis == "1-0:1.8.0": return "positive_energy_total"
        if obis == "1-0:1.8.1": return "positive_energy_tariff_1"
        if obis == "1-0:1.8.2": return "positive_energy_tariff_2"
        if obis == "1-0:1.8.3": return "positive_energy_tariff_3"
        if obis == "1-0:1.8.4": return "positive_energy_tariff_4"
        if obis == "1-0:2.8.0": return "negative_energy_total"
        if obis == "1-0:2.8.1": return "negative_energy_tariff_1"
        if obis == "1-0:2.8.2": return "negative_energy_tariff_2"
        if obis == "1-0:2.8.3": return "negative_energy_tariff_3"
        if obis == "1-0:2.8.4": return "negative_energy_tariff_4"
        if obis == "1-0:3.8.0": return "positive_reactive_energy_total"
        if obis == "1-0:4.8.0": return "negative_reactive_energy_total"
        if obis == "1-0:5.8.0": return "reactive_energy_total_Q1"
        if obis == "1-0:6.8.0": return "reactive_energy_total_Q2"
        if obis == "1-0:7.8.0": return "reactive_energy_total_Q3"
        if obis == "1-0:8.8.0": return "reactive_energy_total_Q4"
        if obis == "1-0:15.8.0": return "absolute_active_energy_total"
        if obis == "1-0:32.7.0": return "instantaneous_voltage_in_phase_L1"
        if obis == "1-0:52.7.0": return "instantaneous_voltage_in_phase_L2"
        if obis == "1-0:72.7.0": return "instantaneous_voltage_in_phase_L3"
        if obis == "1-0:31.7.0": return "instantaneous_current_in_phase_L1"
        if obis == "1-0:51.7.0": return "instantaneous_current_in_phase_L2"
        if obis == "1-0:71.7.0": return "instantaneous_current_in_phase_L3"
        if obis == "1-0:13.7.0": return "instantaneous_power_factor"
        if obis == "1-0:33.7.0": return "instantaneous_power_factor_in_phase_L1"
        if obis == "1-0:53.7.0": return "instantaneous_power_factor_in_phase_L2"
        if obis == "1-0:73.7.0": return "instantaneous_power_factor_in_phase_L3"
        if obis == "1-0:14.7.0": return "frequency"
        if obis == "1-0:1.7.0": return "positive_active_instantaneous_power"
        if obis == "1-0:2.7.0": return "negative_active_instantaneous_power"
        if obis == "1-0:5.7.0": return "reactive_power_instantaneous_Q1"
        if obis == "1-0:6.7.0": return "reactive_power_instantaneous_Q2"
        if obis == "1-0:7.7.0": return "reactive_power_instantaneous_Q3"
        if obis == "1-0:8.7.0": return "reactive_power_instantaneous_Q4"



    #
    # Using walrus operator and regex group get and convert the actual data
    # Three different examples (no overlap)
    #       float: 0.993
    #   floatUnit: 000553.014*kvarh
    # integerUnit: 001*A
    #
    def getValueUsingRegexGroup(self, item : str):
        value = None
        if (match := self._regex_float.match(item) or self._regex_floatUnit.match(item) or self._regex_integerUnit.match(item)):
            value = str(float(match.group(1)))
        return value



    #
    # Iterate over queue items and get them
    # Array value check
    # Build mqttTopic
    # Get actual numeric value in str format
    # Check if the mqttMessage is not None
    # Send the mqtt message
    #
    async def task_queueToMqtt(self):
        while True:
            while (not self._q.empty()):
                myArray = await self._q.get()
                if ((myArray[1] is not None) and (myArray[2] is not None)):
                    mqttTopic = self._baseTopic + "/" + str(myArray[2])
                    mqttMessage = self.getValueUsingRegexGroup(myArray[1])
                    if (mqttMessage is not None):
                        await self._mqttClient.publish(mqttTopic, mqttMessage)
            await asyncio.sleep_ms(1000)



    #
    # Connect with mqttClient
    # Create asyncio tasks
    #
    async def asyncmain(self):
        try:
            await self._mqttClient.connect()
        except OSError:
            print('Connection to MQTT server failed.')
            return
        #asyncio.create_task(self.task_fakeDataToQueue())
        asyncio.create_task(self.task_uartDataToQueue())
        asyncio.create_task(self.task_queueToMqtt())
        while True:
            await asyncio.sleep(1)



    #
    # Main function to call
    # You can interrupt it with CTRL+C if you have a working REPL on your UART
    #
    def loop(self):
        try:
            asyncio.run(self.asyncmain())
        except KeyboardInterrupt:
            print('Interrupted...')
        finally:
            asyncio.new_event_loop()
            print('Stopped.')





