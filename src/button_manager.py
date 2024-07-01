# button_manager.py
from machine import Pin
import time

class ButtonManager:
    def __init__(self, button1_pin=0, button2_pin=2, button3_pin=13, long_press_duration=2000): # Sửa chân nút nhấn
        """
        Khởi tạo ButtonManager.

        Args:
            button1_pin (int, optional): Chân GPIO của nút nhấn 1. Mặc định là D3 (GPIO0).
            button2_pin (int, optional): Chân GPIO của nút nhấn 2. Mặc định là D4 (GPIO2).
            button3_pin (int, optional): Chân GPIO của nút nhấn 3. Mặc định là D7 (GPIO13).
            long_press_duration (int, optional): Thời gian (ms) để coi là nhấn giữ. Mặc định là 2000ms.
        """
        self.buttons = [
            Pin(button1_pin, Pin.IN, Pin.PULL_UP),
            Pin(button2_pin, Pin.IN, Pin.PULL_UP),
            Pin(button3_pin, Pin.IN, Pin.PULL_UP)
        ]
        self.long_press_duration = long_press_duration
        self.last_press_time = [0] * len(self.buttons)

    def check_button_press(self):
        """
        Kiểm tra trạng thái của các nút nhấn.
        Returns:
            tuple: Một tuple chứa 3 phần tử boolean tương ứng với trạng thái của 3 nút nhấn.
                   (True nếu nút được nhấn, False nếu không).
        """
        button_states = []
        for i, button in enumerate(self.buttons):
            if button.value() == 0:  # Nút được nhấn
                if time.ticks_ms() - self.last_press_time[i] > self.long_press_duration:
                    button_states.append("long")  # Nhấn giữ
                else:
                    button_states.append(True)  # Nhấn thường
                self.last_press_time[i] = time.ticks_ms()
            else:
                button_states.append(False)  # Không nhấn
        return button_states
