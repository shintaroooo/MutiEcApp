"""
このファイルは、画面表示に特化した関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import logging
import streamlit as st
import constants as ct


############################################################
# 関数定義
############################################################

def display_app_title():
    """
    タイトル表示
    """
    st.markdown(f"## {ct.APP_NAME}")


def display_initial_ai_message():
    """
    AIメッセージの初期表示
    """
    with st.chat_message("assistant", avatar=ct.AI_ICON_FILE_PATH):
        st.markdown("こちらは対話型の商品レコメンド生成AIアプリです。「こんな商品が欲しい」という情報・要望を画面下部のチャット欄から送信いただければ、おすすめの商品をレコメンドいたします。")
        st.markdown("**入力例**")
        st.info("""
        - 「長時間使える、高音質なワイヤレスイヤホン」
        - 「机のライト」
        - 「USBで充電できる加湿器」
        """)


def display_conversation_log():
    """
    会話ログの一覧表示
    """
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user", avatar=ct.USER_ICON_FILE_PATH):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant", avatar=ct.AI_ICON_FILE_PATH):
                display_product(message["content"])


def display_product(result):
    """
    商品情報の表示

    Args:
        result: LLMからの回答
    """
    logger = logging.getLogger(ct.LOGGER_NAME)

    # LLMレスポンスのテキストを辞書に変換
    product_lines = result[0].page_content.split("\n")
    product = {item.split(": ")[0]: item.split(": ")[1] for item in product_lines}

    st.markdown("以下の商品をご提案いたします。")

    # 「商品名」と「価格」
    st.success(f"""
            商品名：{product['name']}（商品ID: {product['id']}）\n
            価格：{product['price']}
    """)

    # 在庫状況
    if product["stock_status"] == ct.LOW_STOCK:
        st.warning("ご好評につき、在庫数が残りわずかです。購入をご希望の場合、お早めのご注文をおすすめいたします。", icon=ct.WARNING_ICON)
    elif product["stock_status"] == ct.NO_STOCK:
        st.error("申し訳ございませんが、本商品は在庫切れとなっております。入荷までもうしばらくお待ちください。", icon=ct.ERROR_ICON)

    # 「商品カテゴリ」と「メーカー」と「ユーザー評価」
    st.code(f"""
        商品カテゴリ：{product['category']}\n
        メーカー：{product['maker']}\n
        評価：{product['score']}({product['review_number']}件)
    """, language=None, wrap_lines=True)

    # 商品画像
    st.image(f"images/products/{product['file_name']}", width=400)

    # 商品説明
    st.code(product['description'], language=None, wrap_lines=True)

    # おすすめ対象ユーザー
    st.markdown("**こんな方におすすめ！**")
    st.info(product["recommended_people"])

    # 商品ページのリンク
    st.link_button("商品ページを開く", type="primary", use_container_width=True, url="https://google.com")