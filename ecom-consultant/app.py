"""Streamlit UI for the e-commerce consultant agent."""

import os
import streamlit as st
from dotenv import load_dotenv
load_dotenv()
from langchain_core.messages import AIMessage, HumanMessage

st.set_page_config(
    page_title="ShopSmart Consultant",
    page_icon="🛍️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Global styles
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ── Page background ── */
[data-testid="stAppViewContainer"] {
    background: #f7f8fa;
}

/* ── Hide default sidebar toggle on mobile ── */
[data-testid="collapsedControl"] { display: none; }

/* ── Chat column scroll area ── */
.chat-scroll {
    max-height: calc(100vh - 180px);
    overflow-y: auto;
    padding-right: 8px;
}

/* ── Product card ── */
.product-card {
    background: #ffffff;
    border: 1px solid #e8eaed;
    border-radius: 14px;
    padding: 12px;
    text-align: center;
    transition: box-shadow 0.2s, transform 0.2s;
    height: 100%;
}
.product-card:hover {
    box-shadow: 0 6px 20px rgba(0,0,0,0.10);
    transform: translateY(-2px);
}
.product-card img {
    width: 100%;
    height: 140px;
    object-fit: contain;
    border-radius: 8px;
    background: #f0f2f5;
    margin-bottom: 8px;
}
.product-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: #1a1a2e;
    line-height: 1.3;
    min-height: 2.6rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    margin-bottom: 4px;
}
.product-price {
    font-size: 1.05rem;
    font-weight: 700;
    color: #e63946;
    margin-bottom: 10px;
}
.product-condition {
    font-size: 0.72rem;
    color: #888;
    margin-bottom: 8px;
}

/* ── Cart panel ── */
.cart-panel {
    background: #ffffff;
    border: 1px solid #e8eaed;
    border-radius: 16px;
    padding: 16px;
    position: sticky;
    top: 80px;
}
.cart-header {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1a1a2e;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.cart-item {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 8px 0;
    border-bottom: 1px solid #f0f2f5;
    gap: 8px;
}
.cart-item-title {
    font-size: 0.80rem;
    font-weight: 600;
    color: #333;
    line-height: 1.3;
}
.cart-item-price {
    font-size: 0.78rem;
    color: #666;
}
.cart-total {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1a1a2e;
    margin-top: 12px;
    padding-top: 8px;
    border-top: 2px solid #e8eaed;
    text-align: right;
}
.cart-empty {
    text-align: center;
    color: #aaa;
    font-size: 0.85rem;
    padding: 20px 0;
}

/* ── Checkout button ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #e63946, #c1121f);
    border: none;
    border-radius: 10px;
    color: white;
    font-weight: 600;
    width: 100%;
}

/* ── Chat bubbles ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
}

/* ── Suggested chips ── */
.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 8px 0 16px 0;
}
.chip {
    background: #eef2ff;
    color: #3730a3;
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.80rem;
    font-weight: 500;
    cursor: pointer;
    border: 1px solid #c7d2fe;
    white-space: nowrap;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "lc_history" not in st.session_state:
    st.session_state.lc_history = []
if "cart" not in st.session_state:
    st.session_state.cart = {}

# ---------------------------------------------------------------------------
# Layout: left settings strip (sidebar) | centre chat | right cart
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    try:
        _env_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        _env_key = ""
    if not _env_key:
        _env_key = os.environ.get("OPENAI_API_KEY", "")
    if _env_key:
        os.environ["OPENAI_API_KEY"] = _env_key

    if not os.environ.get("OPENAI_API_KEY"):
        v = st.text_input("OpenAI API Key", type="password")
        if v:
            os.environ["OPENAI_API_KEY"] = v
    else:
        st.success("OpenAI key loaded", icon="🔑")

    if not os.environ.get("EBAY_APP_ID"):
        a = st.text_input("eBay App ID", type="password")
        c = st.text_input("eBay Cert ID", type="password")
        if a: os.environ["EBAY_APP_ID"] = a
        if c: os.environ["EBAY_CERT_ID"] = c
    else:
        st.success("eBay keys loaded", icon="🛒")

    st.divider()
    st.markdown("**💡 Try asking:**")
    suggestions = [
        "Planning a summer beach vacation",
        "Best power bank for travel?",
        "I want to start trekking",
        "Winter camping essentials",
        "Budget laptop bag",
    ]
    for s in suggestions:
        st.markdown(f"- *{s}*")

    st.divider()
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.lc_history = []
        st.rerun()

# ---------------------------------------------------------------------------
# Two-column layout: chat (left) + cart (right)
# ---------------------------------------------------------------------------
chat_col, cart_col = st.columns([2, 1], gap="large")

# ---------------------------------------------------------------------------
# Helper: render product grid
# ---------------------------------------------------------------------------
def _render_product_grid(products: list[dict], key_prefix: str = "") -> None:
    if not products:
        return

    cols_per_row = 3
    for row_start in range(0, len(products), cols_per_row):
        row = products[row_start: row_start + cols_per_row]
        cols = st.columns(cols_per_row, gap="small")
        for col, p in zip(cols, row):
            with col:
                img_url = p.get("image_url") or "https://placehold.co/200x200?text=No+Image"
                currency = p.get("currency", "USD")
                condition = p.get("condition", "")
                truncated_title = p["title"][:60] + ("…" if len(p["title"]) > 60 else "")

                st.markdown(f"""
                <div class="product-card">
                    <img src="{img_url}" alt="{truncated_title}" />
                    <div class="product-title">{truncated_title}</div>
                    <div class="product-condition">{condition}</div>
                    <div class="product-price">{currency} {p['price']:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

                btn_key = f"atc_{key_prefix}_{p['id']}"
                in_cart = p["id"] in st.session_state.cart
                label = "✓ In Cart" if in_cart else "🛒 Add to Cart"
                if st.button(label, key=btn_key, use_container_width=True, type="primary" if not in_cart else "secondary"):
                    if p["id"] in st.session_state.cart:
                        st.session_state.cart[p["id"]]["qty"] += 1
                    else:
                        st.session_state.cart[p["id"]] = {
                            "title": p["title"],
                            "price": p["price"],
                            "currency": p.get("currency", "USD"),
                            "image_url": p.get("image_url", ""),
                            "qty": 1,
                        }
                    st.rerun()

# ---------------------------------------------------------------------------
# Cart panel (right column)
# ---------------------------------------------------------------------------
with cart_col:
    st.markdown("### 🛒 Your Cart")

    cart: dict = st.session_state.cart
    if not cart:
        st.markdown('<div class="cart-empty">🛍️<br>Your cart is empty.<br>Add products from the chat!</div>', unsafe_allow_html=True)
    else:
        total = 0.0
        for pid, item in list(cart.items()):
            img = item.get("image_url", "")
            c1, c2, c3 = st.columns([1, 3, 1])
            with c1:
                if img:
                    st.image(img, width=48)
                else:
                    st.markdown("🖼️")
            with c2:
                st.markdown(f"**{item['title'][:35]}{'…' if len(item['title'])>35 else ''}**")
                st.caption(f"{item.get('currency','USD')} {item['price']:.2f} × {item['qty']}")
            with c3:
                if st.button("✕", key=f"rm_{pid}", help="Remove"):
                    del st.session_state.cart[pid]
                    st.rerun()
            total += item["price"] * item["qty"]

        st.divider()
        st.markdown(f"**Total: USD {total:,.2f}**")

        col_checkout, col_clear = st.columns(2)
        with col_checkout:
            st.button("Checkout →", type="primary", use_container_width=True)
        with col_clear:
            if st.button("Clear", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()

# ---------------------------------------------------------------------------
# Chat column
# ---------------------------------------------------------------------------
with chat_col:
    st.markdown("## 🛍️ ShopSmart Consultant")
    st.caption("Your personal shopping advisor — ask about any product or let me build a travel kit for you.")

    # Render history
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("products"):
                _render_product_grid(msg["products"], key_prefix=f"hist_{i}")

    # Chat input
    if prompt := st.chat_input("Ask me anything about products or tell me about your trip..."):
        if not os.environ.get("OPENAI_API_KEY"):
            st.error("Please enter your OpenAI API key in the sidebar.")
            st.stop()
        if not os.environ.get("EBAY_APP_ID") or not os.environ.get("EBAY_CERT_ID"):
            st.error("Please enter your eBay credentials in the sidebar.")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching eBay for the best picks…"):
                from agent import chat as agent_chat
                reply, updated_history, products = agent_chat(prompt, st.session_state.lc_history)
            st.markdown(reply)
            if products:
                st.markdown("---")
                _render_product_grid(products, key_prefix="latest")

        st.session_state.lc_history = updated_history
        st.session_state.messages.append({"role": "assistant", "content": reply, "products": products})
