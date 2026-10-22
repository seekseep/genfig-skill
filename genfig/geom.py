"""幾何モデル — 図形の輪郭と、その点列を作る関数。

当たり判定は **多角形（Poly）** と **楕円（Ellipse）** の 2 種類だけに落とす。
角丸矩形・シリンダーは円弧をサンプリングして多角形にする。

線を図形の境界で止めるために要るのは、ある点から方向 u に伸ばした半直線が
境界と交わるパラメータ列 `hits()` だけ。内側からなら最後の交点が「出口」、
外側からなら最初の交点が「入口」。クリアランスは交点をずらすだけで済むので、
輪郭のオフセット計算は要らない。

`pts_*` は **描画と当たり判定の両方**に使う点列を返す。Canvas 側で points 文字列を
組み立て直さないこと（形がずれる）。
"""

import math

EPS = 1e-9


# ---------------------------------------------------------------------------
# ベクトル小物
# ---------------------------------------------------------------------------

def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def mul(a, k):
    return (a[0] * k, a[1] * k)


def length(a):
    return math.hypot(a[0], a[1])


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def norm(a):
    d = math.hypot(a[0], a[1])
    if d < EPS:
        return (0.0, 0.0)
    return (a[0] / d, a[1] / d)


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


# ---------------------------------------------------------------------------
# 矩形
# ---------------------------------------------------------------------------

class Rect:
    __slots__ = ("x", "y", "w", "h")

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = float(x), float(y), float(w), float(h)

    @property
    def cx(self):
        return self.x + self.w / 2.0

    @property
    def cy(self):
        return self.y + self.h / 2.0

    @property
    def center(self):
        return (self.cx, self.cy)

    @property
    def right(self):
        return self.x + self.w

    @property
    def bottom(self):
        return self.y + self.h

    def union(self, o):
        if o is None:
            return self
        x0, y0 = min(self.x, o.x), min(self.y, o.y)
        x1, y1 = max(self.right, o.right), max(self.bottom, o.bottom)
        return Rect(x0, y0, x1 - x0, y1 - y0)

    def grow(self, p):
        return Rect(self.x - p, self.y - p, self.w + 2 * p, self.h + 2 * p)

    def as_tuple(self):
        return (self.x, self.y, self.w, self.h)

    def __repr__(self):
        return f"Rect({self.x:.1f},{self.y:.1f},{self.w:.1f},{self.h:.1f})"


# ---------------------------------------------------------------------------
# 輪郭
# ---------------------------------------------------------------------------

class Outline:
    """図形の当たり判定。"""

    def hits(self, o, u):
        """点 o から単位方向 u の半直線と境界の交点パラメータ t を昇順で返す。"""
        raise NotImplementedError

    def contains(self, p):
        raise NotImplementedError

    def bbox(self):
        raise NotImplementedError

    @property
    def center(self):
        return self.bbox().center

    def ray_exit(self, o, d, pad=0.0):
        """o（内側の想定）から d 方向へ境界を「出る」点。pad だけ外へ押し出す。

        最後の交点を採るので、非凸な図形（十字・星）でも外周まで抜けきる。
        """
        u = norm(d)
        if u == (0.0, 0.0):
            return o
        ts = [t for t in self.hits(o, u) if t > EPS]
        t = (ts[-1] if ts else 0.0) + pad
        return add(o, mul(u, t))

    def ray_enter(self, o, d, pad=0.0):
        """o（外側の想定）から d 方向へ進んで最初に境界へ当たる点。pad だけ手前で止める。"""
        u = norm(d)
        if u == (0.0, 0.0):
            return None
        ts = [t for t in self.hits(o, u) if t > EPS]
        if not ts:
            return None
        return add(o, mul(u, max(0.0, ts[0] - pad)))


class Poly(Outline):
    __slots__ = ("pts",)

    def __init__(self, pts):
        self.pts = [(float(x), float(y)) for x, y in pts]

    def hits(self, o, u):
        ox, oy = o
        dx, dy = u
        out = []
        n = len(self.pts)
        for i in range(n):
            ax, ay = self.pts[i]
            bx, by = self.pts[(i + 1) % n]
            ex, ey = bx - ax, by - ay
            den = dx * ey - dy * ex           # cross(u, e)
            if abs(den) < EPS:
                continue                      # 平行
            wx, wy = ax - ox, ay - oy
            t = (wx * ey - wy * ex) / den     # 半直線側: P = o + t*u
            s = (wx * dy - wy * dx) / den     # 辺側:     Q = a + s*e
            if -EPS <= s <= 1.0 + EPS:
                out.append(t)
        out.sort()
        return out

    def contains(self, p):
        x, y = p
        n = len(self.pts)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = self.pts[i]
            xj, yj = self.pts[j]
            if (yi > y) != (yj > y):
                xx = xi + (y - yi) * (xj - xi) / (yj - yi)
                if x < xx:
                    inside = not inside
            j = i
        return inside

    def bbox(self):
        xs = [p[0] for p in self.pts]
        ys = [p[1] for p in self.pts]
        return Rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    def svg_points(self):
        return " ".join(f"{x:g},{y:g}" for x, y in self.pts)


class Ellipse(Outline):
    __slots__ = ("cx", "cy", "rx", "ry")

    def __init__(self, cx, cy, rx, ry):
        self.cx, self.cy = float(cx), float(cy)
        self.rx, self.ry = max(float(rx), EPS), max(float(ry), EPS)

    def hits(self, o, u):
        # ((ox + t*ux - cx)/rx)^2 + ((oy + t*uy - cy)/ry)^2 = 1 を t について解く
        px = (o[0] - self.cx) / self.rx
        py = (o[1] - self.cy) / self.ry
        qx = u[0] / self.rx
        qy = u[1] / self.ry
        a = qx * qx + qy * qy
        if a < EPS:
            return []
        b = 2.0 * (px * qx + py * qy)
        c = px * px + py * py - 1.0
        disc = b * b - 4.0 * a * c
        if disc < 0.0:
            return []
        s = math.sqrt(disc)
        return sorted(((-b - s) / (2.0 * a), (-b + s) / (2.0 * a)))

    def contains(self, p):
        px = (p[0] - self.cx) / self.rx
        py = (p[1] - self.cy) / self.ry
        return px * px + py * py <= 1.0 + 1e-9

    def bbox(self):
        return Rect(self.cx - self.rx, self.cy - self.ry, self.rx * 2, self.ry * 2)


# ---------------------------------------------------------------------------
# 図形の点列（描画と当たり判定で共用する）
# ---------------------------------------------------------------------------

def pts_rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def pts_round_rect(x, y, w, h, rx, ry=None, seg=6):
    """角丸矩形を折れ線で近似。seg は角ごとの分割数。"""
    ry = rx if ry is None else ry
    rx = max(0.0, min(float(rx), w / 2.0))
    ry = max(0.0, min(float(ry), h / 2.0))
    if rx < EPS or ry < EPS:
        return pts_rect(x, y, w, h)
    r, b = x + w, y + h
    out = []
    # (角の中心x, 中心y, 開始角) 右上 → 右下 → 左下 → 左上
    for ccx, ccy, a0 in ((r - rx, y + ry, -90.0), (r - rx, b - ry, 0.0),
                         (x + rx, b - ry, 90.0), (x + rx, y + ry, 180.0)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90.0 * k / seg)
            out.append((ccx + rx * math.cos(a), ccy + ry * math.sin(a)))
    return out


def pts_diamond(x, y, w, h):
    cx, cy = x + w / 2.0, y + h / 2.0
    return [(cx, y), (x + w, cy), (cx, y + h), (x, cy)]


def pts_triangle(x, y, w, h, direction="up"):
    cx = x + w / 2.0
    if direction == "down":
        return [(x, y), (x + w, y), (cx, y + h)]
    return [(cx, y), (x + w, y + h), (x, y + h)]


def pts_pentagon(x, y, w, h):
    cx = x + w / 2.0
    return [(cx, y), (x + w, y + h * 0.40), (x + w * 0.82, y + h),
            (x + w * 0.18, y + h), (x, y + h * 0.40)]


def pts_hexagon(x, y, w, h):
    d = w * 0.22
    return [(x + d, y), (x + w - d, y), (x + w, y + h / 2.0),
            (x + w - d, y + h), (x + d, y + h), (x, y + h / 2.0)]


def pts_octagon(x, y, w, h):
    dx, dy = w * 0.29, h * 0.29
    return [(x + dx, y), (x + w - dx, y), (x + w, y + dy), (x + w, y + h - dy),
            (x + w - dx, y + h), (x + dx, y + h), (x, y + h - dy), (x, y + dy)]


def pts_parallelogram(x, y, w, h, skew=0.18):
    s = w * skew
    return [(x + s, y), (x + w, y), (x + w - s, y + h), (x, y + h)]


def pts_cross(x, y, w, h, arm=0.34):
    ax, ay = w * arm, h * arm
    l, r, t, b = x, x + w, y, y + h
    x1, x2 = x + (w - ax) / 2.0, x + (w + ax) / 2.0
    y1, y2 = y + (h - ay) / 2.0, y + (h + ay) / 2.0
    return [(x1, t), (x2, t), (x2, y1), (r, y1), (r, y2), (x2, y2),
            (x2, b), (x1, b), (x1, y2), (l, y2), (l, y1), (x1, y1)]


def pts_arrow(x, y, w, h, direction="right"):
    hy1, hy2 = y + h * 0.28, y + h * 0.72
    head = w * 0.40
    cy = y + h / 2.0
    if direction == "left":
        return [(x, cy), (x + head, y), (x + head, hy1), (x + w, hy1),
                (x + w, hy2), (x + head, hy2), (x + head, y + h)]
    return [(x + w, cy), (x + w - head, y), (x + w - head, hy1), (x, hy1),
            (x, hy2), (x + w - head, hy2), (x + w - head, y + h)]


def pts_chevron(x, y, w, h, notch=0.16):
    d = w * notch
    cy = y + h / 2.0
    return [(x, y), (x + w - d, y), (x + w, cy), (x + w - d, y + h),
            (x, y + h), (x + d, cy)]


def pts_star(x, y, w, h, points=5, inner=0.42):
    cx, cy = x + w / 2.0, y + h / 2.0
    rx, ry = w / 2.0, h / 2.0
    out = []
    for i in range(points * 2):
        ang = -math.pi / 2.0 + i * math.pi / points
        f = 1.0 if i % 2 == 0 else inner
        out.append((cx + rx * f * math.cos(ang), cy + ry * f * math.sin(ang)))
    return out


def cylinder_metrics(w, h):
    """シリンダーの楕円キャップの半径。描画と輪郭で共用する。"""
    ex = w / 2.0
    ey = min(h * 0.16, w * 0.22)
    return ex, ey


def pts_cylinder(x, y, w, h, seg=8):
    """側面 + 上下の楕円キャップ。"""
    ex, ey = cylinder_metrics(w, h)
    cx = x + ex
    top, bot = y + ey, y + h - ey
    out = []
    for k in range(seg + 1):            # 上フタの上半分 180° → 360°
        a = math.pi + math.pi * k / seg
        out.append((cx + ex * math.cos(a), top + ey * math.sin(a)))
    for k in range(seg + 1):            # 下フタの下半分 0° → 180°
        a = math.pi * k / seg
        out.append((cx + ex * math.cos(a), bot + ey * math.sin(a)))
    return out
