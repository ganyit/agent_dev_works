"""Streamlit UI for the e-commerce consultant agent."""

import os
import streamlit as st
from dotenv import load_dotenv
load_dotenv(override=True)
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

/* ── Token usage panel ── */
.token-panel {
    background: linear-gradient(135deg, #f0f4ff, #e8f5e9);
    border: 1px solid #c7d2fe;
    border-radius: 16px;
    padding: 14px 16px;
    margin-top: 16px;
}
.token-panel-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #3730a3;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.token-stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}
.token-label {
    font-size: 0.78rem;
    color: #555;
}
.token-value {
    font-size: 0.82rem;
    font-weight: 700;
    color: #1a1a2e;
}
.token-bar-wrap {
    background: #dde3f0;
    border-radius: 8px;
    height: 7px;
    margin-bottom: 8px;
    overflow: hidden;
}
.token-bar-fill {
    height: 100%;
    border-radius: 8px;
    background: linear-gradient(90deg, #6366f1, #8b5cf6);
    transition: width 0.4s ease;
}
.token-footnote {
    font-size: 0.70rem;
    color: #888;
    margin-top: 6px;
    text-align: center;
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
if "token_totals" not in st.session_state:
    st.session_state.token_totals = {"input_tokens": 0, "output_tokens": 0, "searches": 0}

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
        st.session_state.token_totals = {"input_tokens": 0, "output_tokens": 0, "searches": 0}
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
                reply, updated_history, products, token_usage = agent_chat(prompt, st.session_state.lc_history)
            st.markdown(reply)
            if products:
                st.markdown("---")
                _render_product_grid(products, key_prefix="latest")

        # Accumulate token usage
        st.session_state.token_totals["input_tokens"] += token_usage["input_tokens"]
        st.session_state.token_totals["output_tokens"] += token_usage["output_tokens"]
        if products:
            st.session_state.token_totals["searches"] += 1

        st.session_state.lc_history = updated_history
        st.session_state.messages.append({"role": "assistant", "content": reply, "products": products})

# ---------------------------------------------------------------------------
# AI Usage meter — rendered AFTER chat processing so values are current
# ---------------------------------------------------------------------------
def _fmt_pages(tokens: int) -> str:
    """Format tokens as pages with one decimal when < 1 full page."""
    pages = tokens / 500
    if pages == 0:
        return "0 pages"
    if pages < 1:
        return f"~{pages:.1f} pages"
    return f"~{round(pages)} page{'s' if round(pages) != 1 else ''}"

with cart_col:
    _tok = st.session_state.token_totals
    _total_tok = _tok["input_tokens"] + _tok["output_tokens"]
    _searches = _tok["searches"]
    _cost_usd = _tok["input_tokens"] * 0.00000015 + _tok["output_tokens"] * 0.0000006
    _cost_cents = _cost_usd * 100
    _cost_display = f"${_cost_usd:.4f}" if _cost_cents >= 100 else f"{_cost_cents:.2f}¢"
    _bar_pct = min(100, int(_total_tok / 100))

    st.markdown(f"""
    <div class="token-panel">
        <div class="token-panel-title">🧠 AI Brain Activity — this session</div>
        <div class="token-stat-row">
            <span class="token-label">📖 Context read by AI</span>
            <span class="token-value">{_tok["input_tokens"]:,} tokens</span>
        </div>
        <div class="token-stat-row">
            <span class="token-label">✍️ Responses written</span>
            <span class="token-value">{_tok["output_tokens"]:,} tokens</span>
        </div>
        <div class="token-stat-row">
            <span class="token-label">🔍 eBay searches run</span>
            <span class="token-value">{_searches} search{'es' if _searches != 1 else ''}</span>
        </div>
        <div class="token-bar-wrap">
            <div class="token-bar-fill" style="width:{_bar_pct}%"></div>
        </div>
        <div class="token-stat-row">
            <span class="token-label">⚡ Raw AI tokens used</span>
            <span class="token-value">{_total_tok:,}</span>
        </div>
        <div class="token-stat-row">
            <span class="token-label">💰 Estimated AI cost</span>
            <span class="token-value">{_cost_display}</span>
        </div>
        <div class="token-footnote">Tokens = the units AI models count text in. ~500 tokens ≈ 1 book page.</div>
    </div>
    """, unsafe_allow_html=True)
