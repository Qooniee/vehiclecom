import obd
from   obd import OBDStatus
import os

os.system('sudo hcitool scan')
os.system('sudo hciconfig hci0 up')
os.system('sudo rfcomm bind 0 8A:2A:D4:FF:38:F3')
os.system('sudo rfcomm listen 0 1 &')



connection = obd.OBD()
print (connection.status())

if connection.status() == OBDStatus.CAR_CONNECTED:
	for i in range (0,197):
		try:
			flag = obd.commands.has_pid(1, i) # 使用可能か判定
			print('PID {} : {}'.format(i, flag))
		except KeyboardInterrupt:
			pass
	connection.close()