import math
import numpy as np
import matplotlib.pyplot as plt


size = 51
hero_pos = np.array([0, 0])
def cvt_pos_to_bound(pos):
    """ 将超出范围的treasure,buff,end转为的可用边界 """
    center = np.array([size // 2, size // 2], np.int32)
    delta_pos = pos - hero_pos
    if abs(delta_pos[0]) <= size // 2 and abs(delta_pos[1]) <= size // 2:
        return delta_pos + center
    theta = math.atan2(delta_pos[1], delta_pos[0])
    # print(delta_pos, theta, theta * 180 / math.pi, math.tan(theta))
    if abs(delta_pos[0]) > abs(delta_pos[1]):
        delta_pos[0] = size // 2 * np.sign(delta_pos[0])
        delta_pos[1] = round(size // 2 * abs(math.tan(theta)) * np.sign(delta_pos[1]))
    else:
        delta_pos[1] = size // 2 * np.sign(delta_pos[1])
        delta_pos[0] = round(size // 2 / abs(math.tan(theta)) * np.sign(delta_pos[0]))
    # print(delta_pos, size // 2 * math.tan(theta))
    return center + delta_pos.astype(np.int32)

tranangle = [[-(size // 2), -(size // 2), size // 2, size // 2, -(size // 2)],
         [-(size // 2), size // 2, size // 2, -(size // 2), -(size // 2)]]
plt.plot(tranangle[0], tranangle[1], 'b-')

# for i in range(10, 11):
#     p0 = np.array([i, 10])
# p0 = np.array([5, 10])
# p0 = np.array([-5, -10])
# p0 = np.array([5, -10])
def draw(p0):
    p1 = cvt_pos_to_bound(p0) - np.array([size // 2, size // 2], np.int32)
    plt.plot([hero_pos[0], p0[0]], [hero_pos[1], p0[1]], 'go-')
    plt.plot([hero_pos[0], p1[0]], [hero_pos[1], p1[1]], 'ro-')

# p0 = np.array([10, -0])
p0 = np.array([21, 54]) - np.array([45, 29])
print(p0)
draw(p0)

# for i in range(-10, 11):
# for i in range(-10, 0):
# for i in range(5, 11):
# # for i in range(-1, 4):
#     draw(np.array([i, 10]))
    # draw(np.array([i, -10]))
    # draw(np.array([10, i]))
    # draw(np.array([-10, i]))

plt.show()
