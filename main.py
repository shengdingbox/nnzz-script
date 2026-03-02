import sys
import os
import subprocess
import hashlib
import json
from datetime import datetime, timedelta
import psutil
import winreg
import threading
import time
import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# 常量定义
TAFANG_EXE_NAME = 'tafangmonitor.exe'
TASK_EXE_NAME = 'tafangrunning.exe'
SECRET_KEY = 'tf_secure_2026_custom_888'
SALT = b'tafang_salt_2026_secure_888_xyz_123'
ITERATIONS = 100000
DATE_FORMAT = '%Y%m%d'
DISPLAY_DATE_FORMAT = '%Y-%m-%d'
REG_PATH = 'Software\\TaFangAssistant_Pro'
ACTIVATE_CODE_EXPIRE_MINUTES = 30
SUPPORT_DAYS = {'3小时': 0.125, '1天': 1, '3天': 3, '7天': 7, '30天': 30}
CHECK_INTERVAL = 60

# 工具函数
def resource_path(relative_path):
    """获取资源的绝对路径，兼容开发环境和打包后的exe"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

def get_aes_key():
    """生成AES-256加密密钥（基于密钥+盐值，不可逆）"""
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=ITERATIONS)
    key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode('utf-8')))
    return Fernet(key)

def encrypt_data(data):
    """加密数据（字典→JSON→AES→十六进制，完全乱码）"""
    try:
        fernet = get_aes_key()
        json_data = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        encrypted_bytes = fernet.encrypt(json_data.encode('utf-8'))
        return encrypted_bytes.hex()
    except:
        return None

def decrypt_data(encrypted_hex):
    """解密数据（十六进制→AES→JSON→字典，静默失败则返回None）"""
    try:
        fernet = get_aes_key()
        encrypted_bytes = bytes.fromhex(encrypted_hex)
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
        return json.loads(decrypted_bytes.decode('utf-8'))
    except:
        return None

def save_license(hwid, code, days):
    """激活信息→加密→写入注册表（无文件，完全隐藏）"""
    expire_time = datetime.now() + timedelta(days=days)
    license_data = {'hwid': hwid, 'activate_code': code, 'days': days, 'expire_time': expire_time.strftime('%Y-%m-%d %H:%M:%S'), 'activated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'activated': True}
    encrypted_data = encrypt_data(license_data)
    if not encrypted_data:
        return None
    else:
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
            winreg.SetValueEx(key, 'TF_LICENSE_DATA', 0, winreg.REG_SZ, encrypted_data)
            winreg.CloseKey(key)
        except:
            return None

def load_license():
    """从注册表→解密→读取激活信息（静默验证）"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH)
        encrypted_data, _ = winreg.QueryValueEx(key, 'TF_LICENSE_DATA')
        winreg.CloseKey(key)
        license_data = decrypt_data(encrypted_data)
        if not license_data:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_PATH)
            return
        else:
            return license_data
    except:
        return None

def is_license_valid():
    """验证激活信息（静默恢复：篡改则失效）"""
    license_data = load_license()
    if not license_data or not license_data.get('activated'):
        return False
    else:
        try:
            if license_data['hwid']!= get_hwid():
                raise Exception('机器码不匹配')
            else:
                expire_time = datetime.strptime(license_data['expire_time'], '%Y-%m-%d %H:%M:%S')
                if datetime.now() > expire_time:
                    raise Exception('已过期')
                else:
                    return True
        except:
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_PATH)
                return False
            except:
                return False

def get_today_hash():
    today_raw = datetime.now().strftime(DATE_FORMAT)
    return hashlib.sha256(today_raw.encode()).hexdigest()[:16].upper()

def get_hwid():
    """生成本机唯一机器码（16位）"""
    try:
        # 添加更多系统信息，改变组合方式
        info = (
            f"{os.name}"
            f"{os.environ.get('COMPUTERNAME', '')}"
            f"{os.environ.get('PROCESSOR_IDENTIFIER', '')}"
            f"{os.environ.get('USERNAME', '')}"
            f"{os.environ.get('SYSTEMROOT', '')}"
            f"{os.environ.get('OS', '')}"
            f"{str(os.getpid())}"
        )
        # 使用MD5哈希，然后取中间16位，再进行一次SHA1哈希
        md5_hash = hashlib.md5(info.encode()).hexdigest()
        mid_part = md5_hash[8:24]  # 取中间16位
        final_hash = hashlib.sha1(mid_part.encode()).hexdigest()[:16].upper()
        return final_hash
    except:
        # 异常情况下使用不同的随机数生成方式
        return hashlib.sha1(os.urandom(32)).hexdigest()[:16].upper()

def get_time_token():
    now = datetime.now()
    return now.strftime('%Y%m%d%H') + f'{now.minute // ACTIVATE_CODE_EXPIRE_MINUTES}'

def make_activate_code(hwid, days):
    today_hash = get_today_hash()
    time_token = get_time_token()
    raw_str = f'{today_hash}|{hwid}|{days}|{time_token}|{SECRET_KEY}'
    return hashlib.sha256(raw_str.encode()).hexdigest()[:16].upper()

def verify_activate_code(hwid, input_code):
    today_hash = get_today_hash()
    now = datetime.now()
    valid_tokens = set()
    for minute_delta in range(0, ACTIVATE_CODE_EXPIRE_MINUTES + 1):
        check_time = now - timedelta(minutes=minute_delta)
        token = check_time.strftime('%Y%m%d%H') + f'{check_time.minute // ACTIVATE_CODE_EXPIRE_MINUTES}'
        valid_tokens.add(token)
    for days_name, days_value in SUPPORT_DAYS.items():
        for token in valid_tokens:
            raw_str = f'{today_hash}|{hwid}|{days_value}|{token}|{SECRET_KEY}'
            valid_code = hashlib.sha256(raw_str.encode()).hexdigest()[:16].upper()
            if input_code == valid_code:
                return days_value
    return None

def kill_process_by_name(process_name):
    killed = False
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() == process_name.lower():
                psutil.Process(proc.info['pid']).terminate()
                killed = True
        except:
            continue
    return killed

class LicenseWatchdog(threading.Thread):
    """后台线程：每隔1分钟检查授权是否到期，到期则终止脚本"""
    def __init__(self):
        super().__init__(daemon=True)
    
    def run(self):
        while True:
            time.sleep(CHECK_INTERVAL)
            if not is_license_valid():
                # 直接终止脚本
                kill_process_by_name(TAFANG_EXE_NAME)
                kill_process_by_name(TASK_EXE_NAME)
                break

def stop_all_scripts_silent():
    """静默终止所有脚本，无弹窗、无界面更新"""
    kill_process_by_name(TAFANG_EXE_NAME)
    kill_process_by_name(TASK_EXE_NAME)

def main():
    # 初始化数据
    hwid = get_hwid()
    today_raw = datetime.now().strftime(DISPLAY_DATE_FORMAT)
    license_valid = is_license_valid()
    license_data = load_license() if license_valid else None
    
    # 创建主窗口
    root = tk.Tk()
    root.title('塔防自动化助手 - 专业版')
    root.geometry('700x650')  # 增加窗口高度，确保所有内容都能显示
    root.resizable(True, True)  # 允许调整窗口大小
    
    # 设置字体和颜色
    root.option_add('*Font', 'Arial 10')
    root.option_add('*Background', '#f0f0f0')
    
    # 创建主框架
    main_frame = ttk.Frame(root, padding='10')
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 标题区域
    title_frame = ttk.Frame(main_frame)
    title_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(title_frame, text='逆战未来塔防盛鼎脚本', font=('Arial', 14, 'bold')).pack(side=tk.LEFT, padx=5)
    ttk.Label(title_frame, text='⚡', font=('Arial', 12)).pack(side=tk.LEFT, padx=5)
    
    # 状态区域
    status_frame = ttk.Frame(main_frame)
    status_frame.pack(fill=tk.X, pady=5)
    
    status_text = '未激活 | 请输入激活码' if not license_valid else '已激活 | 到期：' + license_data["expire_time"]
    ttk.Label(status_frame, text=status_text, font=('Arial', 11, 'bold')).pack(anchor=tk.W)
    
    # 公告区域
    announcement_frame = ttk.LabelFrame(main_frame, text='公告', padding='5')
    announcement_frame.pack(fill=tk.X, pady=5)
    
    announcement_texts = [
        '欢迎使用逆战未来塔防盛鼎脚本',
        '遇到问题请前往群文件更新到最新版',
        '点击试用就可以直接启动哦，每天可使用1小时。',
        '游戏每隔一段时间就会来一次大批量检测行为和检测历史战绩记录，请合理安排挂机时间，尽量不要一直挂机，导致禁赛。'
    ]
    
    for text in announcement_texts:
        ttk.Label(announcement_frame, text=text).pack(anchor=tk.W, pady=2)
    
    # 机器码和激活码区域
    activation_frame = ttk.LabelFrame(main_frame, text='激活中心', padding='5')
    activation_frame.pack(fill=tk.X, pady=5)
    
    activation_grid = ttk.Frame(activation_frame)
    activation_grid.pack(fill=tk.X)
    
    # 机器码
    ttk.Label(activation_grid, text='机器码：').grid(row=0, column=0, sticky=tk.W, pady=5)
    ttk.Label(activation_grid, text=hwid).grid(row=0, column=1, sticky=tk.W, pady=5)
    ttk.Button(activation_grid, text='复制', command=lambda: copy_hwid(hwid)).grid(row=0, column=2, padx=10, pady=5)
    
    # 激活码
    ttk.Label(activation_grid, text='激活码：').grid(row=1, column=0, sticky=tk.W, pady=5)
    activate_code_var = tk.StringVar()
    ttk.Entry(activation_grid, textvariable=activate_code_var, width=30).grid(row=1, column=1, sticky=tk.W, pady=5)
    ttk.Button(activation_grid, text='立即激活', command=lambda: activate_code(activate_code_var.get(), hwid, root)).grid(row=1, column=2, padx=10, pady=5)
    
    # 系统信息区域
    info_frame = ttk.LabelFrame(main_frame, text='系统信息', padding='5')
    info_frame.pack(fill=tk.X, pady=5)
    
    info_grid = ttk.Frame(info_frame)
    info_grid.pack(fill=tk.X)
    
    ttk.Label(info_grid, text='当前日期：').grid(row=0, column=0, sticky=tk.W, pady=5)
    ttk.Label(info_grid, text=today_raw).grid(row=0, column=1, sticky=tk.W, pady=5)
    
    # 使用说明区域
    help_frame = ttk.LabelFrame(main_frame, text='使用说明', padding='5')
    help_frame.pack(fill=tk.X, pady=5)
    
    help_texts = [
        '• 一机一码，激活后绑定本机',
        '• 快捷键：F2启动 / F10终止',
        '• 到期时间格式：年-月-日 时:分:秒'
    ]
    
    for text in help_texts:
        ttk.Label(help_frame, text=text).pack(anchor=tk.W, pady=2)
    
    # 功能按钮区域 - 放在最下面
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=5)
    
    # 添加试用按钮
    trial_button = ttk.Button(button_frame, text='试用 (每天2小时)', command=lambda: start_script(True))
    trial_button.pack(side=tk.LEFT, padx=5)
    
    # 启动按钮
    start_button = ttk.Button(button_frame, text='启动塔防脚本 (F2)', command=lambda: start_script(license_valid))
    start_button.pack(side=tk.LEFT, padx=5)
    start_button.state(['disabled'] if not license_valid else [])
    
    # 终止按钮
    stop_button = ttk.Button(button_frame, text='终止所有脚本 (F10)', command=lambda: stop_script(license_valid))
    stop_button.pack(side=tk.LEFT, padx=5)
    stop_button.state(['disabled'] if not license_valid else [])
    
    # 启动授权监控线程
    if license_valid:
        watchdog = LicenseWatchdog()
        watchdog.start()
    
    # 快捷键处理
    def on_key_press(event):
        if event.keysym == 'F2':
            start_script(license_valid)
        elif event.keysym == 'F10':
            stop_script(license_valid)
    
    root.bind('<KeyPress>', on_key_press)
    
    # 窗口关闭处理
    def on_closing():
        stop_all_scripts_silent()
        root.destroy()
    
    root.protocol('WM_DELETE_WINDOW', on_closing)
    
    # 运行主循环
    root.mainloop()

def copy_hwid(hwid):
    try:
        import pyperclip
        pyperclip.copy(hwid)
        messagebox.showinfo('提示', '✅ 复制成功')
    except ImportError:
        messagebox.showinfo('提示', '请安装pyperclip库以使用复制功能')

def activate_code(input_code, hwid, root):
    input_code = input_code.strip().upper()
    if len(input_code) != 16:
        messagebox.showinfo('提示', '激活码必须是16位字符！')
        return
    
    valid_days = verify_activate_code(hwid, input_code)
    if valid_days:
        save_license(hwid, input_code, valid_days)
        days_name = [k for k, v in SUPPORT_DAYS.items() if v == valid_days][0]
        messagebox.showinfo('激活成功', '已激活' + days_name + '权限！程序将重启生效')
        # 重启程序
        root.destroy()
        os.startfile(sys.argv[0])
    else:
        messagebox.showinfo('激活失败', '激活码无效、已过期（30分钟内有效）或不匹配本机！')

def start_script(license_valid):
    if license_valid:
        try:
            tafang_exe_path = resource_path(TAFANG_EXE_NAME)
            if not os.path.exists(tafang_exe_path):
                messagebox.showinfo('错误', '核心文件缺失，请重新获取软件！')
                return
            else:
                subprocess.Popen([tafang_exe_path], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                messagebox.showinfo('成功', '塔防脚本启动成功！')
        except Exception as e:
            messagebox.showinfo('启动失败', '错误信息：\n' + str(e))
    else:
        messagebox.showinfo('提示', '未激活/授权已到期，无法启动脚本！')

def stop_script(license_valid):
    if license_valid:
        monitor_killed = kill_process_by_name(TAFANG_EXE_NAME)
        task_killed = kill_process_by_name(TASK_EXE_NAME)
        if monitor_killed or task_killed:
            messagebox.showinfo('成功', '已终止所有运行的脚本！')
        else:
            messagebox.showinfo('提示', '未检测到运行中的脚本！')
    else:
        messagebox.showinfo('提示', '未激活/授权已到期，无需终止脚本！')

if __name__ == '__main__':
    main()