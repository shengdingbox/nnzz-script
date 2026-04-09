global wave_counter
global last_wave_counter
global wave_lock
import sys
import os
import time
import cv2
import numpy as np
from PIL import ImageGrab
import threading
import msvcrt
import win32api
import win32con
import traceback
from win32comext.propsys.pscon import PKEY_Photo_FocalPlaneXResolution
def resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和 PyInstaller 打包后的环境"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)
_template_cache = {}
cache_lock = threading.Lock()
wave_counter = 0
last_wave_counter = 0
wave_lock = threading.Lock()
def simulate_mouse_wheel(x, y, scroll_amount=120):
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, x, y, scroll_amount, 0)
def repeat_scroll(x, y, scroll_amount=120, times=10):
    """重复滚动指定次数"""
    print(f'开始在({x}, {y})位置滚动{times}次...')
    for i in range(times):
        simulate_mouse_wheel(x, y, scroll_amount)
        time.sleep(0.02)
    print('滚动完成！')
# 定义函数：key=要按的键，press_duration=按键持续时间（默认0.05秒）
def press_key(key, press_duration=0.05):
    # 注释：无关代码（应该是静态分析工具生成的提示，无实际作用）
    # irreducible cflow, using cdg fallback
    # ***<module>.press_key: Failure: Different control flow

    # 字典：映射【按键名称】和Windows系统【虚拟键码】（系统识别按键的唯一编号）
    special_keys = {
        'ENTER': win32con.VK_RETURN,
        'RETURN': win32con.VK_RETURN,
        'SPACE': win32con.VK_SPACE,
        'TAB': win32con.VK_TAB,
        'ESC': win32con.VK_ESCAPE,
        'ESCAPE': win32con.VK_ESCAPE,
        'CTRL': win32con.VK_CONTROL,
        'ALT': win32con.VK_MENU,
        'SHIFT': win32con.VK_SHIFT,
        'BACKSPACE': win32con.VK_BACK,
        'DELETE': win32con.VK_DELETE
    }

    # 判断：如果按键以F开头（F1-F12），且长度是2/3位
    if key.upper().startswith('F') and len(key) in [2, 3]:
        f_num = int(key[1:])  # 提取F后面的数字（如F5 → 5）
        if 1 <= f_num <= 12:  # 判断是否是合法功能键（F1-F12）
            vk_code = getattr(win32con, f'VK_F{f_num}')  # 获取F键的虚拟键码
            # 【致命bug】这里直接抛错误，永远不会执行按键操作
            raise ValueError(f'不支持的功能键: {key}')

    # 【致命bug】缩进错误！这段代码被包含在上面的if里，永远执行不到
    if key.upper() in special_keys:
        vk_code = special_keys[key.upper()]  # 匹配特殊键，获取键码
    else:
        if len(key) == 1:  # 普通单字符按键（A-Z、0-9）
            vk_code = ord(key.upper())  # 转成ASCII码
        else:
            raise ValueError(f'不支持的按键: {key}')  # 不支持的按键抛错

    # 【致命bug】缩进错误！模拟按键的核心代码被包在else里，永远执行不到
    win32api.keybd_event(vk_code, 0, 0, 0)  # 模拟【按下】按键
    time.sleep(press_duration)  # 按住指定时长
    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)  # 模拟【松开】按键
    if logger:
        logger.info(f'已按下: {key}')
    else:
        print(f'已按下: {key}')
# ===================== 修复后的找图函数 =====================
def find_image(template_path, threshold=0.8):
    """
    屏幕找图：在全屏中搜索指定图片
    :param template_path: 要搜索的小图片路径
    :param threshold: 相似度阈值（0~1，越高越严格）
    :return: 找到返回 (中心点x, 中心点y, 相似度)，没找到返回None
    """
    try:
        with cache_lock:
            # 【修复】缓存存在，直接读取，跳过重复加载
            if template_path in _template_cache:
                template, h, w = _template_cache[template_path]
            else:
                # 缓存不存在，读取图片并缓存
                template = cv2.imread(template_path, 0)
                if template is None:
                    if logger:
                        logger.error(f'错误：无法读取图片 -> {template_path}')
                    else:
                        print(f'错误：无法读取图片 -> {template_path}')
                    return None
                h, w = template.shape
                _template_cache[template_path] = (template, h, w)

        # 全屏截图
        screen = ImageGrab.grab()
        # 转换为OpenCV格式
        screen_np = np.array(screen)
        screen_bgr = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
        screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)

        # 模板匹配
        result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        # 判断是否匹配成功
        if max_val >= threshold:
            x = max_loc[0] + w // 2
            y = max_loc[1] + h // 2
            return (x, y, max_val)
        else:
            if logger:
                # logger.info(f'未找到目标图片{template_path} | 最高相似度: {max_val:.3f}')
                time.sleep(0.1)
            else:
                print(f'未找到目标图片 | 最高相似度: {max_val:.3f}')
            return None

    except Exception as e:
        if logger:
            logger.error(f'找图失败，错误信息: {str(e)}')
        else:
            print(f'找图失败，错误信息: {str(e)}')
        return None
    
def click_at(x, y, button='left', delay=0.1):
    win32api.SetCursorPos((x, y))
    time.sleep(0.05)
    if button == 'left':
        down_event = win32con.MOUSEEVENTF_LEFTDOWN
        up_event = win32con.MOUSEEVENTF_LEFTUP
    else:
        if button == 'right':
            down_event = win32con.MOUSEEVENTF_RIGHTDOWN
            up_event = win32con.MOUSEEVENTF_RIGHTUP
        else:
            raise ValueError('button参数必须是\'left\'或\'right\'')
    win32api.mouse_event(down_event, 0, 0)
    time.sleep(delay)
    win32api.mouse_event(up_event, 0, 0)
    time.sleep(delay)
    win32api.SetCursorPos((410, 310))
    print(f'已在坐标 ({x}, {y}) 点击{button}键')
def wait_for_image(template_path, threshold=0.75, check_interval=1.0, Afterrecognition=0.0):
    print(f'等待图片出现: {template_path}')
    while True:
        result = find_image(template_path, threshold)
        if result is not None:
            x, y, similarity = result
            print(f'✅ 检测到目标图片！坐标: ({x}, {y}), 相似度: {similarity:.3f}')
            time.sleep(Afterrecognition)
            return result
        else:
            time.sleep(check_interval)
def periodic_image_check():
    target_image = resource_path('xinggang/guajijiance.png')
    threshold = 0.7
    while True:
        result = find_image(target_image, threshold)
        if result:
            click_at(960, 680, button='left')
            time.sleep(0.1)
            press_key('SPACE')
        time.sleep(60)
def initial_position(W=0, S=0.4):
    press_key('o')
    time.sleep(1.2)
    press_key('SPACE')
    time.sleep(0.2)
    press_key('o')
    time.sleep(2)
    press_key('W', press_duration=W)
    time.sleep(0.5)
    press_key('S', press_duration=S)
def initial_positionscoll(W=0, S=0.4, A=0, D=0):
    press_key('o')
    time.sleep(0.2)
    press_key('SPACE')
    time.sleep(0.2)
    press_key('o')
    time.sleep(0.2)
    repeat_scroll(960, 540, scroll_amount=(-120), times=20)
    time.sleep(0.2)
    if W!= 0:
        press_key('W', press_duration=W)
        time.sleep(0.5)
    if A!= 0:
        press_key('A', press_duration=A)
        time.sleep(0.5)
    if S!= 0:
        press_key('S', press_duration=S)
        time.sleep(0.5)
    if D!= 0:
        press_key('D', press_duration=D)
        time.sleep(0.5)
def wave_monitor():
    global last_wave_counter
    CHECK_INTERVAL = 300
    while True:
        time.sleep(CHECK_INTERVAL)
        with wave_lock:
            currentnow = wave_counter
            print(f'波次监控：当前计数器={currentnow}，上次记录={last_wave_counter}')
            if currentnow == last_wave_counter:
                print('检测到波次卡死，准备重启游戏...')
                restart_game()
                return
            else:
                last_wave_counter = currentnow
def restart_game():
    """尝试关闭游戏并重启进程（退出当前进程由外部监控重启）"""
    for _ in range(2):
        result = find_image(resource_path('photo/shibai.png'), 0.7)
        if result:
            print('识别到失败')
            for i in range(10):
                press_key('SPACE')
                time.sleep(0.5)
            click_at(1454, 220, button='left')
            os._exit(1)
        result = find_image(resource_path('photo/qwlianyukaishi.png'), 0.7)
        if result:
            print('识别到炼狱开始')
            click_at(1454, 220, button='left')
            os._exit(1)
        result = find_image(resource_path('photo/tiaozhanmoshi.png'), 0.7)
        if result:
            print('识别到挑战模式')
            os._exit(1)
        result = find_image(resource_path('photo/zhujiemian.png'), 0.7)
        if result:
            print('识别到主界面')
            click_at(1675, 930, button='left')
            time.sleep(3)
            click_at(521, 502, button='left')
            time.sleep(3)
            result = find_image(resource_path('photo/qwlianyukaishi.png'), 0.7)
            if result:
                print('识别到炼狱开始')
                click_at(1454, 220, button='left')
                os._exit(1)
            result = find_image(resource_path('photo/tiaozhanmoshi.png'), 0.7)
            if result:
                print('识别到挑战模式')
                os._exit(1)
            os._exit(1)
        time.sleep(10)
        print('自检未检测到')
def traverse():
    result = find_image(resource_path('photo/qwlianyukaishi.png'), 0.7)
    if result:
        print('识别到炼狱开始')
        return True
    else:
        result = find_image(resource_path('photo/tiaozhanmoshi.png'), 0.7)
        if result:
            print('识别到挑战模式')
            click_at(1454, 220, button='left')
        result = find_image(resource_path('photo/zhujiemian.png'), 0.7)
        if result:
            print('识别到主界面')
            click_at(1675, 930, button='left')
            time.sleep(3)
            click_at(521, 502, button='left')
            time.sleep(3)
            result = find_image(resource_path('photo/qwlianyukaishi.png'), 0.7)
            if result:
                print('识别到炼狱开始')
                click_at(1688, 954, button='left')
            result = find_image(resource_path('photo/tiaozhanmoshi.png'), 0.7)
            if result:
                print('识别到挑战模式')
        result = find_image(resource_path('photo/shibai.png'), 0.7)
        if result:
            print('识别到失败')
            for i in range(10):
                press_key('SPACE')
                time.sleep(0.5)
            click_at(1454, 220, button='left')
        result = find_image(resource_path('photo/qwbuzaitixing.png'), threshold=0.75)
        if result:
            time.sleep(1)
            click_at(899, 598, button='left')
            time.sleep(1)
            click_at(1100, 670, button='left')
            time.sleep(1)
        return False
def main():
    # irreducible cflow, using cdg fallback
    global wave_counter
    # ***<module>.main: Failure: Compilation Error
    with wave_lock:
        wave_counter += 1
        print(f'当前完成波次: {wave_counter}')
    press_key('N')
    time.sleep(0.5)
    image_path = resource_path('photo/tianwang.png')
    result = find_image(image_path, threshold=0.6)
    if result:
        x, y, similarity = result
        print(f'✅ 找到图片！坐标: ({x}, {y}), 相似度: {similarity:.3f}')
        click_at(x, y, button='left')
    time.sleep(0.5)
    image_path = resource_path('photo/zixiufucibaota.png')
    result = find_image(image_path, threshold=0.6)
    if result:
        x, y, similarity = result
        print(f'✅ 找到图片！坐标: ({x}, {y}), 相似度: {similarity:.3f}')
        click_at(x, y, button='left')
    time.sleep(0.5)
    image_path = resource_path('photo/tianqi.png')
    result = find_image(image_path, threshold=0.6)
    if result:
        x, y, similarity = result
        print(f'✅ 找到图片！坐标: ({x}, {y}), 相似度: {similarity:.3f}')
        click_at(x, y, button='left')
    time.sleep(0.5)
    image_path = resource_path('photo/fangkong.png')
    result = find_image(image_path, threshold=0.6)
    if result:
        x, y, similarity = result
        print(f'✅ 找到图片！坐标: ({x}, {y}), 相似度: {similarity:.3f}')
        click_at(x, y, button='left')
    time.sleep(0.5)
    press_key('N')
    time.sleep(0.5)
    time.sleep(0.5)
    press_key('o')
    time.sleep(0.5)
    initial_positionscoll(W=0.8, S=0, A=0.5, D=0)
    with wave_lock:
        wave_counter += 1
        print(f'当前完成波次: {wave_counter}')
    press_key('G')
    time.sleep(0.5)
    image_path = resource_path('photo/0011.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 650 < xinit < 750 and 200 < yinit < 300:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit - 110
    ybase = yinit + 505
    time.sleep(0.5)
    press_key('4')
    time.sleep(0.5)
    indexes = [0, 1]
    for idx in indexes:
        x = xbase
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 192
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    initial_positionscoll(W=0.8, S=0, A=0, D=2)
    initial_positionscoll(W=0.8, S=0, A=0.5, D=0)
    time.sleep(0.5)
    initial_positionscoll(W=0.8, S=0, A=0.5, D=0)
    time.sleep(0.5)
    image_path = resource_path('photo/0011.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 1150 < xinit < 1250 and 200 < yinit < 300:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit - 103
    ybase = yinit + 505
    time.sleep(0.5)
    press_key('4')
    time.sleep(0.5)
    indexes = [0, 1]
    for idx in indexes:
        x = xbase
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 192
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    time.sleep(10)
    for i in range(10):
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.5)
    wait_for_image(resource_path('photo/BOCIERWANCHENG.png'), threshold=0.7)
    with wave_lock:
        wave_counter += 1
        print(f'当前完成波次: {wave_counter}')
    press_key('G')
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0, A=1, D=0)
    initial_positionscoll(W=0.8, S=0, A=0, D=2)
    time.sleep(0.5)
    initial_positionscoll(W=0.8, S=0, A=0, D=2)
    time.sleep(0.5)
    image_path = resource_path('photo/0021.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 200 < xinit < 300 and 650 < yinit < 750:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit + 266 + 96
    ybase = yinit - 233 - 96
    time.sleep(0.5)
    press_key('4')
    indexes = [0, 1]
    for idx in indexes:
        x = xbase
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 192
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    time.sleep(0.2)
    press_key('5')
    time.sleep(0.5)
    click_at(xinit + 467, yinit - 174, button='left', delay=0.1)
    time.sleep(0.5)
    click_at(xinit + 467, yinit - 174, button='left', delay=0.1)
    initial_positionscoll(W=0, S=0, A=0, D=2)
    initial_positionscoll(W=0, S=0, A=1, D=0)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0, A=1, D=0)
    time.sleep(0.5)
    image_path = resource_path('photo/0022.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 1650 < xinit < 1750 and 650 < yinit < 750:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit - 571
    ybase = yinit - 329
    time.sleep(0.5)
    press_key('4')
    indexes = [0, 1]
    for idx in indexes:
        x = xbase
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 192
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    press_key('5')
    time.sleep(10)
    for i in range(10):
        click_at(xinit - 471, yinit - 169, button='left', delay=0.1)
        time.sleep(0.5)
    wait_for_image(resource_path('photo/BOCIERWANCHENG.png'), threshold=0.75)
    with wave_lock:
        wave_counter += 1
        print(f'当前完成波次: {wave_counter}')
    press_key('G')
    time.sleep(0.5)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0, A=0, D=0.5)
    initial_positionscoll(W=0, S=0, A=0, D=2)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0, A=0, D=2)
    time.sleep(0.5)
    image_path = resource_path('photo/0031.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 1300 < xinit < 1400 and 60 < yinit < 160:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit - 1019
    ybase = yinit + 281
    press_key('2')
    time.sleep(0.5)
    press_key('7')
    indexes = [0, 1, 2]
    for idx in indexes:
        x = xbase
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    indexes = [0, 1, 2, 3]
    for idx in indexes:
        x = xbase + 320
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    xbase = xinit + 70
    ybase = yinit + 281
    indexes = [0, 1, 2]
    for idx in indexes:
        x = xbase
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    indexes = [0, 1, 2, 3]
    for idx in indexes:
        x = xbase - 320
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    press_key('5', press_duration=2)
    time.sleep(10)
    wait_for_image(resource_path('photo/BOCIERWANCHENG.png'), threshold=0.75)
    with wave_lock:
        wave_counter += 1
        print(f'当前完成波次: {wave_counter}')
    press_key('G')
    time.sleep(0.3)
    initial_positionscoll(W=0, S=0, A=1, D=0)
    initial_positionscoll(W=0, S=0, A=0, D=0.5)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0, A=0, D=0.5)
    time.sleep(0.5)
    image_path = resource_path('photo/0021.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 200 < xinit < 300 and 650 < yinit < 750:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit + 362
    ybase = yinit - 233
    click_at(xinit + 467, yinit - 174, button='left', delay=0.1)
    time.sleep(0.3)
    press_key('E')
    time.sleep(0.2)
    initial_positionscoll(W=0, S=0, A=0, D=2)
    initial_positionscoll(W=0, S=0, A=1, D=0)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0, A=1, D=0)
    time.sleep(0.5)
    image_path = resource_path('photo/0022.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 1650 < xinit < 1750 and 650 < yinit < 750:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit - 571
    ybase = yinit - 329
    click_at(xinit - 471, yinit - 169, button='left', delay=0.1)
    time.sleep(0.5)
    press_key('E')
    time.sleep(0.2)
    initial_positionscoll(W=0, S=0.8, A=0, D=0.5)
    initial_positionscoll(W=0, S=0, A=0, D=2)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0, A=0, D=2)
    time.sleep(0.5)
    image_path = resource_path('photo/2041.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 650 < xinit < 750 and 400 < yinit < 500:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit + 53
    ybase = yinit + 1
    time.sleep(0.5)
    press_key('4')
    time.sleep(0.5)
    indexes = [0, 1]
    for idx in indexes:
        x = xbase + 32 - 384
        y = ybase + 32 + 64 * idx - 64
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 32 - 192
        y = ybase + 32 + 64 * idx - 64
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 32
        y = ybase + 32 + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 32 + 192
        y = ybase + 32 + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 32 + 384
        y = ybase + 32 + 64 * idx - 64
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 32 + 576
        y = ybase + 32 + 64 * idx - 64
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    press_key('5')
    indexes = [(-1), 1]
    for idx in indexes:
        x = xbase + 128 + 64 * idx
        y = ybase + 192
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 128 + 384 * idx
        y = ybase + 128
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    press_key('6')
    for idx in indexes:
        x = xbase + 128 + 256 * idx
        y = ybase + 192
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    time.sleep(5)
    press_key('7', press_duration=2)
    time.sleep(30)
    press_key('6', press_duration=2)
    wait_for_image(resource_path('photo/BOCIERWANCHENG.png'), threshold=0.75)
    with wave_lock:
        wave_counter += 1
        print(f'当前完成波次: {wave_counter}')
    press_key('G')
    time.sleep(0.2)
    for idx in indexes:
        x = xbase + 128 + 384 * idx
        y = ybase + 128
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.2)
        press_key('E')
        time.sleep(0.2)
    for idx in indexes:
        x = xbase + 128 + 256 * idx
        y = ybase + 192
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.2)
        press_key('E')
        time.sleep(0.2)
    press_key('5')
    indexes = [0, 1]
    for idx in indexes:
        x = xbase - 320 + 128 * idx
        y = ybase + 128
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 448 + 128 * idx
        y = ybase + 128
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    press_key('6')
    for idx in indexes:
        x = xbase - 256 + 128 * idx
        y = ybase + 256
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 384 + 128 * idx
        y = ybase + 256
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 64 + 128 * idx
        y = ybase + 320
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    indexes = [(-1), 1]
    for idx in indexes:
        x = xbase + 128 + 576 * idx
        y = ybase + 192
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    press_key('7')
    time.sleep(20)
    indexes = [0, 1, 2, 3]
    for idx in indexes:
        x = xbase - 64 - 32
        y = ybase - 320 + 32 + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 320 + 32
        y = ybase - 320 + 32 + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    initial_positionscoll(W=0, S=0, A=0, D=0.5)
    initial_positionscoll(W=0, S=0.8, A=0, D=0.5)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0.8, A=0, D=0.5)
    time.sleep(0.5)
    image_path = resource_path('photo/0031.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 1300 < xinit < 1400 and 60 < yinit < 160:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit - 1019
    ybase = yinit + 281
    time.sleep(0.5)
    press_key('2')
    time.sleep(0.5)
    press_key('7')
    time.sleep(5)
    indexes = [0, 1, 2]
    for idx in indexes:
        x = xbase
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    indexes = [0, 1, 2, 3]
    for idx in indexes:
        x = xbase + 320
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    xbase = xinit + 70
    ybase = yinit + 281
    indexes = [0, 1, 2]
    for idx in indexes:
        x = xbase
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    indexes = [0, 1, 2, 3]
    for idx in indexes:
        x = xbase - 320
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    time.sleep(20)
    xbase = xinit - 1019
    ybase = yinit + 281
    indexes = [0, 1, 2]
    for idx in indexes:
        x = xbase
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    indexes = [0, 1, 2, 3]
    for idx in indexes:
        x = xbase + 320
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    xbase = xinit + 70
    ybase = yinit + 281
    indexes = [0, 1, 2]
    for idx in indexes:
        x = xbase
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    indexes = [0, 1, 2, 3]
    for idx in indexes:
        x = xbase - 320
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    wait_for_image(resource_path('photo/BOCIERWANCHENG.png'), threshold=0.75)
    with wave_lock:
        wave_counter += 1
        print(f'当前完成波次: {wave_counter}')
    press_key('G')
    time.sleep(0.5)
    press_key('5', press_duration=2)
    press_key('6', press_duration=2)
    press_key('7', press_duration=2)
    initial_positionscoll(W=0, S=0, A=0, D=0.5)
    initial_positionscoll(W=0, S=0, A=0, D=0.5)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0, A=0, D=0.5)
    time.sleep(0.5)
    image_path = resource_path('photo/0031.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 1300 < xinit < 1400 and 60 < yinit < 160:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit - 1019
    ybase = yinit + 281
    time.sleep(0.5)
    press_key('2')
    time.sleep(0.5)
    press_key('7')
    time.sleep(0.5)
    indexes = [0, 1, 2]
    for idx in indexes:
        x = xbase
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    indexes = [0, 1, 2, 3]
    for idx in indexes:
        x = xbase + 320
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    xbase = xinit + 70
    ybase = yinit + 281
    indexes = [0, 1, 2]
    for idx in indexes:
        x = xbase
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    indexes = [0, 1, 2, 3]
    for idx in indexes:
        x = xbase - 320
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    initial_positionscoll(W=0, S=1.0, A=0, D=0.5)
    initial_positionscoll(W=0, S=0, A=0, D=0.5)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0, A=0, D=0.5)
    time.sleep(0.5)
    image_path = resource_path('photo/0041.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 1050 < xinit < 1150 and 250 < yinit < 350:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit - 317
    ybase = yinit + 1
    press_key('6')
    time.sleep(0.5)
    indexes = [0, 1, 2]
    for idx in indexes:
        x = xbase + 128 * idx
        y = ybase + 448
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    press_key('7')
    time.sleep(0.5)
    indexes = [0, 1, 2, 3]
    for idx in indexes:
        x = xbase + 320 + 32 + 64 * idx
        y = ybase + 320 + 32
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase - 64 - 32 - 64 * idx
        y = ybase + 320 + 32
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    time.sleep(20)
    press_key('6')
    time.sleep(0.5)
    indexes = [(-1), 1]
    for idx in indexes:
        x = xbase + 128 + 512 * idx
        y = ybase + 320
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    wait_for_image(resource_path('photo/BOCIERWANCHENG.png'), threshold=0.75)
    with wave_lock:
        wave_counter += 1
        print(f'当前完成波次: {wave_counter}')
    press_key('G')
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0, A=0, D=0.5)
    initial_positionscoll(W=0, S=1.0, A=0, D=0.5)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=1.0, A=0, D=0.5)
    time.sleep(0.5)
    image_path = resource_path('photo/0031.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 1300 < xinit < 1400 and 80 < yinit < 150:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit - 982
    ybase = yinit + 505
    time.sleep(0.5)
    press_key('2')
    time.sleep(0.5)
    press_key('4')
    time.sleep(0.5)
    indexes = [0, 1, 2, 3]
    for idx in indexes:
        x = xbase + 32
        y = ybase + 32 + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 32 + 192
        y = ybase + 32 + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 32 + 768
        y = ybase + 32 + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 32 + 960
        y = ybase + 32 + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    initial_positionscoll(W=0, S=0.8, A=0.5, D=0)
    initial_positionscoll(W=0, S=0, A=0, D=0.5)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0, A=0, D=0.5)
    time.sleep(0.5)
    image_path = resource_path('photo/0071.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 500 < xinit < 600 and 750 < yinit < 850:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit + 357
    ybase = yinit - 320
    time.sleep(0.5)
    press_key('7')
    time.sleep(0.5)
    indexes = [0, 1, 2]
    for idx in indexes:
        x = xbase + 64 * idx
        y = ybase
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    initial_positionscoll(W=0, S=0.8, A=0, D=2)
    initial_positionscoll(W=0, S=0.8, A=0.5, D=0)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0.8, A=0.5, D=0)
    time.sleep(0.5)
    image_path = resource_path('photo/0072.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 1400 < xinit < 1500 and 650 < yinit < 750:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit - 562
    ybase = yinit - 199
    time.sleep(0.5)
    press_key('7')
    time.sleep(0.5)
    indexes = [0, 1, 2]
    for idx in indexes:
        x = xbase + 64 * idx
        y = ybase
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    time.sleep(0.5)
    press_key('4', press_duration=2)
    time.sleep(0.5)
    press_key('5', press_duration=2)
    time.sleep(20)
    press_key('6', press_duration=2)
    wait_for_image(resource_path('photo/BOCIERWANCHENG.png'), threshold=0.75)
    with wave_lock:
        wave_counter += 1
        print(f'当前完成波次: {wave_counter}')
    press_key('G')
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0.8, A=0.5, D=0)
    initial_positionscoll(W=0, S=0.8, A=0, D=2)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0.8, A=0, D=2)
    time.sleep(0.5)
    image_path = resource_path('photo/0071.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 500 < xinit < 600 and 750 < yinit < 850:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit + 132
    ybase = yinit - 546
    press_key('5')
    time.sleep(0.5)
    indexes = [0, 1]
    for idx in indexes:
        x = xbase + 64 + 128 * idx
        y = ybase + 64
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    press_key('6')
    time.sleep(0.5)
    for idx in indexes:
        x = xbase - 64
        y = ybase + 128 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 256
        y = ybase + 128 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 320
        y = ybase + 128 * idx + 320
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    click_at(xbase + 192, ybase + 384, button='left', delay=0.1)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0.8, A=0, D=2)
    initial_positionscoll(W=0, S=0.8, A=0.5, D=0)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0.8, A=0.5, D=0)
    time.sleep(0.5)
    image_path = resource_path('photo/0072.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 1400 < xinit < 1500 and 650 < yinit < 750:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit - 210
    ybase = yinit - 426
    press_key('5')
    time.sleep(0.5)
    indexes = [0, 1]
    for idx in indexes:
        x = xbase - 64 - 128 * idx
        y = ybase + 64
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    press_key('6')
    time.sleep(0.5)
    for idx in indexes:
        x = xbase + 64
        y = ybase + 128 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase - 320
        y = ybase + 128 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase - 320
        y = ybase + 128 * idx + 320
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    click_at(xbase - 192, ybase + 384, button='left', delay=0.1)
    initial_positionscoll(W=0, S=0, A=0, D=0.5)
    initial_positionscoll(W=0, S=0.8, A=0, D=2)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0.8, A=0, D=2)
    time.sleep(0.5)
    image_path = resource_path('photo/0031.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 1300 < xinit < 1400 and 60 < yinit < 160:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit - 1019
    ybase = yinit + 281
    press_key('2')
    time.sleep(0.5)
    press_key('7')
    indexes = [0, 1, 2]
    for idx in indexes:
        x = xbase
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    indexes = [0, 1, 2, 3]
    for idx in indexes:
        x = xbase + 320
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    xbase = xinit + 70
    ybase = yinit + 281
    indexes = [0, 1, 2]
    for idx in indexes:
        x = xbase
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    indexes = [0, 1, 2, 3]
    for idx in indexes:
        x = xbase - 320
        y = ybase + 64 * idx
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    initial_positionscoll(W=0, S=1.0, A=0, D=0.5)
    initial_positionscoll(W=0, S=0, A=0, D=0.5)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0, A=0, D=0.5)
    time.sleep(0.5)
    image_path = resource_path('photo/0041.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 1050 < xinit < 1150 and 250 < yinit < 350:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    xbase = xinit - 317
    ybase = yinit + 1
    time.sleep(0.5)
    press_key('5')
    time.sleep(0.5)
    indexes = [0, 1]
    for idx in indexes:
        x = xbase - 320 + 128 * idx
        y = ybase + 128
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 448 + 128 * idx
        y = ybase + 128
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 448 + 128 * idx
        y = ybase + 192
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    time.sleep(0.5)
    press_key('6')
    time.sleep(0.5)
    for idx in indexes:
        x = xbase - 256 + 128 * idx
        y = ybase + 256
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 384 + 128 * idx
        y = ybase + 256
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 64 + 128 * idx
        y = ybase + 320
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    indexes = [(-1), 1]
    for idx in indexes:
        x = xbase + 128 + 576 * idx
        y = ybase + 192
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    for idx in indexes:
        x = xbase + 128 + 512 * idx
        y = ybase + 320
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
        click_at(x, y, button='left', delay=0.1)
        time.sleep(0.1)
    time.sleep(5)
    press_key('7', press_duration=2)
    time.sleep(0.5)
    wait_for_image(resource_path('photo/BOCIERWANCHENG.png'), threshold=0.75)
    with wave_lock:
        wave_counter += 1
        print(f'当前完成波次: {wave_counter}')
    press_key('N')
    time.sleep(0.4)
    click_at(800, 975, button='right', delay=0.1)
    time.sleep(0.1)
    click_at(920, 975, button='right', delay=0.1)
    time.sleep(0.1)
    click_at(1140, 975, button='right', delay=0.1)
    time.sleep(0.5)
    press_key('N')
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0, A=0, D=0)
    initial_positionscoll(W=0, S=1.0, A=0, D=0.5)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=1.0, A=0, D=0.5)
    time.sleep(0.5)
    image_path = resource_path('photo/0091.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 400 < xinit < 600 and 0 < yinit < 200:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    Boss = 0
    if 1500 < xinit < 1800 and 0 < yinit < 400:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    Boss = 1
    initial_positionscoll(W=0, S=0, A=0, D=0)
    time.sleep(0.5)
    image_path = resource_path('photo/0092.png')
    result = find_image(image_path, threshold=0.7)
    if result:
        pass
    xinit, yinit, similarity = result
    if 400 < xinit < 600 and 0 < yinit < 200:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    Boss = 0
    if 1500 < xinit < 1800 and 0 < yinit < 400:
        pass
    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
    Boss = 1
    initial_positionscoll(W=0, S=0, A=0, D=0)
    time.sleep(0.5)
    initial_positionscoll(W=0, S=0, A=0, D=0)
    time.sleep(0.5)
    if Boss == 0:
        initial_positionscoll(W=0.8, S=0, A=0.5, D=0)
        image_path = resource_path('photo/0011.png')
        result = find_image(image_path, threshold=0.7)
        if result:
            pass
        xinit, yinit, similarity = result
        if 650 < xinit < 750 and 200 < yinit < 300:
            pass
        print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
        xbase = xinit - 62
        ybase = yinit + 185
        time.sleep(0.5)
        press_key('6')
        time.sleep(0.5)
        indexes = [0, 1, 2, 3]
        for idx in indexes:
            x = xbase
            y = ybase + 128 * idx
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
        for idx in indexes:
            x = xbase + 128
            y = ybase + 128 * idx
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
        initial_positionscoll(W=0, S=0.2, A=0.5, D=0)
        initial_positionscoll(W=0.8, S=0, A=0.5, D=0)
        time.sleep(0.5)
        initial_positionscoll(W=0.8, S=0, A=0.5, D=0)
        time.sleep(0.5)
        image_path = resource_path('photo/0093.png')
        result = find_image(image_path, threshold=0.7)
        if result:
            pass
        xinit, yinit, similarity = result
        if 200 < xinit < 260 and 470 < yinit < 550:
            pass
        print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
        xbase = xinit + 407
        ybase = yinit - 265
        time.sleep(0.5)
        press_key('6')
        time.sleep(0.5)
        indexes = [0, 1, 2, 3, 4, 5]
        for idx in indexes:
            x = xbase
            y = ybase + 128 * idx
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
        indexes = [0, 1, 2, 3, 4, 5]
        for idx in indexes:
            x = xbase + 128
            y = ybase + 128 * idx
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
        indexes = [0, 1, 2, 3]
        for idx in indexes:
            x = xbase + 256
            y = ybase + 128 * idx + 256
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
        indexes = [0, 1, 2]
        for idx in indexes:
            x = xbase + 384
            y = ybase + 128 * idx + 256
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
        indexes = [0, 1]
        for idx in indexes:
            x = xbase + 512
            y = ybase + 128 * idx + 256
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
        indexes = [0, 1, 2, 3, 4, 5]
        for idx in indexes:
            x = xbase + 704
            y = ybase + 128 * idx + 64
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
        indexes = [0, 1, 2]
        for idx in indexes:
            x = xbase + 832
            y = ybase + 128 * idx + 448
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
        initial_positionscoll(W=0, S=0.8, A=0, D=0)
        initial_positionscoll(W=0, S=0.2, A=0.5, D=0)
        time.sleep(0.5)
        initial_positionscoll(W=0, S=0.2, A=0.5, D=0)
        time.sleep(0.5)
        image_path = resource_path('photo/0194.png')
        result = find_image(image_path, threshold=0.7)
        if result:
            pass
        xinit, yinit, similarity = result
        if 1100 < xinit < 1300 and 200 < yinit < 300:
            pass
        print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
        xbase = xinit - 557
        ybase = yinit + 211
        time.sleep(0.5)
        press_key('6')
        time.sleep(0.5)
        indexes = [0, 1, 2]
        for idx in indexes:
            x = xbase - 64
            y = ybase + 64 + 128 * idx
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
        for idx in indexes:
            x = xbase + 256
            y = ybase + 64 + 128 * idx
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
        for idx in indexes:
            x = xbase + 384
            y = ybase + 64 + 128 * idx
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
        for idx in indexes:
            x = xbase + 640
            y = ybase + 64 + 128 * idx
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
        for idx in indexes:
            x = xbase + 768
            y = ybase + 64 + 128 * idx
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
        indexes = [0, 1]
        for idx in indexes:
            x = xbase - 192
            y = ybase + 192 + 128 * idx
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
        for idx in indexes:
            x = xbase + 128
            y = ybase + 192 + 128 * idx
            click_at(x, y, button='left', delay=0.1)
            time.sleep(0.1)
            initial_positionscoll(W=0, S=0.8, A=0, D=0)
            time.sleep(0.5)
            initial_positionscoll(W=0, S=0.8, A=0, D=0)
            time.sleep(0.5)
        if Boss == 1:
            initial_positionscoll(W=0.8, S=0, A=0, D=2)
            image_path = resource_path('photo/0011.png')
            result = find_image(image_path, threshold=0.7)
            if result:
                pass
            xinit, yinit, similarity = result
            if 1180 < xinit < 1260 and 200 < yinit < 300:
                pass
            print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
            xbase = xinit - 65
            ybase = yinit + 184
            time.sleep(0.5)
            press_key('6')
            time.sleep(0.5)
            indexes = [0, 1, 2, 3]
            for idx in indexes:
                x = xbase
                y = ybase + 128 * idx
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
            for idx in indexes:
                x = xbase + 128
                y = ybase + 128 * idx
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
            initial_positionscoll(W=0, S=0.2, A=0, D=2)
            initial_positionscoll(W=0.8, S=0, A=0, D=2)
            time.sleep(0.5)
            initial_positionscoll(W=0.8, S=0, A=0, D=2)
            time.sleep(0.5)
            image_path = resource_path('photo/0095.png')
            result = find_image(image_path, threshold=0.7)
            if result:
                pass
            xinit, yinit, similarity = result
            if 980 < xinit < 1080 and 330 < yinit < 420:
                pass
            print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
            xbase = xinit + 257
            ybase = yinit - 132
            time.sleep(0.5)
            press_key('6')
            time.sleep(0.5)
            indexes = [0, 1, 2, 3, 4, 5]
            for idx in indexes:
                x = xbase
                y = ybase + 128 * idx
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
            indexes = [0, 1, 2, 3, 4, 5]
            for idx in indexes:
                x = xbase - 128
                y = ybase + 128 * idx
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
            indexes = [0, 1, 2, 3]
            for idx in indexes:
                x = xbase - 256
                y = ybase + 128 * idx + 256
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
            indexes = [0, 1, 2]
            for idx in indexes:
                x = xbase - 384
                y = ybase + 128 * idx + 256
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
            indexes = [0, 1]
            for idx in indexes:
                x = xbase - 512
                y = ybase + 128 * idx + 256
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
            indexes = [0, 1, 2, 3, 4, 5]
            for idx in indexes:
                x = xbase - 704
                y = ybase + 128 * idx + 64
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
            indexes = [0, 1, 2]
            for idx in indexes:
                x = xbase - 832
                y = ybase + 128 * idx + 448
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
            initial_positionscoll(W=0, S=0.8, A=0, D=0.8)
            initial_positionscoll(W=0, S=0.2, A=0, D=2)
            time.sleep(0.5)
            initial_positionscoll(W=0, S=0.2, A=0, D=2)
            time.sleep(0.5)
            image_path = resource_path('photo/0194.png')
            result = find_image(image_path, threshold=0.7)
            if result:
                pass
            xinit, yinit, similarity = result
            if 430 < xinit < 530 and 200 < yinit < 300:
                pass
            print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
            xbase = xinit + 852
            ybase = yinit + 210
            time.sleep(0.5)
            press_key('6')
            time.sleep(0.5)
            indexes = [0, 1, 2]
            for idx in indexes:
                x = xbase + 64
                y = ybase + 64 + 128 * idx
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
            for idx in indexes:
                x = xbase - 256
                y = ybase + 64 + 128 * idx
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
            for idx in indexes:
                x = xbase - 384
                y = ybase + 128 * idx
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
            for idx in indexes:
                x = xbase - 640
                y = ybase + 64 + 128 * idx
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
            for idx in indexes:
                x = xbase - 768
                y = ybase + 64 + 128 * idx
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
            indexes = [0, 1]
            for idx in indexes:
                x = xbase + 192
                y = ybase + 192 + 128 * idx
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
            for idx in indexes:
                x = xbase - 128
                y = ybase + 192 + 128 * idx
                click_at(x, y, button='left', delay=0.1)
                time.sleep(0.1)
                initial_positionscoll(W=0, S=0.8, A=0, D=0.8)
                time.sleep(0.5)
                initial_positionscoll(W=0, S=0.8, A=0, D=0.8)
                time.sleep(0.5)
    press_key('G')
    time.sleep(0.5)
    press_key('SPACE')
    time.sleep(0.1)
    press_key('SPACE', press_duration=5)
    time.sleep(0.5)
    press_key('SPACE', press_duration=2)
    time.sleep(0.5)
    press_key('SPACE', press_duration=2)
    time.sleep(0.5)
    press_key('SPACE', press_duration=2)
def run_game_cycle():
    t1 = threading.Thread(target=periodic_image_check, daemon=True)
    t1.start()
    t2 = threading.Thread(target=wave_monitor, daemon=True)
    t2.start()
    while True:
        while True:
            press_key('SPACE', press_duration=0.1)
            if traverse():
                print('识别到炼狱开始，执行操作后退出循环！')
                break
            else:
                time.sleep(0.5)
        time.sleep(3)
        click_at(1688, 954, button='left')
        time.sleep(0.5)
        click_at(1688, 954, button='left')
        time.sleep(0.5)
        result = find_image(resource_path('photo/qwbuzaitixing.png'), threshold=0.75)
        if result:
            time.sleep(1)
            click_at(899, 598, button='left')
            time.sleep(1)
            click_at(1100, 670, button='left')
            time.sleep(1)
        click_at(960, 540, button='left')
        time.sleep(0.2)
        press_key('SPACE', press_duration=2)
        wait_for_image(resource_path('photo/qwchenggongjinruyouxi.png'), threshold=0.75, Afterrecognition=1)
        time.sleep(2)
        main()
        while True:
            press_key('SPACE', press_duration=0.1)
            if traverse():
                print('识别到炼狱开始，执行操作后退出循环！')
                break
            else:
                time.sleep(0.5)
        time.sleep(5)
if __name__ == '__main__':
    run_game_cycle()