# buzzer.py
from machine import Pin, Timer

class Buzzer:
    def __init__(self, buzzer_pin=2):
        """
        Khởi tạo đối tượng Buzzer.
        Args:
            buzzer_pin (int, optional): Chân GPIO kết nối với buzzer. Mặc định là D4 (GPIO2).
        """
        self.buzzer = Pin(buzzer_pin, Pin.OUT)
        self.timer = Timer(-1)  # Sử dụng timer ảo
        self.is_on = False

    def on(self):
        """
        Bật buzzer.
        """
        self.is_on = True
        self.buzzer.on()

    def off(self):
        """
        Tắt buzzer.
        """
        self.is_on = False
        self.buzzer.off()

    def beep(self, duration=100):  # Thời gian beep mặc định là 100ms
        """
        Phát ra tiếng bíp trong một khoảng thời gian.
        Args:
            duration (int, optional): Thời gian bíp (ms). Mặc định là 100ms.
        """
        self.on()
        self.timer.init(period=duration, mode=Timer.ONE_SHOT, callback=lambda t: self.off())
