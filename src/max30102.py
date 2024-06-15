# max30102.py

from machine import I2C, Pin
import time
import numpy as np
import csv
import joblib
from microsd import MicroSD
from scipy.signal import wiener  # Import hàm lọc Wiener

class MAX30102:
    def __init__(self, i2c, addr=0x57, microsd=None):
        self.i2c = i2c
        self.addr = addr
        self.setup()
        self.red_buffer = []
        self.ir_buffer = []
        self.load_model()
        self.microsd = microsd

    def write_reg(self, reg, value):
        self.i2c.writeto_mem(self.addr, reg, bytes([value]))

    def read_reg(self, reg, nbytes=1):
        return self.i2c.readfrom_mem(self.addr, reg, nbytes)

    def setup(self):
        # Reset the sensor
        self.write_reg(0x09, 0x40)
        time.sleep(1)

        # Set FIFO Configuration
        self.write_reg(0x08, 0x4F)  # Sample Averaging = 4, FIFO Rolls on Full

        # Set Mode Configuration
        self.write_reg(0x09, 0x03)  # SpO2 mode

        # Set SpO2 Configuration
        self.write_reg(0x0A, 0x27)  # ADC Range = 4096nA, Sample Rate = 100Hz, LED Pulse Width = 411µs

        # Set LED Pulse Amplitude
        self.write_reg(0x0C, 0x24)  # RED LED
        self.write_reg(0x0D, 0x24)  # IR LED

    def load_model(self):
        self.nn_model = joblib.load('nn_model.pkl')

    def read_fifo(self):
        fifo_data = self.read_reg(0x07, 6)  # Read 6 bytes from FIFO_DATA
        red = (fifo_data[0] << 16) | (fifo_data[1] << 8) | fifo_data[2]
        ir = (fifo_data[3] << 16) | (fifo_data[4] << 8) | fifo_data[5]
        return red, ir

    def read_sensor(self):
        red, ir = self.read_fifo()
        
        # Áp dụng lọc Wiener
        red_filtered = wiener(red)
        ir_filtered = wiener(ir)

        self.red_buffer.append(red_filtered)
        self.ir_buffer.append(ir_filtered)
        return {'red': red_filtered, 'ir': ir_filtered}

    def kalman_filter(self, data):
        n_iter = len(data)
        sz = (n_iter,)  # size of array
        xhat = np.zeros(sz)      # a posteri estimate of x
        P = np.zeros(sz)         # a posteri error estimate
        xhatminus = np.zeros(sz) # a priori estimate of x
        Pminus = np.zeros(sz)    # a priori error estimate
        K = np.zeros(sz)         # gain or blending factor

        Q = 1e-5 # process variance
        R = 0.1**2 # estimate of measurement variance, change to see effect

        # intial guesses
        xhat[0] = data[0]
        P[0] = 1.0

        for k in range(1, n_iter):
            # time update
            xhatminus[k] = xhat[k-1]
            Pminus[k] = P[k-1] + Q

            # measurement update
            K[k] = Pminus[k] / (Pminus[k] + R)
            xhat[k] = xhatminus[k] + K[k] * (data[k] - xhatminus[k])
            P[k] = (1 - K[k]) * Pminus[k]

        return xhat

    def calculate_heart_rate(self):
        peaks = self.detect_peaks(self.ir_buffer)
        if len(peaks) >= 2:
            peak_intervals = [peaks[i + 1] - peaks[i] for i in range(len(peaks) - 1)]
            avg_peak_interval = sum(peak_intervals) / len(peak_intervals)
            heart_rate = 60 / (avg_peak_interval * 0.01)  # Convert to beats per minute
            return heart_rate
        return 0

    def calculate_spo2(self):
        red_filtered = self.kalman_filter(self.red_buffer)
        ir_filtered = self.kalman_filter(self.ir_buffer)
        red_dc = sum(red_filtered) / len(red_filtered)
        ir_dc = sum(ir_filtered) / len(ir_filtered)
        red_ac = max(red_filtered) - min(red_filtered)
        ir_ac = max(ir_filtered) - min(ir_filtered)
        ratio = (red_ac / red_dc) / (ir_ac / ir_dc)
        spo2 = 110 - 25 * ratio  # Simplified formula
        return spo2

    def detect_peaks(self, data, threshold=0.6):
        # Using a simple peak detection algorithm with low-pass filter
        data = self.low_pass_filter(data)
        peaks = []
        for i in range(1, len(data) - 1):
            if data[i] > data[i - 1] and data[i] > data[i + 1] and data[i] > threshold:
                peaks.append(i)
        return peaks

    def low_pass_filter(self, data, alpha=0.1):
        filtered_data = [data[0]]
        for i in range(1, len(data)):
            filtered_data.append(alpha * data[i] + (1 - alpha) * filtered_data[-1])
        return filtered_data

    def predict_heart_rate(self, data):
        if hasattr(self, 'nn_model'):
            return self.nn_model.predict([data])[0]
        return None

    def save_data(self, filename, data, timestamp):
        """
        Lưu dữ liệu vào file CSV.

        Args:
            filename (str): Tên file CSV (ví dụ: 'sensor_data.csv').
            data (list): Dữ liệu cần lưu.
            timestamp (str): Thời gian đo.
        """
        if self.microsd:
            self.microsd.save_data(filename, [timestamp] + data)  # Thêm timestamp vào dữ liệu
        else:
            print("Chưa khởi tạo MicroSD. Dữ liệu sẽ không được lưu.")

    def start_measurement(self):
        """
        Bắt đầu đo.
        """
        self.measurement_start_time = time.ticks_ms()
        self.red_buffer = []
        self.ir_buffer = []
        print("Bắt đầu đo...")
    
    def stop_measurement(self):
        """
        Dừng đo.

        Returns:
            tuple: Thời gian đo (giây), nhịp tim, SpO2, nhịp tim dự đoán.
        """
        measurement_duration = time.ticks_diff(time.ticks_ms(), self.measurement_start_time) / 1000
        hr = self.calculate_heart_rate()
        spo2 = self.calculate_spo2()
        nn_hr = self.predict_heart_rate([self.red_buffer[-1], self.ir_buffer[-1]])
        print(f"Dừng đo. Thời gian: {measurement_duration:.2f} giây, HR: {hr}, SpO2: {spo2}, NN HR: {nn_hr}")
        return measurement_duration, hr, spo2, nn_hr
    
    def toggle_display_mode(self):
        """
        Chuyển đổi chế độ hiển thị (đồ thị/số liệu).
        """
        self.display_graph = not self.display_graph
        print(f"Chế độ hiển thị: {'Đồ thị' if self.display_graph else 'Số liệu'}")
