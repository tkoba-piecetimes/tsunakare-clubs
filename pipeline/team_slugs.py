# -*- coding: utf-8 -*-
"""チーム名 → URLスラッグの対応表とスラッグ解決ロジック。

解決順: 1) 手動登録の対応表  2) pykakasiによるローマ字化  3) ハッシュフォールバック
手動登録が最優先なので、自動生成のスラッグが気に入らない場合はここに追記すれば
次回生成時にURLが変わる（=リダイレクトが必要になる）点に注意。
"""
import re
import sys

TEAM_SLUGS = {
    # ---- 関東（男子38回リーグ登録チーム）----
    "早稲田大学": "waseda",
    "慶應義塾大学": "keio",
    "中央大学": "chuo",
    "明治大学": "meiji",
    "成蹊大学": "seikei",
    "獨協大学": "dokkyo",
    "法政大学": "hosei",
    "明治学院大学": "meijigakuin",
    "学習院大学": "gakushuin",
    "青山学院大学": "aoyamagakuin",
    "日本体育大学": "nittaidai",
    "一橋大学": "hitotsubashi",
    "成城大学": "seijo",
    "東京農業大学": "tokyo-nodai",
    "東京大学": "tokyo",
    "東洋大学": "toyo",
    "千葉大学": "chiba",
    "帝京大学": "teikyo",
    "武蔵大学": "musashi",
    "横浜国立大学": "yokohama-kokudai",
    "立教大学": "rikkyo",
    "東海大学": "tokai",
    "国士舘大学": "kokushikan",
    "東京学芸大学": "tokyo-gakugei",
    "神奈川大学": "kanagawa",
    "東京理科大学": "tokyo-rika",
    "上智大学": "sophia",
    "埼玉大学": "saitama",
    "慶應義塾高校": "keio-hs",
    "筑波大学": "tsukuba",
    "明星大学": "meisei",
    "東京経済大学": "tokyo-keizai",
    "大東文化大学": "daitobunka",
    "専修大学": "senshu",
    "駒澤大学": "komazawa",
    "城西・関東学院": "josai-kantogakuin",
    "日本大学": "nihon",
    # 過去年度・他リーグで登場
    "城西大学": "josai",
    "関東学院大学": "kantogakuin",
    "玉川・関東学院・淑徳": "tamagawa-kantogakuin-shukutoku",
    "玉川・群馬": "tamagawa-gunma",
    "玉川大学": "tamagawa",
    "群馬大学": "gunma",
    "淑徳大学": "shukutoku",
    # ---- 関東女子でよく登場する大学 ----
    "日本女子大学": "nihon-joshi",
    "東京女子大学": "tokyo-joshi",
    "津田塾大学": "tsudajuku",
    "聖心女子大学": "seishin-joshi",
    "白百合女子大学": "shirayuri",
    "大妻女子大学": "otsuma",
    "昭和女子大学": "showa-joshi",
    "学習院女子大学": "gakushuin-joshi",
    "東洋英和女学院大学": "toyo-eiwa",
    "フェリス女学院大学": "ferris",
    "清泉女子大学": "seisen",
    "共立女子大学": "kyoritsu-joshi",
    "実践女子大学": "jissen-joshi",
    "跡見学園女子大学": "atomi",
    "神田外語大学": "kanda-gaigo",
    "東京外国語大学": "tokyo-gaigo",
    "お茶の水女子大学": "ochanomizu",
    "立正大学": "rissho",
    "國學院大學": "kokugakuin",
    "國學院大学": "kokugakuin",
    "順天堂大学": "juntendo",
    "芝浦工業大学": "shibaura",
    "電気通信大学": "denki-tsushin",
    "首都大学東京": "shutodai",
    "東京都立大学": "tokyo-metropolitan",
    # ---- 関西 ----
    "京都大学": "kyoto",
    "大阪大学": "osaka",
    "神戸大学": "kobe",
    "関西学院大学": "kwansei-gakuin",
    "同志社大学": "doshisha",
    "立命館大学": "ritsumeikan",
    "関西大学": "kansai",
    "大阪経済大学": "osaka-keizai",
    "龍谷大学": "ryukoku",
    "京都産業大学": "kyoto-sangyo",
    "近畿大学": "kindai",
    "甲南大学": "konan",
    "大阪公立大学": "osaka-metropolitan",
    "和歌山大学": "wakayama",
    "兵庫県立大学": "hyogo-kenritsu",
    "武庫川女子大学": "mukogawa-joshi",
    "京都女子大学": "kyoto-joshi",
    "同志社女子大学": "doshisha-joshi",
    "神戸女学院大学": "kobe-jogakuin",
    "神戸市外国語大学": "kobe-gaidai",
    "奈良女子大学": "nara-joshi",
    "京都府立大学": "kyoto-furitsu",
    "滋賀大学": "shiga",
    # ---- 東海 ----
    "名古屋大学": "nagoya",
    "南山大学": "nanzan",
    "名城大学": "meijo",
    "中京大学": "chukyo",
    "愛知大学": "aichi",
    "愛知学院大学": "aichi-gakuin",
    "名古屋工業大学": "nagoya-kogyo",
    "名古屋市立大学": "nagoya-shiritsu",
    "岐阜大学": "gifu",
    "三重大学": "mie",
    "静岡大学": "shizuoka",
    "金城学院大学": "kinjo-gakuin",
    "椙山女学園大学": "sugiyama",
    "愛知淑徳大学": "aichi-shukutoku",
    # ---- 北海道 ----
    "北海道大学": "hokkaido",
    "小樽商科大学": "otaru-shoka",
    "北海学園大学": "hokkai-gakuen",
    "札幌大学": "sapporo",
    "北星学園大学": "hokusei-gakuen",
    "藤女子大学": "fuji-joshi",
    "札幌学院大学": "sapporo-gakuin",
    "酪農学園大学": "rakuno-gakuen",
    # ---- 東北 ----
    "東北大学": "tohoku-univ",
    "東北学院大学": "tohoku-gakuin",
    "山形大学": "yamagata",
    "宮城教育大学": "miyagi-kyoiku",
    "岩手大学": "iwate",
    "福島大学": "fukushima",
    "弘前大学": "hirosaki",
    "秋田大学": "akita",
    "宮城大学": "miyagi",
    "東北福祉大学": "tohoku-fukushi",
    # ---- 中四国 ----
    "広島大学": "hiroshima",
    "岡山大学": "okayama",
    "香川大学": "kagawa",
    "愛媛大学": "ehime",
    "山口大学": "yamaguchi",
    "島根大学": "shimane",
    "高知大学": "kochi",
    "徳島大学": "tokushima",
    "県立広島大学": "kenritsu-hiroshima",
    "広島修道大学": "hiroshima-shudo",
    "松山大学": "matsuyama",
    "広島市立大学": "hiroshima-shiritsu",
    # ---- 九州 ----
    "九州大学": "kyushu-univ",
    "福岡大学": "fukuoka",
    "西南学院大学": "seinan-gakuin",
    "熊本大学": "kumamoto",
    "長崎大学": "nagasaki",
    "鹿児島大学": "kagoshima",
    "北九州市立大学": "kitakyushu",
    "佐賀大学": "saga",
    "大分大学": "oita",
    "宮崎大学": "miyazaki",
    "福岡女子大学": "fukuoka-joshi",
    "九州工業大学": "kyushu-kogyo",
}

_kks = None


def _romaji(name: str) -> str | None:
    global _kks
    try:
        if _kks is None:
            import pykakasi
            _kks = pykakasi.kakasi()
        base = re.sub(r"(大学|高校|短期大学)$", "", name.strip())
        s = "".join(x["hepburn"] for x in _kks.convert(base))
        s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
        return s or None
    except Exception:
        return None


def slug_for(team: str) -> str:
    if team in TEAM_SLUGS:
        return TEAM_SLUGS[team]
    r = _romaji(team)
    if r:
        TEAM_SLUGS[team] = r  # 同一実行内で安定させる
        return r
    print(f"[warn] スラッグ生成不可のチーム名: {team}", file=sys.stderr)
    return f"team-{abs(hash(team)) % 10**8}"
