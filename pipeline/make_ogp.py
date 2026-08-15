# -*- coding: utf-8 -*-
"""OGP画像（1200x630）を生成して assets/ogp.png に保存する。一度実行してコミットすればよい。
要 Pillow（pip install pillow）と日本語フォント（Windows: 游ゴシック）。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "ogp.png"

NAVY = (7, 26, 51)
NAVY2 = (31, 58, 92)
LIME = (144, 180, 62)
WHITE = (255, 255, 255)
GRAY = (195, 209, 224)

FONT = "C:/Windows/Fonts/YuGothB.ttc"

W, H = 1200, 630
img = Image.new("RGB", (W, H), NAVY)
d = ImageDraw.Draw(img)

# 右上に斜めのアクセント帯
d.polygon([(W - 320, 0), (W, 0), (W, 320)], fill=NAVY2)
d.polygon([(W - 180, 0), (W, 0), (W, 180)], fill=LIME)

# 左のアクセントタブ
d.rectangle([70, 205, 96, 305], fill=LIME)

title = ImageFont.truetype(FONT, 110)
sub = ImageFont.truetype(FONT, 40)
small = ImageFont.truetype(FONT, 28)

d.text((130, 195), "ラクロスマニア", font=title, fill=WHITE)
d.text((132, 345), "大学ラクロスの試合結果・日程・順位表", font=sub, fill=GRAY)
d.text((132, 420), "毎日更新　|　全国7地区・男女14リーグの戦績データ", font=small, fill=GRAY)

# 下部バー
d.rectangle([0, H - 14, W, H], fill=LIME)
d.text((132, H - 92), "KANTO  LACROSSE  MEDIA", font=small, fill=LIME)

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT, "PNG")
print(f"OK: {OUT} ({OUT.stat().st_size // 1024} KB)")
