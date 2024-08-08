import obd
import os
import time

os.system('sudo hcitool scan')
os.system('sudo hciconfig hci0 up')
os.system('sudo rfcomm bind 0 8A:2A:D4:FF:38:F3')
os.system('sudo rfcomm listen 0 1 &')


con = obd.OBD()
print()
timeitr = 0
while con.status() == 'Car Connected':
    #THROTTLE_POS SPEED RPM 
    print(str(timeitr) + ": "+str(con.query(obd.commands.SPEED)))
    print(str(timeitr) + ": "+str(con.query(obd.commands.RPM)))
    print(str(timeitr) + ": "+str(con.query(obd.commands.THROTTLE_POS)))
    print(str(timeitr) + ": "+str(con.query(obd.commands.THROTTLE_POS_B)))
    print(str(timeitr) + ": "+str(con.query(obd.commands.THROTTLE_POS_C)))
    print(str(timeitr) + ": "+str(con.query(obd.commands.ACCELERATOR_POS_D)))
    print(str(timeitr) + ": "+str(con.query(obd.commands.ACCELERATOR_POS_E)))
    print(str(timeitr) + ": "+str(con.query(obd.commands.ACCELERATOR_POS_F)))
    print(str(timeitr) + ": "+str(con.query(obd.commands.HYBRID_BATTERY_REMAINING)))
    print(str(timeitr) + ": "+str(con.query(obd.commands.OIL_TEMP)))





    

    time.sleep(1)
    timeitr += 1
else:
    print('error')