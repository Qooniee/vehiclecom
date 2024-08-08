import obd
import os
import time
from collections import deque
import numpy as np
import threading
import sys
import time
import matplotlib.pyplot as plt
import pandas as pd
import datetime

PATH = os.getcwd()

from time import perf_counter
def wait_process(wait_sec):
    until = perf_counter() + wait_sec
    while perf_counter() < until:
        pass
    return

class measurement_ELM327:
    def __init__(self, SAMPLING_FREQUENCY_HZ=1, SEQ_LEN=10, is_offline=False):
        self.is_offline = is_offline
        self.COLUMNS = ["Time",
                        "SPEED", "RPM"
                        ]


        self.SAMPLING_FREQUENCY_HZ = SAMPLING_FREQUENCY_HZ
        self.SAMPLING_TIME = 1 / self.SAMPLING_FREQUENCY_HZ
        self.EXEPATH = PATH
        self.DATAPATH = PATH + '/data'
        self.SEQ_LEN = SEQ_LEN
        self.INIT_LEN = self.SEQ_LEN // self.SAMPLING_FREQUENCY_HZ
        
        self.Time_queue = deque(np.zeros(self.INIT_LEN))# Time
        self.SPEED_queue = deque(np.zeros(self.INIT_LEN))# Vehicle SPEED
        self.RPM_queue = deque(np.zeros(self.INIT_LEN))# RPM
        
        self.current_data_list = np.array([])
        self.assy_data = np.array([])
        self.df = pd.DataFrame(columns=self.COLUMNS)
        self.filtered_df = None
        
        self.IsStart = False
        self.IsStop = True
        self.IsShow = False
        self.Isfilter=False
        self.fpass = 3
        self.fstop = 5
        self.gpass = 3
        self.gstop = 8

        
    def initialize_BLE(self):
        os.system('sudo hcitool scan')
        os.system('sudo hciconfig hci0 up')
        os.system('sudo rfcomm bind 0 8A:2A:D4:FF:38:F3')
        os.system('sudo rfcomm listen 0 1 &')


    def get_data_from_car(self):
        if self.is_offline:
            speed = np.abs(100 * np.random.randn())
            rpm = np.abs(10000 * np.random.randn())
        else:
            speed = self.connection.query(obd.commands.SPEED).value.magnitude
            rpm = self.connection.query(obd.commands.RPM).value.magnitude
        
        return speed, rpm

    def get_update_data_stream(self, Isreturnval=True):
            def update_queue(stream_queue, val):
                stream_queue.popleft()
                stream_queue.append(val)
                return stream_queue
            
            speed, rpm = self.get_data_from_car()

            update_queue(self.Time_queue, self.current_time)
            update_queue(self.SPEED_queue, speed)
            update_queue(self.RPM_queue, rpm)
            
            if Isreturnval:
                return  np.array([speed, rpm])
            else:
                return None



    def concat_meas_data(self):
        dataset = np.append(self.current_time, self.current_data_list).reshape(1, -1)
        if self.main_loop_clock == 0:
            self.assy_data = dataset
        else:
            self.assy_data = np.concatenate([self.assy_data, dataset], axis=0)
            
    def show_current_data(self, data_list, data_label):
        message = ""
        for i in range(len(self.COLUMNS)-1):
            val = data_list[i] if data_list[i] != None else "No val"
            message = message + data_label[i] + ": " + str(val) + " / "

        return message


    def save_data(self):
        t_delta = datetime.timedelta(hours=9)
        JST = datetime.timezone(t_delta, 'JST')# You have to set your timezone
        now = datetime.datetime.now(JST)
        timestamp = now.strftime('%Y%m%d%H%M%S')


        # convert the DataFrame from the numpy array
        self.df = pd.DataFrame(self.assy_data)
        self.df.columns = self.COLUMNS
        self.df.to_csv(self.DATAPATH + '/'+ timestamp +'_measurement_raw_data.csv', sep=',', encoding='utf-8', index=False, header=True)
        if self.Isfilter:
            self.filtered_df = self.filtering(df=self.df, labellist=self.COLUMNS[1:])
            self.filtered_df.to_csv(self.DATAPATH + '/'+ timestamp +'_measurement_filt_data.csv', sep=',', encoding='utf-8', index=False, header=True)





    def meas_start(self):
        print("Start measurement")

        print("Tring to connect ELM327 on the car...")
        try:
             self.initialize_BLE()
             self.connection = obd.OBD()
  
         
        except Exception as e:
            print("----------Exception!----------")
            print(e)

        print(self.connection.status())
        
        if self.connection.status() == obd.OBDStatus.CAR_CONNECTED:
            print("----------Connection establishment is succeed!----------")
        elif self.is_offline:
            print("----------offline mode----------")
            
        else:
            print("----------Connection establishment is unsucceed!----------")
            print("End program. Please check settings of the computer and ELM327")
            exit()
            
        
        self.main_loop_clock = 0
        wait_process(2)# sensor initialization
        self.meas_start_time = time.time()#Logic start time
        self.IsStart = True
        self.IsStop = False
        self.IsShow = True
        
        try: 
            while (self.IsStart and self.connection.status() == obd.OBDStatus.CAR_CONNECTED) or self.is_offline:
                self.itr_start_time = time.time()# Start time of iteration loop
                self.current_time = (self.main_loop_clock / self.SAMPLING_FREQUENCY_HZ)# + self.sampling_time# Current time                    
                ## Process / update data stream, concat data
                """
                1. get data fron a sensor BNO055
                2. deque data from que
                3. enque data to que
                4. create data set at current sample
                5. concatinate data 
                6. Convert numpuy aray to dataframe
                7. save dataframe

                """
                self.current_data_list = self.get_update_data_stream(Isreturnval=True)
                self.concat_meas_data()
                if self.IsShow:
                    message = self.show_current_data(self.current_data_list, self.COLUMNS[1:])
                    print(f'Time: {self.current_time:.3f}')
                    print(message)
                else:
                    message = self.show_current_data(self.current_data_list, self.COLUMNS[1:])


                self.itr_end_time = time.time()# End time of iteration loop
                wait_process(self.SAMPLING_TIME - (self.itr_end_time - self.itr_start_time))# For keeping sampling frequency
                self.main_loop_clock += 1
                


        except Exception as e:
            print("Error")
            print(e)
        
        except KeyboardInterrupt:
            self.meas_end_time = time.time()#0.002s
            
            #plt.plot(self.Time_queue, self.euler_x_queue, 'r', '*')
            #plt.show()
            
            # Elapsed time
            self.elapsed_time = self.meas_end_time - self.meas_start_time
            print("KeybordInterrupt!")     
            print(f'Elapsed Time: {self.elapsed_time:.3f}')

            # save data
            self.save_data()



        print("Finish")
        
        
        
        
        


def main():
    print("----------Main program start!----------")
    elm327 = measurement_ELM327(SAMPLING_FREQUENCY_HZ=10, SEQ_LEN=100, is_offline=False)
    elm327.meas_start()
    
    
    
if __name__ == '__main__':
    main()
    print()