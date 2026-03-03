# 第一步：安装依赖（仅Windows需要）
# pip install pywin32

# 第二步：实际使用代码
import win32api
import time


time.sleep(3)

print("当前鼠标位置:", win32api.GetCursorPos())

# 1. 基础用法：将鼠标移动到屏幕 (500, 300) 的位置
win32api.SetCursorPos((500, 300))
print("当前鼠标位置:", win32api.GetCursorPos())
time.sleep(3)
# 2. 结合多屏幕：移动到右侧副屏的 (2000, 500) 位置（假设主屏宽1920）
win32api.SetCursorPos((-1920, 500))
print("当前鼠标位置:", win32api.GetCursorPos())
time.sleep(3)
# 3. 配合之前的屏幕截取：移动到副屏的指定位置
import screeninfo
screens = screeninfo.get_monitors()
secondary_screen = screens[1]  # 副屏
# 移动到副屏的中心位置
center_x = secondary_screen.x + secondary_screen.width // 2
center_y = secondary_screen.y + secondary_screen.height // 2
win32api.SetCursorPos((center_x, center_y))
print("当前鼠标位置:", win32api.GetCursorPos())
