- `frame*.json`由`StateManager.save_frame()`生成, 用于调试每帧的信息, 包含三种复杂程度的格式
- `map*.png`由`MapManager.save_map()`生成, 用于调试当前记录下的地图信息
- `map_around*.png`由`MapManager.save_around_map()`生成, 用于调试当前状态输入的信息 (以hero为中心的51x51地图信息)

| 第1帧地图 | 第1帧周围信息地图 |
| - | - |
| ![map1](./map1.png) | ![map_around1](./map_around1.png) |

| 第199帧地图 | 第199帧周围信息地图 |
| - | - |
| ![map199](./map199.png) | ![map_around199](./map_around199.png) |
