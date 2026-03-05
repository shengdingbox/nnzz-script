# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'tafangrunning.py'
# Bytecode version: 3.10.b1 (3439)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

global wave_lock
global last_wave_counter
global wave_counter
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

# 全局logger变量
logger = None

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
def repeat_scroll(x, y, scroll_amount=(-120), times=10):
    win32api.SetCursorPos((x, y))
    if logger:
        logger.info(f'开始在({x}, {y})位置滚动{times}次...')
    else:
        print(f'开始在({x}, {y})位置滚动{times}次...')
    for i in range(times):
        simulate_mouse_wheel(x, y, scroll_amount)
        time.sleep(0.1)
    if logger:
        logger.info('滚动完成！')
    else:
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
    if logger:
        logger.info(f'等待图片出现: {template_path}')
        time.sleep(0.5)
    else:
        print(f'等待图片出现: {template_path}')
    while True:
        result = find_image(template_path, threshold)
        if result is not None:
            x, y, similarity = result
            if logger:
                logger.info(f'✅ 检测到目标图片！坐标: ({x}, {y}), 相似度: {similarity:.3f},{template_path}')
            else:
                print(f'✅ 检测到目标图片！坐标: ({x}, {y}), 相似度: {similarity:.3f},{template_path}')
            time.sleep(Afterrecognition)
            return result
        else:
            time.sleep(check_interval)
def periodic_image_check():
    target_image = resource_path('autophoto/guajijiance.png')
    threshold = 0.7
    while True:
        result = find_image(target_image, threshold)
        if result:
            click_at(960, 680, button='left')
        time.sleep(60)
def initial_position(W=0,S=0.4):
    press_key('o')
    time.sleep(1.2)
    press_key('SPACE')
    time.sleep(0.2)
    press_key('o')
    time.sleep(2)
    press_key('W', press_duration=W)
    time.sleep(0.5)
    press_key('S', press_duration=S)
    time.sleep(0.5)
def wave_monitor():
    global last_wave_counter
    CHECK_INTERVAL = 300
    while True:
        time.sleep(CHECK_INTERVAL)
        with wave_lock:
            currentnow = wave_counter
            if logger:
                logger.info(f'波次监控：当前计数器={currentnow}，上次记录={last_wave_counter}')
            else:
                print(f'波次监控：当前计数器={currentnow}，上次记录={last_wave_counter}')
            if currentnow == last_wave_counter:
                if logger:
                    logger.warning('检测到波次卡死，准备重启游戏...')
                else:
                    print('检测到波次卡死，准备重启游戏...')
                restart_game()
                return
            else:
                last_wave_counter = currentnow
def restart_game():
    """尝试关闭游戏并重启进程（退出当前进程由外部监控重启）"""
    for _ in range(2):
        result = find_image(resource_path('autophoto/shibai.png'), 0.7)
        if result:
            if logger:
                logger.info('识别到失败')
            else:
                print('识别到失败')
            for i in range(10):
                press_key('SPACE')
                time.sleep(0.5)
            click_at(1454, 220, button='left')
            os._exit(1)
        result = find_image(resource_path('xinggang/lianyukaishi.png'), 0.7)
        if result:
            if logger:
                logger.info('识别到炼狱开始')
            else:
                print('识别到炼狱开始')
            click_at(1454, 220, button='left')
            os._exit(1)
        result = find_image(resource_path('xinggang/tiaozhanmoshi.png'), 0.7)
        if result:
            if logger:
                logger.info('识别到挑战模式')
            else:
                print('识别到挑战模式')
            os._exit(1)
        result = find_image(resource_path('autophoto/zhujiemian.png'), 0.7)
        if result:
            if logger:
                logger.info('识别到主界面')
            else:
                print('识别到主界面')
            click_at(1675, 930, button='left')
            time.sleep(3)
            click_at(521, 502, button='left')
            time.sleep(3)
            result = find_image(resource_path('xinggang/lianyukaishi.png'), 0.7)
            if result:
                if logger:
                    logger.info('识别到炼狱开始')
                else:
                    print('识别到炼狱开始')
                click_at(1454, 220, button='left')
                os._exit(1)
            result = find_image(resource_path('xinggang/tiaozhanmoshi.png'), 0.7)
            if result:
                if logger:
                    logger.info('识别到挑战模式')
                else:
                    print('识别到挑战模式')
                os._exit(1)
            os._exit(1)
        time.sleep(10)
        if logger:
            logger.info('自检未检测到')
        else:
            print('自检未检测到')


def traverse():
    result = find_image(resource_path('xinggang/lianyukaishi.png'), 0.7)
    if result:
        if logger:
            logger.info('识别到炼狱开始')
        else:
            print('识别到炼狱开始')
        return True
    else:
        result = find_image(resource_path('xinggang/tiaozhanmoshi.png'), 0.7)
        if result:
            if logger:
                logger.info('识别到挑战模式')
            else:
                print('识别到挑战模式')
            click_at(1454, 220, button='left')
        result = find_image(resource_path('xinggang/zhujiemian.png'), 0.7)
        if result:
            if logger:
                logger.info('识别到主界面')
            else:
                print('识别到主界面')
            click_at(1675, 930, button='left')
            time.sleep(3)
            click_at(521, 502, button='left')
            time.sleep(3)
            result = find_image(resource_path('xinggang/lianyukaishi.png'), 0.7)
            if result:
                if logger:
                    logger.info('识别到炼狱开始')
                else:
                    print('识别到炼狱开始')
                click_at(1688, 954, button='left')
            result = find_image(resource_path('xinggang/tiaozhanmoshi.png'), 0.7)
            if result:
                if logger:
                    logger.info('识别到挑战模式')
                else:
                    print('识别到挑战模式')
        result = find_image(resource_path('autophoto/shibai.png'), 0.7)
        if result:
            if logger:
                logger.info('识别到失败')
            else:
                print('识别到失败')
            for i in range(10):
                press_key('SPACE')
                time.sleep(0.5)
            click_at(1454, 220, button='left')
        result = find_image(resource_path('autophoto/buzaitixing.png'), threshold=0.75)
        if result:
            time.sleep(1)
            click_at(899, 598, button='left')
            time.sleep(1)
            click_at(1100, 670, button='left')
            time.sleep(1)
        return False


def main():
    logger.info('开始运行游戏循环main')
    global wave_counter
    # ***<module>.main: Failure: Different control flow
    with wave_lock:
        wave_counter += 1
        print(f'当前完成波次: {wave_counter}')
    print('开局开始选择陷阱')
    press_key('N')
    time.sleep(0.5)
    image_path = resource_path('xianjing/fangkong.png')
    result = find_image(image_path, threshold=0.6)
    if result:
        x, y, similarity = result
        print(f'✅ 找到防空陷阱！坐标: ({x}, {y}), 相似度: {similarity:.3f}')
        click_at(x, y, button='left')
    time.sleep(0.5)
    image_path = resource_path('xianjing/tianqi.png')
    result = find_image(image_path, threshold=0.6)
    if result:
        x, y, similarity = result
        print(f'✅ 找到天启陷阱！坐标: ({x}, {y}), 相似度: {similarity:.3f}')
        click_at(x, y, button='left')
    time.sleep(0.5)
    image_path = resource_path('xianjing/zixiufucibaota.png')
    result = find_image(image_path, threshold=0.6)
    if result:
        x, y, similarity = result
        print(f'✅ 找到自修复磁暴塔！坐标: ({x}, {y}), 相似度: {similarity:.3f}')
        click_at(x, y, button='left')
    time.sleep(0.5)
    image_path = resource_path('xianjing/tianwang.png')
    result = find_image(image_path, threshold=0.6)
    if result:
        x, y, similarity = result
        print(f'✅ 找到天网！坐标: ({x}, {y}), 相似度: {similarity:.3f}')
        click_at(x, y, button='left')
    time.sleep(0.5)
    print('开局关闭选择陷阱页面')
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
                                            time.sleep(0.2)
                                        for idx in indexes:
                                            x = xbase + 510 + 85
                                            y = ybase + 85 + 170 * idx
                                            click_at(x, y, button='left', delay=0.1)
                                            time.sleep(0.2)
                                        initial_position(W=0, S=0)
                                        press_key('5')
                                        time.sleep(10)
                                        click_at(960, 200, button='left', delay=0.1)
                                        wait_for_image(resource_path('xinggang/BOCIERWANCHENG.png'),
                                                       threshold=0.75)
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
                                                    print(
                                                        f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
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
                                                                print(
                                                                    f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
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
                                                                                click_at(x, y, button='left',delay=0.1)
                                                                                time.sleep(0.1)
                                                                            for idx in indexes:
                                                                                x = xbase + 43 * idx
                                                                                y = ybase + 43
                                                                                click_at(x, y, button='left',delay=0.1)
                                                                                time.sleep(0.1)
                                                                            while True:
                                                                                initial_position(W=0, S=0.8)
                                                                                press_key('D', press_duration=0.2)
                                                                                time.sleep(0.2)
                                                                                image_path = resource_path(
                                                                                    'xinggang/0052.png')
                                                                                result = find_image(image_path,threshold=0.7)
                                                                                if result:
                                                                                    xinit, yinit, similarity = result
                                                                                    if 480 < xinit < 540 and 550 < yinit < 620:
                                                                                        print(
                                                                                            f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                                                        break
                                                                                        time.sleep(0.5)
                                                                                        press_key('4')
                                                                                        time.sleep(0.5)
                                                                                        xbase = xinit + 1093
                                                                                        ybase = yinit + 125
                                                                                        indexes = [(-1), 1]
                                                                                        for idx in indexes:
                                                                                            x = xbase + 43 * idx
                                                                                            y = ybase - 43
                                                                                            click_at(x, y,button='left',delay=0.1)
                                                                                            time.sleep(0.1)
                                                                                        for idx in indexes:
                                                                                            x = xbase + 43 * idx
                                                                                            y = ybase + 43
                                                                                            click_at(x, y,button='left',delay=0.1)
                                                                                            time.sleep(0.1)
                                                                                        wait_for_image(
                                                                                            resource_path('xinggang/BOCIERWANCHENG.png'),
                                                                                            threshold=0.75)
                                                                                        with wave_lock:
                                                                                            wave_counter += 1
                                                                                            print(f'当前完成波次: {wave_counter}')
                                                                                        press_key('G')
                                                                                        time.sleep(0.5)
                                                                                        press_key('4',press_duration=2)
                                                                                        time.sleep(0.5)
                                                                                        press_key('5',press_duration=2)
                                                                                        time.sleep(0.5)
                                                                                        press_key('5',press_duration=2)
                                                                                        while True:
                                                                                            initial_position(W=0, S=0.7)
                                                                                            image_path = resource_path('xinggang/0041.png')
                                                                                            result = find_image(image_path,threshold=0.7)
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
                                                                                                        click_at(x,y,button='left',delay=0.1)
                                                                                                        time.sleep(0.1)
                                                                                                    indexes = [0, 1]
                                                                                                    for idx in indexes:
                                                                                                        x = xbase - 510 - 170 * idx
                                                                                                        y = ybase + 425
                                                                                                        click_at(x,y,button='left',delay=0.1)
                                                                                                        time.sleep(0.1)
                                                                                                    for idx in indexes:
                                                                                                        x = xbase + 510 + 170 * idx
                                                                                                        y = ybase + 425
                                                                                                        click_at(x,y,button='left',delay=0.1)
                                                                                                        time.sleep(0.1)
                                                                                                    wait_for_image(resource_path('xinggang/BOCIERWANCHENG.png'),
                                                                                                        threshold=0.75)
                                                                                                    with wave_lock:
                                                                                                        wave_counter += 1
                                                                                                        print(f'当前完成波次: {wave_counter}')
                                                                                                    press_key('G')
                                                                                                    time.sleep(0.5)
                                                                                                    press_key('4',press_duration=2)
                                                                                                    time.sleep(0.5)
                                                                                                    press_key('5',press_duration=2)
                                                                                                    time.sleep(0.5)
                                                                                                    press_key('6',press_duration=2)
                                                                                                    while True:
                                                                                                        initial_position(W=0.3, S=0)
                                                                                                        image_path = resource_path('xinggang/0011.png')
                                                                                                        result = find_image(image_path,threshold=0.7)
                                                                                                        if result:
                                                                                                            xinit, yinit, similarity = result
                                                                                                            if 800 < xinit < 860 and 360 < yinit < 420:
                                                                                                                print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                                                                                xbase = xinit + 132
                                                                                                                ybase = yinit + 6
                                                                                                                time.sleep(0.5)
                                                                                                                press_key('6')
                                                                                                                time.sleep(0.5)
                                                                                                                click_at(xbase,ybase - 85,button='left',delay=0.1)
                                                                                                                time.sleep(0.1)
                                                                                                                click_at(xbase,ybase - 85 - 10,button='left',delay=0.1)
                                                                                                                time.sleep(0.1)
                                                                                                                click_at( xbase,ybase - 10,button='right',delay=0.1)
                                                                                                                time.sleep(0.5)
                                                                                                                press_key('5')
                                                                                                                time.sleep(0.5)
                                                                                                                indexes = [0,1]
                                                                                                                for idx in indexes:
                                                                                                                    x = xbase
                                                                                                                    y = ybase + 170 + 170 * idx
                                                                                                                    click_at(x,y,button='left',delay=0.1)
                                                                                                                    time.sleep(0.1)
                                                                                                                indexes = [(-1),1]
                                                                                                                for idx in indexes:
                                                                                                                    x = xbase + 170 * idx
                                                                                                                    y = ybase + 255
                                                                                                                    click_at( x,y,button='left',delay=0.1)
                                                                                                                    time.sleep(0.1)
                                                                                                                while True:
                                                                                                                    initial_position( W=0.6,S=0)
                                                                                                                    time.sleep(0.2)
                                                                                                                    image_path = resource_path('xinggang/0011.png')
                                                                                                                    result = find_image(image_path,threshold=0.7)
                                                                                                                    if result:
                                                                                                                        xinit, yinit, similarity = result
                                                                                                                        if 800 < xinit < 850 and 740 < yinit < 790:
                                                                                                                            print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                                                                                            time.sleep(0.5)
                                                                                                                            press_key('4')
                                                                                                                            time.sleep(0.5)
                                                                                                                            xbase = xinit - 39
                                                                                                                            ybase = yinit - 589
                                                                                                                            indexes = [0,1,2,3]
                                                                                                                            for idx in indexes:
                                                                                                                                x = xbase - 43 - 85 * idx
                                                                                                                                y = ybase + 43
                                                                                                                                click_at(x,y,button='left',delay=0.1)
                                                                                                                                time.sleep(0.1)
                                                                                                                                click_at(x,y,button='left',delay=0.1)
                                                                                                                                time.sleep(0.1)
                                                                                                                                click_at(x,y,button='left',delay=0.1)
                                                                                                                                time.sleep(0.1)
                                                                                                                            for idx in indexes:
                                                                                                                                x = xbase - 43 - 85 * idx
                                                                                                                                y = ybase + 43 + 85
                                                                                                                                click_at(x,y,button='left',delay=0.1)
                                                                                                                                time.sleep(0.1)
                                                                                                                                click_at(x,y,button='left',delay=0.1)
                                                                                                                                time.sleep(0.1)
                                                                                                                                click_at(x,y,button='left',delay=0.1)
                                                                                                                                time.sleep(0.1)
                                                                                                                            for idx in indexes:
                                                                                                                                x = xbase + 340 + 43 + 85 * idx
                                                                                                                                y = ybase + 43
                                                                                                                                click_at(x,y,button='left',delay=0.1)
                                                                                                                                time.sleep(0.1)
                                                                                                                                click_at(x,y,button='left',delay=0.1)
                                                                                                                                time.sleep(0.1)
                                                                                                                                click_at(x,y,button='left',delay=0.1)
                                                                                                                                time.sleep(0.1)
                                                                                                                            for idx in indexes:
                                                                                                                                x = xbase + 340 + 43 + 85 * idx
                                                                                                                                y = ybase + 43 + 85
                                                                                                                                click_at(x,y,button='left',delay=0.1)
                                                                                                                                time.sleep(0.1)
                                                                                                                                click_at(x,y,button='left',delay=0.1)
                                                                                                                                time.sleep(0.1)
                                                                                                                                click_at(x,y,button='left',delay=0.1)
                                                                                                                                time.sleep(0.1)
                                                                                                                            wait_for_image(resource_path('xinggang/BOCIERWANCHENG.png'),threshold=0.75)
                                                                                                                            with wave_lock:
                                                                                                                                wave_counter += 1
                                                                                                                                print(f'当前完成波次: {wave_counter}')
                                                                                                                            press_key('G')
                                                                                                                            time.sleep(0.5)
                                                                                                                            while True:
                                                                                                                                initial_position(W=0.6,S=0)
                                                                                                                                time.sleep(0.2)
                                                                                                                                image_path = resource_path('xinggang/0011.png')
                                                                                                                                result = find_image(image_path,threshold=0.7)
                                                                                                                                if result:
                                                                                                                                    xinit, yinit, similarity = result
                                                                                                                                    if 800 < xinit < 850 and 740 < yinit < 790:
                                                                                                                                        print(f'✅ 找到图片！坐标: ({xinit}, {yinit}), 相似度: {similarity:.3f}')
                                                                                                                                        time.sleep(0.5)
                                                                                                                                        press_key('4')
                                                                                                                                        time.sleep(0.5)
                                                                                                                                        xbase = xinit - 39
                                                                                                                                        ybase = yinit - 589
                                                                                                                                        indexes = [0,1,2,3]
                                                                                                                                        for idx in indexes:
                                                                                                                                            x = xbase - 43 - 85 * idx
                                                                                                                                            y = ybase + 43
                                                                                                                                            click_at(x,y,button='left',delay=0.1)
                                                                                                                                            time.sleep(0.1)
                                                                                                                                            click_at(x,y,button='left',delay=0.1)
                                                                                                                                            time.sleep(0.1)
                                                                                                                                            click_at(x,y,button='left',delay=0.1)
                                                                                                                                            time.sleep(0.1)
                                                                                                                                        for idx in indexes:
                                                                                                                                            x = xbase - 43 - 85 * idx
                                                                                                                                            y = ybase + 43 + 85
                                                                                                                                            click_at(x,y,button='left',delay=0.1)
                                                                                                                                            time.sleep(0.1)
                                                                                                                                            click_at(x,y,button='left',delay=0.1)
                                                                                                                                            time.sleep(0.1)
                                                                                                                                            click_at(x,y,button='left',delay=0.1)
                                                                                                                                            time.sleep(0.1)
                                                                                                                                        for idx in indexes:
                                                                                                                                            x = xbase + 340 + 43 + 85 * idx
                                                                                                                                            y = ybase + 43
                                                                                                                                            click_at(x,y,button='left',delay=0.1)
                                                                                                                                            time.sleep(0.1)
                                                                                                                                            click_at(x,y,button='left',delay=0.1)
                                                                                                                                            time.sleep(0.1)
                                                                                                                                            click_at(x,y,button='left',delay=0.1)
                                                                                                                                            time.sleep(0.1)
                                                                                                                                        for idx in indexes:
                                                                                                                                            x = xbase + 340 + 43 + 85 * idx
                                                                                                                                            y = ybase + 43 + 85
                                                                                                                                            click_at(x,y,button='left',delay=0.1)
                                                                                                                                            time.sleep(0.1)
                                                                                                                                            click_at(x,y,button='left',delay=0.1)
                                                                                                                                            time.sleep(0.1)
                                                                                                                                            click_at(x,y,button='left',delay=0.1)
                                                                                                                                            time.sleep(0.1)
                                                                                                                                        wait_for_image(
                                                                                                                                            resource_path(
                                                                                                                                                'xinggang/BOCIERWANCHENG.png'),
                                                                                                                                            threshold=0.75)
                                                                                                                                        with wave_lock:
                                                                                                                                            wave_counter += 1
                                                                                                                                            print(f'当前完成波次: {wave_counter}')
                                                                                                                                        press_key('G')
                                                                                                                                        time.sleep(0.5)
                                                                                                                                        press_key('SPACE',press_duration=2)
                                                                                                                                        time.sleep(0.5)
                                                                                                                                        press_key('SPACE')
                                                                                                                                        time.sleep(0.5)
                                                                                                                                        press_key('SPACE',press_duration=2)
                                                                                                                                        time.sleep(0.5)
                                                                                                                                        press_key('SPACE',press_duration=2)
                                                                                                                                        time.sleep(0.5)
                                                                                                                                        press_key('SPACE',press_duration=2)
                                                                                                                                        time.sleep(0.5)
                                                                                                                                        press_key('SPACE',press_duration=2)
                                                                                                                                        time.sleep(90)
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

def waitto():
    time.sleep(1)
    print("5")
    time.sleep(1)
    print("4")
    time.sleep(1)
    print("3")
    time.sleep(1)
    print("2")
    time.sleep(1)
    print("1")
def run_game_cycle():
    """
    游戏自动化核心循环函数
    功能：启动后台监控线程，持续检测游戏状态并执行自动化操作，完成炼狱模式的识别与进入流程
    """
    # ========== 启动后台监控线程 ==========
    # 启动周期性图像检查线程（守护线程，主程序退出时自动结束）
    # 作用：后台持续检查游戏画面中的特定图像，不阻塞主线程
    waitto()
    logger.info('启动游戏自动化核心循环...')
    t1 = threading.Thread(target=periodic_image_check, daemon=True)
    t1.start()

    # 启动波形监控线程（守护线程，主程序退出时自动结束）
    # 作用：后台监控游戏中的波形数据/状态变化
    t2 = threading.Thread(target=wave_monitor, daemon=True)
    t2.start()

    # ========== 主游戏循环（无限循环，持续运行） ==========
    while True:
        # 第一阶段：循环检测"炼狱"标识，直到识别到为止
        while True:
            # 调用traverse函数检测画面中是否出现"炼狱"相关元素
            if traverse():
                if logger:
                    logger.info('识别到炼狱开始，执行操作后退出循环！')
                else:
                    print('识别到炼狱开始，执行操作后退出循环！')
                # 识别到目标，退出当前检测循环，执行后续操作
                break
            else:
                # 未识别到，等待0.5秒后再次检测，降低CPU占用
                time.sleep(0.5)

        # 识别到炼狱后，执行一系列点击/按键操作（模拟人工操作）
        # 短暂等待0.5秒，确保画面稳定后再操作
        time.sleep(0.5)
        # 在坐标(1688, 954)处左键单击（可能是"开始挑战"等按钮）
        click_at(1688, 954, button='left')
        time.sleep(0.5)  # 等待操作生效
        click_at(1688, 954, button='left')  # 再次点击，确保触发成功
        time.sleep(0.5)  # 等待操作生效

        # 检测是否出现"不在提醒"弹窗（路径：autophoto/buzaitixing.png）
        # threshold=0.75：图像匹配相似度阈值，75%以上即认为匹配成功
        result = find_image(resource_path('autophoto/buzaitixing.png'), threshold=0.75)
        if result:
            # 检测到弹窗，执行关闭/确认操作
            time.sleep(1)  # 等待弹窗完全加载
            click_at(899, 598, button='left')  # 点击弹窗第一个按钮
            time.sleep(1)
            click_at(1100, 670, button='left')  # 点击弹窗第二个按钮
            time.sleep(1)

        # 点击游戏画面中心位置(960, 540)，可能是确认/进入游戏按钮
        click_at(960, 540, button='left')
        time.sleep(0.2)  # 短等待，确保点击生效
        # 按住空格键2秒（可能是确认进入游戏/加载场景的操作）
        press_key('SPACE', press_duration=2)
        wait_for_image(resource_path('xinggang/chenggongjinruyouxi.png'), threshold=0.75, Afterrecognition=1)
        time.sleep(2)
        # 调用main函数，执行游戏内的核心操作逻辑（如自动打怪、走位等）
        logger.info('开始运行游戏循环1083')
        main()

        # 第二阶段：游戏结束/退出后，再次循环检测"炼狱"标识
        while True:
            # 按空格键（可能是退出结算界面/返回主界面的操作）
            press_key('SPACE', press_duration=0.1)
            # 检测是否再次出现"炼狱"标识
            if traverse():
                if logger:
                    logger.info('识别到炼狱开始，执行操作后退出循环！')
                else:
                    print('识别到炼狱开始，执行操作后退出循环！')
                break
            else:
                time.sleep(0.5)  # 未识别到则等待0.5秒

        # 完成一轮循环后，等待5秒再进入下一轮，避免操作过快
        time.sleep(5)
def wave_monitor():
    global last_wave_counter
    CHECK_INTERVAL = 300
    while True:
        time.sleep(CHECK_INTERVAL)
        with wave_lock:
            currentnow = wave_counter
            if logger:
                logger.info(f'波次监控：当前计数器={currentnow}，上次记录={last_wave_counter}')
            else:
                print(f'波次监控：当前计数器={currentnow}，上次记录={last_wave_counter}')
            if currentnow == last_wave_counter:
                if logger:
                    logger.warning('检测到波次卡死，准备重启游戏...')
                else:
                    print('检测到波次卡死，准备重启游戏...')
                restart_game()
                return
            else:
                last_wave_counter = currentnow

if __name__ == '__main__':
    run_game_cycle()

# def main():
#     print('开始运行游戏循环')
#     run_game_cycle()
