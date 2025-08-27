import os
import time

async def check_if_logs_exist() -> bool:
    if not os.path.exists("logs.txt"):
        with open("logs.txt", "w", encoding="utf-8") as f:
            time_stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            f.write(f"{time_stamp} - system - Log file created\n")
    return True

async def log_message(message: str, user_id: int):
    with open("logs.txt", "a", encoding="utf-8") as f:
        time_stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        f.write(f"{time_stamp} - {user_id} - {message}\n")
