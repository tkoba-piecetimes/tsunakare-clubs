# 独自ドメイン切替手順（lacrossemania.jp）

※2026-08-14 GitHubリポジトリを tsunakereoff → tkoba-piecetimes へ移管済み。以下のコマンド・CNAME先は移管後の値に更新してある。

ドメイン購入後、以下の順で切り替える。所要15分＋DNS浸透待ち。

## 1. ネームサーバー変更（お名前.com Navi）

ドメイン一覧 → lacrossemania.jp → ネームサーバー設定 → 「その他のネームサーバーを使う」
ns1.xserver.jp / ns2.xserver.jp / ns3.xserver.jp / ns4.xserver.jp / ns5.xserver.jp

## 2. DNSレコード追加（Xserverサーバーパネル）

「ドメイン設定」に lacrossemania.jp を追加後、「DNSレコード設定」で:

| 種別 | ホスト名 | 内容 |
|---|---|---|
| A | （空欄） | 185.199.108.153 |
| A | （空欄） | 185.199.109.153 |
| A | （空欄） | 185.199.110.153 |
| A | （空欄） | 185.199.111.153 |
| CNAME | www | tkoba-piecetimes.github.io |

## 3. GitHub Pages側の設定（gh CLI）

```
gh api -X PUT repos/tkoba-piecetimes/tsunakare-clubs/pages -f cname=lacrossemania.jp
```

HTTPS証明書は自動発行（数分〜1時間）。発行後に enforce_https を有効化:

```
gh api -X PUT repos/tkoba-piecetimes/tsunakare-clubs/pages -F https_enforced=true
```

## 4. サイト側の切替

- `pipeline/generate_site.py` の `SITE_BASE` を `https://lacrossemania.jp/` に変更
- 再生成してコミット＆push（github.ioの素のURLからは自動で301される）

## 5. 事後作業

- Search Console にドメインプロパティ登録（DNS TXT認証）→ sitemap.xml 送信
- GA4測定IDを `GA_MEASUREMENT_ID` に設定
- OGP画像URL・sitemapはSITE_BASE連動なので追加作業なし
