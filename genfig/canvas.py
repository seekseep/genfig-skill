"""Canvas — 図形・テキスト・コネクタを置いて SVG を出す。

図形メソッドはすべて `Node` を返す。線は `link()` でノード同士を結ぶ。
座標を手で計算しないこと。
"""

from . import assets, geom
from .geom import Ellipse, Poly, Rect, norm, sub
from .markers import ARROW_SIZE, default_registry
from .node import AUTO, Node, Point, as_endpoint
from .path import Polyline, clip_ends, quad_polyline
from .route import auto_sides, route_ortho
from .text import esc, font_size, font_weight, set_text_factor, text_extent
from .tokens import (ASCENT, CENTER_R, CLEARANCE, DASH, DESCENT, DETOUR,
                     DISPLAY_WIDTH, FONTS, INK, INK_TOP, LABEL_PAD, LINE,
                     LINE_SUB, MIN_READABLE, MIN_TEXT_GAP, PALETTE, RADIUS,
                     SCALE, SPACING, STROKE, STUB, SUBTLE, gap_value,
                     stroke_width)

# テキスト揃え → SVG text-anchor
_ALIGN = {"left": "start", "center": "middle", "right": "end",
          "start": "start", "middle": "middle", "end": "end"}


class Canvas:
    def __init__(self, width, height, bg="#ffffff", font="simple",
                 display_width=DISPLAY_WIDTH):
        """display_width は図を表示する欄の幅（px）。None なら字を拡大しない。

        キャンバスが display_width より広いと、表示で縮む比率ぶん字を拡大する。
        SCALE の値が「表示したときの px」になるので、キャンバス幅を変えても字の見え方は変わらない。
        """
        self.w = width
        self.h = height
        self.display_width = display_width
        self.text_k = max(1.0, width / display_width) if display_width else 1.0
        set_text_factor(self.text_k)
        self.texts = []   # (box, s, size) — save() で重なり・はみ出し・小さすぎる字を点検する
        self.body = []
        self.bg = bg
        # font は FONTS のキー（'simple' 等）でも実フォント文字列でも可
        self.font = FONTS.get(font, font)
        self.markers = default_registry()

    # ------------------------------------------------------------------
    # 低レベル
    # ------------------------------------------------------------------
    def raw(self, s):
        self.body.append(s)
        return self

    def emoji(self, cp, x, y, size):
        """twemoji（カラー絵文字）を配置する。(x, y) は左上。"""
        self.raw(assets.emoji(cp, x, y, size))
        return Node(x + size / 2.0, y + size / 2.0, size, size,
                    Poly(geom.pts_round_rect(x, y, size, size, 10.0)), kind="emoji")

    def icon(self, name, x, y, size, color=None, stroke=2.0):
        """FigJam 風ラインアイコン（Lucide）を配置する。(x, y) は左上。"""
        self.raw(assets.icon(name, x, y, size, color=color, stroke=stroke))
        return Node(x + size / 2.0, y + size / 2.0, size, size,
                    Poly(geom.pts_round_rect(x, y, size, size, 10.0)), kind="icon")

    # ------------------------------------------------------------------
    # テキスト
    # ------------------------------------------------------------------
    def text(self, x, y, s, scale="label", fill=None, anchor=None, align=None,
             weight=None, bold=False, strike=False, font=None):
        """テキストを描く。`\\n` を含むと複数行（tspan）になる。

        - scale : SCALE のキー（sm/md/lg/xl/xxl または display/heading/label…）
        - align : 'left'|'center'|'right'。anchor は後方互換の別名
        - bold  : 太字。weight 直接指定も可
        - strike: 取り消し線
        - font  : FONTS のキーでこのテキストだけフォントを上書き
        """
        size, w = font_size(scale), font_weight(scale)
        if bold:
            w = "700"
        if weight:
            w = weight
        a = _ALIGN.get(align or anchor or "middle", "middle")
        if fill is None:
            fill = INK if scale in ("display", "title", "heading", "xxl", "xl", "lg") else SUBTLE
        attrs = (f'x="{x:g}" y="{y:g}" text-anchor="{a}" font-size="{size}" '
                 f'fill="{fill}" font-weight="{w}"')
        if font:
            attrs += f' font-family="{FONTS.get(font, font)}"'

        lines = str(s).split("\n")
        if len(lines) == 1:
            self.raw(f'<text {attrs}>{esc(s)}</text>')
        else:
            step = size * 1.45
            spans = "".join(
                f'<tspan x="{x:g}" dy="{0 if i == 0 else step:g}">{esc(ln)}</tspan>'
                for i, ln in enumerate(lines))
            self.raw(f'<text {attrs}>{spans}</text>')

        tw, th = text_extent(s, scale, font=font, bold=bold, weight=weight)
        left = {"start": x, "middle": x - tw / 2.0, "end": x - tw}[a]
        box = Rect(left, y - size * ASCENT, tw, th)
        self.texts.append((box, str(s), size))
        if strike:
            # text-decoration は librsvg で描画されないため明示的に線を引く。
            sy = y - size * 0.3
            self.raw(f'<line x1="{left:.1f}" y1="{sy:.1f}" x2="{left + tw:.1f}" y2="{sy:.1f}" '
                     f'stroke="{fill}" stroke-width="{max(1.4, size * 0.07):.1f}"/>')
        return Node(box.cx, box.cy, box.w, box.h,
                    Poly(geom.pts_rect(box.x, box.y, box.w, box.h)), kind="text")

    def bullets(self, x, y, items, scale="body", gap=None, fill=None,
                marker="•", align="left", font=None):
        """箇条書き。items を行頭マーカー付きで縦に並べる。"""
        size = font_size(scale)
        if gap is None:
            gap = size + 8
        for i, item in enumerate(items):
            self.text(x, y + i * gap, f"{marker} {item}", scale=scale,
                      align=align, fill=fill, font=font)
        return self

    # ------------------------------------------------------------------
    # 図形
    # ------------------------------------------------------------------
    def _shape_fill(self, color, weight="thick", dash="solid"):
        c = PALETTE[color]
        sw = stroke_width(weight)
        out = f'fill="{c["bg"]}" stroke="{c["border"]}" stroke-width="{sw}"'
        da = DASH.get(dash)
        if da:
            out += f' stroke-dasharray="{da}"'
        return out

    def _polygon(self, pts, color, **kw):
        """点列を描画し、同じ点列を輪郭として登録する。"""
        poly = Poly(pts)
        self.raw(f'<polygon points="{poly.svg_points()}" '
                 f'{self._shape_fill(color, **kw)}/>')
        return self._handle(poly, color)

    def _handle(self, outline, color, label_box=None, kind="shape"):
        b = outline.bbox()
        return Node(b.cx, b.cy, b.w, b.h, outline,
                    label_box=label_box, color=color, kind=kind)

    def sticky(self, x, y, w, h, color="yellow", rx=16, weight="thick", dash="solid"):
        """淡い塗り＋濃いボーダーの角丸シェイプ（FigJam の付箋/四角）。"""
        self.raw(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{rx:g}" '
                 f'{self._shape_fill(color, weight, dash)}/>')
        # 描画は <rect rx> のまま（多角形より綺麗）。当たり判定だけ多角形化する。
        return self._handle(Poly(geom.pts_round_rect(x, y, w, h, rx)), color)

    def square(self, x, y, w, h, color="yellow", rx=16, **kw):
        return self.sticky(x, y, w, h, color=color, rx=rx, **kw)

    def cylinder(self, x, y, w, h, color="gray", **kw):
        """データベース（シリンダー）。"""
        ex, ey = geom.cylinder_metrics(w, h)
        l, r, b = x, x + w, y + h
        body = (f'M{l} {y + ey} A{ex} {ey} 0 0 0 {r} {y + ey} '
                f'L{r} {b - ey} A{ex} {ey} 0 0 1 {l} {b - ey} Z')
        c = PALETTE[color]
        self.raw(f'<path d="{body}" {self._shape_fill(color, **kw)}/>')
        # 上面の楕円（フタ）
        self.raw(f'<ellipse cx="{x + ex}" cy="{y + ey}" rx="{ex}" ry="{ey}" '
                 f'fill="{c["bg"]}" stroke="{c["border"]}" stroke-width="2.5"/>')
        return self._handle(Poly(geom.pts_cylinder(x, y, w, h)), color)

    def diamond(self, x, y, w, h, color="yellow", **kw):
        """ひし形（分岐・判断）。(x, y) は外接矩形の左上。"""
        return self._polygon(geom.pts_diamond(x, y, w, h), color, **kw)

    def triangle(self, x, y, w, h, color="green", direction="up", **kw):
        """三角形。direction='up'|'down'。"""
        return self._polygon(geom.pts_triangle(x, y, w, h, direction), color, **kw)

    def pentagon(self, x, y, w, h, color="purple", **kw):
        return self._polygon(geom.pts_pentagon(x, y, w, h), color, **kw)

    def hexagon(self, x, y, w, h, color="purple", **kw):
        """六角形（サービス・処理単位）。"""
        return self._polygon(geom.pts_hexagon(x, y, w, h), color, **kw)

    def octagon(self, x, y, w, h, color="teal", **kw):
        return self._polygon(geom.pts_octagon(x, y, w, h), color, **kw)

    def parallelogram(self, x, y, w, h, color="blue", skew=0.18, **kw):
        """平行四辺形（入出力・データの流れ）。"""
        return self._polygon(geom.pts_parallelogram(x, y, w, h, skew), color, **kw)

    def cross(self, x, y, w, h, color="red", arm=0.34, **kw):
        """十字（プラス）。"""
        return self._polygon(geom.pts_cross(x, y, w, h, arm), color, **kw)

    def arrow(self, x, y, w, h, color="blue", direction="right", **kw):
        """ブロック矢印（図形としての矢印。コネクタは link()）。"""
        return self._polygon(geom.pts_arrow(x, y, w, h, direction), color, **kw)

    def chevron(self, x, y, w, h, color="orange", notch=0.16, **kw):
        """シェブロン／ホームベース（工程・矢羽）。"""
        return self._polygon(geom.pts_chevron(x, y, w, h, notch), color, **kw)

    def star(self, x, y, w, h, color="yellow", points=5, inner=0.42, **kw):
        return self._polygon(geom.pts_star(x, y, w, h, points, inner), color, **kw)

    def ellipse(self, cx, cy, rx, ry, color="green", **kw):
        """楕円・円（開始/終了・アクター）。"""
        self.raw(f'<ellipse cx="{cx:g}" cy="{cy:g}" rx="{rx:g}" ry="{ry:g}" '
                 f'{self._shape_fill(color, **kw)}/>')
        return self._handle(Ellipse(cx, cy, rx, ry), color)

    def speech(self, x, y, w, h, color="blue", **kw):
        """吹き出し（コメント）。下辺左に尾を付けた角丸矩形。"""
        rx = 16
        bh = h * 0.78  # 本体高さ（残りが尾）
        tail_x = x + w * 0.24
        self.raw(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{bh:g}" rx="{rx}" '
                 f'{self._shape_fill(color, **kw)}/>')
        c = PALETTE[color]
        sw = stroke_width(kw.get("weight", "thick"))
        # 尾（本体と一体に見えるよう塗りで重ね、上辺の線は本体で隠す）
        tail = f"M{tail_x},{y + bh - 2} L{tail_x},{y + h} L{tail_x + w * 0.16},{y + bh - 2} Z"
        self.raw(f'<path d="{tail}" fill="{c["bg"]}" stroke="{c["border"]}" '
                 f'stroke-width="{sw}" stroke-linejoin="round"/>')
        self.raw(f'<line x1="{tail_x - 1}" y1="{y + bh - 1}" x2="{tail_x + w * 0.16 + 1}" '
                 f'y2="{y + bh - 1}" stroke="{c["bg"]}" stroke-width="{float(sw) + 1}"/>')
        # 尾は飾りなので当たり判定は本体だけ
        return self._handle(Poly(geom.pts_round_rect(x, y, w, bh, rx)), color)

    def cloud(self, x, y, w, h, color="blue", **kw):
        """雲（インターネット・外部）。"""
        sx, sy = w / 100.0, h / 70.0
        path = ("M25,60 a20,20 0 0 1 -4,-39 a23,23 0 0 1 44,-7 "
                "a17,17 0 0 1 16,13 a16,16 0 0 1 -5,33 Z")
        self.raw(f'<g transform="translate({x},{y}) scale({sx:g},{sy:g})">'
                 f'<path d="{path}" {self._shape_fill(color, **kw)}/></g>')
        # 雲は輪郭が複雑なので外接楕円で近似する（矢印はふくらみで止まる）
        return self._handle(Ellipse(x + w / 2.0, y + h / 2.0, w / 2.0, h / 2.0), color)

    # ------------------------------------------------------------------
    # ノード
    # ------------------------------------------------------------------
    def node(self, cx, cy, label, emoji_cp=None, icon_name=None, shape=None,
             color="yellow", w=120, h=88, label_scale="heading",
             glyph=None, label_gap=None):
        """要素を1つの「ノード」として描く。中身は絵文字 / アイコン / 図形。

        - emoji_cp   : twemoji（カラー絵文字）＋下にラベル
        - icon_name  : Lucide ラインアイコン＋下にラベル
        - shape      : 指定図形＋中央ラベル

        `w` / `h` はノードの箱の大きさとして**実際に効く**。絵文字・アイコンの
        大きさもラベル位置もここから決まる。既定の (120, 88) は従来と同じ 80px。
        """
        if label_gap is None:
            label_gap = SPACING["node_label"]
        gap = gap_value(label_gap)
        x, y = cx - w / 2.0, cy - h / 2.0

        if shape:
            drawer = {
                "cylinder": self.cylinder, "diamond": self.diamond,
                "triangle": self.triangle, "pentagon": self.pentagon,
                "hexagon": self.hexagon, "octagon": self.octagon,
                "parallelogram": self.parallelogram, "cross": self.cross,
                "arrow": self.arrow, "chevron": self.chevron, "star": self.star,
                "speech": self.speech, "cloud": self.cloud,
            }
            if shape == "ellipse":
                n = self.ellipse(cx, cy, w / 2.0, h / 2.0, color=color)
            elif shape in ("sticky", "square"):
                n = self.sticky(x, y, w, h, color=color)
            else:
                n = drawer[shape](x, y, w, h, color=color)
            # 図形の中に入れるグリフとラベル（w/h に比例させる）
            g = glyph if glyph else min(w, h) * 0.59
            if emoji_cp:
                self.emoji(emoji_cp, cx - g / 2.0, cy - g * 0.654, g)
            elif icon_name:
                gi = g * 0.85
                self.icon(icon_name, cx - gi / 2.0, cy - gi * 0.68, gi,
                          color=PALETTE[color]["text"])
            if emoji_cp or icon_name:
                self.text(cx, cy + h * 0.386, label, scale="label",
                          fill=PALETTE[color]["text"])
            else:
                size = font_size(label_scale)
                # 複数行のときは、行のかたまり全体が (cx, cy) の中央に来るよう、
                # 増えた行の分（行送り 1.45 × 行数-1 の半分）だけ上へずらす
                lines = str(label).count("\n")
                self.text(cx, cy + size * CENTER_R - lines * size * 1.45 / 2.0,
                          label, scale=label_scale,
                          fill=PALETTE[color]["text"])
            n.color = color
            return n

        # 図形なし: グリフ＋その下のラベルを、全体が (cx, cy) 中心になるよう積む
        g = glyph if glyph else max(16.0, min(w, h) - 2.0 * SPACING["glyph_pad"])
        size = font_size(label_scale)
        asc, desc = size * INK_TOP, size * DESCENT
        total = g + ((gap + asc + desc) if label else 0.0)
        top = cy - total / 2.0
        if emoji_cp:
            self.emoji(emoji_cp, cx - g / 2.0, top, g)
            kind = "emoji"
        elif icon_name:
            self.icon(icon_name, cx - g / 2.0, top, g)
            kind = "icon"
        else:
            kind = "shape"
        shape_outline = Poly(geom.pts_round_rect(cx - g / 2.0, top, g, g, 10.0))
        label_box = None
        if label:
            base = top + g + gap + asc
            tw, _ = text_extent(label, label_scale)
            self.text(cx, base, label, scale=label_scale)
            label_box = Rect(cx - tw / 2.0, base - asc, tw, asc + desc)
        return Node(cx, cy, g, g, shape_outline,
                    label_box=label_box, color=color, kind=kind)

    # ------------------------------------------------------------------
    # コネクタ
    # ------------------------------------------------------------------
    def _stroke(self, weight, dash, color):
        sw = stroke_width(weight)
        out = (f'stroke="{color}" stroke-width="{sw}" '
               f'stroke-linecap="round" stroke-linejoin="round"')
        da = DASH.get(dash)
        if da:
            out += f' stroke-dasharray="{da}"'
        return out

    def link(self, src, dst, label=None, *,
             route="straight", first=None,
             corner="round", radius=None, curve=0,
             start=None, end=None, offset=0,
             clip="auto", clearance=None, stub=None, detour=None,
             both=False, head=True,
             primary=True, weight=None, dash="solid", color=None,
             arrow_kind="solid", arrow_size=None,
             label_pos="on", label_at="longest", label_scale="label",
             label_font=None, label_fill=None, label_pad=None,
             label_offset=None, label_plate=False):
        """2 つの要素を線で結ぶ。

        端点 `src` / `dst` は `Node`、`(Node, アンカー)`、`(x, y)` のいずれか。

        - `route`  : "straight"（直線）| "elbow"（途中で曲がる）| "curve"
        - `corner` : "round"（角丸）| "sharp"（角）。`radius` で半径
        - `start` / `end` : アンカー。8 方位・"auto"（中心）・角度・(dx, dy)
        - `offset` : 線を進行方向の左へずらす px。往路と復路に同じ値を渡すと
          互いに反対側へ分かれるので、2 本を重ねずに並べられる
        - `label_pos` : "on"（線を切って間に置く）| "above" | "below"
        """
        a_node, a_anchor = as_endpoint(src)
        b_node, b_anchor = as_endpoint(dst)
        if start is not None:
            a_anchor = start
        if end is not None:
            b_anchor = end

        col = color or (LINE if primary else LINE_SUB)
        if weight is None:
            weight = "thick" if primary else "thin"
        if clearance is None:
            clearance = CLEARANCE
        if stub is None:
            stub = STUB
        if detour is None:
            detour = DETOUR
        if label_pad is None:
            label_pad = LABEL_PAD
        # corner="round" + radius=None → 脚の半分（ハンドルが中点）で最も滑らか
        rr = 0.0 if corner == "sharp" else (None if radius is None else float(radius))

        # クリップ対象の輪郭
        mode_a = None if clip == "auto" else clip
        mode_b = None if clip == "auto" else clip
        out_a = a_node.outline(mode_a)
        out_b = b_node.outline(mode_b)

        # --- アンカーを決める ---
        if route == "elbow" and a_anchor is None and b_anchor is None:
            a_anchor, b_anchor = auto_sides(a_node, b_node, first)

        # offset: 線を進行方向の左へずらす。往路/復路を重ねずに並べるときに使う。
        # a→b と b→a に同じ値を渡すと、互いに反対側へ分かれる。
        oa = ob = (0.0, 0.0)
        if offset:
            u = norm(sub(b_node.center, a_node.center))
            perp = (u[1], -u[0])
            oa = ob = (perp[0] * offset, perp[1] * offset)

        pa = self._anchor_point(a_node, a_anchor, b_node.center, clearance, mode_a, oa)
        pb = self._anchor_point(b_node, b_anchor, a_node.center, clearance, mode_b, ob)

        # --- 折れ線を作る ---
        if route == "elbow":
            n1 = self._normal(a_node, pa, pb, a_anchor)
            n2 = self._normal(b_node, pb, pa, b_anchor)
            poly = route_ortho(pa, n1, pb, n2, stub=stub, detour=detour)
        elif route == "curve" or curve:
            mid = ((pa[0] + pb[0]) / 2.0, (pa[1] + pb[1]) / 2.0 + curve)
            poly = quad_polyline(pa, mid, pb)
            rr = 0.0
        else:
            poly = Polyline([pa, pb])

        # --- 図形に重なる部分を落とす ---
        poly = clip_ends(poly, out_a, out_b, clearance, clearance)

        # --- ラベル位置とギャップ ---
        gaps = []
        label_draw = None
        if label:
            label_draw, gaps = self._place_label(
                poly, label, label_scale, label_font, label_pos, label_at,
                label_pad, label_offset)

        # --- 線を描く ---
        st = self._stroke(weight, dash, col)
        asize = arrow_size or ARROW_SIZE
        mid_end = self.markers.get(col, arrow_kind, asize) if (head or both) else None
        mid_start = self.markers.get(col, arrow_kind, asize) if both else None
        subs = poly.subpaths(radius=rr, gaps=gaps)
        for i, d in enumerate(subs):
            attrs = f'<path d="{d}" fill="none" {st}'
            if i == len(subs) - 1 and mid_end:
                attrs += f' marker-end="url(#{mid_end})"'
            if i == 0 and mid_start:
                attrs += f' marker-start="url(#{mid_start})"'
            self.raw(attrs + "/>")

        # --- ラベルを描く ---
        if label_draw:
            lx, ly = label_draw
            if label_plate:
                tw, th = text_extent(label, label_scale, font=label_font)
                self.raw(f'<rect x="{lx - tw / 2 - 4:.1f}" y="{ly - th * 0.72:.1f}" '
                         f'width="{tw + 8:.1f}" height="{th + 2:.1f}" '
                         f'rx="4" fill="{self.bg}"/>')
            self.text(lx, ly, label, scale=label_scale, align="center",
                      font=label_font,
                      fill=label_fill or (INK if primary else SUBTLE))
        return Link(poly, a_node, b_node)

    @staticmethod
    def _anchor_point(node, anchor, toward, clearance, mode, shift):
        """アンカー位置。shift は ray の出発点を横へずらす量（offset 用）。

        ずらした出発点が図形の外に出てしまう場合は、素直に中心から出す。
        """
        if not (shift[0] or shift[1]) or isinstance(node, Point):
            return node.at(anchor, toward=toward, pad=clearance, mode=mode)
        outline = node.outline(mode) or node.shape_outline
        origin = (node.center[0] + shift[0], node.center[1] + shift[1])
        if not outline.contains(origin):
            return node.at(anchor, toward=toward, pad=clearance, mode=mode)
        # ずらした出発点から見た方向。"auto" ならずらす前と同じ向き（＝平行に並ぶ）。
        key = anchor.strip().lower() if isinstance(anchor, str) else anchor
        if key in AUTO:
            d = norm(sub(toward, node.center)) or (1.0, 0.0)
            if d == (0.0, 0.0):
                d = (1.0, 0.0)
        else:
            d = node.direction(anchor)
        return outline.ray_exit(origin, d, pad=clearance)

    @staticmethod
    def _normal(node, p, other, anchor):
        """エルボの出入りの向き。点ノードは相手の方角を軸に丸めて使う。"""
        if isinstance(node, Point):
            return _axis_snap(sub(other, p))
        if anchor is not None and not isinstance(anchor, str):
            return _axis_snap(sub(p, node.center))
        return node.normal_at(p, snap=True)

    def _place_label(self, poly, label, scale, font, pos, at, pad, offset):
        """ラベルの描画位置と、線に開けるギャップ区間を返す。"""
        tw, th = text_extent(label, scale, font=font)
        size = font_size(scale)
        L = poly.length

        # 置く弧長を決める
        if isinstance(at, (int, float)):
            cands = [L * float(at)]
        elif at == "mid" or poly.nseg() == 1 or poly.smooth:
            # 曲線は微小区間の集まりなので「最長区間」に意味がない。弧長の中点に置く。
            cands = [L / 2.0]
        else:
            order = sorted(range(poly.nseg()), key=lambda i: -poly.seg(i)[3])
            cands = [(poly.cum[i] + poly.cum[i + 1]) / 2.0 for i in order]
            cands.append(L / 2.0)

        if offset is not None:
            s = cands[0]
            p = poly.point_at(s)
            return (p[0] + offset[0], p[1] + offset[1]), []

        if pos in ("above", "below"):
            s = cands[0]
            p = poly.point_at(s)
            u = poly.tangent_at(s)
            n = (u[1], -u[0])           # 進行方向の左
            if pos == "above" and n[1] > 0:
                n = (-n[0], -n[1])      # 画面上で「上」に寄せる
            if pos == "below" and n[1] < 0:
                n = (-n[0], -n[1])
            off = th / 2.0 + pad
            return (p[0] + n[0] * off,
                    p[1] + n[1] * off + size * CENTER_R), []

        # pos == "on": 線を切って間に置く
        min_lead = 10.0
        for s in cands:
            u = poly.tangent_at(s)
            # ラベルの箱を線の向きへ射影した長さ。縦線なら文字の「高さ」で切れる。
            gap = tw * abs(u[0]) + th * abs(u[1]) + 2.0 * pad
            g0, g1 = s - gap / 2.0, s + gap / 2.0
            if g0 >= min_lead and g1 <= L - min_lead:
                p = poly.point_at(s)
                return (p[0], p[1] + size * CENTER_R), [(g0, g1)]
        # どこにも入らない → 線は切らずに横へ逃がす
        return self._place_label(poly, label, scale, font, "above", at, pad, None)

    # ------------------------------------------------------------------
    # 出力
    # ------------------------------------------------------------------
    def svg(self):
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" font-family="{self.font}">\n'
            f'{self.markers.defs()}\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="{self.bg}"/>\n'
            + "\n".join(self.body)
            + "\n</svg>\n"
        )

    def check(self):
        """字の点検結果（警告文のリスト）を返す。save() が標準エラーに出す。

        - 表示したときの大きさが MIN_READABLE px 未満の字
        - キャンバスからはみ出す字
        - ほかの字と重なる字、横に MIN_TEXT_GAP px より近い字
        """
        shown = (self.display_width / self.w
                 if self.display_width and self.w > self.display_width else 1.0)
        out = []
        for box, s, size in self.texts:
            px = size * shown
            if px < MIN_READABLE - 0.05:
                out.append(f"小さい字（表示 {px:.1f}px）: {s!r}")
            if box.x < 0 or box.y < 0 or box.x + box.w > self.w or box.y + box.h > self.h:
                out.append(f"キャンバスからはみ出す字: {s!r}")
        gap = MIN_TEXT_GAP / shown   # SVG 座標での最低の隙間
        for i, (a, sa, _) in enumerate(self.texts):
            for b, sb, _ in self.texts[i + 1:]:
                dx = max(b.x - (a.x + a.w), a.x - (b.x + b.w))
                dy = max(b.y - (a.y + a.h), a.y - (b.y + b.h))
                # 縦に積んだ字（行・見出しと説明）は行間で離れていればよいので、重なりだけを見る。
                if dy >= dx:
                    if dy < 0:
                        out.append(f"重なる字: {sa!r} と {sb!r}")
                elif dx < gap:
                    what = "重なる字" if dx < 0 else f"横に近すぎる字（{dx * shown:.0f}px）"
                    out.append(f"{what}: {sa!r} と {sb!r}")
        return out

    def save(self, path):
        import pathlib
        import sys
        for msg in self.check():
            print(f"[genfig] {path}: {msg}", file=sys.stderr)
        p = pathlib.Path(path)
        if p.parent != pathlib.Path(""):
            p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.svg(), encoding="utf-8")
        return str(p)


class Link:
    """引いた線のハンドル。線上に注記を足したいときに使う。"""

    __slots__ = ("poly", "src", "dst")

    def __init__(self, poly, src, dst):
        self.poly = poly
        self.src = src
        self.dst = dst

    def at(self, t):
        """0..1 で線上の点。"""
        return self.poly.point_at(self.poly.length * t)

    def tangent(self, t):
        return self.poly.tangent_at(self.poly.length * t)


def _axis_snap(d):
    d = norm(d)
    if d == (0.0, 0.0):
        return (1.0, 0.0)
    if abs(d[0]) >= abs(d[1]):
        return (1.0 if d[0] > 0 else -1.0, 0.0)
    return (0.0, 1.0 if d[1] > 0 else -1.0)
