"""折れ線 — 弧長パラメータ化・角丸・ギャップ分割。

コネクタは直線もエルボもカーブも、すべて内部では折れ線 `Polyline` にする。
そのうえで

- **弧長**でラベル位置とギャップ区間を決める
- `d()` で **ギャップを先に切ってから角を丸める**

という順にする。逆（丸めてから切る）にすると `corner=` を変えるたびに全長が変わり、
ラベルが線上を滑ってしまう。角がギャップに食われるケースも、先に切っておけば
その角はサブパスの端点になるだけで自然に処理される。
"""

import math

from .geom import EPS, cross, dot, length, lerp, norm, sub


class Polyline:
    def __init__(self, pts, smooth=False):
        # smooth=True は「曲線をサンプリングした折れ線」の印。区間が多数の微小片に
        # なるため、ラベルは最長区間ではなく弧長の中点に置く。
        self.smooth = smooth
        p = []
        for q in pts:
            q = (float(q[0]), float(q[1]))
            # 重複点は畳む（弧長 0 の区間は接線が定義できない）
            if not p or abs(q[0] - p[-1][0]) > 1e-6 or abs(q[1] - p[-1][1]) > 1e-6:
                p.append(q)
        if len(p) < 2:
            p = (p * 2) if p else [(0.0, 0.0), (0.0, 0.0)]
        self.pts = p
        self._cum = None

    # --- 弧長 ---
    @property
    def cum(self):
        if self._cum is None:
            c = [0.0]
            for i in range(1, len(self.pts)):
                c.append(c[-1] + length(sub(self.pts[i], self.pts[i - 1])))
            self._cum = c
        return self._cum

    @property
    def length(self):
        return self.cum[-1]

    def _locate(self, s):
        """弧長 s が属する区間 index と、その区間内の比 0..1。"""
        c = self.cum
        s = max(0.0, min(float(s), c[-1]))
        lo, hi = 0, len(c) - 1
        while lo < hi - 1:
            mid = (lo + hi) // 2
            if c[mid] <= s:
                lo = mid
            else:
                hi = mid
        seg = c[lo + 1] - c[lo]
        return lo, (0.0 if seg < EPS else (s - c[lo]) / seg)

    def point_at(self, s):
        i, f = self._locate(s)
        return lerp(self.pts[i], self.pts[i + 1], f)

    def tangent_at(self, s):
        i, _ = self._locate(s)
        return norm(sub(self.pts[i + 1], self.pts[i]))

    def seg(self, i):
        """区間 i の (開始弧長, 終了弧長, 単位方向, 長さ)。"""
        a, b = self.pts[i], self.pts[i + 1]
        return self.cum[i], self.cum[i + 1], norm(sub(b, a)), self.cum[i + 1] - self.cum[i]

    def nseg(self):
        return len(self.pts) - 1

    # --- 切り出し ---
    def slice(self, s0, s1):
        L = self.length
        s0 = max(0.0, min(s0, L))
        s1 = max(s0, min(s1, L))
        i0, _ = self._locate(s0)
        i1, _ = self._locate(s1)
        return Polyline([self.point_at(s0)] + self.pts[i0 + 1:i1 + 1] + [self.point_at(s1)],
                        smooth=self.smooth)

    def trim(self, head=0.0, tail=0.0):
        return self.slice(head, self.length - tail)

    def reversed(self):
        return Polyline(list(reversed(self.pts)), smooth=self.smooth)

    def longest_segment(self, horiz_bonus=1.08):
        """最も長い区間の index。ほぼ同長なら横向きを優先する
        （`─── ラベル ──▶` と読ませたいため）。"""
        best, bi = -1.0, 0
        for i in range(self.nseg()):
            _, _, u, seg_len = self.seg(i)
            key = seg_len * (horiz_bonus if abs(u[0]) >= abs(u[1]) else 1.0)
            if key > best:
                best, bi = key, i
        return bi

    # --- SVG ---
    def d(self, radius=None, gaps=()):
        """SVG の d 属性。gaps は **丸める前の折れ線上の弧長** 区間 [(s0, s1), ...]。"""
        parts = []
        for a, b in keep_ranges(self.length, gaps):
            if b - a < 0.3:
                continue
            frag = self.slice(a, b)._d_one(radius)
            if frag:
                parts.append(frag)
        return " ".join(parts)

    def subpaths(self, radius=None, gaps=()):
        """ギャップで分けたサブパスの d を個別に返す（矢印を最後だけに付けるため）。"""
        out = []
        for a, b in keep_ranges(self.length, gaps):
            if b - a < 0.3:
                continue
            frag = self.slice(a, b)._d_one(radius)
            if frag:
                out.append(frag)
        return out

    def _d_one(self, radius):
        """radius=None なら「脚の半分」まで戻る（ハンドルが中点に来る滑らかな曲がり）。
        数値を渡すとその長さで頭打ちにする。0 以下なら角のまま。"""
        p = self.pts
        if len(p) < 2:
            return ""
        if (radius is not None and radius <= 0.0) or len(p) == 2:
            return "M" + " L".join(f"{q[0]:.2f} {q[1]:.2f}" for q in p)
        out = [f"M{p[0][0]:.2f} {p[0][1]:.2f}"]
        for i in range(1, len(p) - 1):
            a, b, c = p[i - 1], p[i], p[i + 1]
            u = norm(sub(a, b))     # 角 b から前の点へ
            v = norm(sub(c, b))     # 角 b から次の点へ
            la, lc = length(sub(a, b)), length(sub(c, b))
            # 既定は隣接する脚の半分（＝ベジェのアンカーが中点に来る）。
            # radius が数値ならそこで頭打ち。
            r = min(la / 2.0, lc / 2.0)
            if radius is not None:
                r = min(r, float(radius))
            cz = cross((-u[0], -u[1]), v)   # 進行方向 A→B と B→C の外積 = 曲がる向き
            if r < 0.5 or abs(cz) < 1e-9:
                out.append(f"L{b[0]:.2f} {b[1]:.2f}")
                continue
            if dot(u, v) > 0.997:           # ヘアピンは丸めない
                out.append(f"L{b[0]:.2f} {b[1]:.2f}")
                continue
            # 角から r 手前で折れ線を離れ、**角そのものを制御点にした二次ベジェ**で戻る。
            # 両脚に接するので接線が連続し、円弧より少しだけ角に寄った滑らかな曲がりになる。
            pp = (b[0] + u[0] * r, b[1] + u[1] * r)
            qq = (b[0] + v[0] * r, b[1] + v[1] * r)
            out.append(f"L{pp[0]:.2f} {pp[1]:.2f}")
            out.append(f"Q{b[0]:.2f} {b[1]:.2f} {qq[0]:.2f} {qq[1]:.2f}")
        out.append(f"L{p[-1][0]:.2f} {p[-1][1]:.2f}")
        return " ".join(out)


def keep_ranges(total, gaps):
    """全長 total からギャップ区間を引いた「残す」区間のリスト。"""
    keep = [(0.0, float(total))]
    for g0, g1 in sorted(gaps):
        g0, g1 = max(0.0, float(g0)), min(float(total), float(g1))
        if g1 <= g0:
            continue
        nxt = []
        for a, b in keep:
            if g1 <= a or g0 >= b:
                nxt.append((a, b))
                continue
            if a < g0:
                nxt.append((a, g0))
            if g1 < b:
                nxt.append((g1, b))
        keep = nxt
    return keep


def quad_polyline(p0, p1, p2, samples=64):
    """二次ベジェを折れ線にサンプリングする（カーブコネクタ用）。"""
    pts = []
    for k in range(samples + 1):
        t = k / samples
        pts.append(lerp(lerp(p0, p1, t), lerp(p1, p2, t), t))
    return Polyline(pts, smooth=True)


def clip_start(poly, outline, pad=0.0):
    """折れ線の始点側が outline の内側にある間を切り落とす。

    始点そのものは（アンカーなので）ちょうど輪郭の上に載っている。内外の判定は
    少し進んだ点で行う。こうすると「東にある相手へ 'w' アンカーで結んだ」ような
    指定でも、図形を貫いた部分がきちんと落ちる。
    """
    if outline is None:
        return poly
    probe = poly.point_at(min(1.5, poly.length * 0.5))
    if not outline.contains(probe):
        return poly
    acc = 0.0
    for i in range(poly.nseg()):
        a, b = poly.pts[i], poly.pts[i + 1]
        d = sub(b, a)
        seg_len = length(d)
        if seg_len < EPS:
            continue
        u = (d[0] / seg_len, d[1] / seg_len)
        for t in outline.hits(a, u):
            if EPS < t <= seg_len + EPS:
                return poly.slice(min(acc + t + pad, poly.length), poly.length)
        acc += seg_len
    return poly


def clip_ends(poly, out_a, out_b, pad_a=0.0, pad_b=0.0):
    """両端を、それぞれの図形の輪郭で切り落とす。"""
    poly = clip_start(poly, out_a, pad_a)
    return clip_start(poly.reversed(), out_b, pad_b).reversed()
