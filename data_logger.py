import obd
import os
import time
from collections import deque
import numpy as np
import pandas as pd
import datetime
import asyncio
import scipy
from scipy import signal
import matplotlib as plt

PATH = os.getcwd()
SAVE_INTERVAL = 10  # Save interval in seconds

def wait_process(wait_sec):
    until = time.perf_counter() + wait_sec
    while time.perf_counter() < until:
        pass
    return

# asyncio.to_threadにより同期関数を別スレッドで実行し、その結果を非同期で扱う
async def save_data_async(df, path):
    await asyncio.to_thread(df.to_csv, path, sep=',', encoding='utf-8', index=False, header=False, mode='a')
        
        

class measurement_ELM327:
    def __init__(self, SAMPLING_FREQUENCY_HZ=1, SEQ_LEN=10, is_offline=False):
        self.timezone='JST'
        self.is_offline = is_offline
        self.COLUMNS = ["Time", "SPEED", "RPM"]

        self.SAMPLING_FREQUENCY_HZ = SAMPLING_FREQUENCY_HZ
        self.SAMPLING_TIME = 1 / self.SAMPLING_FREQUENCY_HZ
        self.EXEPATH = PATH
        self.DATAPATH = PATH + '/data'
        self.SEQ_LEN = SEQ_LEN
        self.INIT_LEN = self.SEQ_LEN // self.SAMPLING_FREQUENCY_HZ
        
        self.Time_queue = deque(np.zeros(self.INIT_LEN))
        self.SPEED_queue = deque(np.zeros(self.INIT_LEN))
        self.RPM_queue = deque(np.zeros(self.INIT_LEN))
        
        self.current_data_list = np.zeros(len(self.COLUMNS) - 1)  # Adjust length to match number of sensors
        self.assy_data = np.zeros((0, len(self.COLUMNS)))  # Initialize with the correct number of columns
        self.df = pd.DataFrame(columns=self.COLUMNS, dtype=np.float32)
        self.filtered_df = None
        
        self.IsStart = False
        self.IsStop = True
        self.IsShow = False
        self.Isfilter = True
        self.fpass = 3
        self.fstop = 5
        self.gpass = 3
        self.gstop = 8
        
        
        self.current_file_path = os.path.join(self.DATAPATH, 'measurement_raw_data.csv')

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
            return np.array([speed, rpm])
        else:
            return None

    def concat_meas_data(self):
        current_data = np.append([self.current_time], self.current_data_list)
        dataset = current_data.reshape(1, -1)  # Reshape to ensure 2D
        
        print(f'self.assy_data shape: {self.assy_data.shape}')
        print(f'dataset shape: {dataset.shape}')
        
        if self.main_loop_clock == 0:
            self.assy_data = dataset
        else:
            # Ensure the dimensions are correct for concatenation
            try:
                if self.assy_data.shape[1] == dataset.shape[1]:
                    self.assy_data = np.concatenate([self.assy_data, dataset], axis=0)
                else:
                    print("Dimension mismatch between assy_data and dataset")
            except IndexError as e:
                print("IndexError during concatenation:", e)

    def show_current_data(self, data_list, data_label):
        message = ""
        for i in range(len(self.COLUMNS)-1):
            val = data_list[i] if data_list[i] is not None else "No val"
            message = message + data_label[i] + ": " + str(val) + " / "
        return message


    def butterlowpass(x, fpass, fstop, gpass, gstop, fs, dt, checkflag, labelname='Signal[-]'):

        print('Applying filter against: {0}...'.format(labelname))
        fn = 1 / (2 * dt)
        Wp = fpass / fn
        Ws = fstop / fn
        N, Wn = signal.buttord(Wp, Ws, gpass, gstop)
        b1, a1 = signal.butter(N, Wn, "low")
        y = signal.filtfilt(b1, a1, x)
        print(y)

        if checkflag == True:
            time = np.arange(x.__len__()) * dt
            plt.figure(figsize = (12, 5))
            plt.title('Comparison between signals')
            plt.plot(time, x, color='black', label='Raw signal')
            plt.plot(time, y, color='red', label='Filtered signal')
            plt.xlabel('Time[s]')
            plt.ylabel(labelname)
            plt.show()
        return y
    
    def filtering(self, df, labellist):
        """
        Label list must dropped "Time" label.
        Filter function doesn't need "Time" for the computation.
        """
        filtered_df = df.copy()
        for labelname in labellist:
            # Ensure the column is converted to a numpy array
            x = df[labelname].to_numpy()
            filtered_df[labelname] = self.butterlowpass(
                x=x,  # Correctly pass the numpy array as 'x'
                fpass=self.fpass,
                fstop=self.fstop,
                gpass=self.gpass,
                gstop=self.gstop,
                fs=self.SAMPLING_FREQUENCY_HZ,
                dt=self.SAMPLING_TIME,
                checkflag=False,
                labelname=labelname
            )
        return filtered_df




    async def save_data(self):
        # Convert the DataFrame from the numpy array
        self.df = pd.DataFrame(self.assy_data, columns=self.COLUMNS, dtype=np.float32)
        await save_data_async(self.df, self.current_file_path)
        self.assy_data = np.zeros((0, len(self.COLUMNS)))  # Clear data but keep the correct shape

        # if self.Isfilter:
        #     self.filtered_df = self.filtering(df=self.df, labellist=self.COLUMNS[1:])
        #     await save_data_async(self.filtered_df, self.current_file_path.replace('_raw_data.csv', '_filt_data.csv'))


    async def finish_measurement_and_save_data(self):
        # Convert the DataFrame from the numpy array
        t_delta = datetime.timedelta(hours=9)
        TIMEZONE = datetime.timezone(t_delta, self.timezone)# You have to set your timezone
        now = datetime.datetime.now(TIMEZONE)
        timestamp = now.strftime('%Y%m%d%H%M%S')
        self.df = pd.DataFrame(self.assy_data, columns=self.COLUMNS, dtype=np.float32)
        final_file_path = self.current_file_path.replace(self.current_file_path.split('/')[-1], 
                                                   timestamp + '_' + self.current_file_path.split('/')[-1])
        await save_data_async(self.df, self.current_file_path)
        raw_df = pd.read_csv(self.current_file_path, header=None)
        raw_df.columns = self.COLUMNS
        raw_df.to_csv(final_file_path, sep=',', encoding='utf-8', index=False, header=True)
        print()

        if self.Isfilter:
            filt_df = self.filtering(df=raw_df, labellist=self.COLUMNS[1:])
            filt_df.to_csv(final_file_path.replace('_raw_data.csv', '_filt_data.csv'), sep=',', encoding='utf-8', index=False, header=True)

        if os.path.exists(self.current_file_path):
            os.remove(self.current_file_path)
            print(f"File  '{self.current_file_path}' was deleted")
        else:
            print(f"File '{self.current_file_path}' is not existed")




    async def meas_start(self):
        print("Start measurement")

        if not self.is_offline:
            print("Trying to connect ELM327 on the car...")
            try:
                self.initialize_BLE()
                self.connection = obd.OBD()
            except Exception as e:
                print("----------Exception!----------")
                print(e)
                exit()

            print(self.connection.status())
            if self.connection.status() == obd.OBDStatus.CAR_CONNECTED:
                print("----------Connection establishment is successful!----------")
            else:
                print("----------Connection establishment failed!----------")
                print("End program. Please check settings of the computer and ELM327")
                exit()
        else:
            print("----------Offline mode----------")

        self.main_loop_clock = 0
        wait_process(2)  # Sensor initialization
        self.meas_start_time = time.time()
        self.IsStart = True
        self.IsStop = False
        self.IsShow = True
        
        try:
            while self.is_offline or (self.IsStart and self.connection.status() == obd.OBDStatus.CAR_CONNECTED):
                self.itr_start_time = time.time()
                self.current_time = (self.main_loop_clock / self.SAMPLING_FREQUENCY_HZ)
                
                self.current_data_list = self.get_update_data_stream(Isreturnval=True)
                self.concat_meas_data()
                if self.IsShow:
                    message = self.show_current_data(self.current_data_list, self.COLUMNS[1:])
                    print(f'Time: {self.current_time:.3f}')
                    print(message)

                self.itr_end_time = time.time()
                wait_process(self.SAMPLING_TIME - (self.itr_end_time - self.itr_start_time))
                self.main_loop_clock += 1
                
                if self.main_loop_clock % (SAVE_INTERVAL * self.SAMPLING_FREQUENCY_HZ) == 0:
                    await self.save_data()

        except Exception as e:
            print("Error")
            print(e)
        
        except KeyboardInterrupt:
            self.meas_end_time = time.time()
            self.elapsed_time = self.meas_end_time - self.meas_start_time
            print("KeyboardInterrupt!")
            print(f'Elapsed Time: {self.elapsed_time:.3f}')
            await self.finish_measurement_and_save_data()
            
        print("Finish")

def main():
    print("----------Main program start!----------")
    elm327 = measurement_ELM327(SAMPLING_FREQUENCY_HZ=10, SEQ_LEN=100, is_offline=True)
    asyncio.run(elm327.meas_start())

if __name__ == '__main__':
    main()
