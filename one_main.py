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
import ctypes
import sys

# 常量定义
SECRET_KEY = 'sd_secure_2026_custom_888'
SALT = b'shengding_t_2026_secure_888_xyz_123'
ITERATIONS = 100000
REG_PATH = 'Software\\ShengDingAssistant_Pro'
REG_KEY = 'SD_LICENSE_DATA'
SUPPORT_DAYS = {'1小时': 1/24, '3小时': 0.125, '1天': 1, '3天': 3, '7天': 7, '30天': 30}
CHECK_INTERVAL = 60

# 全局变量
logger = None

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
            winreg.SetValueEx(key, REG_KEY, 0, winreg.REG_SZ, encrypted_data)
            winreg.CloseKey(key)
        except:
            return None

def load_license():
    """从注册表→解密→读取激活信息（静默验证）"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH)
        encrypted_data, _ = winreg.QueryValueEx(key, REG_KEY)
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
        )
        # 使用MD5哈希，然后取中间16位，再进行一次SHA1哈希
        md5_hash = hashlib.md5(info.encode()).hexdigest()
        mid_part = md5_hash[8:24]  # 取中间16位
        final_hash = hashlib.sha1(mid_part.encode()).hexdigest()[:16].upper()
        return final_hash
    except:
        # 异常情况下使用不同的随机数生成方式
        return hashlib.sha1(os.urandom(32)).hexdigest()[:16].upper()

def make_activate_code(hwid, days):
    raw_str = f'{hwid}|{days}|{SECRET_KEY}'
    return hashlib.sha256(raw_str.encode()).hexdigest()[:16].upper()

def verify_activate_code(hwid, input_code):
    for days_name, days_value in SUPPORT_DAYS.items():
        raw_str = f'{hwid}|{days_value}|{SECRET_KEY}'
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
                # 由于我们不再使用tafangmonitor.exe，只需要终止任务进程
                logger.warning('授权已到期，脚本已终止！')
                break

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",                # 请求管理员权限
            sys.executable,        # python.exe
            " ".join(sys.argv),    # 当前参数
            None,
            1
        )
        sys.exit()
    # 初始化数据
    hwid = get_hwid()
    license_valid = is_license_valid()
    license_data = load_license() if license_valid else None

    # 创建主窗口
    root = tk.Tk()
    root.title('塔防自动化助手 - 专业版')
    root.geometry('900x650')
    root.resizable(True, True)

    # 设置样式
    style = ttk.Style()
    style.theme_use('clam')

    # 定义颜色方案
    bg_color = '#2c3e50'
    fg_color = '#ecf0f1'
    accent_color = '#3498db'
    success_color = '#27ae60'
    warning_color = '#f39c12'
    error_color = '#e74c3c'

    # 配置样式
    style.configure('TFrame', background=bg_color)
    style.configure('TLabel', background=bg_color, foreground=fg_color, font=('Microsoft YaHei UI', 10))
    style.configure('TButton', font=('Microsoft YaHei UI', 9, 'bold'), padding=5, background='white', foreground='#2c3e50', relief='flat', borderwidth=2)
    style.configure('TLabelframe', background=bg_color, foreground=accent_color, font=('Microsoft YaHei UI', 11, 'bold'))
    style.configure('TLabelframe.Label', background=bg_color, foreground=accent_color, font=('Microsoft YaHei UI', 11, 'bold'))
    style.configure('TCombobox', fieldbackground='#34495e', background='#34495e', foreground=fg_color, font=('Microsoft YaHei UI', 10))
    style.configure('TEntry', fieldbackground='#34495e', foreground=fg_color, font=('Microsoft YaHei UI', 10))

    # 按钮样式
    style.map('TButton', background=[('active', '#ecf0f1'), ('pressed', '#bdc3c7')], foreground=[('active', '#2c3e50'), ('pressed', '#2c3e50')])

    root.configure(bg=bg_color)

    # 创建主框架
    main_frame = ttk.Frame(root, padding='20')
    main_frame.pack(fill=tk.BOTH, expand=True)

    # 标题区域
    title_frame = ttk.Frame(main_frame)
    title_frame.pack(fill=tk.X, pady=(0, 15))

    title_label = ttk.Label(title_frame, text='🎮 逆战未来塔防盛鼎脚本', font=('Microsoft YaHei UI', 18, 'bold'))
    title_label.pack(side=tk.LEFT, padx=5)

    # 创建双栏容器
    columns_frame = ttk.Frame(main_frame)
    columns_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

    # 左栏
    left_column = ttk.Frame(columns_frame)
    left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))

    # 右栏
    right_column = ttk.Frame(columns_frame, width=450)
    right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(10, 0))
    right_column.pack_propagate(False)

    # 公告区域（左栏）
    announcement_frame = ttk.LabelFrame(left_column, text='📢 公告', padding='10')
    announcement_frame.pack(fill=tk.X, pady=(0, 15))

    announcement_texts = [
        '• 一机一码，激活后绑定本机',
        '• 欢迎使用逆战未来塔防盛鼎脚本',
        '• 遇到问题请前往群文件更新到最新版',
        '• 游戏每隔一段时间就会来一次大批量检测行为和检测历史战绩记录，',
        '• 请合理安排挂机时间，尽量不要一直挂机，导致禁赛。'
    ]

    for text in announcement_texts:
        ttk.Label(announcement_frame, text=text, font=('Microsoft YaHei UI', 9)).pack(anchor=tk.W, pady=2)

    # 机器码和激活码区域（左栏）
    activation_frame = ttk.LabelFrame(left_column, text='🔑 激活中心', padding='10')
    activation_frame.pack(fill=tk.X, pady=(0, 15))

    activation_grid = ttk.Frame(activation_frame)
    activation_grid.pack(fill=tk.X)

    # 机器码
    ttk.Label(activation_grid, text='机器码：', font=('Microsoft YaHei UI', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=8)
    ttk.Label(activation_grid, text=hwid, font=('Microsoft YaHei UI', 9)).grid(row=0, column=1, sticky=tk.W, pady=8)
    copy_btn = ttk.Button(activation_grid, text='📋 复制', command=lambda: copy_hwid(hwid))
    copy_btn.grid(row=0, column=2, padx=10, pady=8)

    # 激活码
    ttk.Label(activation_grid, text='激活码：', font=('Microsoft YaHei UI', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=8)
    activate_code_var = tk.StringVar()
    ttk.Entry(activation_grid, textvariable=activate_code_var, width=30).grid(row=1, column=1, sticky=tk.W, pady=8)
    activate_btn = ttk.Button(activation_grid, text='✅ 立即激活', command=lambda: activate_code(activate_code_var.get(), hwid, root))
    activate_btn.grid(row=1, column=2, padx=10, pady=8)

    # 状态区域（右栏栏首）
    status_frame = ttk.Frame(right_column)
    status_frame.pack(fill=tk.X, pady=(0, 15))

    status_text = '❌ 未激活 | 请输入激活码' if not license_valid else '✅ 已激活 | 到期：' + license_data["expire_time"]
    status_color = error_color if not license_valid else success_color
    status_label = ttk.Label(status_frame, text=status_text, font=('Microsoft YaHei UI', 12, 'bold'))
    status_label.pack(anchor=tk.W)

    # 地图选择区域（右栏）
    map_frame = ttk.LabelFrame(right_column, text='🗺️ 地图选择', padding='10')
    map_frame.pack(fill=tk.X, pady=(0, 15))

    map_grid = ttk.Frame(map_frame)
    map_grid.pack(fill=tk.X)

    ttk.Label(map_grid, text='选择地图：', font=('Microsoft YaHei UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
    map_var = tk.StringVar(value='请选择地图')
    map_combobox = ttk.Combobox(map_grid, textvariable=map_var, values=['请选择地图', '星港20号S2', '蔷薇庄园歼灭者S2','蔷薇庄园天启S2'], state='readonly', width=18)
    map_combobox.pack(side=tk.LEFT, padx=5)

    # 功能按钮区域（右栏）
    button_frame = ttk.Frame(right_column)
    button_frame.pack(fill=tk.X, pady=(0, 15))

    # 启动按钮
    start_button = ttk.Button(button_frame, text='🚀 启动塔防脚本 (F2)', command=lambda: start_script(license_valid, map_var.get()))
    start_button.pack(side=tk.LEFT, padx=8, pady=5)
    start_button.state(['disabled'] if not license_valid else [])

    # 终止按钮
    stop_button = ttk.Button(button_frame, text='⏹️ 终止所有脚本 (F10)', command=lambda: stop_script(license_valid,root))
    stop_button.pack(side=tk.LEFT, padx=8, pady=5)
    stop_button.state(['disabled'] if not license_valid else [])

    # 日志输出区域（右栏）
    log_frame = ttk.LabelFrame(right_column, text='📋 运行日志', padding='10')
    log_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

    # 创建文本框用于显示日志
    log_text = tk.Text(log_frame, height=40, wrap=tk.WORD, bg='#34495e', fg='#ecf0f1', font=('Consolas', 9), insertbackground='#ecf0f1')
    log_text.pack(fill=tk.BOTH, expand=True)

    # 添加滚动条
    scrollbar = ttk.Scrollbar(log_text, orient=tk.VERTICAL, command=log_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log_text.config(yscrollcommand=scrollbar.set)

    # 定义日志类
    class Logger:
        def __init__(self, text_widget):
            self.text_widget = text_widget
            self.text_widget.tag_config('info', foreground='#3498db')
            self.text_widget.tag_config('error', foreground='#e74c3c')
            self.text_widget.tag_config('warning', foreground='#f39c12')
            self.text_widget.tag_config('success', foreground='#27ae60')
            self.text_widget.tag_config('timestamp', foreground='#95a5a6')

        def log(self, message, tag=None):
            """输出日志信息"""
            print(message)
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message = f"[{timestamp}] {message}\n"

            if tag:
                self.text_widget.insert(tk.END, log_message, tag)
            else:
                self.text_widget.insert(tk.END, log_message)
            self.text_widget.see(tk.END)

        def info(self, message):
            """输出信息日志"""
            print(message)
            self.log(f"ℹ️ INFO: {message}", 'info')

        def error(self, message):
            """输出错误日志"""
            print(message)
            self.log(f"❌ ERROR: {message}", 'error')

        def warning(self, message):
            """输出警告日志"""
            print(message)
            self.log(f"⚠️ WARNING: {message}", 'warning')

        def success(self, message):
            """输出成功日志"""
            print(message)
            self.log(f"✅ SUCCESS: {message}", 'success')

    # 创建日志实例
    global logger
    logger = Logger(log_text)

    # 启动授权监控线程
    if license_valid:
        watchdog = LicenseWatchdog()
        watchdog.start()

    # 快捷键处理
    def on_key_press(event):
        if event.keysym == 'F2':
            start_script(license_valid, map_var.get())
        elif event.keysym == 'F10':
            stop_script(license_valid,root)

    root.bind('<KeyPress>', on_key_press)

    # 窗口关闭处理
    def on_closing():
        # stop_all_scripts_silent()
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
        logger.warning('激活码必须是16位字符！')
        messagebox.showinfo('提示', '激活码必须是16位字符！')
        return

    valid_days = verify_activate_code(hwid, input_code)
    if valid_days:
        save_license(hwid, input_code, valid_days)
        days_name = [k for k, v in SUPPORT_DAYS.items() if v == valid_days][0]
        logger.info(f'激活成功：已激活{days_name}权限！')
        messagebox.showinfo('激活成功', '已激活' + days_name + '权限！程序将重启生效')
        # 重启程序
        root.destroy()
        os.startfile(sys.argv[0])
    else:
        logger.error('激活失败：激活码无效、已过期（30分钟内有效）或不匹配本机！')
        messagebox.showinfo('激活失败', '激活码无效、已过期（30分钟内有效）或不匹配本机！')

def start_script(license_valid, map_name):
    if not license_valid:
        logger.warning('未激活/授权已到期，无法启动脚本！')
        messagebox.showinfo('提示', '未激活/授权已到期，无法启动脚本！')
        return

    if map_name == '请选择地图':
        logger.warning('请先选择地图！')
        messagebox.showinfo('提示', '请先选择地图！')
        return

    try:
        if map_name == '联盟大厦S2':
            import dasha
            dasha.set_logger(logger)
            import threading
            t = threading.Thread(target=dasha.run_game_cycle, daemon=True)
            t.start()
            logger.success(f'塔防脚本启动成功！地图：{map_name}')
            messagebox.showinfo('成功', f'塔防脚本启动成功！地图：{map_name}')
        elif map_name == '星港20号S2':
            import xinggang
            xinggang.set_logger(logger)
            import threading
            t = threading.Thread(target=xinggang.run_game_cycle, daemon=True)
            t.start()
            logger.success(f'塔防脚本启动成功！地图：{map_name}')
            messagebox.showinfo('成功', f'塔防脚本启动成功！地图：{map_name}')
        # elif map_name == '联盟大厦KM':
        #     import tafangrunningkm
        #     tafangrunningkm.set_logger(logger)
        #     tafangrunningkm.set_fps(int(fps))
        #     import threading
        #     t = threading.Thread(target=tafangrunningkm.run_game_cycle, daemon=True)
        #     t.start()
        #     logger.success(f'塔防tafangrunningkm脚本启动成功！地图：{map_name}，帧率：{fps}')
        #     messagebox.showinfo('成功', f'塔防脚本tafangrunningkm启动成功！地图：{map_name}，帧率：{fps}')
        elif map_name == '蔷薇庄园歼灭者S2':
            import  zhuangyuanjm
            zhuangyuanjm.set_logger(logger)
            import threading
            t = threading.Thread(target=zhuangyuanjm.run_game_cycle, daemon=True)
            t.start()
            logger.success(f'塔防z脚本启动成功！地图：{map_name}')
            messagebox.showinfo('成功', f'塔防脚本z启动成功！地图：{map_name}')
        elif map_name == '蔷薇庄园天启S2':
            import  zhuangyuantq
            zhuangyuantq.set_logger(logger)
            import threading
            t = threading.Thread(target=zhuangyuantq.run_game_cycle, daemon=True)
            t.start()
            logger.success(f'塔防z脚本启动成功！地图：{map_name}')
            messagebox.showinfo('成功', f'塔防脚本z启动成功！地图：{map_name}')
        else:
            logger.warning('未知的地图选择！')
            messagebox.showinfo('提示', '未知的地图选择！')
    except Exception as e:
        logger.error(f'启动失败：{str(e)}')
        messagebox.showinfo('启动失败', '错误信息：\n' + str(e))

#
def stop_script(license_valid,root):
    if license_valid:
        # 由于我们不再使用tafangmonitor.exe，只需要检查任务进程
        logger.info('已终止所有运行的脚本！')
        # 重启程序
        root.destroy()
        os.startfile(sys.argv[0])
        messagebox.showinfo('成功', '已终止所有运行的脚本！')
    else:
        logger.warning('未激活/授权已到期，无需终止脚本！')
        messagebox.showinfo('提示', '未激活/授权已到期，无需终止脚本！')

if __name__ == '__main__':
    main()
