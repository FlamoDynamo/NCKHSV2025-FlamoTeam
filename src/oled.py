# oled.py
'''from machine import Pin, SoftI2C
from ssd1306 import SSD1306_I2C
from writer import Writer, CWriter
from font8 import font8
import time
import max30102
from microsd import MicroSD'''

# oled.py (phần import)

from machine import Pin, SoftI2C
from ssd1306 import SSD1306_I2C
from writer import Writer, CWriter
from font8 import font8
import time
from collections import deque

# Các module khác cần thiết
import max30102
from microsd import MicroSD
from battery_and_charge import BatteryCharge
from button_manager import ButtonManager
from buzzer import Buzzer
from history_manager import HistoryManager

'''class OLEDDisplay(MAX30102):
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

class OLEDDisplay:
    def __init__(self, i2c_oled, oled_width=128, oled_height=64, microsd=None):
        self.oled = SSD1306_I2C(oled_width, oled_height, i2c_oled, addr=0x3c)
        self.oled.init_display()
        self.writer = Writer(self.oled, font8)
        self.cwriter = CWriter(self.oled, font8)
        self.microsd = microsd

        self.data_buffer = deque(maxlen=oled_width)
        self.current_mode = "measurement"
        self.display_mode = "graph"
        self.measurement_mode = "both"
        self.history_page_index = 0
        self.is_measuring = False
        self.alert_sound_enabled = True

        self.hr = 0
        self.spo2 = 0
        self.nn_hr = 0

    def clear(self):
        self.oled.fill(0)
        self.oled.show()

    def display_text(self, text, x, y):
        self.writer.set_textpos(self.oled, x, y)
        self.writer.printstring(text)
        self.oled.show()

    def display_data(self, hr, spo2, nn_hr):
        self.oled.fill(0)
        if self.display_mode == "graph":
            self.display_graph_data(hr, spo2)
        else:
            self.display_numerical_data(hr, spo2, nn_hr)
        self.oled.show()

    def display_history_data(self, history_manager):
        self.oled.fill(0)
        if history_manager.get_history_length() == 0:
            self.display_text("No history yet", 0, 0)
        else:
            record = history_manager.get_record(self.history_page_index)
            self.display_text(f"Record {self.history_page_index + 1}/{history_manager.get_history_length()}", 0, 0)
            self.display_text(f"Time: {record['timestamp']}", 0, 10)
            self.display_text(f"HR: {record['hr']}, SpO2: {record['spo2']}", 0, 20)
        self.oled.show()

def main():
    i2c_max30102 = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)  # I2C bus cho MAX30102
    i2c_oled = SoftI2C(scl=Pin(14), sda=Pin(12))  # SoftI2C bus cho OLED
    max30102_sensor = max30102.MAX30102(i2c_max30102)
    microsd = MicroSD(spi_id=1, sck_pin=14, mosi_pin=13, miso_pin=12, cs_pin=15)
    microsd.mount()
    oled_display = OLEDDisplay(i2c_oled, microsd=microsd)
    battery_charge = BatteryCharge(adc_pin=0)
    button_manager = ButtonManager()
    history_manager = HistoryManager()
    buzzer = Buzzer()

    while True:
        button_states = button_manager.check_button_press()

        if button_states[0]:  # Nút 1 được nhấn
            oled_display.display_mode = "graph" if oled_display.display_mode == "numerical" else "numerical"
        elif button_states[1]:  # Nút 2 được nhấn
            oled_display.current_mode = "history" if oled_display.current_mode == "measurement" else "measurement"
        elif button_states[2]:  # Nút 3 được nhấn
            # Chức năng của nút 3 (tạm thời chưa có)
            pass

        if oled_display.current_mode == "measurement":
            data = max30102_sensor.read_sensor()
            oled_display.display_data(data['hr'], data['spo2'], data['nn_hr'])
        elif oled_display.current_mode == "history":
            oled_display.display_history_data(history_manager)

        # Hiển thị thông tin pin
        battery_percentage = battery_charge.read_percentage()
        oled_display.display_text(f"Battery: {battery_percentage}%", 0, 54)  # Hiển thị ở dòng cuối cùng

        time.sleep(0.1)

if __name__ == "__main__":
    main()
