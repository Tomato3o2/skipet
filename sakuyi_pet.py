# -*- coding: utf-8 -*-
"""
小狐狸桌宠 v4（sakuyi 分层版）
图层来源：你导出的 PSD 分层 PNG（1140x881 全画布，含剪切蒙版结果）

功能
  · 无边框 / 置顶 / 背景透明，透明区域不挡鼠标
  · 弹簧缓动平滑跟随鼠标（不瞬移）
  · 左右耳朵独立小幅度摇晃（相位错开更自然）
  · 眼珠随鼠标左右移动
  · 待机时自动眨眼（用你画的 0004s 闭眼图层，交叉淡入淡出）
  · 尾巴小幅度摇晃（尾巴+红色纹路剪切蒙版已合并为一层）
  · 打字 / 点击鼠标 → 头顶左上冒出番茄（你画的弹出番茄图层），
    从头发后面升起 + 透明度渐入，停留后渐隐，固定番茄不受影响

依赖：pip install PyQt5
运行：python sakuyi_pet.py
退出：右键菜单 -> 退出，或 Esc
"""

import sys
import math
import json
import os
import random

# ---------- 启动保护：缺依赖时弹窗提示并写错误报告，而不是一闪而过 ----------
def _fatal(msg):
    try:
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) \
            else os.path.dirname(os.path.abspath(__file__))
        report = os.path.join(exe_dir, "启动错误报告.txt")
        with open(report, "w", encoding="utf-8") as f:
            f.write(msg)
    except Exception:
        pass
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,
            "启动失败！\n\n详细原因已写入同目录的「启动错误报告.txt」\n请把这个文件的内容发给 AI 助手即可定位问题。\n\n" + msg[:600],
            "小狐狸桌宠", 0x10)
    print(msg)
    sys.exit(1)

try:
    from PyQt5.QtCore import Qt, QTimer, QPointF, QElapsedTimer
    from PyQt5.QtGui import QPixmap, QPainter, QCursor, QRegion, QBitmap, QImage, QColor
    from PyQt5.QtCore import QRectF
    from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction
except Exception:
    import traceback
    _fatal("启动失败！\n\n最常见原因：没安装 PyQt5，请在 cmd 执行：\n    pip install PyQt5\n\n若提示 pip 不是内部命令，说明 Python 没装好或安装时没勾选 Add Python to PATH。\n\n完整报错：\n" + traceback.format_exc())

if getattr(sys, "frozen", False):          # PyInstaller 打包后的 exe
    BASE_DIR = sys._MEIPASS                 # 资源解包临时目录
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets5")

# ================== 可调参数 ==================
PET_HEIGHT    = 280      # 角色显示高度
STIFFNESS     = 0.012    # 跟随弹簧刚度
DAMPING       = 0.86     # 跟随阻尼
EAR_AMPL_L    = 1.2      # 垂耳（画面左侧那只）摆动幅度（度）
EAR_AMPL_R    = 1.0      # 立耳（画面右侧那只）摆动幅度（度）
EAR_PERIOD    = 1.6      # 耳朵摆动周期（秒）
TAIL_AMPL     = 2.2      # 尾巴摆动幅度（度，尾根藏在身体下，只需尾尖轻晃）
TAIL_PERIOD   = 2.2      # 尾巴摆动周期（秒）
GAZE_MAX      = 5.0      # 左眼水平跟随最大偏移
GAZE_CHAR_R_FACTOR = 0.45  # 角色右眼（画面左侧）偏移比例，限幅防移出脸外
GAZE_IDLE_SEC = 3.0      # 鼠标停止移动多久后切换到半睁眼
TYPING_WINDOW = 2.0      # 停止按键多久后算"打字结束"（进入普通待机）
RAND_EYE_MIN  = 1.2      # 打字时眼睛随机切换的最短间隔（秒）
RAND_EYE_MAX  = 3.2      # 打字时眼睛随机切换的最长间隔（秒）
BLINK_CLOSE   = 0.09     # 闭眼用时（秒）
BLINK_HOLD    = 0.07     # 闭眼保持（秒）
POP_LIFE      = 2.2      # 番茄存活时间（秒）
POP_RISE      = 42.0     # 番茄升起距离（px，显示分辨率）
POP_MAX       = 6        # 同屏最多番茄数
FPS_MS        = 8        # ≈120fps
FOLLOW_OFFSET_Y = 30
# =============================================


# ---------------- 全局输入监听（键盘+鼠标） ----------------
class InputWatcher:
    """轮询系统全局按键/鼠标（Windows 原生 API，无需装库）。
    返回本帧"刚触发"的事件：'key:名字' 或 'click'。"""
    NAME = {
        0x08: "⌫", 0x09: "Tab", 0x0D: "↵", 0x1B: "Esc", 0x20: "Space",
        0x21: "PgUp", 0x22: "PgDn", 0x23: "End", 0x24: "Home",
        0x25: "←", 0x26: "↑", 0x27: "→", 0x28: "↓", 0x2E: "Del",
        0x30: "0", 0x31: "1", 0x32: "2", 0x33: "3", 0x34: "4",
        0x35: "5", 0x36: "6", 0x37: "7", 0x38: "8", 0x39: "9",
        0xBA: ";", 0xBB: "=", 0xBC: ",", 0xBD: "-", 0xBE: ".", 0xBF: "/",
        0xC0: "`", 0xDB: "[", 0xDC: "\\", 0xDD: "]", 0xDE: "'",
    }

    def __init__(self):
        self.prev = set()
        self.ok = False
        if sys.platform == "win32":
            import ctypes
            self.user32 = ctypes.windll.user32
            self.ok = True
        else:
            print("提示：非 Windows 系统暂无全局输入监听，番茄冒出功能停用（其余正常）")

    def poll(self):
        if not self.ok:
            return []
        events = []
        cur = set()
        # 鼠标左/右键
        for vk, ev in ((0x01, "click"), (0x02, "click")):
            if self.user32.GetAsyncKeyState(vk) & 0x8000:
                cur.add(vk)
                if vk not in self.prev:
                    events.append(ev)
        # 键盘
        for vk in range(0x08, 0x5B):
            if self.user32.GetAsyncKeyState(vk) & 0x8000:
                cur.add(vk)
                if vk not in self.prev:
                    name = self.NAME.get(vk) or (
                        chr(vk + 32) if 0x41 <= vk <= 0x5A else None)
                    if name:
                        events.append("key:" + name)
        self.prev = cur
        return events


class SakuyiPet(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
            Qt.Tool | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Sakuyi Pet")

        meta = json.load(open(os.path.join(ASSETS, "meta.json")))
        self.meta = meta
        cw, ch = meta["canvas"]

        # ---------- 缩放 ----------
        s = PET_HEIGHT / ch
        self.s = s
        self.win_w = round(cw * s)
        self.win_h = round(ch * s)
        self.setFixedSize(self.win_w, self.win_h)

        def sp(name):
            pm = QPixmap(os.path.join(ASSETS, name + ".png"))
            pm = pm.scaledToHeight(max(1, round(pm.height() * s)), Qt.SmoothTransformation)
            return pm

        self.base_color = sp("base_color")   # 白色剪影底色
        self.body   = sp("body")             # 身体+脸部+衣服
        self.hair   = sp("hair")
        self.glints = sp("glints")
        self.eye_open_l  = sp("eye_open_l")    # 睁开-左眼
        self.eye_open_r  = sp("eye_open_r")    # 睁开-右眼
        self.eye_half_l  = sp("eye_half_l")    # 半睁-左眼
        self.eye_half_r  = sp("eye_half_r")    # 半睁-右眼
        self.eye_closed  = sp("eye_closed")    # 眨眼眼皮
        self.tail_full   = sp("tail_full")    # 完整尾巴垫底层（防透缝）
        self.tail_ball   = sp("tail_ball")    # 尾巴摆动球体（带红纹）
        self.tomato_fixed = sp("tomato_fixed")
        self.tomato = sp("tomato_pop")
        self.ears = {n: sp(n) for n in ("ear_left", "ear_right")}

        def off(key):
            b = meta[key]
            return QPointF(b[0] * s, b[1] * s)
        self.off_base = off("base_color")
        self.off_body = off("body")
        self.off_hair, self.off_glints = off("hair"), off("glints")
        self.off_eye = {k: off(k) for k in
                        ("eye_open_l", "eye_open_r", "eye_half_l", "eye_half_r", "eye_closed")}
        self.off_tail_f, self.off_tail_b = off("tail_full"), off("tail_ball")
        self.off_tomato = off("tomato_pop")
        self.off_tomato_fixed = off("tomato_fixed")
        self.tail_pivot = QPointF(meta["tail_pivot"][0] * s, meta["tail_pivot"][1] * s)
        self.ears_pivot = {}
        for n in ("ear_left", "ear_right"):
            b = meta[n]["bbox"]; pv = meta[n]["pivot"]
            self.ears_pivot[n] = (QPointF(pv[0] * s, pv[1] * s),
                                  QPointF(b[0] * s, b[1] * s))

        # ---------- 静态点击穿透区域（角色剪影） ----------
        self._build_mask()

        # ---------- 状态 ----------
        cursor = QCursor.pos()
        self.target = self._target_for(cursor)
        self.pos_f = QPointF(self.target)
        self.velocity = QPointF(0, 0)
        self.gaze_x = 0.0
        self.open_a = 1.0              # 1=完全睁开 0=半睁（鼠标停止移动时切半睁）
        self.last_mouse = None         # 上帧鼠标位置（检测是否在动）
        self.last_move_time = -10.0    # 最近一次鼠标移动的时刻
        self.last_key_time = -10.0     # 最近一次按键/点击的时刻
        self.rand_eye_state = 0.0      # 打字时随机眼状态（0=半睁 1=睁开）
        self.rand_eye_next = 0.0       # 下次随机切换的时刻
        self.follow = False             # 默认固定位置；右键菜单可开启跟随

        self.clock = QElapsedTimer(); self.clock.start()
        self.elapsed = 0.0
        self.next_blink = 1.5 + random.random() * 2.5
        self.blink_t = -1.0            # 眨眼进行中的进度时刻，-1 表示未在眨眼
        self.pops = []                 # [{'t0': 冒出时刻, 'dx': 水平抖动}]
        self.last_pop = -1.0

        self.inputs = InputWatcher()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(FPS_MS)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)

    # ---------- 点击区域：用矩形近似（位图 mask 与半透明窗口在部分
    # Windows + Qt 组合下冲突，会导致窗口变白色不透明板） ----------
    def _build_mask(self):
        try:
            s = self.s
            region = QRegion()
            for key in ("base_color", "body", "tail_ball", "tomato_fixed"):
                b = self.meta[key]
                x = round(b[0] * s) - 4
                y = round(b[1] * s) - 4
                w = round((b[2] - b[0]) * s) + 8
                h = round((b[3] - b[1]) * s) + 8
                region |= QRegion(x, y, w, h)
            # 冒出番茄的活动区域（升起距离 + 水平抖动余量），否则会被窗口裁掉
            tb = self.meta["tomato_pop"]
            px = round(tb[0] * s) - 30
            py = round(tb[1] * s) - round(POP_RISE) - 30
            pw = round((tb[2] - tb[0]) * s) + 60
            ph = round((tb[3] - tb[1]) * s) + round(POP_RISE) + 60
            region |= QRegion(px, py, pw, ph)
            self.setMask(region)
        except Exception:
            pass                        # mask 失败也不影响显示

    def _target_for(self, cursor):
        return QPointF(cursor.x() - self.win_w / 2,
                       cursor.y() - self.win_h * 0.62 + FOLLOW_OFFSET_Y)

    # ---------- 主循环 ----------
    def tick(self):
        dt = min(max(self.clock.elapsed() / 1000.0, 0.001), 0.05)
        self.clock.restart()
        self.elapsed += dt

        # —— 输入 → 冒番茄 ——
        for ev in self.inputs.poll():
            if ev.startswith("key:") or ev == "click":
                self.last_key_time = self.elapsed
            if self.elapsed - self.last_pop > 0.08 and len(self.pops) < POP_MAX:
                self.pops.append({"t0": self.elapsed,
                                  "dx": random.uniform(-14, 14)})
                self.last_pop = self.elapsed
        self.pops = [p for p in self.pops
                     if self.elapsed - p["t0"] < POP_LIFE]

        # —— 眨眼调度 ——
        if self.blink_t < 0 and self.elapsed >= self.next_blink:
            self.blink_t = 0.0
        if self.blink_t >= 0:
            self.blink_t += dt
            total = BLINK_CLOSE * 2 + BLINK_HOLD
            if self.blink_t >= total:
                self.blink_t = -1.0
                self.next_blink = self.elapsed + 2.0 + random.random() * 3.5

        # —— 弹簧跟随 ——
        mouse = QCursor.pos()
        if self.follow:
            self.target = self._target_for(mouse)
        k = dt / 0.016
        self.velocity += QPointF((self.target.x() - self.pos_f.x()) * STIFFNESS * k,
                                 (self.target.y() - self.pos_f.y()) * STIFFNESS * k)
        self.velocity *= DAMPING ** k
        self.pos_f += self.velocity
        if (math.hypot(self.target.x() - self.pos_f.x(),
                       self.target.y() - self.pos_f.y()) < 1.0 and
                math.hypot(self.velocity.x(), self.velocity.y()) < 0.1):
            self.pos_f = QPointF(self.target)
            self.velocity = QPointF(0, 0)
        self.move(round(self.pos_f.x()), round(self.pos_f.y()))

        # —— 眼珠水平跟随（只左右移动）+ 鼠标静止切半睁 ——
        dx = mouse.x() - (self.pos_f.x() + self.win_w / 2)
        gx = max(-GAZE_MAX, min(GAZE_MAX, dx / 260.0 * GAZE_MAX))
        self.gaze_x += (gx - self.gaze_x) * min(1.0, 10.0 * dt)

        if self.last_mouse is not None and \
                (abs(mouse.x() - self.last_mouse.x()) > 1 or
                 abs(mouse.y() - self.last_mouse.y()) > 1):
            self.last_move_time = self.elapsed
        self.last_mouse = QPointF(mouse)
        mouse_active = self.elapsed - self.last_move_time < GAZE_IDLE_SEC
        typing = self.elapsed - self.last_key_time < TYPING_WINDOW
        if mouse_active:
            target_open = 1.0                       # 鼠标在动 → 完全睁开
        elif typing:
            # 打字中 → 随机在睁开/半睁之间切换（间隔 RAND_EYE_MIN~MAX 秒）
            if self.elapsed >= self.rand_eye_next:
                self.rand_eye_state = random.choice((0.0, 1.0))
                self.rand_eye_next = self.elapsed + random.uniform(RAND_EYE_MIN, RAND_EYE_MAX)
            target_open = self.rand_eye_state
        else:
            target_open = 0.0                       # 无输入 → 待机半睁
        self.open_a += (target_open - self.open_a) * min(1.0, 6.0 * dt)

        self.update()

    # ---------- 绘制 ----------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.setRenderHint(QPainter.Antialiasing)
        e = self.elapsed
        R = lambda v: round(v)          # PyQt5 的 drawPixmap 只接受整数坐标

        bob = math.sin(e * 2.2) * 2.5       # 呼吸浮动

        p.setOpacity(1.0)
        p.drawPixmap(R(self.off_base.x()), R(self.off_base.y() + bob), self.base_color)  # 剪影底色

        # 完整尾巴垫底（不透明）：球体转走的部分露出原尾巴，杜绝半透明浅色缝
        p.drawPixmap(R(self.off_tail_f.x()), R(self.off_tail_f.y() + bob), self.tail_full)

        # 尾巴摆动球体（带红纹的部分，在垫底层之上、身体之下）
        ang = TAIL_AMPL * math.sin(e * 2 * math.pi / TAIL_PERIOD)
        p.save()
        p.translate(self.tail_pivot.x(), self.tail_pivot.y() + bob)
        p.rotate(ang)
        p.drawPixmap(R(self.off_tail_b.x() - self.tail_pivot.x()),
                     R(self.off_tail_b.y() - self.tail_pivot.y()), self.tail_ball)
        p.restore()

        # 身体+脸部+衣服（盖住尾根）
        p.drawPixmap(R(self.off_body.x()), R(self.off_body.y() + bob), self.body)

        # 耳朵（左右相位错开，各自幅度；画在头发之下）
        for n, ph, ampl in (("ear_left", 0.0, EAR_AMPL_L), ("ear_right", 0.9, EAR_AMPL_R)):
            ang = ampl * math.sin(e * 2 * math.pi / EAR_PERIOD + ph)
            pv, ob = self.ears_pivot[n]
            p.save()
            p.translate(pv.x(), pv.y() + bob)
            p.rotate(ang)
            p.drawPixmap(R(ob.x() - pv.x()), R(ob.y() - pv.y()), self.ears[n])
            p.restore()

        # 眼睛三态：睁开↔半睁（鼠标静止切换）+ 眨眼眼皮交叉淡化
        # 左眼跟随幅度大、右眼限幅（GAZE_R_FACTOR）
        ph_blink = self._blink_phase()
        vis = 1.0 - ph_blink                    # 睁/半睁的可见度
        if vis > 0.01:
            oa = self.open_a                    # 1=睁开 0=半睁
            gx_l = self.gaze_x * GAZE_CHAR_R_FACTOR   # 画面左 = 角色右眼（限幅）
            gx_r = self.gaze_x * GAZE_CHAR_R_FACTOR   # 画面右 = 角色左眼（恢复上一版限幅幅度）
            if oa > 0.01:                       # 睁开层
                p.setOpacity(vis * oa)
                p.drawPixmap(R(self.off_eye["eye_open_l"].x() + gx_l),
                             R(self.off_eye["eye_open_l"].y() + bob), self.eye_open_l)
                p.drawPixmap(R(self.off_eye["eye_open_r"].x() + gx_r),
                             R(self.off_eye["eye_open_r"].y() + bob), self.eye_open_r)
            if oa < 0.99:                       # 半睁层
                p.setOpacity(vis * (1.0 - oa))
                p.drawPixmap(R(self.off_eye["eye_half_l"].x() + gx_l),
                             R(self.off_eye["eye_half_l"].y() + bob), self.eye_half_l)
                p.drawPixmap(R(self.off_eye["eye_half_r"].x() + gx_r),
                             R(self.off_eye["eye_half_r"].y() + bob), self.eye_half_r)
        if ph_blink > 0.01:                     # 眨眼眼皮（盖在最上）
            p.setOpacity(ph_blink)
            p.drawPixmap(R(self.off_eye["eye_closed"].x()),
                         R(self.off_eye["eye_closed"].y() + bob), self.eye_closed)
        p.setOpacity(1.0)

        # 冒出的番茄（从头发后面升起，渐入渐出）
        for pop in self.pops:
            age = e - pop["t0"]
            prog = age / POP_LIFE
            alpha = min(1.0, age / 0.30)                     # 前0.3s渐入
            if prog > 0.75:                                  # 后段渐出
                alpha = min(alpha, max(0.0, (1.0 - prog) / 0.25))
            rise = POP_RISE * (1.0 - min(1.0, age / 0.45)) ** 1.5
            scale = 0.85 + 0.15 * min(1.0, age / 0.30)       # 轻微放大冒出
            cx = self.off_tomato.x() + self.tomato.width() / 2 + pop["dx"]
            cy = self.off_tomato.y() + rise + bob
            p.setOpacity(alpha)
            p.save()
            p.translate(cx, cy + self.tomato.height() / 2)
            p.scale(scale, scale)
            p.drawPixmap(R(-self.tomato.width() / 2), R(-self.tomato.height() / 2), self.tomato)
            p.restore()
        p.setOpacity(1.0)

        # 头发（盖在耳朵、眼睛、冒出番茄之上 —— 剪切蒙版层级）
        p.drawPixmap(R(self.off_hair.x()), R(self.off_hair.y() + bob), self.hair)
        p.drawPixmap(R(self.off_glints.x()), R(self.off_glints.y() + bob), self.glints)

        # 固定番茄（在尾巴前面 —— 最顶层）
        p.drawPixmap(R(self.off_tomato_fixed.x()), R(self.off_tomato_fixed.y() + bob),
                     self.tomato_fixed)
        p.end()

    def _blink_phase(self):
        """0=全开 1=全闭，闭-停-开 的平滑过渡"""
        if self.blink_t < 0:
            return 0.0
        t = self.blink_t
        if t < BLINK_CLOSE:
            return t / BLINK_CLOSE
        if t < BLINK_CLOSE + BLINK_HOLD:
            return 1.0
        return max(0.0, 1.0 - (t - BLINK_CLOSE - BLINK_HOLD) / BLINK_CLOSE)

    # ---------- 交互 ----------
    def show_menu(self, pos):
        menu = QMenu(self)
        act_follow = QAction("暂停跟随" if self.follow else "开始跟随", self)

        def _toggle():
            self.follow = not self.follow
            act_follow.setText("暂停跟随" if self.follow else "开始跟随")

        act_follow.triggered.connect(_toggle)
        act_quit = QAction("退出", self)
        act_quit.triggered.connect(QApplication.quit)
        menu.addAction(act_follow)
        menu.addSeparator()
        menu.addAction(act_quit)
        menu.exec_(self.mapToGlobal(pos))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            QApplication.quit()


def main():
    try:
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        pet = SakuyiPet()
        scr = app.primaryScreen().availableGeometry()
        pet.move(scr.center().x() - pet.width() // 2, scr.center().y() - pet.height() // 2)
        pet.pos_f = QPointF(pet.pos())
        pet.target = QPointF(pet.pos())
        pet.show()
        print("小狐狸 v4 已上线：打字/点击鼠标会冒番茄！右键/Esc 退出。")
        sys.exit(app.exec_())
    except SystemExit:
        raise
    except Exception:
        import traceback
        _fatal(traceback.format_exc())


if __name__ == "__main__":
    main()
