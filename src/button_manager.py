'''# button_manager.py

from machine import Pin
import time

class ButtonManager:
    def __init__(self, button1_pin, button2_pin, long_press_duration=1.0, double_click_interval=0.3):
        """
        Khởi tạo ButtonManager.

        Args:
            button1_pin (int): Chân GPIO cho nút nhấn 1.
            button2_pin (int): Chân GPIO cho nút nhấn 2.
            long_press_duration (float, optional): Thời gian giữ nút để tính là nhấn giữ (giây). Mặc định là 1.0 giây.
            double_click_interval (float, optional): Khoảng thời gian tối đa giữa 2 lần nhấn để tính là nhấn đúp (giây). Mặc định là 0.3 giây.
        """
        self.button1 = Pin(button1_pin, Pin.IN, Pin.PULL_UP)
        self.button2 = Pin(button2_pin, Pin.IN, Pin.PULL_UP)
        self.long_press_duration = long_press_duration
        self.double_click_interval = double_click_interval

        self.button1_pressed_time = 0
        self.button1_last_pressed_time = 0
        self.button2_pressed_time = 0
        self.button2_last_pressed_time = 0

        self.on_button1_press = None
        self.on_button1_long_press = None
        self.on_button1_double_click = None
        self.on_button2_press = None
        self.on_button2_long_press = None
        self.on_button2_double_click = None

    def set_callbacks(self, on_button1_press=None, on_button1_long_press=None, on_button1_double_click=None,
                       on_button2_press=None, on_button2_long_press=None, on_button2_double_click=None):
        """
        Thiết lập các hàm callback cho các sự kiện nút nhấn.

        Args:
            on_button1_press (function, optional): Hàm được gọi khi nút 1 được nhấn.
            on_button1_long_press (function, optional): Hàm được gọi khi nút 1 được nhấn giữ.
            on_button1_double_click (function, optional): Hàm được gọi khi nút 1 được nhấn đúp.
            on_button2_press (function, optional): Hàm được gọi khi nút 2 được nhấn.
            on_button2_long_press (function, optional): Hàm được gọi khi nút 2 được nhấn giữ.
            on_button2_double_click (function, optional): Hàm được gọi khi nút 2 được nhấn đúp.
        """
        self.on_button1_press = on_button1_press
        self.on_button1_long_press = on_button1_long_press
        self.on_button1_double_click = on_button1_double_click
        self.on_button2_press = on_button2_press
        self.on_button2_long_press = on_button2_long_press
        self.on_button2_double_click = on_button2_double_click

    def check_events(self):
        """
        Kiểm tra các sự kiện nút nhấn và gọi các hàm callback tương ứng.
        """
        if self.button1.value() == 0:  # Nút 1 được nhấn
            if self.button1_pressed_time == 0:
                self.button1_pressed_time = time.ticks_ms()
            if time.ticks_diff(time.ticks_ms(), self.button1_pressed_time) >= self.long_press_duration * 1000:
                if self.on_button1_long_press:
                    self.on_button1_long_press()
        else:  # Nút 1 được nhả
            if self.button1_pressed_time != 0:
                if time.ticks_diff(time.ticks_ms(), self.button1_pressed_time) < self.long_press_duration * 1000:
                    if self.on_button1_press:
                        self.on_button1_press()
                    if time.ticks_diff(time.ticks_ms(), self.button1_last_pressed_time) <= self.double_click_interval * 1000:
                        if self.on_button1_double_click:
                            self.on_button1_double_click()
                self.button1_last_pressed_time = time.ticks_ms()
                self.button1_pressed_time = 0

        # Tương tự cho nút 2
        if self.button2.value() == 0:
            if self.button2_pressed_time == 0:
                self.button2_pressed_time = time.ticks_ms()
            if time.ticks_diff(time.ticks_ms(), self.button2_pressed_time) >= self.long_press_duration * 1000:
                if self.on_button2_long_press:
                    self.on_button2_long_press()
        else:
            if self.button2_pressed_time != 0:
                if time.ticks_diff(time.ticks_ms(), self.button2_pressed_time) < self.long_press_duration * 1000:
                    if self.on_button2_press:
                        self.on_button2_press()
                    if time.ticks_diff(time.ticks_ms(), self.button2_last_pressed_time) <= self.double_click_interval * 1000:
                        if self.on_button2_double_click:
                            self.on_button2_double_click()
                self.button2_last_pressed_time = time.ticks_ms()
                self.button2_pressed_time = 0'''

class ButtonManager:
    def __init__(self, button1_pin, button2_pin, button3_pin, long_press_duration=1.0, double_click_interval=0.3):
        self.button1 = Pin(button1_pin, Pin.IN, Pin.PULL_UP)
        self.button2 = Pin(button2_pin, Pin.IN, Pin.PULL_UP)
        self.button3 = Pin(button3_pin, Pin.IN, Pin.PULL_UP)
        self.long_press_duration = long_press_duration
        self.double_click_interval = double_click_interval

        self.button_states = {
            1: {"pressed_time": 0, "last_pressed_time": 0},
            2: {"pressed_time": 0, "last_pressed_time": 0},
            3: {"pressed_time": 0, "last_pressed_time": 0}
        }

        self.callbacks = {
            1: {"press": None, "long_press": None, "double_click": None},
            2: {"press": None, "long_press": None, "double_click": None},
            3: {"press": None, "long_press": None, "double_click": None}
        }

    def set_callbacks(self, button, on_press=None, on_long_press=None, on_double_click=None):
        self.callbacks[button]["press"] = on_press
        self.callbacks[button]["long_press"] = on_long_press
        self.callbacks[button]["double_click"] = on_double_click

    def check_events(self):
        for button_num, button in enumerate([self.button1, self.button2, self.button3], 1):
            self._check_button_events(button_num, button)

    def _check_button_events(self, button_num, button):
        state = self.button_states[button_num]
        if button.value() == 0:  # Button pressed
            if state["pressed_time"] == 0:
                state["pressed_time"] = time.ticks_ms()
            if time.ticks_diff(time.ticks_ms(), state["pressed_time"]) >= self.long_press_duration * 1000:
                if self.callbacks[button_num]["long_press"]:
                    self.callbacks[button_num]["long_press"]()
        else:  # Button released
            if state["pressed_time"] != 0:
                if time.ticks_diff(time.ticks_ms(), state["pressed_time"]) < self.long_press_duration * 1000:
                    if self.callbacks[button_num]["press"]:
                        self.callbacks[button_num]["press"]()
                    if time.ticks_diff(time.ticks_ms(), state["last_pressed_time"]) <= self.double_click_interval * 1000:
                        if self.callbacks[button_num]["double_click"]:
                            self.callbacks[button_num]["double_click"]()
                state["last_pressed_time"] = time.ticks_ms()
                state["pressed_time"] = 0
