"""アローヘッド — 色ごとに <marker> を用意して <defs> にまとめる。

librsvg は SVG2 の `fill="context-stroke"` を実装していないので、線の色に追従する
マーカーは作れない。色ごとに marker を登録するのが唯一の移植可能な方法。
"""

from .tokens import LINE, LINE_SUB

# viewBox 0..10 のうち、頭の先端は x=9。refX=9 で先端がちょうど終点に載る。
# （旧実装は refX=8 で、先端が終点を 0.7×線幅ぶん行き過ぎていた）
ARROW_REF_X = 9.0
ARROW_SIZE = 7.0

SHAPES = {
    "solid": '<path d="M0 1 L9 5 L0 9 z" fill="{c}"/>',
    "open":  ('<path d="M1 1 L8.5 5 L1 9" fill="none" stroke="{c}" stroke-width="1.6" '
              'stroke-linecap="round" stroke-linejoin="round"/>'),
    "dot":   '<circle cx="5" cy="5" r="3.2" fill="{c}"/>',
    "bar":   '<path d="M8 1 L8 9" stroke="{c}" stroke-width="2" stroke-linecap="round"/>',
}


class MarkerRegistry:
    """(色, 種類, サイズ) ごとに marker を 1 つだけ作る。"""

    def __init__(self):
        self._defs = {}     # id -> markup
        self._bykey = {}    # (color, kind, size) -> id

    def seed(self, mid, color, kind="solid", size=ARROW_SIZE, refx=ARROW_REF_X):
        """固定 id を先に押さえる（既存図との互換用の aR / aRsub）。"""
        key = (color.lower(), kind, round(float(size), 2))
        self._bykey[key] = mid
        self._defs[mid] = self._markup(mid, color, kind, size, refx)
        return mid

    def get(self, color, kind="solid", size=ARROW_SIZE):
        key = (color.lower(), kind, round(float(size), 2))
        if key in self._bykey:
            return self._bykey[key]
        mid = "a{}{}{}".format(kind[0].upper(),
                               color.lstrip("#").lower(),
                               ("%g" % size).replace(".", "_"))
        self._bykey[key] = mid
        self._defs[mid] = self._markup(mid, color, kind, size, ARROW_REF_X)
        return mid

    @staticmethod
    def _markup(mid, color, kind, size, refx):
        body = SHAPES[kind].format(c=color)
        return (f'<marker id="{mid}" viewBox="0 0 10 10" refX="{refx:g}" refY="5" '
                f'markerWidth="{size:g}" markerHeight="{size:g}" '
                f'orient="auto-start-reverse">{body}</marker>')

    def defs(self):
        if not self._defs:
            return ""
        return "<defs>" + "".join(self._defs[k] for k in sorted(self._defs)) + "</defs>"


def default_registry():
    r = MarkerRegistry()
    # 既存 SVG と同じ id を先に確保しておく（差分を小さく保つ）
    r.seed("aR", LINE)
    r.seed("aRsub", LINE_SUB)
    return r
