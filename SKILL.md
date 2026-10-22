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
   なく **インライン**する（`genfig` が取得・キャッシュ・インライン化）。GitHub / markdown /
   Astro どこでも描画されるため。
2. **日本語ラベル**。フォントは FigJam の 4 ファミリー（`FONTS`: simple/formal/technical/cute）
   から選び、日本語優先で指定する。既定は `simple`（ゴシック）。
3. **段階的フォントスケール**。サイズを直書きせず `SCALE` のトークンだけを使う。FigJam の
   サイズ別名（sm/md/lg/xl/xxl ＝ 小/中/大/特大/超特大）でも、意味別名（display/title/
   heading/label/body/caption）でも引ける。図内で大きさの階層が一目で分かるようにする。
   `SCALE` の値は **表示したときの px**（下記「字の大きさと表示幅」）。
4. **FigJam 風スタイル**。淡い塗り＋濃いボーダーのシェイプ（16 種）、太さ 2 段階（thin/thick）×
   スタイル（実線/破線）を選べるコネクタ、十分な余白、8 色相 × 2 段階＋無彩色 4 段階の
   カラー（`PALETTE` / `INK_SCALE`）。
5. **座標を手で計算しない**。線は `link(nodeA, nodeB)` で結ぶ。図形の辺やラベルとの
   隙間は genfig が計算する。マージンを手で足した数値（`cx + 55` 等）が出てきたら間違い。
6. **生成後は必ず目視**。`rsvg-convert` で PNG 化して Read で確認し、はみ出し・重なり・
   見切れが無いか点検してから設置する。

## 字の大きさと表示幅

SVG はドキュメントの本文欄の幅に縮めて表示される。キャンバス 1240px の図を 720px の欄に
出すと 0.58 倍になり、13px の注記は 7.5px に見えて読めない。そこで genfig は字の大きさを
**表示したときの px** で扱う。

- `Canvas(w, h, display_width=720)`。`display_width` は図を出す欄の幅（既定は `DISPLAY_WIDTH`
  = Starlight の本文欄 45rem）。`w` がこれより広いと、`w / display_width` 倍（`c.text_k`）に字を
  拡大して書き出す。表示で縮んだあとに `SCALE` どおりの大きさになる。字を拡大したくない図
  （画面いっぱいに出す図など）は `display_width=None`
- 拡大するのは字だけ。図形・絵文字・線・隙間（`GAP` や `below(26)` の数値）は拡大しない。
  **キャンバスを広く取るほど、字に対して図形が小さく、間隔が狭くなる**
- そのため **キャンバスの幅は表示幅に近く取る（目安 720〜960）**。横に要素を 5 つ以上並べる、
  長い説明を横に並べる、といった図は、幅を広げるのではなく 2 段に折る・説明を短くする・
  要素を減らす。字の大きさは `SCALE` のトークンで決まるので、`label` を `caption` に下げて
  帳尻を合わせることもしない
- `save()` が字を点検し、問題があれば標準エラーに `[genfig] ...` を出す（`c.check()` でも取れる）。
  - 表示したときに `MIN_READABLE`（12px）より小さい字
  - キャンバスからはみ出す字
  - 重なる字、横に `MIN_TEXT_GAP`（8px）より近い字
  
  警告が出たら配置を直す。点検するのは `text()` / `node()` / `link()` のラベルなど genfig が描いた
  字だけで、`raw()` で直接書いた字や、字と図形の重なりは見ないので、PNG の目視も必ずする。
- 目視の PNG は **表示幅で書き出す**（`rsvg-convert -w 720`）。キャンバスの原寸で見ると、
  実際より字が大きく見えて小ささに気づけない

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
7. **関係の描画** — `link()` でノード同士を結び、ラベルを添える。座標は書かない。

実装としては 5〜7 を `genfig` を import した短いビルドスクリプトにまとめて SVG を生成する。

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

## 描き方（genfig を使う）

スキルディレクトリの `genfig` パッケージを import して `Canvas` で組み立てる。直接 SVG
文字列を手書きしないこと（スケール・スタイルの一貫性が崩れる）。

**鉄則: 線の座標を手で計算しない。** 図形メソッドは `Node` を返すので、線は
`link()` でノード同士を結ぶ。どの辺から出てどこで止めるかは genfig が計算する。

```python
import sys
sys.path.insert(0, "<このスキルのディレクトリ>")  # genfig パッケージのある場所
from genfig import Canvas

c = Canvas(760, 300)
browser = c.node(150, 150, "ブラウザ", emoji_cp="1f310")   # 🌐
server  = c.node(610, 150, "サーバー", emoji_cp="1f5a5")   # 🖥️
c.link(browser, server, label="リクエスト")                        # 往路（濃い）
c.link(server, browser, label="レスポンス", primary=False,
       start="s", end="s")                                         # 復路（薄い・下側）
c.save("00-thumbnail.svg")   # ← 相対パス。絶対パスは書かない
```

主な API:
- `Canvas(w, h, display_width=720)` / `.save(path)` / `.svg()` / `.check()`（字の点検。save() も呼ぶ）
- `.text(x, y, s, scale=..., align=..., fill=...)` — scale は SCALE のキーのみ。`\n` で複数行
- `.node(cx, cy, label, emoji_cp=..., icon_name=..., shape=..., color=..., w=, h=)`
  → **`Node` を返す**。`w`/`h` は箱の大きさとして実際に効く（絵文字の大きさもここから）
- `.sticky(x, y, w, h, color=...)` — FigJam 風シェイプ → `Node` を返す
- 図形: `.cylinder` `.diamond` `.hexagon` `.octagon` `.parallelogram` `.triangle`
  `.pentagon` `.cross` `.chevron` `.star` `.ellipse(cx,cy,rx,ry)` `.speech` `.cloud`
  — すべて `Node` を返す
- `.link(a, b, label=..., ...)` — 線を引く（唯一のコネクタ API）
- `.emoji(cp, x, y, size)` / `.icon(name, x, y, size)` — 単体で置きたいとき

`Node` の便利プロパティ: `.cx` `.cy` `.left` `.right` `.top` `.bottom` `.width` `.height`、
`.below(gap)` / `.above(gap)`（ノード基準でテキストのベースライン y を出す）。

### link() — 線を引く

```python
c.link(a, b, label="送る",
       route="straight",     # "straight" 直線 / "elbow" 途中で曲がる / "curve" 弧
       corner="round",       # "round" 角丸 / "sharp" 角          （elbow のとき）
       radius=None,          # None = 脚の半分（最も滑らか）。数値で頭打ち
       start="auto", end="auto",   # アンカー
       offset=0,             # 線を進行方向の左へずらす px（往復2本を並べるとき）
       primary=True,         # True 濃い主線 / False 薄い副線
       dash="solid",         # "solid" / "dashed" / "dotted"
       both=False,           # True で両端に矢印
       label_pos="on")       # "on" 線を切って間に置く / "above" / "below"
```

端点 `a` / `b` に渡せるもの:

| 書き方 | 意味 |
|---|---|
| `node` | ノード。アンカーは `start=` / `end=` |
| `(node, "e")` | 端点ごとにアンカーを指定 |
| `(420, 186)` | 絶対座標（クリップなし）。ノードが無い所を指すとき |

アンカー（`start=` / `end=` / タプルの 2 番目）:

| 指定 | 意味 |
|---|---|
| `"auto"`（既定）/ `"c"` | **中心アンカー**。相手の中心へ向かう線を、図形の輪郭で切る |
| `"n" "ne" "e" "se" "s" "sw" "w" "nw"` | 8 方位。その辺から出る |
| `45` | 任意角度（度・0 = 東・時計回り） |
| `(dx, dy)` | 任意方向ベクトル |

**線は図形に重ならない。** アンカー位置は輪郭との交点から求め、図形に食い込む部分は
落とす。絵文字ノードは*キャプションまで含めた箱*で止まるので、ラベルを矢印が
突き抜けない。

### 往復 2 本を並べる（CYCLE スキーマの定番）

`offset` は線を**進行方向の左**へずらす。往路と復路に**同じ値**を渡すと互いに
反対側へ分かれるので、2 本が重ならない。y 座標を手で 2 レーンに分ける必要はない。

```python
c.link(browser, server, label="リクエスト", offset=24)
c.link(server, browser, label="レスポンス", offset=24, primary=False)
```

### ラベルは線を切る

`label_pos="on"`（既定）では、ラベルの位置で**線に穴が開く**（`─── ラベル ──▶`）。
穴の幅はラベルの箱を**線の向きに射影した長さ**なので、

- 横線 → 文字の**幅**ぶん切れる
- 縦線 → 文字の**高さ**ぶん切れる
- 斜線 → 両方が効く

エルボでは既定で**最も長い直線区間の中央**に置く（角の上に載らないように）。
`label_at="mid"` で弧長の中点、`label_at=0.25` で割合指定。入る隙間が無いときは
自動で線の横（`"above"`）に逃げる。

完全な実例は `examples/request-response.py`、全パターンの見本は
`examples/connectors.py`（生成すると 1 枚の確認用シートになる）。
スケール/カラー/間隔トークンの定義は `genfig/tokens.py`、スキーマは `reference/` を読むこと。

## 生成 → 確認 → 設置

**ビルドスクリプトは最終的な設置先（`images/`）に置き、そこを作業ディレクトリにして走らせる。**
スクリプト内のパスはすべて **相対パス**で書くこと。

```sh
cd <ドキュメントと同階層の images ディレクトリ>
python3 00-thumbnail.py                    # SVG 生成（同ディレクトリに出力）
rsvg-convert 00-thumbnail.svg -w 720 -o 00-thumbnail.png   # 表示幅で PNG 化（別のSVGレンダラでも可）
```

パスの原則:
- `c.save(...)` は **`"00-thumbnail.svg"` のような相対パス**にする。
  `/Users/...` から始まる絶対パスを書かない（リポジトリを移動・共有すると壊れるため）。
- 出力ファイル名は元になる markdown / 図の役割に対応させる（例: `00-thumbnail.svg`）。
- 例外は `sys.path.insert()` に渡す **genfig パッケージのあるスキルディレクトリだけ**。ここは
  リポジトリ外なので絶対パス（`~` 展開済み）で構わない。
- 確認用 PNG は一時ファイル。点検が済んだら消すか、リポジトリに置くなら意図して残す。

`[genfig]` の警告が無く、PNG を Read して点検して問題なければ、そのまま設置完了。ドキュメント用途では原則
**LECTURE/記事と同階層の `images/` フォルダ**に置き、markdown から相対パスで参照する。
画像の直前に生成仕様、直後に `*図: ...*` のキャプションを添えると後で再生成しやすい。

## スキーマ早見

SOURCE-PATH-GOAL / LINK / CYCLE / CONTAINER / VERTICALITY / CENTER-PERIPHERY /
PART-WHOLE / FORCE系(COMPULSION・BLOCKAGE・COUNTERFORCE) / BALANCE / SCALE /
SPLITTING / NEAR-FAR / CONTACT — 認識の手がかりとレイアウト指針は
`reference/schemas.md` を参照。
