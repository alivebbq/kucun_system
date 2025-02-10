import serial
import threading
from typing import Optional, Callable
from app.core.config import settings

class BarcodeScanner:
    def __init__(self):
        self.port = settings.SCANNER_PORT
        self.baudrate = settings.SCANNER_BAUDRATE
        self.serial: Optional[serial.Serial] = None
        self.is_running = False
        self.callback: Optional[Callable[[str], None]] = None
        
    def connect(self) -> bool:
        """连接扫码枪"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            return True
        except Exception as e:
            print(f"扫码枪连接失败: {str(e)}")
            return False
    
    def disconnect(self):
        """断开扫码枪连接"""
        if self.serial and self.serial.is_open:
            self.serial.close()
    
    def start_reading(self, callback: Callable[[str], None]):
        """开始读取扫码数据"""
        if not self.serial or not self.serial.is_open:
            if not self.connect():
                return
        
        self.callback = callback
        self.is_running = True
        
        # 在新线程中读取数据
        thread = threading.Thread(target=self._read_loop)
        thread.daemon = True
        thread.start()
    
    def stop_reading(self):
        """停止读取扫码数据"""
        self.is_running = False
        self.disconnect()
    
    def _read_loop(self):
        """读取循环"""
        while self.is_running and self.serial and self.serial.is_open:
            try:
                if self.serial.in_waiting:
                    barcode = self.serial.readline().decode().strip()
                    if barcode and self.callback:
                        self.callback(barcode)
            except Exception as e:
                print(f"读取扫码数据错误: {str(e)}")
                break
        
        self.stop_reading()

# 创建全局扫码器实例
scanner = BarcodeScanner() 