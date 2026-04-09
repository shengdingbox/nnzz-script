import hashlib
from datetime import datetime

SECRET_KEY = 'tf_secure_2026_custom_666'
ACTIVATE_CODE_EXPIRE_MINUTES = 30

hwid = "F21F0FAA29CC3AA3"
days = 30  # 1天卡
now = datetime(2026, 3, 15, 23, 00)  # 你的电脑当前时间

# today_hash
today_raw = now.strftime('%Y%m%d')
today_hash = hashlib.sha256(today_raw.encode()).hexdigest()[:16].upper()

# time token
time_token = now.strftime('%Y%m%d%H') + str(now.minute // ACTIVATE_CODE_EXPIRE_MINUTES)

# raw string
raw = f"{today_hash}|{hwid}|{days}|{time_token}|{SECRET_KEY}"

# 最终激活码
activate_code = hashlib.sha256(raw.encode()).hexdigest()[:16].upper()
print("激活码:", activate_code)