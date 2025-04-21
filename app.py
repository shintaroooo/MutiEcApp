import streamlit as st
import requests
import os
import json
from datetime import datetime
from openai import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain

# --- ECサイト選択 ---
st.set_page_config(page_title="AIチャット商品検索", layout="wide")
st.title("🧠 AIコンシェルジュに商品を相談しよう")
st.write("### 🔍 検索対象のECサイトを選んでください")
selected_sites = st.multiselect("ECサイトを選択", ["楽天", "Yahoo", "Amazon"], default=["楽天", "Yahoo", "Amazon"])

# --- OpenAIクライアント初期化 ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- LangChain用モデルとメモリ初期化 ---
language_model = ChatOpenAI(model_name="gpt-4o", temperature=0.7)
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=language_model, memory=memory, verbose=False)

# --- 設定 ---
RAKUTEN_APP_ID = st.secrets["RAKUTEN_APP_ID"]
RAKUTEN_AFFILIATE_ID = st.secrets["RAKUTEN_AFFILIATE_ID"]
YAHOO_APP_ID = st.secrets["YAHOO_APP_ID"]
VC_AFFILIATE_ID = st.secrets["VC_AFFILIATE_ID"]

AMAZON_DATA = [
    {"name": "AmazonイヤホンC", "price": 8200, "rating": 4.6, "url": "#", "image": "https://via.placeholder.com/150"},
]

# --- チャット履歴の保存/読み込み ---
CHAT_HISTORY_FILE = "chat_logs.json"

if os.path.exists(CHAT_HISTORY_FILE):
    with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
        all_chat_sessions = json.load(f)
else:
    all_chat_sessions = {}

# --- セッション初期化 ---
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []
    st.session_state.results_ready = False
    st.session_state.search_keyword = ""
    st.session_state.active_session = "現在のセッション"
    st.session_state.session_name = ""

# --- 新しいセッション名入力 ---
with st.sidebar.expander("💾 チャット履歴の保存"):
    st.text_input("セッション名を入力して保存", key="session_name")
    if st.button("保存する"):
        if st.session_state.session_name:
            all_chat_sessions[st.session_state.session_name] = st.session_state.chat_log
            with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(all_chat_sessions, f, ensure_ascii=False, indent=2)
            st.success(f"セッション '{st.session_state.session_name}' を保存しました！")
        else:
            st.warning("セッション名を入力してください。")

# --- 過去セッション選択 ---
session_options = ["現在のセッション"] + list(all_chat_sessions.keys())
selected_session = st.sidebar.selectbox("🗂 過去のチャット履歴を選択", session_options)

if selected_session != "現在のセッション":
    st.session_state.chat_log = all_chat_sessions.get(selected_session, [])
    st.session_state.active_session = selected_session
else:
    st.session_state.active_session = "現在のセッション"


# --- サイドバーにチャット履歴表示 ---
st.sidebar.header("💬 表示中のチャット履歴")
if st.session_state.chat_log:
    for idx, pair in enumerate(st.session_state.chat_log, start=1):
        st.sidebar.markdown(f"**{idx}. ユーザー:** {pair['user']}")
        st.sidebar.markdown(f"**{idx}. AI:** {pair['ai']}")
else:
    st.sidebar.info("チャットを開始すると、ここに履歴が表示されます。")

# --- チャット入力 ---
user_input = st.chat_input("どんな商品をお探しですか？（例：軽くて安いノートPC）")
if user_input:
    ai_response = conversation.predict(input=user_input)
    st.session_state.chat_log.append({"user": user_input, "ai": ai_response})

# --- チャット履歴表示 ---
for pair in st.session_state.chat_log:
    st.chat_message("user").write(pair["user"])
    st.chat_message("assistant").write(pair["ai"])

# --- 条件抽出 ---
def extract_search_conditions():
    prompt = "このユーザーの希望を1つの検索キーワードにまとめて。"
    return conversation.predict(input=prompt)

# --- API呼び出し関数 ---
def search_rakuten(query):
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
    params = {
        "applicationId": RAKUTEN_APP_ID,
        "affiliateId": RAKUTEN_AFFILIATE_ID,
        "keyword": query,
        "format": "json",
        "hits": 10
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

def search_yahoo(query):
    url = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"
    params = {
        "appid": YAHOO_APP_ID,
        "query": query,
        "affiliate_type": "vc",
        "affiliate_id": VC_AFFILIATE_ID,
        "results": 10
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

# --- おすすめ理由生成 ---
def generate_recommendation(item_name, site, user_conditions):
    prompt = f"""
あなたは商品コンシェルジュAIです。以下の条件をもとに、商品をおすすめする理由を短く説明してください。

ユーザーの希望条件:
{user_conditions}

商品名: {item_name}
販売サイト: {site}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# --- 条件が十分になったか確認ボタン ---
if len(st.session_state.chat_log) >= 3:
    if st.button("条件が揃いました！商品を探す 🔍"):
        keyword = extract_search_conditions()
        st.session_state.search_keyword = keyword
        st.session_state.results_ready = True

# --- 検索＆結果表示 ---
if st.session_state.results_ready and st.session_state.search_keyword:
    query = st.session_state.search_keyword
    st.chat_message("assistant").write(f"条件に合う商品を探しています... 🔍 キーワード: 『{query}』")

    all_items = []
    if "楽天" in selected_sites:
        all_items += search_rakuten(query)
    if "Yahoo" in selected_sites:
        all_items += search_yahoo(query)
    if "Amazon" in selected_sites:
        all_items += AMAZON_DATA

    top_items = sorted(all_items, key=lambda x: -x["rating"])[:3]

    st.write("### 🏆 おすすめ商品ランキング（上位3件）")
    for i, item in enumerate(top_items, start=1):
        recommendation = generate_recommendation(item["name"], ", ".join(selected_sites), query)
        st.markdown(f"**{i}. [{item['name']}]({item['url']})**")
        st.image(item["image"], width=150)
        st.write(f"価格: ¥{item['price']}  | 評価: ⭐ {item['rating']}")
        st.success(f"おすすめ理由: {recommendation}")
        st.markdown("---")