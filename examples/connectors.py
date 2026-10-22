"""コネクタの全パターンを 1 枚に並べる目視回帰用ギャラリー。

実行: python3 examples/connectors.py → examples/connectors.svg
確認したいこと:
  1. ラベルの位置で線が途切れる。**縦線では文字の高さぶん**開く
  2. 直線 / エルボ（角・角丸）/ カーブ
  3. 8 方位アンカーと中心アンカー
  4. 図形ごとに、線が輪郭で止まる（図形に重ならない）
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from genfig import Canvas, PALETTE  # noqa: E402

c = Canvas(1180, 1320)


def title(x, y, s):
    c.text(x, y, s, scale="lg", align="left")


def note(x, y, s):
    c.text(x, y, s, scale="sm", align="left")


# ---------------------------------------------------------------------------
# 1. ラベルで線が途切れる — 向きごとのギャップ
# ---------------------------------------------------------------------------
title(40, 46, "1. ラベルの位置で線が切れる（ギャップは線の向きへの射影で決まる）")

a1 = c.sticky(40, 80, 130, 70, color="green")
c.text(105, 122, "draw", scale="md", font="technical", fill=PALETTE["green"]["text"])
b1 = c.sticky(360, 80, 130, 70, color="blue")
c.text(425, 122, "apply", scale="md", font="technical", fill=PALETTE["blue"]["text"])
c.link(a1, b1, label="呼ぶ")
note(180, 172, "横線 → 文字の幅ぶん切れる")

a2 = c.sticky(600, 80, 130, 70, color="green")
c.text(665, 122, "draw", scale="md", font="technical", fill=PALETTE["green"]["text"])
b2 = c.sticky(600, 250, 130, 70, color="blue")
c.text(665, 292, "apply", scale="md", font="technical", fill=PALETTE["blue"]["text"])
c.link(a2, b2, label="呼ぶ", primary=False)
note(745, 190, "縦線 → 文字の「高さ」ぶん切れる")
note(745, 212, "（ここが今回の本丸）")

a3 = c.sticky(900, 80, 110, 60, color="purple")
b3 = c.sticky(1020, 250, 110, 60, color="orange")
c.link(a3, b3, label="斜め")
note(880, 340, "斜線 → 幅と高さの両方が効く")

# ---------------------------------------------------------------------------
# 2. ルートと角
# ---------------------------------------------------------------------------
title(40, 400, "2. 直線 / エルボ（角・角丸）/ カーブ")

for i, (kind, kw, cap) in enumerate([
    ("straight", {}, "route='straight'"),
    ("elbow-sharp", {"route": "elbow", "corner": "sharp"}, "route='elbow', corner='sharp'"),
    ("elbow-round", {"route": "elbow", "corner": "round"}, "route='elbow', corner='round'"),
    ("curve", {"route": "curve", "curve": -50}, "route='curve', curve=-50"),
]):
    x = 40 + i * 285
    s = c.sticky(x, 470, 100, 56, color="teal")
    c.text(x + 50, 504, "A", scale="md", fill=PALETTE["teal"]["text"])
    t = c.sticky(x + 150, 570, 100, 56, color="pink")
    c.text(x + 200, 604, "B", scale="md", fill=PALETTE["pink"]["text"])
    c.link(s, t, label="送る", label_scale="sm", **kw)
    note(x, 664, cap)

# ---------------------------------------------------------------------------
# 3. アンカー — 8 方位 + 中心
# ---------------------------------------------------------------------------
title(40, 730, "3. アンカー（8 方位と中心）")

hub = c.sticky(430, 830, 160, 90, color="yellow")
c.text(510, 882, "hub", scale="md", fill=PALETTE["yellow"]["text"])

ring = [("n", 510, 760), ("ne", 700, 780), ("e", 760, 875), ("se", 700, 970),
        ("s", 510, 1000), ("sw", 320, 970), ("w", 260, 875), ("nw", 320, 780)]
for name, tx, ty in ring:
    tgt = c.ellipse(tx, ty, 26, 22, color="gray")
    c.text(tx, ty + 6, name, scale="sm", fill=PALETTE["gray"]["text"])
    c.link(hub, tgt, start=name, primary=False)

note(40, 1035, "start='n' … 'nw' で辺を固定。相手側は 'auto'（中心へ向かう ray を輪郭で切る）")

# ---------------------------------------------------------------------------
# 4. 図形ごとのクリップ
# ---------------------------------------------------------------------------
title(40, 1090, "4. どの図形でも輪郭で止まる（図形に重なる部分は描かない）")

shapes = [
    ("ellipse", lambda x: c.ellipse(x + 60, 1200, 52, 40, color="green")),
    ("diamond", lambda x: c.diamond(x + 8, 1158, 104, 84, color="yellow")),
    ("hexagon", lambda x: c.hexagon(x + 8, 1162, 104, 76, color="purple")),
    ("cylinder", lambda x: c.cylinder(x + 12, 1158, 96, 84, color="gray")),
    ("cloud", lambda x: c.cloud(x, 1152, 120, 96, color="teal")),
]
# 対ごとに独立させる（線同士が重ならないように）
for i, (name, make) in enumerate(shapes):
    x = 60 + i * 228
    s = c.ellipse(x + 18, 1200, 18, 18, color="gray")
    n = make(x + 68)
    c.link(s, n, primary=(i % 2 == 0))
    c.text(x + 128, 1276, name, scale="sm")

out = pathlib.Path(__file__).parent / "connectors.svg"
print(c.save(out))
