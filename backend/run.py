import uvicorn
import os
import signal
import sys
from pathlib import Path

def main():
    # 获取PID文件路径
    pid_file = Path("server.pid")
    
    # 检查是否有旧的进程
    if pid_file.exists():
        try:
            with open(pid_file) as f:
                old_pid = int(f.read())
            # 尝试终止旧进程
            try:
                os.kill(old_pid, signal.SIGTERM)
                print(f"Terminated old process (PID: {old_pid})")
            except ProcessLookupError:
                pass
        except Exception as e:
            print(f"Error handling old PID file: {e}")
        pid_file.unlink(missing_ok=True)
    
    # 写入新的PID
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))
    
    # 启动服务器
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_delay=2,
            log_level="info"
        )
    finally:
        # 清理PID文件
        pid_file.unlink(missing_ok=True)

if __name__ == "__main__":
    main() 