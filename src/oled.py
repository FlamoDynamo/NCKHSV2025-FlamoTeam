'''# oled.py

from machine import I2C, Pin, SoftI2C
import time
import ssd1306
from max30102 import MAX30102
from battery_and_charge import BatteryCharge
from microsd import MicroSD
from button_manager import ButtonManager
from history_manager import HistoryManager
from buzzer import Buzzer

class OLEDDisplay(MAX30102):
    def __init__(self, i2c_max30102, i2c_oled, adc_pin, charge_status_pin, button1_pin, button2_pin, buzzer_pin, oled_width=128, oled_height=64):
        super().__init__(i2c_max30102)
        self.oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c_oled)
        self.battery_charge = BatteryCharge(adc_pin, charge_status_pin=charge_status_pin)
        self.button_manager = ButtonManager(button1_pin, button2_pin)
        self.history_manager = HistoryManager()
        self.buzzer = Buzzer(buzzer_pin)

        self.data_buffer = deque(maxlen=oled_width)  # Buffer dữ liệu cho đồ thị
        self.current_mode = "measurement"  # Chế độ hiện tại: "measurement" hoặc "history"
        self.history_page_index = 0  # Vị trí trang hiện tại trong lịch sử

        # Thiết lập các hàm callback cho button_manager
        self.button_manager.set_callbacks(
            on_button1_press=self.on_button1_press,
            on_button1_long_press=self.on_button1_long_press,
            on_button1_double_click=self.on_button1_double_click,
            on_button2_press=self.on_button2_press
        )
        self.hr = 0
        self.spo2 = 0
        self.nn_hr = 0
        
    def display_data(self, hr, spo2, nn_hr):
        """
        Hiển thị dữ liệu lên OLED.
        """
        self.oled.fill(0)

        if self.current_mode == "measurement":
            if self.is_measuring: # Chỉ hiển thị dữ liệu khi đang đo
                if self.display_graph:
                    self.display_graph_data(hr, spo2)
                else:
                    self.display_numerical_data(hr, spo2, nn_hr)
        elif self.current_mode == "history":
            self.display_history_data()

        # Hiển thị thông tin pin
        battery_percentage = self.battery_charge.read_percentage()
        self.oled.text("Battery: {}%".format(battery_percentage), 0, 55)

        charging_status = self.battery_charge.is_charging()
        charging_text = "Charging" if charging_status else "Not Charging"
        self.oled.text(charging_text, 90, 55)

        self.oled.show()

    def display_numerical_data(self, hr, spo2, nn_hr):
        """
        Hiển thị dữ liệu số.
        """
        self.oled.text("Heart Rate: {}".format(hr), 0, 0)
        self.oled.text("SpO2: {}".format(spo2), 0, 10)
        self.oled.text("NN Heart Rate: {}".format(nn_hr), 0, 20)

    def display_graph_data(self, hr, spo2):
        """
        Hiển thị dữ liệu đồ thị.
        """
        self.data_buffer.append((hr, spo2))

        # Vẽ đồ thị nhịp tim
        for i in range(1, len(self.data_buffer)):
            x1 = i - 1
            y1 = 63 - int(self.data_buffer[i - 1][0] / 200 * 63)  # Chia tỷ lệ trục tung
            x2 = i
            y2 = 63 - int(self.data_buffer[i][0] / 200 * 63)
            self.oled.line(x1, y1, x2, y2, 1)

        # Vẽ đồ thị SpO2 (dùng nét đứt)
        for i in range(1, len(self.data_buffer)):
            if i % 2 == 0:  # Vẽ nét đứt
                x1 = i - 1
                y1 = 63 - int(self.data_buffer[i - 1][1] / 100 * 63)  # Chia tỷ lệ trục tung
                x2 = i
                y2 = 63 - int(self.data_buffer[i][1] / 100 * 63)
                self.oled.line(x1, y1, x2, y2, 1)

    def display_history_data(self):
        """
        Hiển thị dữ liệu lịch sử.
        """
        record = self.history_manager.get_record(self.history_page_index)
        if record:
            self.oled.text(record['timestamp'], 0, 0)
            self.oled.text("HR: {}".format(record['hr']), 0, 10)
            self.oled.text("SpO2: {}".format(record['spo2']), 0, 20)
        else:
            self.oled.text("Không có dữ liệu", 0, 0)

    def on_button1_press(self):
        """
        Xử lý sự kiện nút 1 nhấn.
        """
        if self.current_mode == "measurement":
            if self.is_measuring:
                self.toggle_display_mode()
        elif self.current_mode == "history":
            # Điều hướng trang lịch sử (lên)
            self.history_page_index = max(0, self.history_page_index - 1)

    def on_button1_long_press(self):
        """
        Xử lý sự kiện nút 1 nhấn giữ.
        """
        if self.current_mode == "measurement":
            if self.is_measuring:
                measurement_duration, hr, spo2, nn_hr = self.stop_measurement()
                self.history_manager.add_record(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), hr, spo2)
            else:
                self.start_measurement()

    def on_button1_double_click(self):
        """
        Xử lý sự kiện nút 1 nhấn đúp.
        """
        if self.current_mode == "measurement" and not self.is_measuring:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.save_data('sensor_data.csv', [self.hr, self.spo2, self.nn_hr], timestamp)

    def on_button2_press(self):
        """
        Xử lý sự kiện nút 2 nhấn.
        """
        if self.current_mode == "measurement":
            self.current_mode = "history"
            self.history_page_index = 0  # Reset vị trí trang khi chuyển sang chế độ lịch sử
        elif self.current_mode == "history":
            # Điều hướng trang lịch sử (xuống)
            self.history_page_index = min(self.history_manager.get_history_length() - 1, self.history_page_index + 1)
            self.current_mode = "measurement"

# Main function (chạy file này để test)
def main():
    i2c_max30102 = I2C(1, scl=Pin(22), sda=Pin(21), freq=400000)
    i2c_oled = SoftI2C(scl=Pin(4), sda=Pin(5))
    adc_pin = 34  # Thay đổi chân ADC cho phù hợp
    charge_status_pin = 13  # Thay đổi chân GPIO cho phù hợp
    
    # Khởi tạo MicroSD (thay đổi chân GPIO cho phù hợp)
    microsd = MicroSD(spi_id=1, sck_pin=14, mosi_pin=13, miso_pin=12, cs_pin=15)
    microsd.mount()  # Mount thẻ nhớ

    # Khởi tạo MAX30102 với microsd
    max30102 = MAX30102(i2c_max30102, microsd=microsd)
    
    # Khởi tạo OLEDDisplay với max30102 đã có microsd
    oled_display = OLEDDisplay(i2c_max30102, i2c_oled, adc_pin, charge_status_pin)

    data_file = 'sensor_data.csv'

    while True:
        if oled_display.current_mode == "measurement":
            if oled_display.is_measuring:
                data = max30102.read_sensor()
                print("RED:", data['red'], "IR:", data['ir'])
                if len(max30102.ir_buffer) >= 100:
                    oled_display.hr = max30102.calculate_heart_rate()
                    oled_display.spo2 = max30102.calculate_spo2()
                    oled_display.nn_hr = max30102.predict_heart_rate([data['red'], data['ir']])
                    print("Heart Rate:", oled_display.hr, "SpO2:", oled_display.spo2, "NN Heart Rate:", oled_display.nn_hr)

                    # Cảnh báo
                    if oled_display.hr < 40 or oled_display.hr > 120:
                        oled_display.buzzer.beep()
                    if oled_display.spo2 < 90:
                        oled_display.buzzer.beep(duty_cycle=768)  # Âm lượng 75%
                    elif oled_display.spo2 < 92 and oled_display.hr < 40:
                        oled_display.buzzer.beep()
                    elif oled_display.spo2 < 95 and oled_display.hr >= 40:
                        oled_display.buzzer.beep()

                    max30102.red_buffer = []
                    max30102.ir_buffer = []
        
        oled_display.button_manager.check_events()
        oled_display.display_data(oled_display.hr, oled_display.spo2, oled_display.nn_hr)
        time.sleep(0.1)
      
    # ... (Đưa microsd.unmount() ra ngoài vòng lặp while)
    microsd.unmount()  # Unmount thẻ nhớ

if __name__ == "__main__":
    main()'''

class OLEDDisplay(MAX30102):
    def __init__(self, i2c_max30102, i2c_oled, adc_pin, charge_status_pin, button1_pin, button2_pin, button3_pin, buzzer_pin, oled_width=128, oled_height=64):
        super().__init__(i2c_max30102)
        self.oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c_oled)
        self.battery_charge = BatteryCharge(adc_pin, charge_status_pin=charge_status_pin)
        self.button_manager = ButtonManager(button1_pin, button2_pin, button3_pin)
        self.history_manager = HistoryManager()
        self.buzzer = Buzzer(buzzer_pin)

        self.data_buffer = deque(maxlen=oled_width)
        self.current_mode = "measurement"
        self.display_mode = "graph"
        self.measurement_mode = "both"
        self.history_page_index = 0
        self.is_measuring = False
        self.alert_sound_enabled = True

        self.button_manager.set_callbacks(1, self.on_button1_press, self.on_button1_long_press, self.on_button1_double_click)
        self.button_manager.set_callbacks(2, self.on_button2_press, self.on_button2_long_press)
        self.button_manager.set_callbacks(3, self.on_button3_press, self.on_button3_long_press, self.on_button3_double_click)

        self.hr = 0
        self.spo2 = 0
        self.nn_hr = 0

    def on_button1_press(self):
        if self.current_mode == "measurement":
            self.display_mode = "graph" if self.display_mode == "numerical" else "numerical"

    def on_button1_long_press(self):
        if self.current_mode == "measurement":
            if self.is_measuring:
                self.stop_measurement()
            else:
                self.start_measurement()

    def on_button1_double_click(self):
        if self.current_mode == "measurement" and not self.is_measuring:
            self.save_current_data()

    def on_button2_press(self):
        if self.current_mode == "history":
            self.history_page_index = max(0, self.history_page_index - 1)

    def on_button2_long_press(self):
        if self.current_mode == "measurement":
            modes = ["both", "hr", "spo2"]
            self.measurement_mode = modes[(modes.index(self.measurement_mode) + 1) % len(modes)]

    def on_button3_press(self):
        if self.current_mode == "history":
            self.history_page_index = min(self.history_manager.get_history_length() - 1, self.history_page_index + 1)
        else:
            self.current_mode = "history" if self.current_mode == "measurement" else "measurement"

    def on_button3_long_press(self):
        self.alert_sound_enabled = not self.alert_sound_enabled

    def on_button3_double_click(self):
        if self.current_mode == "measurement":
            self.save_current_data()

    def save_current_data(self):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.save_data('sensor_data.csv', [self.hr, self.spo2, self.nn_hr], timestamp)

    def display_data(self):
        self.oled.fill(0)

        if self.current_mode == "measurement":
            if self.is_measuring:
                if self.display_mode == "graph":
                    self.display_graph_data()
                else:
                    self.display_numerical_data()
        elif self.current_mode == "history":
            self.display_history_data()

        self.display_battery_info()
        self.oled.show()

    def display_numerical_data(self):
        if self.measurement_mode in ["both", "hr"]:
            self.oled.text("HR: {}".format(self.hr), 0, 0)
        if self.measurement_mode in ["both", "spo2"]:
            self.oled.text("SpO2: {}".format(self.spo2), 0, 10)
        self.oled.text("NN HR: {}".format(self.nn_hr), 0, 20)

    def display_graph_data(self):
        # Implementation remains the same

    def display_history_data(self):
        # Implementation remains the same

    def display_battery_info(self):
        # Implementation remains the same

    def check_alerts(self):
        if not self.alert_sound_enabled:
            return

        if self.hr < 40 or self.hr > 120:
            self.buzzer.beep()
        if self.spo2 < 90:
            self.buzzer.beep(duty_cycle=768)
        elif self.spo2 < 92 and self.hr < 40:
            self.buzzer.beep()
        elif self.spo2 < 95 and self.hr >= 40:
            self.buzzer.beep()

    def main_loop(self):
        while True:
            self.button_manager.check_events()

            if self.current_mode == "measurement" and self.is_measuring:
                data = self.read_sensor()
                if len(self.ir_buffer) >= 100:
                    self.hr = self.calculate_heart_rate()
                    self.spo2 = self.calculate_spo2()
                    self.nn_hr = self.predict_heart_rate([data['red'], data['ir']])
                    self.check_alerts()
                    self.red_buffer = []
                    self.ir_buffer = []

            self.display_data()
            time.sleep(0.1)

def main():
    i2c_max30102 = I2C(1, scl=Pin(6), sda=Pin(7), freq=400000)
    i2c_oled = SoftI2C(scl=Pin(2), sda=Pin(0))
    adc_pin = 4
    charge_status_pin = 3
    button1_pin = 18
    button2_pin = 19
    button3_pin = 21
    buzzer_pin = 25
    
    microsd = MicroSD(spi_id=1, sck_pin=11, mosi_pin=10, miso_pin=9, cs_pin=8)
    microsd.mount()

    oled_display = OLEDDisplay(i2c_max30102, i2c_oled, adc_pin, charge_status_pin, button1_pin, button2_pin, button3_pin, buzzer_pin)
    oled_display.microsd = microsd

    try:
        oled_display.main_loop()
    finally:
        microsd.unmount()

if __name__ == "__main__":
    main()
