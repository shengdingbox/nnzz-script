import cv2
import numpy as np
from PIL import ImageGrab
import pyautogui  # 用于便捷获取主屏幕信息，需提前安装

import screeninfo  # 用于精准获取多屏幕坐标，需安装

# 1. 获取所有屏幕的信息（包含主/副屏的坐标、宽高）
screens = screeninfo.get_monitors()
print("所有屏幕信息：")
for idx, screen in enumerate(screens):
    print(f"屏幕 {idx}：坐标({screen.x},{screen.y})，宽{screen.width}，高{screen.height}")

# 1. 获取主屏幕的尺寸和位置（主屏幕的左上角坐标默认是 (0,0)）
screen_width, screen_height = pyautogui.size()  # 获取主屏幕的宽和高
secondary_screen = screens[1]  # 改为你实际的副屏索引
main_screen_region = (-4096, 0, screen_width, screen_height)  # 主屏幕区域：(左, 上, 右, 下)

secondary_region = (
    secondary_screen.x,          # 副屏左上角x坐标
    secondary_screen.y,          # 副屏左上角y坐标
    secondary_screen.x + secondary_screen.width,  # 副屏右下角x坐标
    secondary_screen.y + secondary_screen.height  # 副屏右下角y坐标
)
print("副屏区域：", secondary_region)

# 5. 截取副屏画面
screen = ImageGrab.grab(bbox=secondary_region)

# 6. 转换为OpenCV格式（RGB→BGR）
frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)

# 7. 验证：显示副屏画面（可选）
cv2.imshow('Secondary Screen Capture', frame)
cv2.waitKey(0)
cv2.destroyAllWindows()

# （可选）保存副屏截图
cv2.imwrite('2secondary_screen_capture.jpg', frame)

# 2. 只截取主屏幕
screen = ImageGrab.grab(bbox=main_screen_region)  # bbox参数指定截取区域

# 3. 将PIL图像转换为OpenCV格式（PIL是RGB，OpenCV是BGR）
frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)

# 4. 验证：显示截取的主屏幕画面（可选）
cv2.imshow('Main Screen Capture', frame)
cv2.waitKey(0)  # 按任意键关闭窗口
cv2.destroyAllWindows()

# （可选）保存截取的主屏幕图片
cv2.imwrite('1main_screen_capture.jpg', frame)



screen = ImageGrab.grab()
frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
cv2.imwrite('main_screen_capture.jpg', frame)