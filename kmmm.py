import kmNet
import time
import pyautogui


time.sleep(5)
ip='192.168.2.188'
port='7300'
mac='3CC6DC32'
result = kmNet.init(ip, port, mac)
if result == 0:
    print('kmboxNet初始化成功')
else:
    print(f'kmboxNet初始化失败，错误码：{result}')
x, y = pyautogui.position()
print(f'当前鼠标位置：({x}, {y})')
kmNet.move_auto(10-x, 310-y,300)
