"""テキストの実寸見積もりとエスケープ。

SVG には自動改行も `textLength` の実装（librsvg）も無いので、ラベルで線を切る幅も
ベースライン計算も、ここでの見積もりに頼る。誤差は余白（LABEL_PAD）で吸収する。
"""

from .tokens import ASCENT, DESCENT, FONTS, LINE_HEIGHT, SCALE

# ---------------------------------------------------------------------------
# 文字幅テーブル（em 比）
# ---------------------------------------------------------------------------

_DEFAULT_W = 0.55
_W = {}


def _fill(chars, w):
    for ch in chars:
        _W[ch] = w


_fill(" ",                   0.28)
_fill(".,:;'`|!ilj",         0.26)
_fill("I",                   0.30)
_fill("()[]{}/\\-",          0.33)
_fill("rft",                 0.35)
_fill('"',                   0.40)
_fill("_",                   0.55)
_fill("abcdeghknopqsuvxyz",  0.55)
_fill("0123456789",          0.56)
_fill("+<=>~^*",             0.58)
_fill("JC",                  0.66)
_fill("ABEFHKLNPRSTUVXYZ",   0.68)
_fill("ODQG",                0.74)
_fill("mw",                  0.85)
_fill("MW",                  0.88)
_fill("@#%&",                0.90)

# 全角として扱う範囲（CJK・かな・全角記号・絵文字）
_FULLWIDTH = (
    (0x1100, 0x115F), (0x2E80, 0x303E), (0x3041, 0x33FF), (0x3400, 0x4DBF),
    (0x4E00, 0x9FFF), (0xA000, 0xA4CF), (0xAC00, 0xD7A3), (0xF900, 0xFAFF),
    (0xFE30, 0xFE6F), (0xFF00, 0xFF60), (0xFFE0, 0xFFE6),
    (0x2600, 0x27BF), (0x1F300, 0x1FAFF), (0x20000, 0x2FFFD),
)


def _char_w(ch, mono=False):
    o = ord(ch)
    if 0x0300 <= o <= 0x036F:       # 結合記号は幅 0
        return 0.0
    for lo, hi in _FULLWIDTH:
        if lo <= o <= hi:
            return 1.0
    if 0xFF61 <= o <= 0xFF9F:       # 半角カナ
        return 0.5
    if mono:
        return 0.60
    if o < 0x2E80:
        return _W.get(ch, _DEFAULT_W)
    return _DEFAULT_W


# ---------------------------------------------------------------------------
# 実寸
# ---------------------------------------------------------------------------

# SCALE のキーで引いた字の大きさに掛ける倍率。Canvas が「キャンバス幅 / 表示幅」から決める
# （表示で縮む分を先に拡大しておき、表示したときに SCALE どおりの px になるようにする）。
# 図は 1 スクリプト 1 キャンバスで作るので、モジュールの状態として持つ。
_TEXT_FACTOR = 1.0


def set_text_factor(k):
    global _TEXT_FACTOR
    _TEXT_FACTOR = float(k)


def text_factor():
    return _TEXT_FACTOR


def font_size(scale):
    """SCALE のキーでも数値でも受け付けて px（SVG 座標）を返す。

    キーで引いたときは text_factor() を掛ける。数値で渡したときはそのまま使う。
    """
    if isinstance(scale, str):
        return SCALE[scale][0] * _TEXT_FACTOR
    return float(scale)


def font_weight(scale):
    if isinstance(scale, str):
        return SCALE[scale][1]
    return "400"


def text_extent(s, scale="label", font=None, bold=False, weight=None):
    """描画されるテキストの外接サイズ (w, h) を px で返す。'\\n' で複数行。

    h は 1 行なら em box（size × 1.0）、複数行なら行送りぶん伸びる。
    ラベルで線を切る幅の計算に使う。
    """
    size = font_size(scale)
    base_w = font_weight(scale)
    fam = FONTS.get(font, font) or ""
    mono = "monospace" in fam
    heavy = bold or int(weight or base_w) >= 600

    lines = str(s).split("\n")
    em = max(sum(_char_w(ch, mono) for ch in line) for line in lines)
    w = em * size * (1.04 if heavy else 1.0)    # 太字はわずかに広い
    if len(lines) > 1:
        h = size * LINE_HEIGHT * len(lines)
    else:
        h = size * (ASCENT + DESCENT)
    return w, h


def text_width(s, scale="label", **kw):
    return text_extent(s, scale, **kw)[0]


def esc(s):
    """SVG テキストとして安全にする。"""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
