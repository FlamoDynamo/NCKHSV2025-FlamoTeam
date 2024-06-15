# buzzer.py

from machine import Pin, PWM
import time

class Buzzer:
    def __init__(self, buzzer_pin):
        """
        Khởi tạo Buzzer.

        Args:
            buzzer_pin (int): Chân GPIO được kết nối với buzzer.
        """
        self.buzzer = Pin(buzzer_pin, Pin.OUT)
        self.pwm = PWM(self.buzzer)
        self.pwm.duty(0)  # Tắt buzzer ban đầu

    def beep(self, frequency=440, duration=0.2, duty_cycle=512):
        """
        Phát ra âm thanh bíp.

        Args:
            frequency (int, optional): Tần số âm thanh (Hz). Mặc định là 440 Hz.
            duration (float, optional): Thời gian phát âm thanh (giây). Mặc định là 0.2 giây.
            duty_cycle (int, optional): Duty cycle của PWM (0-1023). Mặc định là 512 (50%).
        """
        self.pwm.freq(frequency)
        self.pwm.duty(duty_cycle)  # Thiết lập duty cycle
        time.sleep(duration)
        self.pwm.duty(0)  # Tắt buzzer

    def long_beep(self, frequency=440, duration=0.5):
        """
        Phát ra âm thanh bíp dài hơn.

        Args:
            frequency (int, optional): Tần số âm thanh (Hz). Mặc định là 440 Hz.
            duration (float, optional): Thời gian phát âm thanh (giây). Mặc định là 0.5 giây.
        """
        self.beep(frequency, duration)
