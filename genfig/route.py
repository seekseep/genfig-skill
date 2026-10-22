"""コネクタのルーティング — 直交（エルボ）折れ線を作る。

アンカーの外向き法線が「最初/最後の区間の向き」を決める。`"e"` から出た線は
必ず一度東へ出てから曲がる。各端に短いスタブを付けることで、図形から垂直に
離れてから曲がる FigJam 風の見た目になり、線が図形へ戻ることもない。
"""

from .path import Polyline

H, V = "h", "v"


def _axis(n):
    return H if abs(n[0]) >= abs(n[1]) else V


def _sign(n, ax):
    return 1.0 if (n[0] if ax == H else n[1]) >= 0.0 else -1.0


def _ahead(frm, to, s, eps=0.5):
    """to は frm から見て s の向きに（十分）前方か。"""
    return (to - frm) * s > eps


def route_ortho(p1, n1, p2, n2, stub=18.0, detour=28.0, bias=1.0):
    """外向き法線 n1 / n2 を持つ 2 点を直交折れ線で結ぶ。

    n1 は最初の区間が向かう方向、n2 は最後の区間が「来る方向の逆」。
    """
    a = (p1[0] + n1[0] * stub, p1[1] + n1[1] * stub)
    b = (p2[0] + n2[0] * stub, p2[1] + n2[1] * stub)
    ax1, ax2 = _axis(n1), _axis(n2)
    s1, s2 = _sign(n1, ax1), _sign(n2, ax2)
    mid = []

    if ax1 == H and ax2 == H:
        if abs(a[1] - b[1]) < 0.5 and _ahead(a[0], b[0], s1) and _ahead(b[0], a[0], s2):
            mid = []                                        # 一直線（縮退）
        else:
            mx = (a[0] + b[0]) / 2.0
            if _ahead(a[0], mx, s1) and _ahead(b[0], mx, s2):
                mid = [(mx, a[1]), (mx, b[1])]              # Z 字（最頻）
            else:                                           # 同じ向き / 背中合わせ
                my = (a[1] + b[1]) / 2.0
                if abs(a[1] - b[1]) < 1.0:
                    my = a[1] + detour * bias               # 完全同高なら上下へ逃がす
                x1, x2 = a[0] + s1 * detour, b[0] + s2 * detour
                mid = [(x1, a[1]), (x1, my), (x2, my), (x2, b[1])]

    elif ax1 == V and ax2 == V:
        if abs(a[0] - b[0]) < 0.5 and _ahead(a[1], b[1], s1) and _ahead(b[1], a[1], s2):
            mid = []
        else:
            my = (a[1] + b[1]) / 2.0
            if _ahead(a[1], my, s1) and _ahead(b[1], my, s2):
                mid = [(a[0], my), (b[0], my)]
            else:
                mx = (a[0] + b[0]) / 2.0
                if abs(a[0] - b[0]) < 1.0:
                    mx = a[0] + detour * bias
                y1, y2 = a[1] + s1 * detour, b[1] + s2 * detour
                mid = [(a[0], y1), (mx, y1), (mx, y2), (b[0], y2)]

    elif ax1 == H:                                          # H → V
        ok1 = _ahead(a[0], b[0], s1)
        ok2 = _ahead(b[1], a[1], s2)
        if ok1 and ok2:
            mid = [(b[0], a[1])]                            # 単純な L
        else:
            mx = (a[0] + s1 * detour) if not ok1 else (b[0] + s1 * detour)
            if abs(mx - b[0]) < 1.0:
                mx = b[0] + s1 * detour
            my = b[1] + s2 * detour
            mid = [(mx, a[1]), (mx, my), (b[0], my)]

    else:                                                   # V → H
        ok1 = _ahead(a[1], b[1], s1)
        ok2 = _ahead(b[0], a[0], s2)
        if ok1 and ok2:
            mid = [(a[0], b[1])]
        else:
            my = (a[1] + s1 * detour) if not ok1 else (b[1] + s1 * detour)
            if abs(my - b[1]) < 1.0:
                my = b[1] + s1 * detour
            mx = b[0] + s2 * detour
            mid = [(a[0], my), (mx, my), (mx, b[1])]

    return Polyline([p1, a] + mid + [b, p2])


def auto_sides(src, dst, first=None, l_ratio=0.75):
    """アンカー未指定のとき、2 つのノードの位置関係から出入りの辺を決める。

    - 主に横に離れていれば東西、縦なら南北
    - **ほぼ真斜め**のときだけ L 字（出口と入口の軸を変える）

    L 字は「角が両方の図形の外に素直に取れる」ときしか綺麗にならない。少しでも
    軸が勝っていると角が図形の裏に回り、フック状の迂回が生まれる。そのため
    既定はコの字（Z）で、真斜め（l_ratio=0.75 ≒ 37°〜53°）だけ L 字にする。
    """
    dx = dst.cx - src.cx
    dy = dst.cy - src.cy
    adx, ady = abs(dx), abs(dy)
    if first is None:
        axis = H if adx >= ady else V
        elbow_l = min(adx, ady) > l_ratio * max(adx, ady, 1.0)
    else:
        axis = first.lower()
        elbow_l = False
    if axis == H:
        s = "e" if dx >= 0 else "w"
        d = ("n" if dy >= 0 else "s") if elbow_l else ("w" if dx >= 0 else "e")
    else:
        s = "s" if dy >= 0 else "n"
        d = ("w" if dx >= 0 else "e") if elbow_l else ("n" if dy >= 0 else "s")
    return s, d
