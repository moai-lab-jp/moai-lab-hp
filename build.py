#!/usr/bin/env python3
"""MOAI Lab サイトのビルドスクリプト（Python 3 標準ライブラリのみ）。

src/pages/ 以下の本文HTML断片を、共通のヘッダー・ナビ・フッターで包んで site/ に出力する。

- src/pages/index.html            -> site/index.html                 (URL: /)
- src/pages/demo.html             -> site/demo/index.html            (URL: /demo/)
- src/pages/solutions/index.html  -> site/solutions/index.html       (URL: /solutions/)
- src/pages/en/...                -> site/en/...                     (英語ページ)

各断片の先頭には、メタ情報を1行のJSONコメントで書く:

    <!-- {"title": "ページ名", "description": "検索結果に出る説明文", "nav": "solutions"} -->

本文中の {{root}} は、そのページから見たサイトのルートへの相対パスに置き換わる。
内部リンクは {{root}}solutions/energy-solution/ のように末尾スラッシュ付きで書く。

使い方:  python3 build.py
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
PAGES = os.path.join(SRC, "pages")
OUT = os.path.join(HERE, "site")

BASE_URL = "https://www.moai-lab.jp"
SITE_NAME = {"ja": "MOAI Lab", "en": "MOAI Lab"}
OG_IMAGE = "assets/img/og-image.png"  # src/assets/img/ に置けば自動で使われる

# ---------------------------------------------------------------- ナビゲーション
# (ラベル, リンク先) または (ラベル, [子項目...], navキー)。http で始まるものは外部リンク。
NAV = {
    "ja": [
        ("Home", ""),
        ("Solutions", [
            ("ソリューション一覧", "solutions/"),
            ("Supply Chain最適化", "solutions/supply-chain-design-solution/"),
            ("需要予測と在庫最適化", "solutions/forecasting-inventory-solution/"),
            ("生産／製造最適化", "solutions/manufacturing-solution/"),
            ("輸送／配送最適化", "solutions/distribution-solution/"),
            ("人員配置最適化", "solutions/workforce-planning-solution/"),
            ("エネルギー最適化", "solutions/energy-solution/"),
            ("防災計画最適化", "solutions/humanitarian_logistics/"),
        ], "solutions"),
        ("Products", [
            ("MOAI Platform", "products/moai-platform/"),
            ("MOAI SaaS", "https://saas.moai-lab.jp/"),
            ("AGI4OPT", "https://agi.moai-lab.jp/"),
            ("AMPL", "products/ampl/"),
        ], "products"),
        ("セミナー", "seminar/"),
        ("デモ", "demo/"),
        ("Resources", [
            ("News", "resources/news/"),
            ("技術紹介", "resources/technology-intro/"),
            ("ブログ", "resources/blog/"),
            ("FAQs", "resources/faqs/"),
        ], "resources"),
        ("About", [
            ("企業情報", "about/about-us/"),
            ("お問い合わせ", "about/contact-us/"),
            ("資料ダウンロード", "about/service_pamphlet_download/"),
            ("商品・サービス利用規約", "about/eula/"),
        ], "about"),
    ],
    "en": [
        ("Home", "en/"),
        ("MOAI Platform", [
            ("Supply Chain Optimization", "en/moai-platform/supply-chain-optimization-platform/"),
            ("Energy Optimization", "en/moai-platform/energy-optimization-platform/"),
            ("Workforce Optimization", "en/moai-platform/workforce-planning-platform/"),
        ], "moai-platform"),
        ("About Us", "en/about/about-us/"),
        ("Contact Form", "en/about/contact-us/"),
    ],
}

TEXT = {
    "ja": {
        "skip": "本文へ移動", "menu": "メニュー", "contact": "お問い合わせ", "contact_href": "about/contact-us/",
        "lang_label": "English", "lang_href": "en/", "home_href": "",
        "tagline": "数理最適化（MO）とAIを融合した「MOAI Technology」で、ビジネスの意思決定を最適化します。",
        "copyright": "MOAI Lab Inc. 2024-2026",
        "foot_cta": [
            ("無料相談", "モジュールやスキルなどの個別機能から、完成品のSaaSまで、クラウド、API連携、オンプレミスに柔軟に対応。企業規模や導入目的に応じた最適なプランをご提案します。", "無料相談", "about/contact-us/"),
            ("メーリングリスト", "MOAI Labの最適化に関するブログ、イベント、商品の最新情報をお送りさせていただきます。", "メーリングリスト登録", "about/mailinglist/"),
            ("資料ダウンロード", "商品・サービス紹介資料をダウンロードいただけます。", "資料ダウンロード", "about/service_pamphlet_download/"),
        ],
        "foot_legal": [("情報セキュリティポリシー", "about/security-policy/"), ("プライバシーポリシー", "about/privacy-policy/"), ("商品・サービス利用規約", "about/eula/")],
    },
    "en": {
        "skip": "Skip to main content", "menu": "Menu", "contact": "Contact", "contact_href": "en/about/contact-us/",
        "lang_label": "日本語", "lang_href": "", "home_href": "en/",
        "tagline": "MOAI Technology fuses Mathematical Optimization (MO) and AI to optimize business decision-making.",
        "copyright": "MOAI Lab Inc. 2024-2026",
        "foot_cta": [],
        "foot_legal": [("Privacy Policy", "en/about/privacy-policy/")],
    },
}

# 日本語と英語で対になるページ（hreflang 用）。キーは日本語側のURLパス。
ALTERNATES = {
    "": "en/",
    "about/about-us/": "en/about/about-us/",
    "about/contact-us/": "en/about/contact-us/",
    "about/privacy-policy/": "en/about/privacy-policy/",
}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900'
         '&family=Noto+Sans+JP:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">')


def esc(s):
    return html.escape(s, quote=True)


def is_ext(href):
    return href.startswith(("http://", "https://", "mailto:"))


def link(label, href, root, current, cls=""):
    """ナビ用の <a> を返す。外部リンクは別タブで開く。"""
    attrs = f' class="{cls}"' if cls else ""
    if is_ext(href):
        return f'<a{attrs} href="{esc(href)}" target="_blank" rel="noopener">{esc(label)}</a>'
    cur = ' aria-current="page"' if href == current else ""
    return f'<a{attrs} href="{root}{href}"{cur}>{esc(label)}</a>'


def render_nav(lang, root, current, nav_key):
    parts = []
    for item in NAV[lang]:
        if isinstance(item[1], list):
            label, children, key = item
            cur = " current" if key == nav_key else ""
            drop = "".join(link(l, h, root, current) for l, h in children)
            parts.append(f'<div class="nav-item{cur}"><button type="button" aria-expanded="false">{esc(label)}</button>'
                         f'<div class="nav-drop">{drop}</div></div>')
        else:
            parts.append(link(item[0], item[1], root, current))
    return "\n        ".join(parts)


def render_footer(lang, root):
    t = TEXT[lang]
    cta = ""
    if t["foot_cta"]:
        cards = "".join(
            f'<div class="card"><h3>{esc(h)}</h3><p>{esc(p)}</p>'
            f'<a class="btn sm" href="{root}{href}">{esc(b)}</a></div>'
            for h, p, b, href in t["foot_cta"])
        cta = f'<div class="foot-cta"><div class="wrap"><div class="grid cols-3">{cards}</div></div></div>'
    cols = []
    for item in NAV[lang]:
        if isinstance(item[1], list):
            lis = "".join(f"<li>{link(l, h, root, None)}</li>" for l, h in item[1])
            cols.append(f"<div><h2>{esc(item[0])}</h2><ul>{lis}</ul></div>")
    singles = "".join(f"<li>{link(i[0], i[1], root, None)}</li>" for i in NAV[lang] if not isinstance(i[1], list))
    if lang == "ja":
        singles += f'<li>{link("メーリングリスト", "about/mailinglist/", root, None)}</li>'
    singles += f'<li>{link(t["lang_label"], t["lang_href"], root, None)}</li>'
    cols.append(f"<div><h2>Menu</h2><ul>{singles}</ul></div>")
    legal = "".join(link(l, h, root, None) for l, h in t["foot_legal"])
    return f"""<footer class="site-foot">
    {cta}
    <div class="wrap foot-main">
      <div class="foot-brand">
        <a class="brand" href="{root}{t['home_href']}"><img src="{root}assets/img/moai-logo.png" alt="" width="39" height="34"><span class="mark">MOAI Lab</span></a>
        <p>{esc(t['tagline'])}</p>
      </div>
      {''.join(cols)}
    </div>
    <div class="wrap foot-bottom">
      <span>© {esc(t['copyright'])}</span>
      <nav aria-label="Legal">{legal}</nav>
    </div>
  </footer>"""


def page_url(rel):
    """src/pages からの相対パス -> サイト内のURLパス（先頭スラッシュなし、末尾スラッシュあり）。"""
    rel = rel.replace(os.sep, "/")
    if rel.endswith("index.html"):
        return rel[: -len("index.html")]
    return rel[: -len(".html")] + "/"


def read_fragment(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"\s*<!--\s*(\{.*?\})\s*-->", text, re.S)
    if not m:
        sys.exit(f"メタ情報のJSONコメントがありません: {path}")
    try:
        meta = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        sys.exit(f"メタ情報のJSONが壊れています: {path}: {e}")
    return meta, text[m.end():].strip()


def last_modified(path):
    """git の最終コミット日。未コミットなら今日の日付。"""
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", path], cwd=HERE,
                             capture_output=True, text=True, timeout=10).stdout.strip()
        if out:
            return out
    except Exception:
        pass
    return date.today().isoformat()


def render(url, meta, body, has_og):
    lang = "en" if url == "en/" or url.startswith("en/") else "ja"
    t = TEXT[lang]
    depth = url.count("/")
    root = "../" * depth
    is_home = url in ("", "en/")
    title = meta["title"] if is_home else f'{meta["title"]} | {SITE_NAME[lang]}'
    desc = meta.get("description", "")
    canonical = f"{BASE_URL}/{url}"
    body = body.replace("{{root}}", root)

    alt = ""
    pairs = {**ALTERNATES, **{v: k for k, v in ALTERNATES.items()}}
    if url in pairs:
        ja, en = (url, pairs[url]) if lang == "ja" else (pairs[url], url)
        alt = (f'\n  <link rel="alternate" hreflang="ja" href="{BASE_URL}/{ja}">'
               f'\n  <link rel="alternate" hreflang="en" href="{BASE_URL}/{en}">'
               f'\n  <link rel="alternate" hreflang="x-default" href="{BASE_URL}/{ja}">')
    lang_href = pairs.get(url, t["lang_href"])

    og_img = (f'\n  <meta property="og:image" content="{BASE_URL}/{OG_IMAGE}">'
              f'\n  <meta name="twitter:image" content="{BASE_URL}/{OG_IMAGE}">') if has_og else ""
    ld = ""
    if is_home:
        ld = '\n  <script type="application/ld+json">' + json.dumps({
            "@context": "https://schema.org", "@graph": [
                {"@type": "Organization", "@id": BASE_URL + "/#org", "name": "株式会社MOAI Lab",
                 "alternateName": "MOAI Lab Inc.", "url": BASE_URL + "/",
                 "logo": BASE_URL + "/assets/img/moai-logo.png",
                 "sameAs": ["https://www.youtube.com/@MOAI_Lab", "https://note.com/moai_lab"]},
                {"@type": "WebSite", "@id": BASE_URL + "/#website", "url": BASE_URL + "/",
                 "name": "MOAI Lab", "inLanguage": lang, "publisher": {"@id": BASE_URL + "/#org"}},
            ]}, ensure_ascii=False) + "</script>"
    robots = "noindex, follow" if meta.get("noindex") else "index, follow, max-image-preview:large"

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}">
  <meta name="robots" content="{robots}">
  <link rel="canonical" href="{canonical}">{alt}
  <meta property="og:type" content="{'website' if is_home else 'article'}">
  <meta property="og:site_name" content="{SITE_NAME[lang]}">
  <meta property="og:locale" content="{'ja_JP' if lang == 'ja' else 'en_US'}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(desc)}">{og_img}
  <meta name="twitter:card" content="{'summary_large_image' if has_og else 'summary'}">
  <meta name="theme-color" content="#0a0e1a">
  <link rel="icon" href="{root}assets/img/moai-logo.png">
  {FONTS}
  <link rel="stylesheet" href="{root}assets/style.css">{ld}
  <script>document.documentElement.classList.add('js')</script>
</head>
<body>
  <a class="skip" href="#main">{t['skip']}</a>
  <header class="site-head">
    <div class="wrap">
      <a class="brand" href="{root}{t['home_href']}" aria-label="MOAI Lab">
        <img src="{root}assets/img/moai-logo.png" alt="" width="39" height="34">
        <span class="mark">MOAI Lab</span>
      </a>
      <button class="nav-toggle" type="button" aria-label="{t['menu']}" aria-expanded="false" aria-controls="site-nav"><span></span><span></span><span></span></button>
      <nav class="site-nav" id="site-nav" aria-label="{t['menu']}">
        {render_nav(lang, root, url, meta.get('nav'))}
        <a class="lang" href="{root}{lang_href}" lang="{'en' if lang == 'ja' else 'ja'}">{t['lang_label']}</a>
      </nav>
      <a class="btn sm head-cta" href="{root}{t['contact_href']}">{t['contact']}</a>
    </div>
  </header>
  <main id="main">
{body}
  </main>
  {render_footer(lang, root)}
  <script src="{root}assets/main.js" defer></script>
</body>
</html>
"""


def check_links(pages):
    """生成したHTMLの内部リンク・画像が、実在するファイルを指しているか確かめる。"""
    problems = []
    for url, out_path in pages:
        with open(out_path, encoding="utf-8") as f:
            text = f.read()
        base = os.path.dirname(out_path)
        for attr, target in re.findall(r'\b(href|src)="([^"]*)"', text):
            if not target or is_ext(target) or target.startswith(("#", "tel:", "data:", "//")):
                continue
            path = target.split("#")[0].split("?")[0]
            if path.startswith("/"):
                problems.append(f"/{url}: ルート相対のリンクは使えません（{{{{root}}}} を使う）: {target}")
                continue
            full = os.path.normpath(os.path.join(base, path))
            if os.path.isdir(full):
                full = os.path.join(full, "index.html")
            if not os.path.exists(full):
                problems.append(f"/{url}: リンク切れ {attr}=\"{target}\"")
        if "{{" in text:
            problems.append(f"/{url}: 置換されていない {{{{...}}}} が残っています")
    return problems


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(SRC, "assets"), os.path.join(OUT, "assets"))
    for extra in os.listdir(os.path.join(SRC, "static")) if os.path.isdir(os.path.join(SRC, "static")) else []:
        shutil.copy(os.path.join(SRC, "static", extra), os.path.join(OUT, extra))
    has_og = os.path.exists(os.path.join(SRC, OG_IMAGE))

    pages, sitemap = [], []
    for dirpath, _, files in os.walk(PAGES):
        for name in sorted(files):
            if not name.endswith(".html"):
                continue
            src = os.path.join(dirpath, name)
            url = page_url(os.path.relpath(src, PAGES))
            meta, body = read_fragment(src)
            out_path = os.path.join(OUT, url, "index.html")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(render(url, meta, body, has_og))
            pages.append((url, out_path))
            if not meta.get("noindex"):
                sitemap.append((url, last_modified(src)))

    sitemap.sort()
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for url, mod in sitemap:
            f.write(f"  <url><loc>{esc(BASE_URL + '/' + url)}</loc><lastmod>{mod}</lastmod></url>\n")
        f.write("</urlset>\n")
    with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n")

    problems = check_links(pages)
    print(f"{len(pages)} ページを site/ に出力しました。")
    if problems:
        print(f"\n問題が {len(problems)} 件あります:")
        for p in problems:
            print("  -", p)
        sys.exit(1)


if __name__ == "__main__":
    main()
