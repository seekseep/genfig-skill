"""デザイントークン — FigJam のツールバー UI に 1:1 対応させた定数群。

サイズ・色・線種を直書きせず、必ずここのキーで指定する。
"""

# ---------------------------------------------------------------------------
# フォント
# ---------------------------------------------------------------------------

# フォントファミリー（FigJam: シンプル / フォーマル / テクニカル / キュート）。
# 日本語を優先指定しつつ欧文フォールバックを添える。
FONTS = {
    "simple":    "'Hiragino Sans','Noto Sans JP','Yu Gothic','Segoe UI',sans-serif",   # ゴシック
    "formal":    "'Hiragino Mincho ProN','Noto Serif JP','Yu Mincho',serif",            # 明朝
    "technical": "'SFMono-Regular','Consolas','Noto Sans Mono','Courier New',monospace",# 等幅
    "cute":      "'Kosugi Maru','Yusei Magic','Hiragino Maru Gothic ProN',sans-serif",  # 丸ゴシック
}
FONT = FONTS["simple"]  # 既定

# 図が実際に表示される幅（px）。ドキュメントサイトの本文欄（Starlight は 45rem ≒ 720px）。
# SVG は本文欄の幅に縮めて表示されるので、キャンバスがこれより広いと字も同じ比率で小さく見える。
DISPLAY_WIDTH = 720

# 表示したときに読める最小の字の大きさ（px）。これを下回る字があると save() が警告する。
MIN_READABLE = 12

# 字と字のあいだに最低限空ける隙間（表示したときの px）。これより近いと save() が警告する。
MIN_TEXT_GAP = 8

# 段階的フォントスケール。FigJam のサイズ別名（sm/md/lg/xl/xxl ＝ 小/中/大/特大/超特大）と
# 意味ベースの別名（display/title/heading/label/body/caption）を両方引けるようにする。
# 値は「DISPLAY_WIDTH で表示したときの px」。キャンバスが DISPLAY_WIDTH より広いときは、
# Canvas が幅の比率ぶん拡大して書き出す（text.text_factor）。
SCALE = {
    # 意味ベース
    "display": (33, "700"),  # 図全体のタイトル
    "title":   (26, "700"),  # ノードの主役ラベル
    "heading": (21, "700"),  # ノード見出し・層タイトル
    "label":   (17, "600"),  # 矢印・要素ラベル
    "body":    (15, "400"),  # 補足の本文
    "caption": (13, "400"),  # 注記・キャプション
    # FigJam サイズ別名
    "xxl": (33, "700"),  # 超特大
    "xl":  (26, "700"),  # 特大
    "lg":  (21, "700"),  # 大
    "md":  (17, "600"),  # 中
    "sm":  (13, "400"),  # 小
}

# 大きい側のスケール（既定の文字色を INK にする判定に使う）
BIG_SCALES = ("display", "title", "heading", "xxl", "xl", "lg")

# フォントメトリクスの仮定（em box に対する比）。日本語フォントの実測に近い値。
# 和文は em box をほぼ使い切り、ベースラインは下から 12% あたりに来る。
ASCENT = 0.88       # ベースライン → 文字上端（em box の上端）
DESCENT = 0.12      # ベースライン → 文字下端
INK_TOP = 0.80      # 和欧混在ラベルの「実際にインクがある」上端。図の下にラベルを置くときの基準
CENTER_R = 0.35     # cy に視覚的に中央合わせするときのベースラインオフセット比
LINE_HEIGHT = 1.45  # 行送り（複数行テキスト）

# ---------------------------------------------------------------------------
# 色
# ---------------------------------------------------------------------------

# 無彩色 4 段階（FigJam の黒〜淡灰）。テキスト/線の濃淡に使う。
INK_SCALE = {
    "ink":   "#0f172a",  # 黒（最濃）— 主役テキスト
    "dark":  "#475569",  # 濃灰   — 主コネクタ・サブテキスト
    "gray":  "#94a3b8",  # 灰     — 副コネクタ・弱い関係
    "light": "#cbd5e1",  # 淡灰   — 補助線・ガイド
}
INK = INK_SCALE["ink"]
SUBTLE = INK_SCALE["dark"]
LINE = INK_SCALE["dark"]
LINE_SUB = INK_SCALE["gray"]

# 色相 8 系統 × 2 段階。淡（bg）＝塗り、濃（border）＝枠線、text＝ラベル色。
PALETTE = {
    "red":    {"bg": "#fee2e2", "border": "#ef4444", "text": "#b91c1c"},
    "orange": {"bg": "#ffedd5", "border": "#f97316", "text": "#c2410c"},
    "yellow": {"bg": "#fef9c3", "border": "#f59e0b", "text": "#b45309"},
    "green":  {"bg": "#dcfce7", "border": "#22c55e", "text": "#15803d"},
    "teal":   {"bg": "#ccfbf1", "border": "#14b8a6", "text": "#0f766e"},
    "blue":   {"bg": "#dbeafe", "border": "#3b82f6", "text": "#1d4ed8"},
    "purple": {"bg": "#ede9fe", "border": "#8b5cf6", "text": "#6d28d9"},
    "pink":   {"bg": "#fce7f3", "border": "#ec4899", "text": "#be185d"},
    "gray":   {"bg": "#f1f5f9", "border": "#94a3b8", "text": "#475569"},
}

# ---------------------------------------------------------------------------
# 線
# ---------------------------------------------------------------------------

# 線の太さ 2 段階（FigJam の細/太）。
STROKE = {"thin": 2.0, "thick": 3.5}

# 線スタイル（FigJam: 実線 / 破線）。値は stroke-dasharray（None=実線）。
DASH = {"solid": None, "dashed": "7 6", "dotted": "2 6"}

# ---------------------------------------------------------------------------
# 間隔
# ---------------------------------------------------------------------------

# 要素とラベルの間隔。「図とラベルが近すぎる」を防ぐため、直値ではなくこれを使う。
GAP = {"tight": 6, "snug": 10, "normal": 16, "loose": 24}

# 各所の既定の間隔（px）
SPACING = {
    "node_label": 10.0,   # グリフ下端 ↔ ラベルのインク上端
    "glyph_pad":   4.0,   # ノードの箱 ↔ グリフ。(w,h)=(120,88) → グリフ 80px
}

# コネクタ既定値
CLEARANCE = 6   # 図形の輪郭から線を離す距離
STUB = 18       # エルボが図形から垂直に離れてから曲がるまでの長さ
DETOUR = 28     # 素直に曲がれないときの迂回量
RADIUS = 14     # 角丸コネクタの既定半径
LABEL_PAD = 8   # ラベル両脇に空ける余白（線を切る幅に足される）


def gap_value(gap):
    """GAP のキーでも数値でも受け付けて px を返す。"""
    if isinstance(gap, str):
        return GAP[gap]
    return float(gap)


def stroke_width(weight):
    """STROKE のキーでも数値でも受け付けて px を返す。"""
    if isinstance(weight, str):
        return STROKE[weight]
    return float(weight)
