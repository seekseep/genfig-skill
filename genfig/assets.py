"""twemoji（カラー絵文字）と Lucide（ラインアイコン）の取得・キャッシュ・インライン化。

外部 href は GitHub 等で描画がブロックされるため、SVG に必ずインラインする。
キャッシュはスキルディレクトリ直下（このパッケージの 1 つ上）に置く。
"""

import pathlib
import re
import urllib.request

from .tokens import INK_SCALE

# パッケージの 1 つ上＝スキルディレクトリ。キャッシュはここに置く。
_SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent

_CACHE = _SKILL_DIR / ".twemoji-cache"
_CDN = "https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/svg/{}.svg"

_ICON_CACHE = _SKILL_DIR / ".lucide-cache"
_ICON_CDN = "https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/{}.svg"

# 呼びやすい別名 → Lucide のファイル名。未登録の名前はそのまま Lucide 名として扱う。
ICON_ALIASES = {
    "activity": "activity", "pulse": "activity",
    "archive": "archive", "box-archive": "archive",
    "key": "key",
    "comment": "message-circle", "speech": "message-circle", "chat": "message-circle",
    "cloud": "cloud",
    "cpu": "cpu", "chip": "cpu",
    "database": "database", "db": "database",
    "monitor": "monitor", "display": "monitor", "screen": "monitor",
    "mail": "mail", "envelope": "mail", "email": "mail",
    "file": "file-text", "doc": "file-text", "document": "file-text",
    "code": "code",
    "zap": "zap", "lightning": "zap", "bolt": "zap",
    "pin": "map-pin", "location": "map-pin", "map-pin": "map-pin",
    "phone": "smartphone", "mobile": "smartphone", "smartphone": "smartphone",
    "package": "package", "parcel": "package",
    "dollar": "circle-dollar-sign", "money": "circle-dollar-sign", "price": "circle-dollar-sign",
    "shield": "shield", "security": "shield",
    "send": "send", "paper-plane": "send",
    "server": "server",
    "box": "box", "cube": "box",
    "settings": "settings", "gear": "settings", "config": "settings",
    "hard-drive": "hard-drive", "disk": "hard-drive", "storage": "hard-drive",
    "terminal": "terminal", "console": "terminal", "shell": "terminal",
    "user": "user", "person": "user", "account": "user",
    "wallet": "wallet", "card": "credit-card",
    "globe": "globe", "world": "globe", "internet": "globe",
}


def _norm_cp(cp):
    """'1f310' でも '🌐' でも受け付けて twemoji のファイル名 codepoint に正規化する。"""
    if all(c in "0123456789abcdef-" for c in cp.lower()):
        return cp.lower()
    # 絵文字文字列 → コードポイント列（twemoji 慣習で fe0f は落とす）
    pts = [f"{ord(ch):x}" for ch in cp if ord(ch) != 0xFE0F]
    return "-".join(pts)


def _svg_inner(raw):
    """SVG 文字列から外周 <svg ...>…</svg> を剥がして中身だけ返す。
    先頭の XML 宣言・ライセンスコメントや複数行の開始タグも吸収する。"""
    inner = re.sub(r"^.*?<svg\b[^>]*>", "", raw, flags=re.S)
    inner = re.sub(r"</svg>\s*$", "", inner)
    return inner


def fetch_emoji_raw(cp):
    """twemoji の生 SVG を取得（ローカルキャッシュ）。cp は hex か絵文字文字列。"""
    name = _norm_cp(cp)
    _CACHE.mkdir(exist_ok=True)
    f = _CACHE / f"{name}.svg"
    if not f.exists():
        with urllib.request.urlopen(_CDN.format(name), timeout=20) as r:
            f.write_bytes(r.read())
    return f.read_text(encoding="utf-8")


def emoji(cp, x, y, size):
    """twemoji を nested <svg> としてインライン配置する文字列を返す。"""
    inner = _svg_inner(fetch_emoji_raw(cp).strip())
    return (f'<svg x="{x:.1f}" y="{y:.1f}" width="{size:.1f}" height="{size:.1f}" '
            f'viewBox="0 0 36 36">{inner}</svg>')


def fetch_icon_raw(name):
    """Lucide のラインアイコン生 SVG を取得（ローカルキャッシュ）。"""
    fname = ICON_ALIASES.get(name, name)
    _ICON_CACHE.mkdir(exist_ok=True)
    f = _ICON_CACHE / f"{fname}.svg"
    if not f.exists():
        with urllib.request.urlopen(_ICON_CDN.format(fname), timeout=20) as r:
            f.write_bytes(r.read())
    return f.read_text(encoding="utf-8")


def icon(name, x, y, size, color=None, stroke=2.0):
    """Lucide ラインアイコンを nested <svg> としてインライン配置する文字列を返す。
    Lucide は stroke="currentColor" なので、外周 svg に stroke 属性を再付与して色を効かせる。
    name は ICON_ALIASES のキー（'database' 等）か Lucide 名そのまま。
    """
    if color is None:
        color = INK_SCALE["dark"]
    inner = _svg_inner(fetch_icon_raw(name).strip())
    return (f'<svg x="{x:.1f}" y="{y:.1f}" width="{size:.1f}" height="{size:.1f}" '
            f'viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="{stroke}" stroke-linecap="round" '
            f'stroke-linejoin="round">{inner}</svg>')