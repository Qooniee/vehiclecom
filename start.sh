sudo hciconfig hci0 up
sudo rmmod rfcomm
sudo modprobe rfcomm
sudo rfcomm bind 0 8A:2A:D4:FF:38:F3
ls /dev | grep rfcomm
sudo rfcomm listen 0 1 &

#sudo python logging.py
# 33:33:1A:04:00:00 Small OBD2