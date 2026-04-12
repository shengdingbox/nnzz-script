import hashlib
from datetime import datetime

# 常量定义（与main.py保持一致）
SECRET_KEY = 'sd_secure_2026_custom_888'
ACTIVATE_CODE_EXPIRE_MINUTES = 30
SUPPORT_DAYS = {'3小时': 0.125, '1天': 1, '3天': 3, '7天': 7, '30天': 30}
DATE_FORMAT = '%Y%m%d'



def make_activate_code(hwid, days):
    """生成激活码"""
    raw_str = f'{hwid}|{days}|{SECRET_KEY}'
    return hashlib.sha256(raw_str.encode()).hexdigest()[:16].upper()

def main():
    print("塔防自动化助手 - 激活码生成器")
    print("=" * 40)
    
    # 输入机器码
    hwid = input("请输入机器码: ").strip().upper()
    if not hwid or len(hwid) != 16:
        print("错误：机器码必须是16位字符！")
        return
    
    # 选择有效期
    print("\n请选择有效期:")
    for i, (name, value) in enumerate(SUPPORT_DAYS.items(), 1):
        print(f"{i}. {name}")
    
    choice = input("请输入选项编号: ").strip()
    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(SUPPORT_DAYS):
            days_name = list(SUPPORT_DAYS.keys())[choice_idx]
            days_value = SUPPORT_DAYS[days_name]
        else:
            print("错误：无效的选项编号！")
            return
    except ValueError:
        print("错误：请输入有效的数字！")
        return
    
    # 生成激活码
    activate_code = make_activate_code(hwid, days_value)
    
    # 显示结果
    print("\n" + "=" * 40)
    print("生成结果:")
    print(f"机器码: {hwid}")
    print(f"有效期: {days_name}")
    print(f"激活码: {activate_code}")
    print("=" * 40)
    print("注意：激活码有效期为30分钟，请及时使用！")

if __name__ == '__main__':
    main()