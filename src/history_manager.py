# history_manager.py
from collections import deque

class HistoryManager:
    def __init__(self, max_entries=30):
        """
        Khởi tạo HistoryManager.
        Args:
            max_entries (int, optional): Số lượng kết quả đo tối đa được lưu trữ. Mặc định là 30.
        """
        self.history = deque(maxlen=max_entries)

    def add_record(self, timestamp, hr, spo2):
        """
        Thêm một kết quả đo vào lịch sử.
        Args:
            timestamp (str): Thời gian đo (ví dụ: "2024-06-16 10:00:00").
            hr (int): Nhịp tim.
            spo2 (int): SpO2.
        """
        self.history.append({'timestamp': timestamp, 'hr': hr, 'spo2': spo2})

    def get_record(self, index):
        """
        Lấy kết quả đo tại vị trí index.
        Args:
            index (int): Vị trí của kết quả đo trong lịch sử (0 là kết quả mới nhất).
        Returns:
            dict: Kết quả đo (hoặc None nếu index không hợp lệ).
        """
        if 0 <= index < len(self.history):
            return self.history[index]
        else:
            return None

    def get_history_length(self):
        """
        Lấy số lượng kết quả đo trong lịch sử.
        Returns:
            int: Số lượng kết quả đo.
        """
        return len(self.history)
