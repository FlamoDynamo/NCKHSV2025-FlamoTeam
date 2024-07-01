# battery_and_charge.py
from machine import Pin, ADC
import time

class BatteryCharge:
    def __init__(self, adc_pin=0, battery_voltage=3.7, resistor_divider=2, charge_status_pin=16):
        """
        Khởi tạo module BatteryCharge.

        Args:
            adc_pin (int, optional): Chân ADC được kết nối với pin đo điện áp. Mặc định là 0 (A0).
            battery_voltage (float, optional): Điện áp của pin khi đầy. Mặc định là 3.7V.
            resistor_divider (int, optional): Tỉ số của bộ chia điện áp (nếu có). Mặc định là 2.
            charge_status_pin (int, optional): Chân GPIO được kết nối với chân báo sạc của module TP4056. Mặc định là 16 (D0).
        """
        self.adc = ADC(Pin(adc_pin))
        self.adc.atten(ADC.ATTN_11DB)  # Đặt dải đo của ADC (0-3.3V)
        self.battery_voltage = battery_voltage
        self.resistor_divider = resistor_divider
        self.charge_status_pin = Pin(charge_status_pin, Pin.IN)

    def read_voltage(self):
        """
        Đọc giá trị điện áp từ pin.

        Returns:
            float: Điện áp của pin (V).
        """
        adc_value = self.adc.read()
        voltage = adc_value * (3.3 / 1023) * self.resistor_divider  # Chuyển đổi ADC sang V
        return voltage

    def read_percentage(self):
        """
        Đọc phần trăm pin còn lại.

        Returns:
            int: Phần trăm pin còn lại (%).
        """
        voltage = self.read_voltage()
        percentage = int(voltage / self.battery_voltage * 100)
        return max(0, min(percentage, 100))  # Giới hạn giá trị từ 0-100%

    def is_charging(self):
        """
        Kiểm tra xem pin có đang được sạc hay không.

        Returns:
            bool: True nếu đang sạc, False nếu không sạc.
        """
        return self.charge_status_pin.value() == 0  # Trạng thái sạc thấp là đang sạc (active low)
