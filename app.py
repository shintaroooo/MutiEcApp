import streamlit as st
import requests
import openai
import os
from dotenv import load_dotenv

# --- 環境変数の読み込み ---
load_dotenv()

# --- 設定 ---
RAKUTEN_APP_ID = os.getenv("RAKUTEN_APP_ID", "")
RAKUTEN_AFFILIATE_ID = os.getenv("RAKUTEN_AFFILIATE_ID", "")
YAHOO_APP_ID = os.getenv("YAHOO_APP_ID", "")
VC_AFFILIATE_ID = os.getenv("VC_AFFILIATE_ID", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
openai.api_key = OPENAI_API_KEY

AMAZON_DATA = [
    {"name": "AmazonイヤホンC", "price": 8200, "rating": 4.6, "url": "#", "image": "https://via.placeholder.com/150"},
]  # ★AmazonはまだAPI制限があるため仮データ

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

# --- Yahoo!ショッピングAPI呼び出し関数 ---
def search_yahoo(query):
    url = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"
    params = {
        "appid": YAHOO_APP_ID,
        "query": query,
        "affiliate_type": "vc",
        "affiliate_id": VC_AFFILIATE_ID,
        "results": 5
    }
    res = requests.get(url, params=params)
    if res.status_code == 200:
        data = res.json()
        return [
            {
                "name": item["name"],
                "price": item["price"],
                "rating": item.get("review", {}).get("rate", 0),
                "url": item["url"],
                "image": item["image"]["medium"]
            }
            for item in data.get("hits", [])
        ]
    else:
        return []

# --- AIによるおすすめ理由生成 ---
def generate_recommendation(item_name, site):
    prompt = f"""
以下はECサイトで販売されている商品です。
ユーザーにこの商品をおすすめする短いコメントを日本語で作成してください。

商品名: {item_name}
販売サイト: {site}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

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
        if "Yahoo" in selected_sites:
            results["Yahoo"] = search_yahoo(query)
        if "Amazon" in selected_sites:
            results["Amazon"] = AMAZON_DATA  # APIが使えるようになるまで仮データ

        # --- 表示レイアウト ---
        cols = st.columns(len(selected_sites))

        for idx, site in enumerate(selected_sites):
            with cols[idx]:
                st.markdown(f"### {site}")
                for item in results.get(site, []):
                    st.image(item["image"])
                    st.write(f"**{item['name']}**")
                    st.write(f"価格: ¥{item['price']}")
                    st.write(f"評価: ⭐ {item['rating']}")
                    try:
                        comment = generate_recommendation(item["name"], site)
                        st.success(f"AIおすすめ理由: {comment}")
                    except Exception as e:
                        st.warning("AIによるおすすめ理由の生成に失敗しました。")
                    st.markdown(f"[購入リンク]({item['url']})")
                    st.markdown("---")

else:
    st.info("サイドバーから検索条件を入力してください。")
