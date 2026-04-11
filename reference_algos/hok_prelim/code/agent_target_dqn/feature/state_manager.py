"""
将环境返回的frame_state (Observation, ExtraInfo['game_info'])转为我们所需的obs特征并计算reward函数
"""

import math
import numpy as np
from collections import deque
from agent_target_dqn.conf.conf import Config as cfg
from agent_target_dqn.utils.display_iterable_struct import save_json, simplify_iter, too_simplify_iter
from agent_target_dqn.utils import PATH_DEBUG
from agent_target_dqn.conf.constants import (
    name2sub_type,
    DirectionAngles, RelativeDirection, RelativeDistance
)

PATH_FRAMES = PATH_DEBUG / "frames"
PATH_MAP = PATH_DEBUG / "map"
PATH_FRAMES.mkdir(parents=True, exist_ok=True)
PATH_MAP.mkdir(parents=True, exist_ok=True)

def norm(x, min_x, max_x, eps=1e-8):
    """ clip到min, max并缩放到(-1, 1) """
    if not isinstance(x, np.ndarray):
        x = np.array(x, np.float32)
    x = np.maximum(np.minimum(max_x, x), min_x)
    return (x - min_x) / (max_x - min_x + eps)

def round_pos(pos):
    """ 将pos列表的浮点数四舍五入为整数"""
    return np.array(pos, np.float32).round().astype(np.int32)

def get_position_feature(hero_pos, target_pos, found, available):
    """ 返回目标的位置特征信息 (6维) """
    if target_pos[0] == -1 or not available:  # 若位置不存在则返回全0, 目标距离为1
        x = np.full((6,), 0, np.float32)
        x[3] = 1.0
        return x
    relative_pos = [target_pos[0] - hero_pos[0], target_pos[1] - hero_pos[1]]
    delta_distance = max(np.linalg.norm(relative_pos), 1e-4)
    pos_norm = norm(target_pos, -128, 128)
    feature = np.array([
        found,  # 是否有确定坐标
        norm(relative_pos[0] / delta_distance, -1, 1),  # 相对位置
        norm(relative_pos[1] / delta_distance, -1, 1),
        norm(delta_distance, 0, math.sqrt(2) * 128),  # 目标距离
        pos_norm[0], pos_norm[1],  # 目标位置
    ], np.float32)
    return feature

def get_hero_info_and_pos(frame_state):
    hero_info = frame_state['obs']['frame_state']['heroes'][0]
    hero_pos = [hero_info['pos']['x'], hero_info['pos']['z']]
    return hero_info, hero_pos

class OrganManager:
    """ 对start, end, treasure, buff位置进行估计
    当未看到时, 则用方向+距离进行估计, 当看到时，则记录下位置, 可输出为特征信息
    """
    def __init__(self, name, config_id=None):
        self.name = name
        assert self.name in name2sub_type, f"[ERROR - OrganManager]: name={self.name} not in names={name2sub_type.keys()}"
        self.config_id = config_id
        self.found = False  # 是否有
        self.last_pos = np.array([-1, -1], np.float32)
        self.pos = np.array([-1, -1], np.float32)
        self.direction, self.distance = None, None  # 离散的大致距离和方向
        self.last_real_distance, self.real_distance = -1, -1  # 上一帧的真实距离和当前帧的真实距离
        self.available = True  # 是否可获取宝箱/buff, 宝箱仅有在获取过的一帧变为status=0, 因此available变为False永远就是False了
    
    def update(self, organ, hero_pos):
        """ 更新位置信息, organ为obs['organs']中的RealmOrgan消息, 格式如下:
        ```
        message RealmOrgan {
            int32 sub_type = 1;   // 物件类型,1代表宝箱,2代表加速buff,3代表起点,4代表终点
            int32 config_id = 2;  // 物件id 0代表buff，1~13代表宝箱 21代表起点, 22代表终点
            int32 status = 3;     // 0表示不可获取，1表示可获取, -1表示视野外
            Position pos = 4;     // 物件位置坐标
            int32 cooldown = 5;                // 物件剩余冷却时间
            RelativePosition relative_pos = 6; // 物件相对位置
        }
        ```
        """
        assert organ['sub_type'] == name2sub_type[self.name], f"[ERROR - OrganManager]: Update name error, update: {name2sub_type[self.name]} != {self.name}"
        assert self.config_id is None or (organ['config_id'] == self.config_id), f"[ERROR - OrganManager]: Update config_id error, update: {organ['config_id']} != {self.config_id}"

        relative_pos = organ['relative_pos']
        direction = RelativeDirection[relative_pos['direction']]
        distance = RelativeDistance[relative_pos['l2_distance']]

        self.last_real_distance = self.real_distance
        self.last_pos = self.pos.copy()
        if organ['status'] == 0:  # 不可获取 (已经拿过了)
            self.available = False

        if self.found:  # 已经找到过, 就按照已知坐标进行更新
            self.real_distance = np.linalg.norm(self.pos - np.array(hero_pos, np.float32))
            return

        # 没找到过, 或第一次找到, 或据方向和距离进行估计
        if organ['status'] != -1:  # 视野内
            self.pos = np.array([organ['pos']['x'], organ['pos']['z']], np.float32)
            self.found = True
            self.real_distance = np.linalg.norm(self.pos - np.array(hero_pos, np.float32))
        elif self.direction != direction or self.distance != distance:
            self.direction = direction
            self.distance = distance
            self.real_distance = distance * 20
            theta = DirectionAngles[direction]
            dx = self.real_distance * math.cos(math.radians(theta))
            dz = self.real_distance * math.sin(math.radians(theta))
            self.pos = np.array([
                max(0, min(127, round(hero_pos[0] + dx))),
                max(0, min(127, round(hero_pos[1] + dz))),
            ], np.float32)

        if self.last_real_distance == -1:  # 第一帧
            self.last_real_distance = self.real_distance
            self.last_pos = self.pos.copy()

    def get_feature(self, hero_pos):
        """ 返回该organ的位置特征信息 (6维) """
        return get_position_feature(hero_pos, self.pos, self.found, self.available)

class MapManager:
    """ 管理地图中的各种物件信息, 构建地图特征 (4, 128, 128)
1. dim 0: 障碍物 (-1, 0, 1) 分别为 (未知, 无, 有)
2. dim 1: 走过的次数 (0 ~ 1) 分别为次数 (0,1,2,...), 作用 clip(x/10,0,1)
3. dim 2: buff/宝箱 (-1, -0.5, 0, 0.5, 1) 分别为 (buff精确位置, buff大致位置, 无, 宝箱大致位置, 宝箱精确位置)
4. dim 3: 终点 (0, 0.5, 1)  分别为 (无, 终点大致位置, 终点精确位置)
5. dim 4: 英雄位置 (0, 1) 分别为 (无, 有)
    """
    def __init__(self):
        self.obstacles = np.full((128, 128), -1.0, np.float32)
        self.memory = np.zeros((128, 128), np.float32)
        self.buff_treasures = np.zeros((128, 128), np.float32)
        self.hero = np.zeros((128, 128), np.float32)
        self.end = np.zeros((128, 128), np.float32)
        self.explored = np.zeros((128, 128), np.float32)  # 是否探索过区域

        self.avail_treasures = [False] * 13
        self.avail_buff = False
        self.last_pos_treasures = [None] * 13
        self.last_pos_buff = None
        self.last_pos_end = None
        self.step = 0
        self.now_explore_grid = 0  # 当前帧新探索的网格数
    
    def update_treasure(self, organ: OrganManager):
        id = organ.config_id - 1
        pos = round_pos(organ.pos)
        def clean_last_pos():
            if self.last_pos_treasures[id] is not None:
                self.buff_treasures[*self.last_pos_treasures[id]] = 0.0
            self.last_pos_treasures[id] = pos
        if not organ.available:
            if self.avail_treasures[id]:  # 取到宝箱, 将已有状态删去
                self.buff_treasures[*pos] = 0.0
            self.avail_treasures[id] = False
            return
        self.avail_treasures[id] = True
        if not organ.found:  # 大致位置
            if organ.last_real_distance >= organ.real_distance:
                clean_last_pos()
                self.buff_treasures[*pos] = 0.5
        else:  # 准确位置
            clean_last_pos()
            self.buff_treasures[*pos] = 1.0
    
    def update_buff(self, organ: OrganManager):
        pos = round_pos(organ.pos)
        def clean_last_pos():
            if self.last_pos_buff is not None:
                self.buff_treasures[*self.last_pos_buff] = 0.0
            self.last_pos_buff = pos
        if not organ.available:
            if self.avail_buff:  # 取到buff
                self.buff_treasures[*pos] = 0.0
            self.avail_buff = False
            return
        self.avail_buff = True
        if not organ.found:  # 大致位置
            if organ.last_real_distance >= organ.real_distance:
                clean_last_pos()
                self.buff_treasures[*pos] = -0.5
        else:  # 准确位置
            clean_last_pos()
            self.buff_treasures[*pos] = -1.0
    
    def update_end(self, organ: OrganManager):
        pos = round_pos(organ.pos)
        def clean_last_pos():
            if self.last_pos_end is not None:
                self.end[*self.last_pos_end] = 0.0
            self.last_pos_end = pos
        if not organ.found:  # 大致位置
            if organ.last_real_distance >= organ.real_distance:
                clean_last_pos()
                self.end[*pos] = 0.5
        else:  # 准确位置
            clean_last_pos()
            self.end[*pos] = 1.0
    
    def update_obstacles(self, hero_pos, map_info):
        """ 更新障碍物信息和新探索的区域 """
        hero_pos = round_pos(hero_pos)
        # 0表示不可通行，1表示可以通行，2表示起点位置，3表示终点位置，4表示宝箱位置，6表示加速增益位置
        # 但是这里障碍物我们只关心0, 1两种情况
        map = np.array([line['values'] for line in map_info], np.float32)
        map = np.clip(map, 0, 1)
        map_size = map.shape[0]
        self.now_explore_grid = 0
        for i in range(map.shape[0]):
            for j in range(map.shape[1]):
                u, v = hero_pos[0] + i - map_size // 2, hero_pos[1] + j - map_size // 2
                if u < 0 or u >= 128 or v < 0 or v >= 128:
                    continue
                self.obstacles[u, v] = map[i, j]
                if self.explored[u, v] == 0 and self.step > 0:
                    self.now_explore_grid += 1
                self.explored[u, v] = 1

    def update_hero(self, hero_pos):
        """ **最后**更新hero和memory """
        self.hero_pos = round_pos(hero_pos)
        self.hero = np.zeros((128, 128), np.float32)
        self.hero[*hero_pos] = 1.0
        self.memory[*hero_pos] += 1.0
        self.step += 1
        # if self.step < 10:
        #     np.savetxt(PATH_FRAMES / f"memory{self.step}.txt", self.memory, fmt="%.0f")
        # print(f"{'='*10}[DEBUG] {hero_pos=}{'='*10}")
    
    def get_feature(self):
        x = np.zeros((5, 128, 128), np.float32)
        x[0] = self.obstacles
        x[1] = np.clip(self.memory / 10, 0, 1)
        x[2] = self.buff_treasures
        x[3] = self.end
        x[4] = self.hero
        return x
    
    def get_around_memory(self, size=5):
        """ 获取周围的memory信息, size为周围的大小 """
        assert size % 2 == 1, f"[ERROR - MapManager]: size must be odd, but got {size}"
        x = np.zeros((size, size), np.float32)
        for i in range(size):
            for j in range(size):
                ii = self.hero_pos[0] + i - size // 2
                jj = self.hero_pos[1] + j - size // 2
                if ii < 0 or ii >= 128 or jj < 0 or jj >= 128:
                    continue
                x[i, j] = self.memory[ii, jj]
        return x
    
    def get_around_feature(self, size=51):
        """ 获取周围的obstacles, memory, buff_treasure, end信息 """
        assert size % 2 == 1, f"[ERROR - MapManager]: size must be odd, but got {size}"
        x = np.zeros((4, size, size), np.float32)
        for i in range(size):
            for j in range(size):
                ii = self.hero_pos[0] + i - size // 2
                jj = self.hero_pos[1] + j - size // 2
                if ii < 0 or ii >= 128 or jj < 0 or jj >= 128:
                    continue
                x[0, i, j] = self.obstacles[ii, jj]
                x[1, i, j] = np.clip(self.memory[ii, jj] / 10, 0, 1)
                # x[2, i, j] = self.buff_treasures[ii, jj]
                # x[3, i, j] = self.end[ii, jj]
        
        def cvt_pos_to_bound(pos):
            """ 将超出范围的treasure,buff,end转为的可用边界 """
            center = np.array([size // 2, size // 2], np.int32)
            delta_pos = pos - self.hero_pos
            if abs(delta_pos[0]) <= size // 2 and abs(delta_pos[1]) <= size // 2:
                return delta_pos + center
            theta = math.atan2(delta_pos[1], delta_pos[0])
            if abs(delta_pos[0]) > abs(delta_pos[1]):
                delta_pos[0] = size // 2 * np.sign(delta_pos[0])
                delta_pos[1] = round(size // 2 * abs(math.tan(theta)) * np.sign(delta_pos[1]))
            else:
                delta_pos[1] = size // 2 * np.sign(delta_pos[1])
                delta_pos[0] = round(size // 2 / abs(math.tan(theta)) * np.sign(delta_pos[0]))
            return center + delta_pos.astype(np.int32)

        treasures_pos = np.argwhere(self.buff_treasures > 0)
        buff_pos = np.argwhere(self.buff_treasures < 0)
        end_pos = np.argwhere(self.end > 0)
        for pos in treasures_pos:
            p = cvt_pos_to_bound(pos)
            # print(f"[DEBUG] {self.hero_pos=}, {pos=}, {p=}")
            x[2, p[0], p[1]] = max(x[2, p[0], p[1]], self.buff_treasures[pos[0], pos[1]])
        for pos in buff_pos:
            p = cvt_pos_to_bound(pos)
            x[2, p[0], p[1]] = min(x[2, p[0], p[1]], self.buff_treasures[pos[0], pos[1]])
        for pos in end_pos:
            p = cvt_pos_to_bound(pos)
            x[3, p[0], p[1]] = max(x[3, p[0], p[1]], self.end[pos[0], pos[1]])
        return x
    
    def save_map(self):
        import cv2
        memory_img = np.clip(self.memory/10, 0, 1) * 255
        img = np.zeros((128, 128, 3), np.uint8)
        img = cv2.cvtColor((self.obstacles*255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
        img[self.obstacles == -1] = [80, 80, 80]  # 未知障碍物 (gray)
        img[memory_img > 0] = memory_img[memory_img > 0, None]  # 加入记忆
        img[self.hero_pos[0], self.hero_pos[1]] = [255, 0, 0]  # 英雄位置 (blue)
        img[self.buff_treasures == 0.5] = [0, 255//2, 0]  # 宝箱大致位置 (green)
        img[self.buff_treasures == 1.0] = [0, 255, 0]  # 宝箱精确位置
        img[self.buff_treasures == -0.5] = [0, 0, 255//2]  # buff大致位置 (red)
        img[self.buff_treasures == -1.0] = [0, 0, 255]  # buff精确位置
        img[self.end > 0] = [255, 0, 255] * self.end[self.end > 0]  # 终点位置 (pink)
        cv2.imwrite(str(PATH_MAP / f"map{self.step}.png"), img)
        print(f"Finished saving map images. {self.step=}")
    
    def save_around_map(self, size=51):
        x = self.get_around_feature(size=size)
        import cv2
        memory_img = x[1] * 255
        img = cv2.cvtColor((x[0]*255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
        img[x[0] == -1] = [80, 80, 80]  # 未知障碍物 (gray)
        img[memory_img > 0] = memory_img[memory_img > 0, None]  # 加入记忆
        img[size//2, size//2] = [255, 0, 0]  # 英雄位置 (blue)
        img[x[2] == 0.5] = [0, 255//2, 0]  # 宝箱大致位置 (green)
        img[x[2] == 1.0] = [0, 255, 0]  # 宝箱精确位置
        img[x[2] == -0.5] = [0, 0, 255//2]  # buff大致位置 (red)
        img[x[2] == -1.0] = [0, 0, 255]  # buff精确位置
        img[x[3] > 0] = [255, 0, 255] * x[3][x[3] > 0]  # 终点位置 (pink)
        cv2.imwrite(str(PATH_MAP / f"map_around{self.step}.png"), img)
        print(f"Finished saving around map images. {self.step=}")
    
    def save_obstacles(self):
        # (弃用, 无法保存) 这个 /data/projects/back_to_the_realm_v2/ckpt/ 路径为加载模型的路径 (只需要保存下来即可)
        hash_id = np.random.randint(0, 100000)
        np.save(f"/data/projects/back_to_the_realm_v2/ckpt/obstacles_{hash_id}.npy", self.obstacles)
        print(f"Finished saving obstacles to /data/projects/back_to_the_realm_v2/ckpt/obstacles_{hash_id}.npy")

class StateManager:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.n_step = 0
        self.last_action = -1
        self.curr_frame = None
        self.hit_actions = set()  # 记录当前撞墙的动作
        self.talent_max_cd = 0  # 记录闪现的最大cd
        self.terminated, self.truncated = False, False
        self.prev_frames = deque(maxlen=cfg.SEQUENCE_LENGTH)
        self.end = OrganManager('end')
        self.buff = OrganManager('buff')
        self.treasures = [OrganManager('treasure', i+1) for i in range(13)]
        self.map_manager = MapManager()
        self.buff_count = 0
        self.win_rate = 0.0  # 在agent.update_win_rate中每个epsiode结束后更新
        # FOR DEBUG
        self.total_reward = 0
        self.total_treasure_get = 0
    
    def update(
            self, frame_state: list, last_action: int,
            terminated: bool, truncated: bool
        ):
        """ 更新当前帧信息, 更新全部organ的位置信息
        Args:
            frame_state: list, 环境返回的帧状态信息, [0]: Observation, [1]: ExtraInfo
            last_action: int, 上一帧的动作
            terminated: 到达终点导致的终止
            truncated: 超时导致的终止
        """
        self.n_step += 1
        self.terminated, self.truncated = terminated, truncated
        self.last_action = last_action
        if self.curr_frame is not None:
            self.prev_frames.append(self.curr_frame)
        self.curr_frame = {
            'obs': frame_state[0],
            'extra_info': frame_state[1]
        }
        if len(self.prev_frames) == 0:
            # 第一帧就用相同的帧作为prev_frame
            self.prev_frames.append(self.curr_frame)
        hero_info, hero_pos = get_hero_info_and_pos(self.curr_frame)
        # 更新闪现最大cd
        self.talent_max_cd = max(self.talent_max_cd, hero_info['talent']['cooldown'])
        # 更新organ
        for organ in self.curr_frame['obs']['frame_state']['organs']:
            if organ['sub_type'] == 1:  # 宝箱
                id: int = organ['config_id'] - 1
                self.treasures[id].update(organ, hero_pos)
                self.map_manager.update_treasure(self.treasures[id])
            elif organ['sub_type'] == 2:  # buff
                self.buff.update(organ, hero_pos)
                self.map_manager.update_buff(self.buff)
            elif organ['sub_type'] == 4:  # 终点
                self.end.update(organ, hero_pos)
                self.map_manager.update_end(self.end)
        # 更新obstacles
        self.map_manager.update_obstacles(hero_pos, self.curr_frame['obs']['map_info'])
        # 更新hero位置
        self.map_manager.update_hero(hero_pos)
        # FOR DEBUG
        # if self.terminated or self.truncated:
        #     self.map_manager.save_obstacles()
    
    def get_reward(
            self, action_mask: np.ndarray,
            delta_distance: float, hit_wall: bool
        ) -> float:
        """ 计算reward """
        r = 0
        last_frame = self.prev_frames[-1]
        # 1. 到终点
        if self.terminated:
            # 终点奖励
            r += cfg.REW_FINISH
        if self.truncated:
            r -= cfg.REW_TRUNCATED_PUNISH
        # 2. 惩罚没有得到的宝箱
        if self.terminated or self.truncated:
            rew_miss_treasures = 0
            for treasure in self.treasures:
                if treasure.pos[0] != -1 and treasure.available:  # 遗漏的宝箱
                    rew_miss_treasures -= cfg.REW_TREASURE
            # r += rew_miss_treasures * self.win_rate  # 胜率越高, 惩罚比例越大
            r += rew_miss_treasures
        # 3. 闪现距离惩罚(官方写闪现距离为16个单位)
        use_flash = self.last_action >= 8
        if use_flash:
            r += np.clip(
                (delta_distance - 15) * cfg.REW_FLASH,
                -5.0, 0.0, dtype=np.float32
            )
        # 4. 撞墙惩罚
        if hit_wall:
            r -= cfg.REW_HIT_WALL_PUNISH
        # 5. 宝箱奖励
        treasure_get = (self.curr_frame['obs']['score_info']['treasure_collected_count'] -
            last_frame['obs']['score_info']['treasure_collected_count'])
        if treasure_get > 0:
            r += cfg.REW_TREASURE * treasure_get
        # 6. buff奖励
        if (
            self.curr_frame['obs']['score_info']['buff_count'] -
            last_frame['obs']['score_info']['buff_count'] > 0
        ):
            r += cfg.REW_BUFF * (0.5 ** self.buff_count)  # 每次buff奖励递减
            self.buff_count += 1
        # 7. 步数惩罚
        r -= cfg.REW_EACH_STEP_PUNISH
        # 8. 距离奖励
        # 优先宝箱
        min_distance, treasure_delta_distance = None, None
        for treasure in self.treasures:
            if treasure.pos[0] != -1 and treasure.available:  # 遗漏的宝箱
                if min_distance is None or treasure.real_distance < min_distance:  # 最近的宝箱
                    min_distance = treasure.real_distance
                    treasure_delta_distance = treasure.last_real_distance - treasure.real_distance
                    if not treasure.found:  # 当没找到时, 则给出限制后的距离 (-1, 1)
                        treasure_delta_distance = np.clip(treasure_delta_distance, -1.0, 1.0, dtype=np.float32)
        if treasure_delta_distance is not None:  # 如果有宝箱只考虑最近宝箱距离
            r += treasure_delta_distance * cfg.REW_DISTANCE
        if self.end.pos[0] != -1:  # 终点存在
            d = self.end.last_real_distance - self.end.real_distance
            if not self.end.found:  # 当没找到时, 则给出限制后的距离 (-1, 1)
                d = np.clip(d, -1.0, 1.0, dtype=np.float32)
            r += d * cfg.REW_DISTANCE
        # 9. 周围重复步数惩罚
        around_memory = self.map_manager.get_around_memory(cfg.REW_MEMORY_PUNISH_SIZE)
        r -= min(
            max(np.sum(around_memory) - cfg.REW_MEMORY_PUNISH_THRESHOLD, 0.0) * cfg.REW_MEMORY_PUNISH_COEF,
            1.0
        )
        # 10. 探索奖励
        r += self.map_manager.now_explore_grid * cfg.REW_EXPLORATION

        # print(f"{'='*10}[DEBUG] {self.n_step=} step_reward: {r}{'='*10}")
        # self.total_reward += r
        # self.total_treasure_get += treasure_get
        # print(f"{'='*10}[DEBUG] {self.n_step=} total_reward: {self.total_reward} total_treasure_get: {self.total_treasure_get}{'='*10}")
        # self.save_frame()
        # if self.n_step < 200:
        #     self.map_manager.save_map()
        #     self.map_manager.save_around_map(size=51)
        r *= cfg.REW_GLOBAL_SCALE
        return r
    
    def get_obs(self, action_mask) -> np.ndarray:
        """ 计算obs特征 """
        feature = []
        # 1. 英雄当前位置 (2,)
        hero_info, hero_pos = get_hero_info_and_pos(self.curr_frame)
        x = norm(hero_pos, -128, 128)
        feature.append(x)
        # 2. 闪现是否可用 (1,)
        feature.append([hero_info['talent']['status'] == 1])
        # 3. 闪现cd (1,)
        feature.append([norm(hero_info['talent']['cooldown'], 0, self.talent_max_cd)])
        # 4. buff是否存在 (1,)
        feature.append([hero_info['buff_remain_time'] > 0])
        # 5. 当前走过步数 (1,)
        feature.append([self.n_step / 1000])
        # 6. 地图特征 (4, 51, 51)
        feature.append(self.map_manager.get_around_feature(size=51).reshape(-1))  # (4, 51, 51) -> (4*51*51,)

        # FOR DEBUG
        # map = np.array([line['values'] for line in self.curr_frame['obs']['map_info']], np.float32).reshape(-1)
        # feature.append(map)

        feature = np.concatenate(feature, dtype=np.float32)
        assert feature.shape[0] == cfg.DIM_OF_OBSERVATION, f"[ERROR - StateManager] now {feature.shape=} != {cfg.FEATURE_LEN=}"
        return feature
    
    def get_action_mask(self) -> np.ndarray:
        """ 根据撞墙给出动作mask, 并根据是否有闪现对后8维进行mask """
        mask = [True] * cfg.ACTION_NUM
        self.hit_wall = False
        _, last_hero_pos = get_hero_info_and_pos(self.prev_frames[-1])
        hero_info, curr_hero_pos = get_hero_info_and_pos(self.curr_frame)
        last_move_action = self.last_action % 8  # 转为不带闪现的action
        delta_pos = np.array([last_hero_pos[0] - curr_hero_pos[0], last_hero_pos[1] - curr_hero_pos[1]], np.float32)
        delta_pos = np.abs(delta_pos)
        delta_distance = np.linalg.norm(delta_pos)
        if delta_pos[0] == 0 and delta_pos[1] == 0 and self.last_action != -1:  # 撞墙
            self.hit_wall = True
            self.hit_actions.add(last_move_action)
        else:  # 已解除撞墙, 重新记录撞墙动作
            self.hit_actions = set()
        
        for action in self.hit_actions:
            mask[action] = False
        
        if True not in mask:  # 全撞墙, 则再随机探索一次
            self.hit_actions = set()
            mask = [True] * cfg.ACTION_NUM
        
        if hero_info['talent']['status'] == 0:
            for i in range(8):
                mask[i+8] = False
        
        return mask, delta_distance, self.hit_wall
    
    def get_all(self) -> tuple[np.ndarray, np.ndarray, float]:
        """ 返回当前帧的obs, action_mask, reward """
        action_mask, delta_distance, hit_wall = self.get_action_mask()
        obs = self.get_obs(action_mask)
        reward = self.get_reward(action_mask, delta_distance, hit_wall)
        return obs, action_mask, reward
    
    def save_frame(self):
        if self.n_step < 500:
            save_json(self.curr_frame, PATH_FRAMES / f"frame{self.n_step}.json")
            simplify_iter(self.curr_frame,  PATH_FRAMES / f"frame{self.n_step}_simplify.json")
            too_simplify_iter(self.curr_frame,  PATH_FRAMES / f"frame{self.n_step}_too_simplify.json")
