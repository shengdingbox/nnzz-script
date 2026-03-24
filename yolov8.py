import cv2
import time
import torch
import dxcam
import numpy as np
from queue import Queue
from threading import Thread
from ultralytics import YOLO


# ==============================
# GPU 检查
# ==============================

if not torch.cuda.is_available():
    raise RuntimeError("CUDA GPU 不可用")

DEVICE = "cuda:0"

print("Using GPU:", torch.cuda.get_device_name(0))


# ==============================
# YOLOv8 加载
# ==============================

model = YOLO("yolov8n.pt")
model.to(DEVICE)


# ==============================
# 屏幕区域
# ==============================

REGION = (600, 200, 1240, 840)  # left top right bottom


# ==============================
# 队列
# ==============================

frame_queue = Queue(maxsize=3)
result_queue = Queue(maxsize=3)


# ==============================
# 屏幕捕获线程
# ==============================

class CaptureThread:

    def __init__(self):

        self.camera = dxcam.create()
        self.camera.start(region=REGION, target_fps=240)

        self.running = True

        Thread(target=self.update, daemon=True).start()

    def update(self):

        while self.running:

            frame = self.camera.get_latest_frame()

            if frame is None:
                continue

            if not frame_queue.full():
                frame_queue.put(frame)


# ==============================
# YOLO 推理线程
# ==============================

class InferenceThread:

    def __init__(self):

        self.running = True

        Thread(target=self.update, daemon=True).start()

    def update(self):

        while self.running:

            if frame_queue.empty():
                continue

            frame = frame_queue.get()

            results = model(
                frame,
                device=0,
                conf=0.4,
                iou=0.5,
                half=True,
                verbose=False
            )

            if not result_queue.full():
                result_queue.put((frame, results))


# ==============================
# 启动线程
# ==============================

capture = CaptureThread()
inference = InferenceThread()


# ==============================
# FPS 统计
# ==============================

prev_time = time.time()


# ==============================
# 主循环（显示）
# ==============================

while True:

    if result_queue.empty():
        continue

    frame, results = result_queue.get()


    # 解析检测框
    for r in results:

        if r.boxes is None:
            continue

        for box in r.boxes:

            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

            conf = float(box.conf[0])
            cls = int(box.cls[0])

            label = model.names[cls]

            cv2.rectangle(
                frame,
                (int(x1), int(y1)),
                (int(x2), int(y2)),
                (0,255,0),
                2
            )

            cv2.putText(
                frame,
                f"{label} {conf:.2f}",
                (int(x1), int(y1)-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0,255,0),
                2
            )


    # FPS
    now = time.time()
    fps = 1 / (now - prev_time)
    prev_time = now

    cv2.putText(
        frame,
        f"FPS: {int(fps)}",
        (20,40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0,0,255),
        2
    )


    cv2.imshow("YOLOv8 RealTime Detection", frame)

    if cv2.waitKey(1) == 27:
        break


cv2.destroyAllWindows()