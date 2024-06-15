# microsd.py

from machine import SPI, Pin, SDCard
import os

class MicroSD:
    def __init__(self, spi_id, sck_pin, mosi_pin, miso_pin, cs_pin):
        """
        Khởi tạo đối tượng MicroSD.

        Args:
            spi_id (int): ID của bus SPI (thường là 1 hoặc 2).
            sck_pin (int): Chân GPIO cho SCK (Serial Clock).
            mosi_pin (int): Chân GPIO cho MOSI (Master Out Slave In).
            miso_pin (int): Chân GPIO cho MISO (Master In Slave Out).
            cs_pin (int): Chân GPIO cho CS (Chip Select).
        """
        self.spi = SPI(spi_id, sck=Pin(sck_pin), mosi=Pin(mosi_pin), miso=Pin(miso_pin))
        self.sd = SDCard(self.spi, Pin(cs_pin))

    def mount(self, mount_point='/sd'):
        """
        Mount thẻ nhớ microSD.

        Args:
            mount_point (str, optional): Điểm mount (thường là '/sd').
        """
        try:
            os.mount(self.sd, mount_point)
            print(f"Đã mount thẻ nhớ tại {mount_point}")
        except OSError as e:
            print(f"Lỗi khi mount thẻ nhớ: {e}")

    def unmount(self, mount_point='/sd'):
        """
        Unmount thẻ nhớ microSD.

        Args:
            mount_point (str, optional): Điểm mount (thường là '/sd').
        """
        try:
            os.umount(mount_point)
            print(f"Đã unmount thẻ nhớ từ {mount_point}")
        except OSError as e:
            print(f"Lỗi khi unmount thẻ nhớ: {e}")

    def save_data(self, filename, data, mount_point='/sd'):
        """
        Lưu dữ liệu vào file CSV trên thẻ nhớ microSD.

        Args:
            filename (str): Tên file CSV (ví dụ: 'sensor_data.csv').
            data (list): Dữ liệu cần lưu.
            mount_point (str, optional): Điểm mount (thường là '/sd').
        """
        try:
            # Tạo đường dẫn đầy đủ đến file
            full_path = f"{mount_point}/{filename}"

            # Mở file để ghi (thêm 'a' để ghi tiếp vào file)
            with open(full_path, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(data)

            print(f"Đã lưu dữ liệu vào {full_path}")
        except OSError as e:
            print(f"Lỗi khi lưu file: {e}")
