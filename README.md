
## 操作说明

- 无边框 / 置顶 / 背景透明，透明区域不挡鼠标
- **默认固定在屏幕中央**；右键菜单「开始跟随鼠标」开启跟随，再点一次暂停
- 右键菜单：开始/暂停跟随、退出；Esc 退出
- 全局监听键盘鼠标（Windows 自带 API，免装库）：**打字 / 点击鼠标 → 左上冒出番茄**

## 动画行为

- 左右耳朵小幅度摇晃
- 眼珠随鼠标左右移动
- 鼠标移动时完全睁开；停止约 3 秒后切回半睁眼待机
- 打字时眼睛随机在睁开/半睁之间切换（间隔 1.2~3.2 秒随机）
- 随机自动眨眼（眼皮交叉淡化）


## 可调参数（sakuyi_pet.py 顶部）

`PET_HEIGHT` 显示大小、`FOLLOW_OFFSET_Y` 跟随高度、`EAR_AMPL_L/EAR_AMPL_R` 耳朵摆动、`TAIL_AMPL/TAIL_PERIOD` 尾巴摆动、
`GAZE_MAX` 眼神幅度、`GAZE_CHAR_R_FACTOR` 角色右眼限幅比例、`GAZE_IDLE_SEC` 待机切换延时、
`TYPING_WINDOW` 打字判定窗口、`RAND_EYE_MIN/RAND_EYE_MAX` 打字随机眼间隔、`POP_LIFE` 番茄存活时间、`STIFFNESS/DAMPING` 跟随手感。

