---
name: genfig
description: 自然文を「イメージスキーマ（身体経験に根ざす空間構造）」に写像し、twemoji を登場物にした FigJam 風の SVG 図を生成する。ドキュメント執筆中に概念図・構成図・フロー図を手早く挿入したいときに使う。「/genfig <説明>」「〜の図を作って」「この説明に図を入れて」のような依頼で発火。
---

# genfig — イメージスキーマ図ジェネレータ

自然文の説明を **イメージスキーマ**（Johnson『The Body in the Mind』, Lakoff & Johnson
『Metaphors We Live By』『Philosophy in the Flesh』に由来する、身体経験から繰り返し立ち
あらわれる空間構造）に写像し、その構造を **twemoji を登場物にした SVG 図**として描く。

例: 「ブラウザがサーバーにリクエストしたらレスポンスが返ってくる」
→ SOURCE-PATH-GOAL（起点→経路→着点）+ CYCLE（往復）→ 左右2ノード＋往復2矢印の図。

## 出力の鉄則

1. **SVG 単体・自己完結**。twemoji（カラー絵文字）も Lucide（ラインアイコン）も外部 href では
   なく **インライン**する（`genfig.py` が取得・キャッシュ・インライン化）。GitHub / markdown /
   Astro どこでも描画されるため。
2. **日本語ラベル**。フォントは FigJam の 4 ファミリー（`FONTS`: simple/formal/technical/cute）
   から選び、日本語優先で指定する。既定は `simple`（ゴシック）。
3. **段階的フォントスケール**。サイズを直書きせず `SCALE` のトークンだけを使う。FigJam の
   サイズ別名（sm/md/lg/xl/xxl ＝ 小/中/大/特大/超特大）でも、意味別名（display/title/
   heading/label/body/caption）でも引ける。図内で大きさの階層が一目で分かるようにする。
4. **FigJam 風スタイル**。淡い塗り＋濃いボーダーのシェイプ（16 種）、太さ 2 段階（thin/thick）×
   スタイル（実線/破線）を選べるコネクタ、十分な余白、8 色相 × 2 段階＋無彩色 4 段階の
   カラー（`PALETTE` / `INK_SCALE`）。
5. **生成後は必ず目視**。`rsvg-convert` で PNG 化して Read で確認し、はみ出し・重なり・
   見切れが無いか点検してから設置する。

## 手順（7ステップ）

図の生成は次の順で考える。前半（1〜4）が「何を描くか」の決定、後半（5〜7）が「どう描くか」。

1. **要素の取り出し** — 説明文から登場物(entity)を列挙する。
2. **関係の決定** — 文を元に要素間の関係（送る/含む/分ける/対抗 等）を洗い出す。
   ここでイメージスキーマを判定する（複数の合成可）。`reference/schemas.md` 参照。
3. **要素数の決定** — 図に実際に出す要素を絞る。多すぎると伝わらないので主役を選ぶ
   （目安 2〜6 個）。省いた要素はキャプションで補える。
4. **描画する関係の決定** — 出す関係を絞り、各関係の向き・主従（往路/復路、強/弱）を決める。
5. **絵文字と図形の決定** — 各要素に twemoji を割り当てる（`reference/twemoji.md`）。
   **絵文字でうまく表せない概念は FigJam 風の図形で代替する**（下記「絵文字 vs 図形」）。
6. **要素の配置** — スキーマのレイアウト指針に従い座標を決める。十分な余白を取る。
7. **関係の描画** — `connector`/`biconnector` で関係を結び、ラベルを添える。

実装としては 5〜7 を `genfig.py` を import した短いビルドスクリプトにまとめて SVG を生成する。

## 絵文字 vs 図形

要素は「絵文字」または「図形」で表す。**まず絵文字を試し、適切な絵文字が無い・抽象的すぎる
場合に図形にフォールバックする**。両者は `node()` で統一的に置ける。

| 表したいもの | 手段 | genfig での描き方 |
|---|---|---|
| 具体物（ブラウザ・鍵・ファイル等） | twemoji | `emoji()` / `node(emoji_cp=...)` |
| データベース | シリンダー | `cylinder()` / `node(shape="cylinder")` |
| 判断・分岐 | ひし形 | `diamond()` / `node(shape="diamond")` |
| 処理・サービス単位 | 六角形 | `hexagon()` |
| 入出力・データの流れ | 平行四辺形 | `parallelogram()` |
| 開始/終了・アクター・状態 | 円/楕円 | `ellipse()` |
| インターネット・外部 | 雲 | `cloud()` |
| 枠・グループ・コンテナ | 角丸シェイプ | `sticky()` |

図形には FigJam 風の付箋カラー（`PALETTE`）を塗る。図形＋絵文字の併用も可
（例: シリンダーの中に🗄️）。`node(shape=..., emoji_cp=...)`。

## 描き方（genfig.py を使う）

スキルディレクトリの `genfig.py` を import して `Canvas` で組み立てる。直接 SVG 文字列を
手書きしないこと（スケール・スタイルの一貫性が崩れる）。

```python
import sys
sys.path.insert(0, "<このスキルのディレクトリ>")  # genfig.py のある場所
from genfig import Canvas

c = Canvas(760, 300)
c.emoji("1f310", 80, 110, 80)                       # 🌐 ブラウザ
c.text(120, 215, "ブラウザ", scale="heading")
c.emoji("1f5a5", 600, 110, 80)                      # 🖥️ サーバー
c.text(640, 215, "サーバー", scale="heading")
c.connector(190, 120, 565, 120, label="リクエスト", primary=True)   # 往路（濃い）
c.connector(570, 180, 195, 180, label="レスポンス", primary=False)  # 復路（薄い）
c.save("out.svg")
```

主な API:
- `Canvas(w, h)` / `.save(path)` / `.svg()`
- `.emoji(cp, x, y, size)` — cp は `"1f310"` でも `"🌐"` でも可
- `.text(x, y, s, scale=..., anchor=..., fill=...)` — scale は SCALE のキーのみ
- `.sticky(x, y, w, h, color=...)` — FigJam 風シェイプ（color は PALETTE のキー）
- 図形: `.cylinder` `.diamond` `.hexagon` `.parallelogram` `.ellipse(cx,cy,rx,ry)` `.cloud`
- `.node(cx, cy, label, emoji_cp=..., shape=..., color=...)` — 要素を絵文字 or 図形で1個置く
- `.connector(x1,y1,x2,y2, label=..., primary=..., curve=...)` — 片方向矢印
- `.biconnector(x1,y1,x2,y2)` — 両方向矢印（層間の往復など）

完全な実例は `examples/request-response.py`。スケール/カラー/スキーマの定義は
`genfig.py` 冒頭と `reference/` を読むこと。

## 生成 → 確認 → 設置

```sh
cd <スキルのディレクトリ>
python3 <ビルドスクリプト>.py            # SVG 生成
rsvg-convert out.svg -o out.png          # PNG 化（無ければ別のSVGレンダラ可）
```
PNG を Read して点検 → 問題なければ目的地へ。ドキュメント用途では原則
**LECTURE/記事と同階層の `images/` フォルダ**に置き、markdown から相対パスで参照する。
画像の直前に生成仕様、直後に `*図: ...*` のキャプションを添えると後で再生成しやすい。

## スキーマ早見

SOURCE-PATH-GOAL / LINK / CYCLE / CONTAINER / VERTICALITY / CENTER-PERIPHERY /
PART-WHOLE / FORCE系(COMPULSION・BLOCKAGE・COUNTERFORCE) / BALANCE / SCALE /
SPLITTING / NEAR-FAR / CONTACT — 認識の手がかりとレイアウト指針は
`reference/schemas.md` を参照。
