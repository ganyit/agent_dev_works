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
# Sidebar — settings + cart
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    # On Streamlit Community Cloud, secrets live in st.secrets.
    # On HF Spaces (and locally), the key comes from the environment / .env file.
    # The text input below is a fallback for cases where neither is set.
    try:
        _env_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        _env_key = ""
    if not _env_key:
        _env_key = os.environ.get("OPENAI_API_KEY", "")
    if _env_key:
        os.environ["OPENAI_API_KEY"] = _env_key

    if not os.environ.get("OPENAI_API_KEY"):
        api_key_input = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Enter your OpenAI API key. Not needed when deployed with secrets configured.",
        )
        if api_key_input:
            os.environ["OPENAI_API_KEY"] = api_key_input
    else:
        st.success("API key loaded from secrets.", icon="🔑")

    st.divider()
    st.markdown("**Try asking:**")
    st.markdown("- *I'm planning a summer beach vacation*")
    st.markdown("- *Best power bank for travel?*")
    st.markdown("- *I want to start trekking*")
    st.markdown("- *Recommend a budget sunscreen*")
    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.session_state.lc_history = []
        st.session_state.cart = {}
        st.rerun()

    st.divider()
    st.header("🛒 Your Cart")
    cart: dict = st.session_state.get("cart", {})
    if not cart:
        st.caption("Your cart is empty.")
    else:
        total = 0
        for pid, item in list(cart.items()):
            col1, col2 = st.columns([3, 1])
            col1.markdown(f"**{item['title'][:28]}…**  \n₹{item['price']} × {item['qty']}")
            if col2.button("✕", key=f"remove_{pid}"):
                del st.session_state.cart[pid]
                st.rerun()
            total += item["price"] * item["qty"]
        st.divider()
        st.markdown(f"**Total: ₹{total:,}**")
        if st.button("🧹 Clear cart"):
            st.session_state.cart = {}
            st.rerun()

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
# Main title
# ---------------------------------------------------------------------------
st.title("🛍️ ShopSmart Consultant")
st.caption("Your personal shopping advisor — ask about any product or let me build a travel/occasion kit for you.")

# ---------------------------------------------------------------------------
# Helper: product cards
# ---------------------------------------------------------------------------
def _render_product_cards(products: list[dict]) -> None:
    """Render a row of product cards with image + Add to Cart button."""
    if not products:
        return
    cols_per_row = 4
    for row_start in range(0, len(products), cols_per_row):
        row = products[row_start: row_start + cols_per_row]
        cols = st.columns(len(row))
        for col, p in zip(cols, row):
            with col:
                st.image(p.get("image_url", ""), width=140)
                st.markdown(f"**{p['title']}**")
                st.markdown(f"₹{p['price']:,}")
                if st.button(f"🛒 Add to cart", key=f"atc_{p['id']}_{id(products)}"):
                    cart = st.session_state.cart
                    if p["id"] in cart:
                        cart[p["id"]]["qty"] += 1
                    else:
                        cart[p["id"]] = {"title": p["title"], "price": p["price"], "qty": 1}
                    st.rerun()


# ---------------------------------------------------------------------------
# Render chat history
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("products"):
            _render_product_cards(msg["products"])


# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Ask me anything about products or tell me about your trip..."):
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("Please enter your OpenAI API key in the sidebar to continue.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            from agent import chat as agent_chat
            reply, updated_history, products = agent_chat(prompt, st.session_state.lc_history)
        st.markdown(reply)
        _render_product_cards(products)

    st.session_state.lc_history = updated_history
    st.session_state.messages.append({"role": "assistant", "content": reply, "products": products})
