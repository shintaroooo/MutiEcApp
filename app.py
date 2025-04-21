import streamlit as st
import requests

# --- 設定 ---
RAKUTEN_APP_ID = "YOUR_APP_ID"  # ★ここにあなたの楽天APIキーを入れてください
RAKUTEN_AFFILIATE_ID = "YOUR_AFFILIATE_ID"  # 任意

# --- 楽天API呼び出し関数 ---
def search_rakuten(query):
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
    params = {
        "applicationId": RAKUTEN_APP_ID,
        "affiliateId": RAKUTEN_AFFILIATE_ID,
        "keyword": query,
        "format": "json",
        "hits": 5
    }
    res = requests.get(url, params=params)
    if res.status_code == 200:
        data = res.json()
        return [
            {
                "name": item["Item"]["itemName"],
                "price": item["Item"]["itemPrice"],
                "rating": item["Item"].get("reviewAverage", 0),
                "url": item["Item"]["affiliateUrl"],
                "image": item["Item"]["mediumImageUrls"][0]["imageUrl"]
            }
            for item in data.get("Items", [])
        ]
    else:
        return []

# --- ヘッダー ---
st.set_page_config(page_title="AIショッピング比較アプリ", layout="wide")
st.title("🛒 AI × 複数EC 商品比較アプリ")
st.write("楽天 / Yahoo / Amazon の商品をまとめて比較しよう！")

# --- チェックボックス（ECサイト選択） ---
st.sidebar.header("比較対象サイト")
ec_sites = ["楽天", "Yahoo", "Amazon"]
selected_sites = [site for site in ec_sites if st.sidebar.checkbox(site, value=True)]

# --- キーワード入力 ---
st.sidebar.header("商品検索キーワード")
query = st.sidebar.text_input("例：ワイヤレスイヤホン、ゲーミングマウス", "ワイヤレスイヤホン")

# --- 検索ボタン ---
if st.sidebar.button("検索する"):
    if not selected_sites:
        st.warning("少なくとも1つのECサイトを選択してください。")
    else:
        st.subheader(f"🔍 検索結果：『{query}』の比較（{', '.join(selected_sites)}）")

        results = {}
        if "楽天" in selected_sites:
            results["楽天"] = search_rakuten(query)

        # 今はYahoo / Amazonはダミーのまま
        dummy_data = {
            "Yahoo": [
                {"name": "YahooイヤホンB", "price": 7480, "rating": 4.3, "url": "#", "image": "https://via.placeholder.com/150"},
            ],
            "Amazon": [
                {"name": "AmazonイヤホンC", "price": 8200, "rating": 4.6, "url": "#", "image": "https://via.placeholder.com/150"},
            ]
        }
        for site in [s for s in selected_sites if s != "楽天"]:
            results[site] = dummy_data[site]

        # --- 表示レイアウト ---
        cols = st.columns(len(selected_sites))

        for idx, site in enumerate(selected_sites):
            with cols[idx]:
                st.markdown(f"### {site}")
                for item in results[site]:
                    st.image(item["image"])
                    st.write(f"**{item['name']}**")
                    st.write(f"価格: ¥{item['price']}")
                    st.write(f"評価: ⭐ {item['rating']}")
                    st.markdown(f"[購入リンク]({item['url']})")
                    st.markdown("---")

else:
    st.info("サイドバーから検索条件を入力してください。")
