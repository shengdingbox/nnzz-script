"""
加解密和授权验证工具类
提供AES加密、激活码生成与验证、机器码生成、注册表存储等功能
支持多产品区分
"""

import hashlib
import json
import os
import base64
import winreg
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


def get_reg_path(product='default'):
    """获取注册表路径（包含产品标识）"""
    return f'Software\\ShengDingAssistant_Pro\\{product}'


def save_license(hwid, code, days, product='default'):
    """激活信息→加密→写入注册表（无文件，完全隐藏）"""
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
    else:
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, get_reg_path(product))
            winreg.SetValueEx(key, REG_KEY, 0, winreg.REG_SZ, encrypted_data)
            winreg.CloseKey(key)
            return True
        except:
            return False


def load_license(product='default'):
    """从注册表→解密→读取激活信息（静默验证）"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, get_reg_path(product))
        encrypted_data, _ = winreg.QueryValueEx(key, REG_KEY)
        winreg.CloseKey(key)
        license_data = decrypt_data(encrypted_data, product)
        if not license_data:
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, get_reg_path(product))
            except:
                pass
            return None
        else:
            return license_data
    except:
        return None


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
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, get_reg_path(product))
            except:
                pass
            return False


def get_today_hash(product='default'):
    today_raw = datetime.now().strftime(DATE_FORMAT)
    return hashlib.sha256((today_raw + product).encode()).hexdigest()[:16].upper()


def get_hwid(product='default'):
    """生成本机唯一机器码（16位），基于产品标识生成不同机器码"""
    try:
        info = (
            f"{os.name}"
            f"{os.environ.get('COMPUTERNAME', '')}"
            f"{os.environ.get('PROCESSOR_IDENTIFIER', '')}"
            f"{os.environ.get('USERNAME', '')}"
            f"{os.environ.get('SYSTEMROOT', '')}"
            f"{os.environ.get('OS', '')}"
            f"{product}"
        )
        md5_hash = hashlib.md5(info.encode()).hexdigest()
        mid_part = md5_hash[8:24]
        final_hash = hashlib.sha1(mid_part.encode()).hexdigest()[:16].upper()
        return final_hash
    except:
        return hashlib.sha1(os.urandom(32)).hexdigest()[:16].upper()


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
    - 成功返回 (True, '激活成功', 天数)
    - 失败返回 (False, '失败原因', None)
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


if __name__ == '__main__':
    print("=" * 50)
    print("加解密工具类 - 多产品支持")
    print("=" * 50)
    
    products = ['塔防助手', '星港脚本', 'default']
    
    for product in products:
        print(f"\n【产品: {product}】")
        hwid = get_hwid(product)
        print(f"  机器码: {hwid}")
        print(f"  授权状态: {'已激活' if is_license_valid(product) else '未激活'}")
        license_data = load_license(product)
        if license_data:
            print(f"  过期时间: {license_data.get('expire_time', 'N/A')}")
        
    print("\n" + "=" * 50)
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
    print("=" * 50)
    print("\n支持的授权时长:", list(SUPPORT_DAYS.keys()))
