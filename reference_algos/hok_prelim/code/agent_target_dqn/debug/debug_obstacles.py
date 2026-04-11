import numpy as np
import cv2

obstacles = np.load(r"C:\Coding\kaiwu2025\hok_prelim\code\ckpt\obstacles.npy")
print(obstacles)
img = np.zeros((128, 128), dtype=np.uint8)
img[obstacles == 1] = 255  # 将障碍物位置设为白色
img[obstacles == 0] = 0    # 将非障碍物位置设为黑色
img[obstacles == -1] = 127  # 将未探索位置设为灰色
cv2.imwrite(r"C:\Coding\kaiwu2025\hok_prelim\code\ckpt\obstacles.png", img)
print("Obstacles image saved as obstacles.png")
