# -*- coding: utf-8 -*-
"""从 sakuyi 图层生成桌宠素材 v5.1
- 固定番茄独立图层（在尾巴之上）
- 眼睛三态：0003s 睁开 / 0005s 半睁 / 0004s 闭眼（眨眼用）
- 睁开与半睁组按左右眼拆分（右眼单独限幅）
输出 assets5/
"""
from PIL import Image
import numpy as np
from scipy import ndimage
import json, glob, os, re

os.makedirs('assets5', exist_ok=True)
L = {}
for f in glob.glob('src_layers/*未命名作品_*.png'):
    m = re.search(r'未命名作品_(.+)\.png$', f)
    L[m.group(1)] = Image.open(f).convert('RGBA')
print("读取图层:", len(L))
W, H = 1140, 881

def merge(keys):
    c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for k in keys:
        c.alpha_composite(L[k])
    return c

def crop_save(img, name):
    a = np.array(img)[:, :, 3]
    ys, xs = np.where(a > 8)
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    img.crop((x0, y0, x1, y1)).save(f'assets5/{name}.png')
    return [x0, y0, x1, y1]

meta = {}

meta['base_color'] = crop_save(merge(['0006_底色']), 'base_color')
meta['body']       = crop_save(merge(['0005_身体', '0004_脸部', '0003_衣服']), 'body')
meta['hair']       = crop_save(merge(['0001s_0001_头发-', '0001s_0000_图层-18']), 'hair')
meta['glints']     = crop_save(merge(['0000_高光']), 'glints')
meta['tomato_fixed'] = crop_save(merge(['0002_番茄-固定部分']), 'tomato_fixed')
meta['eye_closed'] = crop_save(merge(['0004s_0000_眉毛']), 'eye_closed')

# ---------- 眼睛：睁开(0003s) / 半睁(0005s)，各拆左右 ----------
def split_eyes(keys, base_name):
    full = merge(keys)
    arr = np.array(full)
    alpha = arr[..., 3]
    cols = (alpha > 8).sum(axis=0)
    xs = np.where(cols > 0)[0]
    x0, x1 = int(xs.min()), int(xs.max())
    lo, hi = x0 + (x1 - x0) // 3, x1 - (x1 - x0) // 3
    gap = lo + int(np.argmin(cols[lo:hi]))
    print(f"{base_name}: x {x0}-{x1} 分割线 {gap}")
    for side, (a, b) in (('l', (x0 - 2, gap)), ('r', (gap + 1, x1 + 3))):
        seg = arr[:, a:b].copy()
        sa = seg[..., 3]
        ys2, xs2 = np.where(sa > 8)
        bx0, by0 = int(a + xs2.min()), int(ys2.min())      # 绝对坐标（存 meta）
        bx1, by1 = int(a + xs2.max()) + 1, int(ys2.max()) + 1
        # seg 是 x∈[a,b) 的切片，裁剪必须用段内相对坐标
        Image.fromarray(seg).crop((bx0 - a, by0, bx1 - a, by1)).save(f'assets5/{base_name}_{side}.png')
        meta[f'{base_name}_{side}'] = [bx0, by0, bx1, by1]

split_eyes(['0005s_0000_眉毛', '0005s_0001_眼珠'], 'eye_open')   # 睁开（运动时）
split_eyes(['0003s_0000_眉毛', '0003s_0001_眼珠'], 'eye_half')   # 半睁（待机时）

# ---------- 尾巴：合并尾巴基体+红色纹路，羽化拆分为 静止根 + 摆动球 ----------
tail_full = merge(['0000s_0001_尾巴', '0000s_0000_图层-13'])
FADE_L, FADE_R = 632, 648          # 交叉淡化带（x 坐标），两组 alpha 严格互补
arr_t = np.array(tail_full).copy()
xs_grid = np.arange(W, dtype=np.float32)
a_static = np.clip((FADE_R - xs_grid) / (FADE_R - FADE_L), 0, 1)   # 左 1 → 右 0
a_ball   = 1.0 - a_static                                          # 左 0 → 右 1，和恒为 1
ts = arr_t.copy(); ts[..., 3] = (arr_t[..., 3] * a_static[None, :]).astype(np.uint8)
tb_ = arr_t.copy(); tb_[..., 3] = (arr_t[..., 3] * a_ball[None, :]).astype(np.uint8)
meta['tail_full'] = crop_save(tail_full, 'tail_full')      # 完整尾巴（垫底层，防透缝）
meta['tail_static'] = crop_save(Image.fromarray(ts), 'tail_static')
meta['tail_ball']   = crop_save(Image.fromarray(tb_), 'tail_ball')
meta['tail_pivot'] = [650, 715]    # 转轴在羽化带中（尾根处）

# ---------- 耳朵：合并耳朵+耳内，按连通域拆左右 ----------
ears = merge(['0002s_0000_耳朵', '0002s_0001_耳内'])
a = np.array(ears)[:, :, 3]
lbl, n = ndimage.label(a > 8)
sizes = ndimage.sum(a > 8, lbl, range(1, n + 1))
big = [i + 1 for i in range(n) if sizes[i] > 1500]
comps = []
for li in big:
    ys, xs = np.where(lbl == li)
    comps.append((xs.mean(), li))
comps.sort()
for (cx, li), name in zip(comps, ['ear_left', 'ear_right']):
    m = (lbl == li)
    ys_e, xs_e = np.where(m)
    ytop, ybot = int(ys_e.min()), int(ys_e.max())
    band = ys_e > ybot - (ybot - ytop) * 0.2
    px = float(xs_e[band].mean()); py = float(ybot)
    spr = np.array(ears).copy()
    spr[..., 3] = (a * m).astype(np.uint8)
    im = Image.fromarray(spr)
    bx0, by0 = int(xs_e.min()) - 4, ytop - 4
    bx1, by1 = int(xs_e.max()) + 5, ybot + 5
    im.crop((bx0, by0, bx1, by1)).save(f'assets5/{name}.png')
    meta[name] = {'bbox': [bx0, by0, bx1, by1],
                  'pivot': [round(px - bx0, 1), round(py - by0, 1)]}
    print(name, meta[name])

meta['tomato_pop'] = crop_save(merge(['0001_番茄-弹出部分']), 'tomato_pop')
meta['canvas'] = [W, H]
json.dump(meta, open('assets5/meta.json', 'w'), indent=1)
print("素材已导出")

# ---------- 剪影 mask（仅备档，程序改用矩形区域） ----------
mask = Image.new('L', (W, H), 0)
for name in ['base_color', 'body', 'hair', 'glints', 'tail_full', 'tail_static', 'tail_ball', 'tomato_fixed', 'eye_closed']:
    bbox = meta[name]
    la = np.array(Image.open(f'assets5/{name}.png').convert('RGBA'))[:, :, 3]
    base = np.array(mask)
    region = base[bbox[1]:bbox[3], bbox[0]:bbox[2]]
    np.maximum(region, la, out=region)
    mask = Image.fromarray(base)
arr = np.array(mask)
tb = meta['tomato_pop']
arr[tb[1]:tb[3], tb[0]:tb[2]] = 255
mask = Image.fromarray(arr).point(lambda v: 255 if v > 60 else 0).convert('1')
mask.save('assets5/mask.png')
print("mask.png 已生成")
