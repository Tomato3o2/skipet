# 小狐狸桌宠 v5（sakuyi 分层版）

## 怎么给别人用：两种方式

### 方式一：exe 单文件（推荐——对方什么都不用装）

exe 会自动包含 Python 运行环境和全部素材，别人下载后**双击就能跑**。

exe 必须在 Windows 上生成，推荐用 GitHub 免费服务器自动打包：

1. 注册/登录 [github.com](https://github.com) → 右上角 **+** → **New repository** 新建仓库（Public）
2. 仓库页 **Add file → Upload files**，把本项目所有文件拖上去上传（`.github` 开头的隐藏文件夹网页传不了，可跳过，见下方替代办法）
3. 替代办法（推荐，能传上 `.github`）：下载 GitHub Desktop，或用命令：
   ```bash
   git init
   git add .
   git commit -m "小狐狸桌宠"
   git remote add origin https://github.com/你的用户名/仓库名.git
   git push -u origin main
   ```
4. 仓库页顶部 **Actions** 标签 → 左侧选 **Build Windows EXE** → 右侧 **Run workflow** → 点绿色按钮
5. 等约 3~5 分钟 → 进这次运行详情 → 底部 **Artifacts** 下载 `sakuyi_pet-exe`，解压得 `sakuyi_pet.exe`
6. 把这一个 exe 发给任何人即可（微信/网盘/Release 都行）
7. （进阶）推送标签 `git tag v1.0 && git push origin v1.0` 会自动发布到 **Releases**，别人无需登录 GitHub 就能直接下载

> 若 Actions 报错找不到 workflow，多半是 `.github` 文件夹没传上去，用第 3 步的 git 方式重传即可。

### 方式二：源码运行（需要对方装 Python）

1. 把 `sakuyi_pet_v5.zip` 解压到一个文件夹（不要在压缩包里直接双击）
2. 装一次依赖：`pip install PyQt5`
3. 双击 **`启动宠物.bat`**（或 cmd 里 `python sakuyi_pet.py`）

### 自己电脑上手动打包 exe（可选）

在任意 Windows 电脑的项目目录里：

```bash
pip install PyQt5 pyinstaller
pyinstaller pet.spec
```

产物在 `dist/sakuyi_pet.exe`（约 40MB 单文件）。

## 操作说明

- 无边框 / 置顶 / 背景透明，透明区域不挡鼠标
- **默认固定在屏幕中央**；右键菜单「开始跟随鼠标」开启跟随，再点一次暂停
- 右键菜单：开始/暂停跟随、退出；Esc 退出
- 全局监听键盘鼠标（Windows 自带 API，免装库）：**打字 / 点击鼠标 → 左上冒出番茄**（从头发后面升起、渐入渐出），固定番茄不受影响

## 动画行为

- 左右耳朵小幅度摇晃（垂耳 1.2°、立耳 1.0°，藏在头发下）
- 眼珠随鼠标左右移动（双眼均限幅，角色右眼稍小，不会移出脸外）
- 鼠标移动时完全睁开；停止约 3 秒后切回半睁眼待机
- 打字时眼睛随机在睁开/半睁之间切换（间隔 1.2~3.2 秒随机）
- 随机自动眨眼（眼皮交叉淡化）
- 尾巴只有带红纹的球体部分轻晃（球体下垫完整不透明尾巴，无透缝浅线，尾根贴身不动）

## 绘制顺序（从下到上）

```
尾巴(+红色纹路，最底层) → 底色剪影 → 身体+脸部+衣服 → 耳朵 → 眼睛(睁开/半睁/眨眼三态) → 弹出番茄 → 头发+图层18 → 高光 → 固定番茄（最顶层，在尾巴前面）
```

## 文件说明

| 文件 | 作用 |
|---|---|
| `sakuyi_pet.py` | 主程序（已支持 PyInstaller 打包） |
| `pet.spec` | 打包配置（PyInstaller 用） |
| `.github/workflows/build-windows.yml` | GitHub 自动打包 exe 的流水线 |
| `启动宠物.bat` | 双击启动源码版（出错时窗口不消失） |
| `assets5/` | 拆好的图层素材 + meta.json + mask.png |
| `prepare_assets_v5.py` | 拆层脚本（换新图时改 src_layers 重跑） |
| `src_layers/` | 原始 18 张图层（备档） |

## 可调参数（sakuyi_pet.py 顶部）

`PET_HEIGHT` 显示大小、`FOLLOW_OFFSET_Y` 跟随高度、`EAR_AMPL_L/EAR_AMPL_R` 耳朵摆动、`TAIL_AMPL/TAIL_PERIOD` 尾巴摆动、
`GAZE_MAX` 眼神幅度、`GAZE_CHAR_R_FACTOR` 角色右眼限幅比例、`GAZE_IDLE_SEC` 待机切换延时、
`TYPING_WINDOW` 打字判定窗口、`RAND_EYE_MIN/RAND_EYE_MAX` 打字随机眼间隔、`POP_LIFE` 番茄存活时间、`STIFFNESS/DAMPING` 跟随手感。

## 启动失败排查

- exe 双击没反应/报错：程序会在 exe 旁边生成「启动错误报告.txt」，把内容发给 AI 助手即可
- 源码方式报 `No module named PyQt5`：执行 `pip install PyQt5`
- 源码方式报 `python 不是内部或外部命令`：Python 没装好或没勾选 Add to PATH
