# oled.py

from machine import I2C, Pin, SoftI2C
import time
import ssd1306
from max30102 import MAX30102
from battery_and_charge import BatteryCharge
from microsd import MicroSD

class OLEDDisplay(MAX30102):
    def __init__(self, i2c_max30102, i2c_oled, adc_pin, charge_status_pin, oled_width=128, oled_height=64):
        super().__init__(i2c_max30102)
        self.oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c_oled)
        self.battery_charge = BatteryCharge(adc_pin, charge_status_pin=charge_status_pin)

    def display_data(self, hr, spo2, nn_hr):
        self.oled.fill(0)
        self.oled.text("Heart Rate: {}".format(hr), 0, 0)
        self.oled.text("SpO2: {}".format(spo2), 0, 10)
        self.oled.text("NN Heart Rate: {}".format(nn_hr), 0, 20)

        # Hiển thị thông tin pin
        battery_percentage = self.battery_charge.read_percentage()
        self.oled.text("Battery: {}%".format(battery_percentage), 0, 30)

        charging_status = self.battery_charge.is_charging()
        if charging_status:
            self.oled.text("Charging", 0, 40)
        else:
            self.oled.text("Not Charging", 0, 40)

        self.oled.show()

# Main function (chạy file này để test)
def main():
    i2c_max30102 = I2C(1, scl=Pin(22), sda=Pin(21), freq=400000)
    i2c_oled = SoftI2C(scl=Pin(4), sda=Pin(5))
    adc_pin = 34  # Thay đổi chân ADC cho phù hợp
    charge_status_pin = 13  # Thay đổi chân GPIO cho phù hợp
    oled_display = OLEDDisplay(i2c_max30102, i2c_oled, adc_pin, charge_status_pin)

    data_file = 'sensor_data.csv'

    # Khởi tạo MicroSD (thay đổi chân GPIO cho phù hợp)
    microsd = MicroSD(spi_id=1, sck_pin=14, mosi_pin=13, miso_pin=12, cs_pin=15)
    microsd.mount()  # Mount thẻ nhớ

    # ... (Khởi tạo MAX30102)
    max30102 = MAX30102(i2c_max30102, microsd=microsd)

    while True:
        data = oled_display.read_sensor()
        print("RED:", data['red'], "IR:", data['ir'])
        if len(oled_display.ir_buffer) >= 100:
            hr = oled_display.calculate_heart_rate()
            spo2 = oled_display.calculate_spo2()
            nn_hr = oled_display.predict_heart_rate([data['red'], data['ir']])
            print("Heart Rate:", hr, "SpO2:", spo2, "NN Heart Rate:", nn_hr)

            oled_display.save_data(data_file, [data['red'], data['ir'], hr, spo2, nn_hr])
            oled_display.display_data(hr, spo2, nn_hr)

            oled_display.red_buffer = []
            oled_display.ir_buffer = []

        # ... (Lưu dữ liệu)
        max30102.save_data('sensor_data.csv', [data['red'], data['ir'], hr, spo2, nn_hr])
        time.sleep(0.1)
      
        # ... (Cuối chương trình)
        microsd.unmount()  # Unmount thẻ nhớ

if __name__ == "__main__":
    main()
