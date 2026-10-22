"""genfig — イメージスキーマに基づく twemoji 図を SVG で描くための再利用プリミティブ。

設計方針:
- twemoji / Lucide を SVG に「インライン」して自己完結させる
  （外部 href は GitHub 等で描画がブロックされるため）。
- 見た目・トークンは FigJam のツールバー UI に 1:1 対応させる。
- **座標を手で計算しない**。図形メソッドは `Node` を返し、線は `link()` で
  ノード同士を結ぶ。どの辺から出てどこで止まるかは genfig が計算する。

    from genfig import Canvas

    c = Canvas(760, 300)
    a = c.node(150, 150, "ブラウザ", emoji_cp="1f310")
    b = c.node(610, 150, "サーバー", emoji_cp="1f5a5")
    c.link(a, b, label="リクエスト")
    c.save("out.svg")

使い方は examples/ と SKILL.md を参照。
"""

from .assets import (ICON_ALIASES, emoji, fetch_emoji_raw, fetch_icon_raw, icon)
from .canvas import Canvas, Link
from .geom import Ellipse, Poly, Rect
from .markers import ARROW_SIZE, MarkerRegistry
from .node import COMPASS, Node, Point, pt
from .path import Polyline
from .route import auto_sides, route_ortho
from .text import (esc, font_size, set_text_factor, text_extent, text_factor,
                   text_width)
from .tokens import (ASCENT, CENTER_R, CLEARANCE, DASH, DESCENT, DETOUR,
                     DISPLAY_WIDTH, FONT, MIN_READABLE, MIN_TEXT_GAP,
                     FONTS, GAP, INK, INK_SCALE, INK_TOP, LABEL_PAD, LINE,
                     LINE_HEIGHT, LINE_SUB, PALETTE, RADIUS, SCALE, SPACING,
                     STROKE, STUB, SUBTLE)

__all__ = [
    "Canvas", "Link", "Node", "Point", "pt",
    "Poly", "Ellipse", "Rect", "Polyline",
    "MarkerRegistry", "ARROW_SIZE",
    "route_ortho", "auto_sides", "COMPASS",
    "emoji", "icon", "fetch_emoji_raw", "fetch_icon_raw", "ICON_ALIASES",
    "text_extent", "text_width", "font_size", "esc",
    "set_text_factor", "text_factor", "DISPLAY_WIDTH", "MIN_READABLE", "MIN_TEXT_GAP",
    "FONTS", "FONT", "SCALE", "INK_SCALE", "INK", "SUBTLE", "LINE", "LINE_SUB",
    "PALETTE", "STROKE", "DASH", "GAP", "SPACING",
    "ASCENT", "DESCENT", "INK_TOP", "CENTER_R", "LINE_HEIGHT",
    "CLEARANCE", "STUB", "DETOUR", "RADIUS", "LABEL_PAD",
]
