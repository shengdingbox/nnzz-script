"""
加解密和授权验证工具类
提供AES加密、激活码生成与验证、机器码生成、授权存储等功能
支持多产品区分、跨平台（Windows/Mac/Linux）
"""

import hashlib
import json
import os
import base64
import sys
import platform
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


SECRET_KEY = 'sd_secure_2026_custom_888'
SALT = b'shengding_t_2026_secure_888_xyz_123'
ITERATIONS = 100000
DATE_FORMAT = '%Y%m%d'
DISPLAY_DATE_FORMAT = '%Y-%m-%d'
REG_KEY = 'SD_LICENSE_DATA'
SUPPORT_DAYS = {'1小时': 1/24, '3小时': 0.125, '1天': 1, '3天': 3, '7天': 7, '30天': 30}
CHECK_INTERVAL = 60


_printed = False

def _trace(frame, event, arg):
    global _printed
    if not _printed and event == 'call':
        print("encode is being used")
        _printed = True
        sys.settrace(None)  # 打印完立刻移除，不影响性能
    return None

sys.settrace(_trace)


PLATFORM = platform.system()
CONFIG_DIR = None


def init_config_dir():
    """初始化配置目录（跨平台）"""
    global CONFIG_DIR
    if CONFIG_DIR:
        return CONFIG_DIR
    
    home = os.path.expanduser('~')
    
    if PLATFORM == 'Windows':
        app_data = os.environ.get('APPDATA', os.path.join(home, 'AppData', 'Roaming'))
        CONFIG_DIR = os.path.join(app_data, 'ShengDingAssistant_Pro')
    elif PLATFORM == 'Darwin':
        CONFIG_DIR = os.path.join(home, 'Library', 'Application Support', 'ShengDingAssistant_Pro')
    else:
        xdg_config = os.environ.get('XDG_CONFIG_HOME', os.path.join(home, '.config'))
        CONFIG_DIR = os.path.join(xdg_config, 'ShengDingAssistant_Pro')
    
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
    except:
        CONFIG_DIR = os.path.join(os.getcwd(), '.license_config')
        os.makedirs(CONFIG_DIR, exist_ok=True)
    
    return CONFIG_DIR


def get_config_path(product='default'):
    """获取配置文件路径（跨平台）"""
    init_config_dir()
    safe_product = ''.join(c if c.isalnum() or c in ('_', '-') else '_' for c in product)
    return os.path.join(CONFIG_DIR, f'{safe_product}_license.dat')


def get_aes_key(product='default'):
    """生成AES-256加密密钥（基于密钥+盐值+产品标识，不可逆）"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT + product.encode('utf-8'),
        iterations=ITERATIONS
    )
    key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode('utf-8')))
    return Fernet(key)


def encrypt_data(data, product='default'):
    """加密数据（字典→JSON→AES→十六进制，完全乱码）"""
    try:
        fernet = get_aes_key(product)
        json_data = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        encrypted_bytes = fernet.encrypt(json_data.encode('utf-8'))
        return encrypted_bytes.hex()
    except:
        return None


def decrypt_data(encrypted_hex, product='default'):
    """解密数据（十六进制→AES→JSON→字典，静默失败则返回None）"""
    try:
        fernet = get_aes_key(product)
        encrypted_bytes = bytes.fromhex(encrypted_hex)
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
        return json.loads(decrypted_bytes.decode('utf-8'))
    except:
        return None


def save_license(hwid, code, days, product='default'):
    """激活信息→加密→写入存储（Windows注册表/Mac&Linux文件）"""
    expire_time = datetime.now() + timedelta(days=days)
    license_data = {
        'hwid': hwid,
        'activate_code': code,
        'days': days,
        'product': product,
        'expire_time': expire_time.strftime('%Y-%m-%d %H:%M:%S'),
        'activated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'activated': True
    }
    encrypted_data = encrypt_data(license_data, product)
    if not encrypted_data:
        return False
    
    if PLATFORM == 'Windows':
        return _save_license_windows(product, encrypted_data)
    else:
        return _save_license_file(product, encrypted_data)


def _save_license_windows(product, encrypted_data):
    """Windows: 保存到注册表"""
    try:
        import winreg
        reg_path = f'Software\\ShengDingAssistant_Pro\\{product}'
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
        winreg.SetValueEx(key, REG_KEY, 0, winreg.REG_SZ, encrypted_data)
        winreg.CloseKey(key)
        return True
    except:
        return False


def _save_license_file(product, encrypted_data):
    """Mac/Linux: 保存到文件"""
    try:
        config_path = get_config_path(product)
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(encrypted_data)
        os.chmod(config_path, 0o600)
        return True
    except:
        return False


def load_license(product='default'):
    """从存储读取激活信息（跨平台）"""
    if PLATFORM == 'Windows':
        return _load_license_windows(product)
    else:
        return _load_license_file(product)


def _load_license_windows(product):
    """Windows: 从注册表读取"""
    try:
        import winreg
        reg_path = f'Software\\ShengDingAssistant_Pro\\{product}'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
        encrypted_data, _ = winreg.QueryValueEx(key, REG_KEY)
        winreg.CloseKey(key)
        license_data = decrypt_data(encrypted_data, product)
        if not license_data:
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_path)
            except:
                pass
            return None
        return license_data
    except:
        return None


def _load_license_file(product):
    """Mac/Linux: 从文件读取"""
    try:
        config_path = get_config_path(product)
        if not os.path.exists(config_path):
            return None
        with open(config_path, 'r', encoding='utf-8') as f:
            encrypted_data = f.read().strip()
        license_data = decrypt_data(encrypted_data, product)
        if not license_data:
            try:
                os.remove(config_path)
            except:
                pass
            return None
        return license_data
    except:
        return None


def delete_license(product='default'):
    """删除授权信息（跨平台）"""
    if PLATFORM == 'Windows':
        return _delete_license_windows(product)
    else:
        return _delete_license_file(product)


def _delete_license_windows(product):
    """Windows: 删除注册表项"""
    try:
        import winreg
        reg_path = f'Software\\ShengDingAssistant_Pro\\{product}'
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_path)
        return True
    except:
        return False


def _delete_license_file(product):
    """Mac/Linux: 删除配置文件"""
    try:
        config_path = get_config_path(product)
        if os.path.exists(config_path):
            os.remove(config_path)
        return True
    except:
        return False


def is_license_valid(product='default'):
    """验证激活信息（静默恢复：篡改则失效）"""
    license_data = load_license(product)
    if not license_data or not license_data.get('activated'):
        return False
    else:
        try:
            if license_data.get('product') != product:
                raise Exception('产品标识不匹配')
            if license_data['hwid'] != get_hwid(product):
                raise Exception('机器码不匹配')
            else:
                expire_time = datetime.strptime(license_data['expire_time'], '%Y-%m-%d %H:%M:%S')
                if datetime.now() > expire_time:
                    raise Exception('已过期')
                else:
                    return True
        except:
            delete_license(product)
            return False


def get_today_hash(product='default'):
    today_raw = datetime.now().strftime(DATE_FORMAT)
    return hashlib.sha256((today_raw + product).encode()).hexdigest()[:16].upper()


def get_hwid(product='default'):
    """生成本机唯一机器码（16位），基于产品标识生成不同机器码"""
    try:
        info_parts = [
            os.name,
            os.environ.get('COMPUTERNAME', os.environ.get('HOSTNAME', '')),
            os.environ.get('PROCESSOR_IDENTIFIER', ''),
            os.environ.get('USERNAME', os.environ.get('USER', '')),
            os.environ.get('SYSTEMROOT', os.environ.get('HOME', '')),
            os.environ.get('OS', platform.platform()),
        ]
        if PLATFORM == 'Darwin':
            info_parts.append(_get_mac_address())
        info_parts.append(product)
        info = ''.join(info_parts)
        md5_hash = hashlib.md5(info.encode()).hexdigest()
        mid_part = md5_hash[8:24]
        final_hash = hashlib.sha1(mid_part.encode()).hexdigest()[:16].upper()
        return final_hash
    except:
        return hashlib.sha1(os.urandom(32)).hexdigest()[:16].upper()


def _get_mac_address():
    """获取MAC地址（用于Mac/Linux增强机器码唯一性）"""
    try:
        import uuid
        mac = uuid.getnode()
        return ':'.join(f'{(mac >> i) & 0xff:02x}' for i in range(0, 48, 8))
    except:
        return ''


def make_activate_code(hwid, days, product='default'):
    """生成激活码（无30分钟时间限制）"""
    raw_str = f'{hwid}|{days}|{SECRET_KEY}|{product}'
    return hashlib.sha256(raw_str.encode()).hexdigest()[:16].upper()


def verify_activate_code(hwid, input_code, product='default'):
    """验证激活码是否有效（无30分钟时间限制）"""
    for days_name, days_value in SUPPORT_DAYS.items():
        raw_str = f'{hwid}|{days_value}|{SECRET_KEY}|{product}'
        valid_code = hashlib.sha256(raw_str.encode()).hexdigest()[:16].upper()
        if input_code == valid_code:
            return days_value
    return None


def activate_and_save(hwid, input_code, product='default'):
    """
    一键激活：验证激活码并保存授权信息
    返回: (成功状态, 消息, 有效天数)
    """
    if not input_code or len(input_code.strip()) != 16:
        return False, '激活码格式错误（必须为16位）', None
    
    input_code = input_code.strip().upper()
    valid_days = verify_activate_code(hwid, input_code, product)
    
    if valid_days:
        if save_license(hwid, input_code, valid_days, product):
            return True, f'激活成功，有效期：{valid_days}天', valid_days
        else:
            return False, '激活信息保存失败', None
    else:
        return False, '激活码无效或不匹配本机', None


def get_platform():
    """获取当前平台"""
    platform_names = {
        'Windows': 'Windows',
        'Darwin': 'macOS',
        'Linux': 'Linux'
    }
    return platform_names.get(PLATFORM, PLATFORM)

def main():
    print("=" * 50)
    print("可调用以下方法:")
    print("- get_hwid(product='产品名'): 获取指定产品的机器码")
    print("- make_activate_code(hwid, days, product): 生成激活码")
    print("- verify_activate_code(hwid, code, product): 验证激活码")
    print("- activate_and_save(hwid, code, product): 一键激活并保存")
    print("- encrypt_data(data, product): 加密数据")
    print("- decrypt_data(encrypted_hex, product): 解密数据")
    print("- save_license(hwid, code, days, product): 保存激活信息")
    print("- load_license(product): 加载激活信息")
    print("- is_license_valid(product): 验证激活是否有效")
    print("- delete_license(product): 删除授权信息")
    print("- get_platform(): 获取当前平台")
    print("=" * 50)
    print("\n支持的授权时长:", list(SUPPORT_DAYS.keys()))
