"""ノードハンドル — 描いた要素を線の端点として指せるようにする。

`c.node(...)` や `c.sticky(...)` は Node を返す。あとは

    a = c.node(140, 160, "ブラウザ", emoji_cp="1f310")
    b = c.sticky(600, 120, 200, 90, color="blue")
    c.link(a, b, label="送る")

と書けば、どの辺から出てどこで止めるかは Node が知っている。
"""

import math

from .geom import EPS, Ellipse, Poly, Rect, norm, pts_rect, pts_round_rect, sub
from .text import font_size
from .tokens import ASCENT, DESCENT, INK_TOP, gap_value

# 8 方位 + 別名
COMPASS = {
    "n":  (0.0, -1.0),
    "ne": (0.70711, -0.70711),
    "e":  (1.0, 0.0),
    "se": (0.70711, 0.70711),
    "s":  (0.0, 1.0),
    "sw": (-0.70711, 0.70711),
    "w":  (-1.0, 0.0),
    "nw": (-0.70711, -0.70711),
    "north": (0.0, -1.0), "east": (1.0, 0.0),
    "south": (0.0, 1.0), "west": (-1.0, 0.0),
    "top": (0.0, -1.0), "right": (1.0, 0.0),
    "bottom": (0.0, 1.0), "left": (-1.0, 0.0),
}

AUTO = (None, "", "c", "center", "auto")


class Node:
    """描画済み要素のハンドル。

    - `shape_outline` … 図形そのものの輪郭
    - `label_box`     … 図形の外にはみ出すラベルの矩形（絵文字ノードのキャプション等）
    - `visual_outline`… 図形 ∪ ラベル を囲む角丸矩形

    線をどちらで止めるかは `default_clip` が決める。図形ノードは図形の輪郭
    （ひし形の頂点に矢印が触ってほしい）、絵文字ノードは見た目全体
    （キャプションを矢印が突き抜けてほしくない）。
    """

    def __init__(self, cx, cy, w, h, outline,
                 label_box=None, color="yellow", kind="shape"):
        self.cx, self.cy = float(cx), float(cy)
        self.w, self.h = float(w), float(h)
        self.shape_outline = outline
        self.label_box = label_box
        self.color = color
        self.kind = kind                    # "shape" | "emoji" | "icon" | "point"
        self._visual = None
        self.default_clip = "shape" if kind == "shape" else "visual"

    # --- ボックス ---
    @property
    def center(self):
        return (self.cx, self.cy)

    @property
    def box(self):
        """図形そのものの外接矩形。"""
        return self.shape_outline.bbox()

    @property
    def visual_box(self):
        """図形 ∪ はみ出しラベル の外接矩形。"""
        return self.box.union(self.label_box)

    @property
    def visual_outline(self):
        if self._visual is None:
            if self.label_box is None:
                self._visual = self.shape_outline
            else:
                r = self.visual_box
                self._visual = Poly(pts_round_rect(r.x, r.y, r.w, r.h, 10.0))
        return self._visual

    def outline(self, mode=None):
        mode = mode or self.default_clip
        if mode == "none":
            return None
        if mode == "visual":
            return self.visual_outline
        if mode == "box":
            r = self.box
            return Poly(pts_rect(r.x, r.y, r.w, r.h))
        return self.shape_outline

    # 便利プロパティ（視覚ボックス基準）
    @property
    def left(self):
        return self.visual_box.x

    @property
    def top(self):
        return self.visual_box.y

    @property
    def right(self):
        return self.visual_box.right

    @property
    def bottom(self):
        return self.visual_box.bottom

    @property
    def width(self):
        return self.visual_box.w

    @property
    def height(self):
        return self.visual_box.h

    # --- アンカー ---
    def direction(self, anchor="auto", toward=None):
        """アンカー指定を「中心から外へ向かう単位ベクトル」に解決する。"""
        if isinstance(anchor, str):
            key = anchor.strip().lower()
        else:
            key = anchor
        if key in AUTO:
            if toward is None:
                return (1.0, 0.0)
            d = norm(sub(toward, self.center))
            return d if d != (0.0, 0.0) else (1.0, 0.0)
        if isinstance(key, str):
            if key not in COMPASS:
                raise ValueError(
                    f"未知のアンカー: {anchor!r}。使えるのは "
                    f"{sorted(k for k in COMPASS if len(k) <= 2)}、'auto'/'c'、"
                    f"角度（度・0=東）、(dx, dy)。")
            return COMPASS[key]
        if isinstance(anchor, (int, float)):
            a = math.radians(float(anchor))
            return (math.cos(a), math.sin(a))
        if isinstance(anchor, (tuple, list)) and len(anchor) == 2:
            d = norm((float(anchor[0]), float(anchor[1])))
            return d if d != (0.0, 0.0) else (1.0, 0.0)
        raise TypeError(f"アンカーに使えない値: {anchor!r}")

    def at(self, anchor="auto", toward=None, pad=0.0, mode=None):
        """アンカー位置（輪郭上の点）を返す。"""
        o = self.outline(mode) or self.shape_outline
        d = self.direction(anchor, toward)
        return o.ray_exit(self.center, d, pad=pad)

    def normal_at(self, p, snap=True):
        """点 p における外向き法線。snap=True で上下左右に丸める（直交ルータ用）。"""
        d = norm(sub(p, self.center))
        if d == (0.0, 0.0):
            return (1.0, 0.0)
        if not snap:
            return d
        if abs(d[0]) >= abs(d[1]):
            return (1.0 if d[0] > 0 else -1.0, 0.0)
        return (0.0, 1.0 if d[1] > 0 else -1.0)

    # --- ラベル配置 ---
    def below(self, gap="normal", scale="label"):
        """ノードの下にテキストを置くときのベースライン y。"""
        return self.bottom + gap_value(gap) + font_size(scale) * INK_TOP

    def above(self, gap="normal", scale="label"):
        """ノードの上にテキストを置くときのベースライン y。"""
        return self.top - gap_value(gap) - font_size(scale) * DESCENT

    def __repr__(self):
        r = self.visual_box
        return (f"<Node {self.kind} c=({self.cx:.0f},{self.cy:.0f}) "
                f"box=({r.x:.0f},{r.y:.0f},{r.w:.0f},{r.h:.0f})>")


class Point(Node):
    """座標そのものを端点として扱うための退化ノード。クリップはしない。"""

    def __init__(self, x, y):
        super().__init__(x, y, 0.0, 0.0,
                         Poly(pts_rect(float(x), float(y), 1e-3, 1e-3)),
                         kind="point")
        self.default_clip = "none"
        self._p = (float(x), float(y))

    @property
    def center(self):
        return self._p

    @property
    def box(self):
        return Rect(self._p[0], self._p[1], 0.0, 0.0)

    def at(self, anchor="auto", toward=None, pad=0.0, mode=None):
        return self._p

    def __repr__(self):
        return f"<Point {self._p[0]:.0f},{self._p[1]:.0f}>"


def pt(x, y):
    """座標を線の端点として渡すためのヘルパー。"""
    return Point(x, y)


def as_endpoint(obj):
    """線の端点を (Node, anchor) に正規化する。

    受け付ける形:
      - Node                    … アンカーは呼び出し側の既定
      - (Node, anchor)          … アンカーを個別指定
      - (x, y)  数値 2 つ        … 絶対座標（クリップなし）
    """
    if isinstance(obj, Node):
        return obj, None
    if isinstance(obj, (tuple, list)) and len(obj) == 2:
        a, b = obj
        if isinstance(a, Node):
            return a, b
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return Point(a, b), None
    raise TypeError(
        "線の端点は Node、(Node, アンカー)、(x, y) のいずれか。"
        f"受け取ったのは {type(obj).__name__}: {obj!r}")
