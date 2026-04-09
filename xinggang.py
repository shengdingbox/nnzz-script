# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'xinggang.py'
# Bytecode version: 3.10.b1 (3439)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

global wave_counter
global last_wave_counter
global wave_lock
import os
import sys
import threading
import time

import cv2
import numpy as np
import win32api
import win32con
from PIL import ImageGrab


def set_logger(log_instance):
    """设置logger实例"""
    global logger
    logger = log_instance
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
def press_key(key, press_duration=0.05):
    # irreducible cflow, using cdg fallback
    # ***<module>.press_key: Failure: Different control flow
    special_keys = {'ENTER': win32con.VK_RETURN, 'RETURN': win32con.VK_RETURN, 'SPACE': win32con.VK_SPACE, 'TAB': win32con.VK_TAB, 'ESC': win32con.VK_ESCAPE, 'ESCAPE': win32con.VK_ESCAPE, 'CTRL': win32con.VK_CONTROL, 'ALT': win32con.VK_MENU, 'SHIFT': win32con.VK_SHIFT, 'BACKSPACE': win32con.VK_BACK, 'DELETE': win32con.VK_DELETE}
    if key.upper().startswith('F') and len(key) in [2, 3]:
        f_num = int(key[1:])
        if 1 <= f_num <= 12:
                vk_code = getattr(win32con, f'VK_F{f_num}')
                raise ValueError(f'不支持的功能键: {key}')
        if key.upper() in special_keys:
            vk_code = special_keys[key.upper()]
        else:
            if len(key) == 1:
                vk_code = ord(key.upper())
            else:
                raise ValueError(f'不支持的按键: {key}')
                win32api.keybd_event(vk_code, 0, 0, 0)
                time.sleep(press_duration)
                win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                print(f'已按下: {key}')
def find_image(template_path, threshold=0.8):
    # irreducible cflow, using cdg fallback
    # ***<module>.find_image: Failure: Compilation Error
    with cache_lock:
        if template_path in _template_cache:
            template, h, w = _template_cache[template_path]
            template = cv2.imread(template_path, 0)
            if template is None:
                print(f'无法读取图片: {template_path}')
                return
                h, w = template.shape
                _template_cache[template_path] = (template, h, w)
                        screen = ImageGrab.grab()
                        screen_cv = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
                        screen_gray = cv2.cvtColor(screen_cv, cv2.COLOR_BGR2GRAY)
                        result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, max_loc = cv2.minMaxLoc(result)
                        if max_val >= threshold:
                            x = max_loc[0] + w // 2
                            y = max_loc[1] + h // 2
                            return (x, y, max_val)
                        else:
                            print(f'未找到图片，最高相似度: {max_val:.3f}')
                            return
                        except Exception as e:
                            print(f'识别出错: {e}')
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
def initial_positionscoll(W=0, S=0.4):
    press_key('o')
    time.sleep(1.2)
    press_key('SPACE')
    time.sleep(0.2)
    press_key('o')
    time.sleep(2)
    repeat_scroll(960, 540, scroll_amount=(-120), times=50)
    press_key('W', press_duration=W)
    time.sleep(0.5)
    press_key('S', press_duration=S)
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
        result = find_image(resource_path('xinggang/shibai.png'), 0.7)
        if result:
            print('识别到失败')
            for i in range(10):
                press_key('SPACE')
                time.sleep(0.5)
            click_at(1454, 220, button='left')
            os._exit(1)
        result = find_image(resource_path('xinggang/lianyukaishi.png'), 0.7)
        if result:
            print('识别到炼狱开始')
            click_at(1454, 220, button='left')
            os._exit(1)
        result = find_image(resource_path('xinggang/tiaozhanmoshi.png'), 0.7)
        if result:
            print('识别到挑战模式')
            os._exit(1)
        result = find_image(resource_path('xinggang/zhujiemian.png'), 0.7)
        if result:
            print('识别到主界面')
            click_at(1675, 930, button='left')
            time.sleep(3)
            click_at(521, 502, button='left')
            time.sleep(3)
            result = find_image(resource_path('xinggang/lianyukaishi.png'), 0.7)
            if result:
                print('识别到炼狱开始')
                click_at(1454, 220, button='left')
                os._exit(1)
            result = find_image(resource_path('xinggang/tiaozhanmoshi.png'), 0.7)
            if result:
                print('识别到挑战模式')
                os._exit(1)
            os._exit(1)
        time.sleep(10)
        print('自检未检测到')
def traverse():
    result = find_image(resource_path('xinggang/lianyukaishi.png'), 0.7)
    if result:
        print('识别到炼狱开始')
        return True
    else:
        result = find_image(resource_path('xinggang/tiaozhanmoshi.png'), 0.7)
        if result:
            print('识别到挑战模式')
            click_at(1454, 220, button='left')
        result = find_image(resource_path('xinggang/zhujiemian.png'), 0.7)
        if result:
            print('识别到主界面')
            click_at(1675, 930, button='left')
            time.sleep(3)
            click_at(521, 502, button='left')
            time.sleep(3)
            result = find_image(resource_path('xinggang/lianyukaishi.png'), 0.7)
            if result:
                print('识别到炼狱开始')
                click_at(1688, 954, button='left')
            result = find_image(resource_path('xinggang/tiaozhanmoshi.png'), 0.7)
            if result:
                print('识别到挑战模式')
        result = find_image(resource_path('xinggang/shibai.png'), 0.7)
        if result:
            print('识别到失败')
            for i in range(10):
                press_key('SPACE')
                time.sleep(0.5)
            click_at(1454, 220, button='left')
        result = find_image(resource_path('xinggang/buzaitixing.png'), threshold=0.75)
        if result:
            time.sleep(1)
            click_at(899, 598, button='left')
            time.sleep(1)
            click_at(1100, 670, button='left')
            time.sleep(1)
        return False
def main():
    global wave_counter
    # ***<module>.main: Failure: Different control flow
    with wave_lock:
        wave_counter += 1
        print(f'当前完成波次: {wave_counter}')
    press_key('N')
    time.sleep(0.5)
    image_path = resource_path('xinggang/fangkong.png')
    result = find_image(image_path, threshold=0.6)
    if result:
        x, y, similarity = result
        print(f'✅ 找到图片！坐标: ({x}, {y}), 相似度: {similarity:.3f}')
        click_at(x, y, button='left')
    time.sleep(0.5)
    image_path = resource_path('xinggang/jianmie.png')
    result = find_image(image_path, threshold=0.6)
    if result:
        x, y, similarity = result
        print(f'✅ 找到图片！坐标: ({x}, {y}), 相似度: {similarity:.3f}')
        click_at(x, y, button='left')
    time.sleep(0.5)
    image_path = resource_path('xinggang/zixiufucibaota.png')
    result = find_image(image_path, threshold=0.6)
    if result:
        x, y, similarity = result
        print(f'✅ 找到图片！坐标: ({x}, {y}), 相似度: {similarity:.3f}')
        click_at(x, y, button='left')
    time.sleep(0.5)
    image_path = resource_path('xinggang/tianwang.png')
    result = find_image(image_path, threshold=0.6)
    if result:
        x, y, similarity = result
        print(f'✅ 找到图片！坐标: ({x}, {y}), 相似度: {similarity:.3f}')
        click_at(x, y, button='left')
    time.sleep(0.5)
    press_key('N')
    time.sleep(0.5)
    press_key('S', press_duration=0.6)
    time.sleep(0.5)
    press_key('o')
    time.sleep(2)
    press_key('W', press_duration=0.6)
    with wave_lock:
        wave_counter += 1
        print(f'当前完成波次: {wave_counter}')
    press_key('G')
    time.sleep(5)
    time.sleep(0.5)
    while True:
        image_path = resource_path('xinggang/0011.png')
        result = find_image(image_path, threshold=0.7)
        if result:
            xinit, yinit, similarity = result
            if 800 < xinit < 850 and 740 < yinit < 790:
                            print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                            xbase = xinit + 10
                            ybase = yinit - 534
                            time.sleep(0.5)
                            press_key('7')
                            time.sleep(0.5)
                            indexes = [0, 1, 2, 3]
                            for idx in indexes:
                                x = xbase + 43
                                y = ybase + 85 * idx
                                click_at(x, y, button='left', delay=0.1)
                                time.sleep(0.1)
                            for idx in indexes:
                                x = xbase + 43 + 170
                                y = ybase + 85 * idx
                                click_at(x, y, button='left', delay=0.1)
                                time.sleep(0.1)
                            time.sleep(1)
                            wait_for_image(resource_path('xinggang/BOCIERWANCHENG.png'), threshold=0.7)
                            with wave_lock:
                                wave_counter += 1
                                print(f'当前完成波次: {wave_counter}')
                            press_key('G')
                            time.sleep(0.5)
                            press_key('7', press_duration=2)
                            time.sleep(0.5)
                            indexes = [4, 5]
                            for idx in indexes:
                                x = xbase + 43
                                y = ybase + 85 * idx
                                click_at(x, y, button='left', delay=0.1)
                                time.sleep(0.2)
                            indexes = [3, 4, 5]
                            for idx in indexes:
                                x = xbase + 43 + 170
                                y = ybase + 85 * idx
                                click_at(x, y, button='left', delay=0.1)
                                time.sleep(0.1)
                            initial_position(W=0, S=0)
                            press_key('7')
                            time.sleep(0.5)
                            click_at(960, 416, button='left', delay=0.1)
                            wait_for_image(resource_path('xinggang/BOCIERWANCHENG.png'), threshold=0.75)
                            with wave_lock:
                                wave_counter += 1
                                print(f'当前完成波次: {wave_counter}')
                            press_key('G')
                            time.sleep(0.5)
                            press_key('4')
                            time.sleep(0.5)
                            click_at(277, 541, button='left', delay=0.1)
                            time.sleep(0.5)
                            click_at(1643, 541, button='left', delay=0.1)
                            while True:
                                initial_position(W=0.6, S=0)
                                time.sleep(0.2)
                                image_path = resource_path('xinggang/0011.png')
                                result = find_image(image_path, threshold=0.7)
                                if result:
                                    xinit, yinit, similarity = result
                                    if 800 < xinit < 850 and 740 < yinit < 790:
                                                    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                    press_key('6')
                                                    time.sleep(0.5)
                                                    click_at(xinit + 132, yinit - 78, button='left', delay=0.1)
                                                    time.sleep(0.5)
                                                    xbase = xinit - 39
                                                    ybase = yinit - 589
                                                    press_key('4')
                                                    time.sleep(0.5)
                                                    indexes = [0, 1, 2, 3]
                                                    for idx in indexes:
                                                        x = xbase - 43 - 85 * idx
                                                        y = ybase + 43
                                                        click_at(x, y, button='left', delay=0.1)
                                                        time.sleep(0.1)
                                                    for idx in indexes:
                                                        x = xbase - 43 - 85 * idx
                                                        y = ybase + 43 + 85
                                                        click_at(x, y, button='left', delay=0.1)
                                                        time.sleep(0.1)
                                                    for idx in indexes:
                                                        x = xbase + 340 + 43 + 85 * idx
                                                        y = ybase + 43
                                                        click_at(x, y, button='left', delay=0.1)
                                                        time.sleep(0.1)
                                                    for idx in indexes:
                                                        x = xbase + 340 + 43 + 85 * idx
                                                        y = ybase + 43 + 85
                                                        click_at(x, y, button='left', delay=0.1)
                                                        time.sleep(0.1)
                                                    time.sleep(10)
                                                    wait_for_image(resource_path('xinggang/BOCIERWANCHENG.png'), threshold=0.75)
                                                    with wave_lock:
                                                        wave_counter += 1
                                                        print(f'当前完成波次: {wave_counter}')
                                                    press_key('G')
                                                    time.sleep(0.5)
                                                    initial_position(W=0, S=0)
                                                    click_at(963, 438, button='left', delay=0.1)
                                                    time.sleep(0.5)
                                                    press_key('E')
                                                    time.sleep(0.5)
                                                    while True:
                                                        initial_position(W=0, S=0.6)
                                                        image_path = resource_path('xinggang/0041.png')
                                                        result = find_image(image_path, threshold=0.7)
                                                        if result:
                                                            xinit, yinit, similarity = result
                                                            if 620 < xinit < 660 and 400 < yinit < 480:
                                                                            print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                                            xbase = xinit + 58
                                                                            ybase = yinit + 57
                                                                            time.sleep(0.5)
                                                                            press_key('5')
                                                                            time.sleep(0.5)
                                                                            click_at(xbase - 425, ybase - 85, button='left', delay=0.1)
                                                                            time.sleep(0.5)
                                                                            click_at(xbase + 510 + 425, ybase - 85, button='left', delay=0.1)
                                                                            time.sleep(0.5)
                                                                            press_key('7')
                                                                            time.sleep(0.5)
                                                                            indexes = [0, 1, 2]
                                                                            for idx in indexes:
                                                                                x = xbase - 43 - 85 - 85 * idx
                                                                                y = ybase + 43
                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                time.sleep(0.2)
                                                                            for idx in indexes:
                                                                                x = xbase - 43 - 85 - 85 * idx
                                                                                y = ybase + 43 + 255
                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                time.sleep(0.2)
                                                                            for idx in indexes:
                                                                                x = xbase + 510 + 43 + 85 + 85 * idx
                                                                                y = ybase + 43
                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                time.sleep(0.2)
                                                                            for idx in indexes:
                                                                                x = xbase + 510 + 43 + 85 + 85 * idx
                                                                                y = ybase + 43 + 255
                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                time.sleep(0.2)
                                                                            press_key('6')
                                                                            time.sleep(0.5)
                                                                            indexes = [0, 1]
                                                                            for idx in indexes:
                                                                                x = xbase - 85
                                                                                y = ybase + 85 + 170 * idx
                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                time.sleep(0.1)
                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                time.sleep(0.1)
                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                time.sleep(0.1)
                                                                            for idx in indexes:
                                                                                x = xbase + 510 + 85
                                                                                y = ybase + 85 + 170 * idx
                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                time.sleep(0.1)
                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                time.sleep(0.1)
                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                time.sleep(0.1)
                                                                            time.sleep(20)
                                                                            press_key('5', press_duration=2)
                                                                            initial_position(W=0, S=0)
                                                                            press_key('5')
                                                                            time.sleep(10)
                                                                            click_at(960, 200, button='left', delay=0.1)
                                                                            wait_for_image(resource_path('xinggang/BOCIERWANCHENG.png'), threshold=0.75)
                                                                            with wave_lock:
                                                                                wave_counter += 1
                                                                                print(f'当前完成波次: {wave_counter}')
                                                                            press_key('6', press_duration=2)
                                                                            time.sleep(0.5)
                                                                            press_key('6', press_duration=2)
                                                                            time.sleep(0.5)
                                                                            press_key('7', press_duration=2)
                                                                            time.sleep(0.5)
                                                                            press_key('G')
                                                                            time.sleep(0.2)
                                                                            while True:
                                                                                initial_position(W=0.6, S=0)
                                                                                time.sleep(0.2)
                                                                                image_path = resource_path('xinggang/0011.png')
                                                                                result = find_image(image_path, threshold=0.7)
                                                                                if result:
                                                                                    xinit, yinit, similarity = result
                                                                                    if 800 < xinit < 850 and 740 < yinit < 790:
                                                                                                    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                                                                    time.sleep(0.5)
                                                                                                    press_key('4')
                                                                                                    time.sleep(0.5)
                                                                                                    xbase = xinit - 39
                                                                                                    ybase = yinit - 589
                                                                                                    indexes = [0, 1, 2, 3]
                                                                                                    for idx in indexes:
                                                                                                        x = xbase - 43 - 85 * idx
                                                                                                        y = ybase + 43
                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                        time.sleep(0.1)
                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                        time.sleep(0.1)
                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                        time.sleep(0.1)
                                                                                                    for idx in indexes:
                                                                                                        x = xbase - 43 - 85 * idx
                                                                                                        y = ybase + 43 + 85
                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                        time.sleep(0.1)
                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                        time.sleep(0.1)
                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                        time.sleep(0.1)
                                                                                                    for idx in indexes:
                                                                                                        x = xbase + 340 + 43 + 85 * idx
                                                                                                        y = ybase + 43
                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                        time.sleep(0.1)
                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                        time.sleep(0.1)
                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                        time.sleep(0.1)
                                                                                                    for idx in indexes:
                                                                                                        x = xbase + 340 + 43 + 85 * idx
                                                                                                        y = ybase + 43 + 85
                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                        time.sleep(0.1)
                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                        time.sleep(0.1)
                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                        time.sleep(0.1)
                                                                                                    while True:
                                                                                                        initial_position(W=0, S=0.2)
                                                                                                        time.sleep(0.2)
                                                                                                        image_path = resource_path('xinggang/0051.png')
                                                                                                        result = find_image(image_path, threshold=0.7)
                                                                                                        if result:
                                                                                                            xinit, yinit, similarity = result
                                                                                                            if 680 < xinit < 720 and 430 < yinit < 500:
                                                                                                                            print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                                                                                            time.sleep(0.5)
                                                                                                                            press_key('4')
                                                                                                                            time.sleep(0.5)
                                                                                                                            xbase = xinit + 259
                                                                                                                            ybase = yinit - 258
                                                                                                                            indexes = [0, 1, 2, 3, 4]
                                                                                                                            for idx in indexes:
                                                                                                                                x = xbase - 680
                                                                                                                                y = ybase + 170 + 85 * idx
                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                time.sleep(0.1)
                                                                                                                            for idx in indexes:
                                                                                                                                x = xbase + 680
                                                                                                                                y = ybase + 170 + 85 * idx
                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                time.sleep(0.1)
                                                                                                                            while True:
                                                                                                                                initial_position(W=0, S=0.8)
                                                                                                                                press_key('A', press_duration=0.2)
                                                                                                                                time.sleep(0.2)
                                                                                                                                image_path = resource_path('xinggang/0052.png')
                                                                                                                                result = find_image(image_path, threshold=0.7)
                                                                                                                                if result:
                                                                                                                                    xinit, yinit, similarity = result
                                                                                                                                    if 980 < xinit < 1040 and 550 < yinit < 620:
                                                                                                                                                    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                    press_key('4')
                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                    xbase = xinit - 699
                                                                                                                                                    ybase = yinit + 125
                                                                                                                                                    indexes = [(-1), 1]
                                                                                                                                                    for idx in indexes:
                                                                                                                                                        x = xbase + 43 * idx
                                                                                                                                                        y = ybase - 43
                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                    for idx in indexes:
                                                                                                                                                        x = xbase + 43 * idx
                                                                                                                                                        y = ybase + 43
                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                    while True:
                                                                                                                                                        initial_position(W=0, S=0.8)
                                                                                                                                                        press_key('D', press_duration=0.2)
                                                                                                                                                        time.sleep(0.2)
                                                                                                                                                        image_path = resource_path('xinggang/0052.png')
                                                                                                                                                        result = find_image(image_path, threshold=0.7)
                                                                                                                                                        if result:
                                                                                                                                                            xinit, yinit, similarity = result
                                                                                                                                                            if 480 < xinit < 540 and 550 < yinit < 620:
                                                                                                                                                                            print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                                            press_key('4')
                                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                                            xbase = xinit + 1093
                                                                                                                                                                            ybase = yinit + 125
                                                                                                                                                                            indexes = [(-1), 1]
                                                                                                                                                                            for idx in indexes:
                                                                                                                                                                                x = xbase + 43 * idx
                                                                                                                                                                                y = ybase - 43
                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                            for idx in indexes:
                                                                                                                                                                                x = xbase + 43 * idx
                                                                                                                                                                                y = ybase + 43
                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                            wait_for_image(resource_path('xinggang/BOCIERWANCHENG.png'), threshold=0.75)
                                                                                                                                                                            with wave_lock:
                                                                                                                                                                                wave_counter += 1
                                                                                                                                                                                print(f'当前完成波次: {wave_counter}')
                                                                                                                                                                            press_key('G')
                                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                                            press_key('4', press_duration=2)
                                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                                            press_key('5', press_duration=2)
                                                                                                                                                                            while True:
                                                                                                                                                                                initial_position(W=0, S=0.7)
                                                                                                                                                                                image_path = resource_path('xinggang/0041.png')
                                                                                                                                                                                result = find_image(image_path, threshold=0.7)
                                                                                                                                                                                if result:
                                                                                                                                                                                    xinit, yinit, similarity = result
                                                                                                                                                                                    if 620 < xinit < 660 and 280 < yinit < 350:
                                                                                                                                                                                                    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                    press_key('5')
                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                    xbase = xinit + 58 + 255
                                                                                                                                                                                                    ybase = yinit + 57
                                                                                                                                                                                                    indexes = [(-1), 1]
                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                        x = xbase - 510 * idx
                                                                                                                                                                                                        y = ybase - 85
                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                    indexes = [0, 1]
                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                        x = xbase - 510 - 170 * idx
                                                                                                                                                                                                        y = ybase + 425
                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                        x = xbase + 510 + 170 * idx
                                                                                                                                                                                                        y = ybase + 425
                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                    wait_for_image(resource_path('xinggang/BOCIERWANCHENG.png'), threshold=0.75)
                                                                                                                                                                                                    with wave_lock:
                                                                                                                                                                                                        wave_counter += 1
                                                                                                                                                                                                        print(f'当前完成波次: {wave_counter}')
                                                                                                                                                                                                    press_key('G')
                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                    press_key('4', press_duration=2)
                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                    press_key('5', press_duration=2)
                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                    press_key('6', press_duration=2)
                                                                                                                                                                                                    while True:
                                                                                                                                                                                                        initial_position(W=0.3, S=0)
                                                                                                                                                                                                        image_path = resource_path('xinggang/0011.png')
                                                                                                                                                                                                        result = find_image(image_path, threshold=0.7)
                                                                                                                                                                                                        if result:
                                                                                                                                                                                                            xinit, yinit, similarity = result
                                                                                                                                                                                                            if 800 < xinit < 860 and 360 < yinit < 420:
                                                                                                                                                                                                                            print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                                                                                                                                                                                            break
                                                                                                                                                                                                                            xbase = xinit + 132
                                                                                                                                                                                                                            ybase = yinit + 6
                                                                                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                                                                                            press_key('6')
                                                                                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                                                                                            click_at(xbase, ybase - 85, button='left', delay=0.1)
                                                                                                                                                                                                                            time.sleep(0.1)
                                                                                                                                                                                                                            click_at(xbase, ybase - 85 - 10, button='left', delay=0.1)
                                                                                                                                                                                                                            time.sleep(0.1)
                                                                                                                                                                                                                            click_at(xbase, ybase - 10, button='right', delay=0.1)
                                                                                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                                                                                            press_key('5')
                                                                                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                                                                                            indexes = [0, 1]
                                                                                                                                                                                                                            for idx in indexes:
                                                                                                                                                                                                                                x = xbase
                                                                                                                                                                                                                                y = ybase + 170 + 170 * idx
                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                            indexes = [(-1), 1]
                                                                                                                                                                                                                            for idx in indexes:
                                                                                                                                                                                                                                x = xbase + 170 * idx
                                                                                                                                                                                                                                y = ybase + 255
                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                            while True:
                                                                                                                                                                                                                                initial_position(W=0.6, S=0)
                                                                                                                                                                                                                                time.sleep(0.2)
                                                                                                                                                                                                                                image_path = resource_path('xinggang/0011.png')
                                                                                                                                                                                                                                result = find_image(image_path, threshold=0.7)
                                                                                                                                                                                                                                if result:
                                                                                                                                                                                                                                    xinit, yinit, similarity = result
                                                                                                                                                                                                                                    if 800 < xinit < 850 and 740 < yinit < 790:
                                                                                                                                                                                                                                                    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                    press_key('4')
                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                    xbase = xinit - 39
                                                                                                                                                                                                                                                    ybase = yinit - 589
                                                                                                                                                                                                                                                    indexes = [0, 1, 2, 3]
                                                                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                                                                        x = xbase - 43 - 85 * idx
                                                                                                                                                                                                                                                        y = ybase + 43
                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                                                                        x = xbase - 43 - 85 * idx
                                                                                                                                                                                                                                                        y = ybase + 43 + 85
                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                                                                        x = xbase + 340 + 43 + 85 * idx
                                                                                                                                                                                                                                                        y = ybase + 43
                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                                                                        x = xbase + 340 + 43 + 85 * idx
                                                                                                                                                                                                                                                        y = ybase + 43 + 85
                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                    wait_for_image(resource_path('xinggang/BOCIERWANCHENG.png'), threshold=0.75)
                                                                                                                                                                                                                                                    with wave_lock:
                                                                                                                                                                                                                                                        wave_counter += 1
                                                                                                                                                                                                                                                        print(f'当前完成波次: {wave_counter}')
                                                                                                                                                                                                                                                    press_key('G')
                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                    while True:
                                                                                                                                                                                                                                                        initial_position(W=0.6, S=0)
                                                                                                                                                                                                                                                        time.sleep(0.2)
                                                                                                                                                                                                                                                        image_path = resource_path('xinggang/0011.png')
                                                                                                                                                                                                                                                        result = find_image(image_path, threshold=0.7)
                                                                                                                                                                                                                                                        if result:
                                                                                                                                                                                                                                                            xinit, yinit, similarity = result
                                                                                                                                                                                                                                                            if 800 < xinit < 850 and 740 < yinit < 790:
                                                                                                                                                                                                                                                                            print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                                                                                                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                                                                                                                                            press_key('4')
                                                                                                                                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                                                                                                                                            xbase = xinit - 39
                                                                                                                                                                                                                                                                            ybase = yinit - 589
                                                                                                                                                                                                                                                                            indexes = [0, 1, 2, 3]
                                                                                                                                                                                                                                                                            for idx in indexes:
                                                                                                                                                                                                                                                                                x = xbase - 43 - 85 * idx
                                                                                                                                                                                                                                                                                y = ybase + 43
                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                            for idx in indexes:
                                                                                                                                                                                                                                                                                x = xbase - 43 - 85 * idx
                                                                                                                                                                                                                                                                                y = ybase + 43 + 85
                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                            for idx in indexes:
                                                                                                                                                                                                                                                                                x = xbase + 340 + 43 + 85 * idx
                                                                                                                                                                                                                                                                                y = ybase + 43
                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                            for idx in indexes:
                                                                                                                                                                                                                                                                                x = xbase + 340 + 43 + 85 * idx
                                                                                                                                                                                                                                                                                y = ybase + 43 + 85
                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                            while True:
                                                                                                                                                                                                                                                                                initial_position(W=0.3, S=0)
                                                                                                                                                                                                                                                                                image_path = resource_path('xinggang/0011.png')
                                                                                                                                                                                                                                                                                result = find_image(image_path, threshold=0.7)
                                                                                                                                                                                                                                                                                if result:
                                                                                                                                                                                                                                                                                    xinit, yinit, similarity = result
                                                                                                                                                                                                                                                                                    if 800 < xinit < 860 and 360 < yinit < 420:
                                                                                                                                                                                                                                                                                                    print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                                                                                                                                                                                                                                                                    break
                                                                                                                                                                                                                                                                                                    xbase = xinit + 132
                                                                                                                                                                                                                                                                                                    ybase = yinit + 6
                                                                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                                                                    press_key('6')
                                                                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                                                                    click_at(xbase, ybase - 85, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                    time.sleep(0.1)
                                                                                                                                                                                                                                                                                                    click_at(xbase, ybase - 85 - 10, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                    time.sleep(0.1)
                                                                                                                                                                                                                                                                                                    click_at(xbase, ybase - 10, button='right', delay=0.1)
                                                                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                                                                    press_key('5')
                                                                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                                                                    indexes = [0, 1]
                                                                                                                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                                                                                                                        x = xbase
                                                                                                                                                                                                                                                                                                        y = ybase + 170 + 170 * idx
                                                                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                                                                    indexes = [(-1), 1]
                                                                                                                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                                                                                                                        x = xbase + 170 * idx
                                                                                                                                                                                                                                                                                                        y = ybase + 255
                                                                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                                                                    wait_for_image(resource_path('xinggang/BOCIERWANCHENG.png'), threshold=0.75)
                                                                                                                                                                                                                                                                                                    with wave_lock:
                                                                                                                                                                                                                                                                                                        wave_counter += 1
                                                                                                                                                                                                                                                                                                        print(f'当前完成波次: {wave_counter}')
                                                                                                                                                                                                                                                                                                    press_key('N')
                                                                                                                                                                                                                                                                                                    time.sleep(0.4)
                                                                                                                                                                                                                                                                                                    click_at(800, 975, button='right', delay=0.1)
                                                                                                                                                                                                                                                                                                    time.sleep(0.1)
                                                                                                                                                                                                                                                                                                    click_at(920, 975, button='right', delay=0.1)
                                                                                                                                                                                                                                                                                                    time.sleep(0.1)
                                                                                                                                                                                                                                                                                                    click_at(1030, 975, button='right', delay=0.1)
                                                                                                                                                                                                                                                                                                    time.sleep(0.1)
                                                                                                                                                                                                                                                                                                    click_at(1140, 975, button='right', delay=0.1)
                                                                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                                                                    image_path = resource_path('xinggang/jianmie.png')
                                                                                                                                                                                                                                                                                                    result = find_image(image_path, threshold=0.6)
                                                                                                                                                                                                                                                                                                    if result:
                                                                                                                                                                                                                                                                                                        x, y, similarity = result
                                                                                                                                                                                                                                                                                                        print(f'✅ 找到图片！坐标: ({x}, {y}), 相似度: {similarity:.3f}')
                                                                                                                                                                                                                                                                                                        click_at(x, y, button='left')
                                                                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                                                                    press_key('N')
                                                                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                                                                    press_key('4', press_duration=2)
                                                                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                                                                    press_key('4', press_duration=2)
                                                                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                                                                    press_key('4', press_duration=2)
                                                                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                                                                    initial_positionscoll(W=2.5, S=0)
                                                                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                                                                    press_key('4')
                                                                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                                                                    indexes = [(-2), (-1), 0, 1, 2]
                                                                                                                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                                                                                                                        x = 933 - 85 * idx
                                                                                                                                                                                                                                                                                                        y = 181
                                                                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                                                                    indexes = [0, 1, 2, 3, 4]
                                                                                                                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                                                                                                                        x = 763
                                                                                                                                                                                                                                                                                                        y = 266 + 85 * idx
                                                                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                                                                                                                        x = 1103
                                                                                                                                                                                                                                                                                                        y = 266 + 85 * idx
                                                                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                                                                    indexes = [0, 1, 2, 3]
                                                                                                                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                                                                                                                        x = 933
                                                                                                                                                                                                                                                                                                        y = 563 + 85 * idx
                                                                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                                                                    indexes = [0, 1]
                                                                                                                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                                                                                                                        x = 804 - 85 * idx
                                                                                                                                                                                                                                                                                                        y = 691
                                                                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                                                                                                                        x = 1062 + 85 * idx
                                                                                                                                                                                                                                                                                                        y = 691
                                                                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                                                                    indexes = [(-1), 1]
                                                                                                                                                                                                                                                                                                    for idx in indexes:
                                                                                                                                                                                                                                                                                                        x = 933 + 85 * idx
                                                                                                                                                                                                                                                                                                        y = 563
                                                                                                                                                                                                                                                                                                        click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                        time.sleep(0.1)
                                                                                                                                                                                                                                                                                                    while True:
                                                                                                                                                                                                                                                                                                        initial_positionscoll(W=0, S=0.4)
                                                                                                                                                                                                                                                                                                        image_path = resource_path('xinggang/0091.png')
                                                                                                                                                                                                                                                                                                        result = find_image(image_path, threshold=0.7)
                                                                                                                                                                                                                                                                                                        if result:
                                                                                                                                                                                                                                                                                                            xinit, yinit, similarity = result
                                                                                                                                                                                                                                                                                                            if 780 < xinit < 830 and 350 < yinit < 420:
                                                                                                                                                                                                                                                                                                                            print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                                                                                                                                                                                                                                                                                            press_key('4')
                                                                                                                                                                                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                                                                                                                                                                                            xbase = xinit + 129
                                                                                                                                                                                                                                                                                                                            ybase = yinit - 220
                                                                                                                                                                                                                                                                                                                            indexes = [0, 1, 2, 3, 4]
                                                                                                                                                                                                                                                                                                                            for idx in indexes:
                                                                                                                                                                                                                                                                                                                                x = xbase + 85 + 85 * idx
                                                                                                                                                                                                                                                                                                                                y = ybase
                                                                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                                                                            for idx in indexes:
                                                                                                                                                                                                                                                                                                                                x = xbase + 425
                                                                                                                                                                                                                                                                                                                                y = ybase + 85 + 85 * idx
                                                                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                                                                            indexes = [0, 1, 2, 3, 4, 5, 6]
                                                                                                                                                                                                                                                                                                                            for idx in indexes:
                                                                                                                                                                                                                                                                                                                                x = xbase + 680 + 42 - 85 * idx
                                                                                                                                                                                                                                                                                                                                y = ybase + 510
                                                                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                                                                            for idx in indexes:
                                                                                                                                                                                                                                                                                                                                x = xbase + 680 + 42 - 85 * idx
                                                                                                                                                                                                                                                                                                                                y = ybase + 510 + 85
                                                                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                                                                            click_at(1383, 872, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                                            indexes = [0, 1]
                                                                                                                                                                                                                                                                                                                            for idx in indexes:
                                                                                                                                                                                                                                                                                                                                x = xbase + 340 - 85 * idx
                                                                                                                                                                                                                                                                                                                                y = ybase + 425
                                                                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                                                time.sleep(0.1)
                                                                                                                                                                                                                                                                                                                            for idx in indexes:
                                                                                                                                                                                                                                                                                                                                x = xbase + 340 - 85 * idx
                                                                                                                                                                                                                                                                                                                                y = ybase + 680
                                                                                                                                                                                                                                                                                                                                click_at(x, y, button='left', delay=0.1)
                                                                                                                                                                                                                                                                                                                                time.sleep(0.1)
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
                                                                                                                                                                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                                                                                                                                                                        time.sleep(0.5)
                                                                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                                                                time.sleep(0.5)
                                                                                                                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                                                                                                                            continue
                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                                                    continue
                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                                                                        time.sleep(0.5)
                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                                                    continue
                                                                                                                                                                                else:
                                                                                                                                                                                    time.sleep(0.5)
                                                                                                                                                            time.sleep(0.5)
                                                                                                                                                            continue
                                                                                                                                                        else:
                                                                                                                                                            time.sleep(0.5)
                                                                                                                                    time.sleep(0.5)
                                                                                                                                    continue
                                                                                                                                else:
                                                                                                                                    time.sleep(0.5)
                                                                                                            time.sleep(0.5)
                                                                                                            continue
                                                                                                        else:
                                                                                                            time.sleep(0.5)
                                                                                    time.sleep(0.5)
                                                                                    continue
                                                                                else:
                                                                                    time.sleep(0.5)
                                                            time.sleep(0.5)
                                                            continue
                                                        else:
                                                            time.sleep(0.5)
                                    time.sleep(0.5)
                                    continue
                                else:
                                    time.sleep(0.5)
            initial_position(W=0.6, S=0)
            time.sleep(0.5)
        initial_position(W=0.6, S=0)
        time.sleep(0.5)
def run_game_cycle():
    t1 = threading.Thread(target=periodic_image_check, daemon=True)
    t1.start()
    t2 = threading.Thread(target=wave_monitor, daemon=True)
    t2.start()
    while True:
        while True:
            if traverse():
                print('识别到炼狱开始，执行操作后退出循环！')
                break
            else:
                time.sleep(0.5)
        time.sleep(0.5)
        click_at(1688, 954, button='left')
        time.sleep(0.5)
        click_at(1688, 954, button='left')
        time.sleep(0.5)
        result = find_image(resource_path('xinggang/buzaitixing.png'), threshold=0.75)
        if result:
            time.sleep(1)
            click_at(899, 598, button='left')
            time.sleep(1)
            click_at(1100, 670, button='left')
            time.sleep(1)
        click_at(960, 540, button='left')
        time.sleep(0.2)
        press_key('SPACE', press_duration=2)
        wait_for_image(resource_path('xinggang/chenggongjinruyouxi.png'), threshold=0.75, Afterrecognition=1)
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
