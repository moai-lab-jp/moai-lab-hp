# MOAI Lab Website

https://www.moai-lab.jp/ （Google サイト）と https://en.moai-lab.jp/ を、静的HTMLに作り直したサイトです。
デザインは agi.moai-lab.jp / saas.moai-lab.jp と共通の「MOAI Design System」に揃えています。
依存ライブラリはありません（Python 3 の標準ライブラリだけでビルドします）。

## 構成

```
build.py            ビルドスクリプト（共通ヘッダー・ナビ・フッターで各ページを包む）
src/assets/         style.css / main.js / img/（画像）
src/pages/          各ページの本文（HTML断片）。日本語は直下、英語は en/ 以下
site/               ビルド出力。このフォルダをそのまま公開する
```

## ビルドとプレビュー

```bash
python3 build.py
```

```bash
python3 -m http.server 8766 --directory site
```

ビルド時に、内部リンクと画像のリンク切れを自動で検査します。問題があれば一覧を表示して終了コード1で終わります。

## ページの書き方

`src/pages/` のパスがそのままURLになります。

| ファイル | URL |
| --- | --- |
| `src/pages/index.html` | `/` |
| `src/pages/demo.html` | `/demo/` |
| `src/pages/solutions/index.html` | `/solutions/` |
| `src/pages/solutions/energy-solution.html` | `/solutions/energy-solution/` |
| `src/pages/en/about/about-us.html` | `/en/about/about-us/` |

各ファイルの1行目に、メタ情報をJSONコメントで書きます。

```html
<!-- {"title": "エネルギー最適化", "description": "検索結果に出る説明文（80〜120字）", "nav": "solutions"} -->
```

- `title`：ページ名。`<title>` には自動で「 | MOAI Lab」が付きます（トップページを除く）。
- `description`：検索結果やSNSに出る説明文。
- `nav`：ヘッダーで強調するメニュー。`solutions` / `products` / `resources` / `about` / `moai-platform`（英語）。該当しなければ省略。
- `noindex`：`true` にすると検索エンジンに登録させず、サイトマップにも載せません。

本文のルール:

- リンクと画像のパスは `{{root}}` から書きます。例：`{{root}}about/contact-us/`、`{{root}}assets/img/foo.jpg`。内部リンクは末尾スラッシュ付き。`/` で始まるパスは使いません。
- 外部リンクには `target="_blank" rel="noopener"` を付けます。
- ページ内に `<h1>` は1つだけ（`.page-hero` の中）。
- ナビゲーションとフッターの項目は `build.py` の `NAV` と `TEXT` で編集します。

## 部品（style.css のクラス）

下層ページは「ページ見出し → セクション」の順に並べます。`src/pages/index.html` が実例です。

```html
<section class="page-hero">
  <div class="wrap">
    <ol class="crumbs"><li><a href="{{root}}">Home</a></li><li><a href="{{root}}solutions/">Solutions</a></li><li>エネルギー最適化</li></ol>
    <h1>エネルギー最適化</h1>
    <p class="lead">ページの概要（任意）</p>
  </div>
</section>

<section class="sec">            <!-- 交互に class="sec alt" を使うと背景色が変わる -->
  <div class="wrap">
    <div class="sec-head">       <!-- 中央寄せは class="sec-head center" -->
      <p class="section-label">英字の小見出し（任意）</p>
      <h2>セクション見出し</h2>
      <p class="lead">リード文（任意）</p>
    </div>
    ...
  </div>
</section>
```

| クラス | 用途 |
| --- | --- |
| `.prose` | 文章のかたまり（h2/h3/p/ul/ol/a/img に本文用のスタイルが付く）。幅820px。全幅は `.prose.wide`、中央寄せは `.prose.center` |
| `.grid.cols-2` `.cols-3` `.cols-4` | カードなどを並べるグリッド。狭い画面では自動で段数が減る |
| `.card` | ガラス調のカード。中に `h3`、`p.kicker`（青い小見出し）、`p`、`ul`（チェックリスト）、`a.more`。`h3` の中を `<a>` にするとカード全体がリンクになる。上端に色線を付けるなら `.card.accent` |
| `.card > .thumb` | カード上部の画像（16:10で切り抜き）。切り抜かず全体を見せるなら `.thumb.contain` |
| `.split` | 文章と画像を左右に並べる（`.split.reverse` で左右入れ替え、`.split.wide-text` で文章側を広く） |
| `.stats > .stat` | 数値の強調。`<div class="stat"><b>50か国＋</b><span>説明</span></div>` |
| `.chips` | 小さなタグの列。`<ul class="chips"><li>生産計画</li>...</ul>` |
| `.figure` | 図版。`<figure class="figure"><img ...><figcaption>...</figcaption></figure>`。図の背景を白にしない場合は `.figure.plain` |
| `.video` | 16:9 の動画埋め込み。`<div class="video"><iframe src="https://www.youtube.com/embed/ID" title="..." allowfullscreen loading="lazy"></iframe></div>` |
| `.table-wrap > table` | 表（横スクロール対応） |
| `dl.facts` | 項目と値の一覧（会社概要など）。`<dl class="facts"><dt>社名</dt><dd>株式会社MOAI Lab</dd>...</dl>` |
| `.people > .person` | メンバー紹介。`<div class="person"><img ...><h3>氏名</h3><p class="role">役職</p><p>経歴</p></div>` |
| `ul.news-list` | 日付つきの一覧。`<li><time datetime="2026-10-15">2026.10.15</time><span class="tag press">プレスリリース</span><p>本文 <a>詳細はこちら</a></p></li>`。タグの色：`.tag`（青）`.tag.press`（緑）`.tag.blog`（紫）`.tag.event`（橙） |
| `.faq > details` | 開閉式のQ&A。`<details><summary>質問</summary><div class="answer"><p>回答</p></div></details>` |
| `.cta-band` | お問い合わせへ誘導する帯。`h3` + `p` + `.actions > a.btn` |
| `.btn` `.btn.ghost` `.btn.sm` | ボタン。並べるときは `.actions` で囲む |
| `a.more` | 「詳細はこちら →」形式のテキストリンク |
| `.form-embed` | Google フォームの埋め込み。`<div class="form-embed"><iframe src="..." title="..." loading="lazy"></iframe></div>`。短いフォームは `.form-embed.short` |
| `.fade-in` | スクロールで表示されたときにふわっと出す。カードやセクション見出しに付ける |
| `.center` `.mt-s` `.mt-m` `.mt-l` `.muted` | 中央寄せ、上余白、薄い文字色 |

## 公開

`site/` を静的ホスティングに置くだけで動きます。URLは元の Google サイトと同じ構成（末尾スラッシュ付き）です。
英語ページは元の `en.moai-lab.jp` から `/en/` 以下に移しています。
