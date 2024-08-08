import obd
import os
import time
from obd import OBDCommand, Unit
from obd.protocols import ECU
from obd.utils import bytes_to_int


os.system('sudo hcitool scan')
os.system('sudo hciconfig hci0 up')
os.system('sudo rfcomm bind 0 8A:2A:D4:FF:38:F3')
os.system('sudo rfcomm listen 0 1 &')

# 0 to 100 %
def percent(messages):
    d = messages[0].data[2:]
    v = d[0]
    v = v * 100.0 / 255.0
    return v * Unit.percent

def angle(messages):
    print(messages[0].data)
    d = messages[0].data
    d = d[2:]
    v = bytes_to_int(d)
    print(v)


    return v * Unit.degree

def rpm(messages):
    print(messages[0].data)


    d = messages[0].data
    d = d[2:]
    v = bytes_to_int(d)
    print(v)

    return v * Unit.rpm


con = obd.OBD()
timeitr = 0
if con.status() == 'Car Connected':

    cmd_swa = OBDCommand("Angle",
                     "Steering Wheel Angle",
                     b"0149",#2147
                     4,
                     angle,
                     ECU.ALL,
                     False)
    cmd_throttle =  OBDCommand("ACCELERATOR_POS_D",
                     "Accelerator pedal position D",
                     b"0149",#2147
                     3,
                     percent,
                     ECU.ALL,
                     False)
    cmd_rpm = OBDCommand("RPM",
                    "Engine RPM",
                    b"010c",
                    4,
                    rpm,
                    ECU.ENGINE,
                    True)
    con.supported_commands.add(cmd_throttle)
    value = con.query(cmd_throttle)
    print(value)

else:
    print('error')


con.close()