# microsd.py
from machine import Pin, SPI
import os

class MicroSD:
    def __init__(self, spi_id=1, sck_pin=14, mosi_pin=13, miso_pin=12, cs_pin=15):
        """
        Khởi tạo đối tượng MicroSD.
        Args:
            spi_id (int, optional): ID của bus SPI. Mặc định là 1 (HSPI).
            sck_pin (int, optional): Chân SCK của SPI. Mặc định là D5 (GPIO14).
            mosi_pin (int, optional): Chân MOSI của SPI. Mặc định là D7 (GPIO13).
            miso_pin (int, optional): Chân MISO của SPI. Mặc định là D6 (GPIO12).
            cs_pin (int, optional): Chân CS của SPI. Mặc định là D8 (GPIO15).
        """
        self.spi = SPI(spi_id, baudrate=1000000, polarity=0, phase=0, sck=Pin(sck_pin), mosi=Pin(mosi_pin), miso=Pin(miso_pin))
        self.cs = Pin(cs_pin, Pin.OUT)
        self.mounted = False

    def mount(self):
        """
        Mount thẻ nhớ MicroSD.
        """
        try:
            os.mount(self.spi, "/sd")
            self.mounted = True
            print("MicroSD mounted at /sd")
        except OSError:
            print("Error mounting MicroSD")

    def unmount(self):
        """
        Unmount thẻ nhớ MicroSD.
        """
        try:
            os.umount("/sd")
            self.mounted = False
            print("MicroSD unmounted")
        except OSError:
            print("Error unmounting MicroSD")

    def is_mounted(self):
        """
        Kiểm tra xem thẻ nhớ có được mount hay không.
        Returns:
            bool: True nếu đã mount, False nếu chưa.
        """
        return self.mounted
