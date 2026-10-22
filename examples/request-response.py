"""実例: 「ブラウザがサーバーにリクエストしたらレスポンスが返ってくる」

イメージスキーマ = SOURCE-PATH-GOAL（往路）+ CYCLE（復路で往復）。
実行: python3 examples/request-response.py  → request-response.svg を生成。

座標を手で計算していないことに注目。node() が返す Node をそのまま link() に渡すと、
どの辺から出てどこで止めるか（＝図形やキャプションに重ならない位置）は genfig が
計算する。ラベルの位置では線に穴が開く。
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from genfig import Canvas  # noqa: E402

c = Canvas(760, 300)

# 登場物（twemoji + 段階的スケールのラベル）
browser = c.node(150, 150, "ブラウザ", emoji_cp="1f310")   # 🌐
server = c.node(610, 150, "サーバー", emoji_cp="1f5a5")    # 🖥️

# 往路: リクエスト（濃い主線）は絵文字の高さでまっすぐ
c.link(browser, server, label="リクエスト")
# 復路: レスポンス（薄い副線）はキャプションの下を回す。角は既定で角丸（ベジェ）
c.link(server, browser, label="レスポンス", primary=False,
       route="elbow", start="s", end="s")

out = pathlib.Path(__file__).parent / "request-response.svg"
print(c.save(out))
