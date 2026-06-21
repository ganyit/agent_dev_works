"""
E-commerce consultant LangGraph agent.

Supports two modes:
  - Single-product consultation: recommend the best eBay item for a specific need.
  - Essentials kit assembly: for occasion/goal requests (trips, "getting started with X",
    parties, home office setup, etc.) expand the goal into a grouped multi-item basket.
"""

import json
import os
import re
import sys
import time
import base64
from pathlib import Path

import httpx
from dotenv import load_dotenv
load_dotenv(override=True)

# Ensure UTF-8 output on Windows so symbols render correctly
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from typing import Annotated, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# ---------------------------------------------------------------------------
# eBay API client
# ---------------------------------------------------------------------------

_EBAY_ENV = os.environ.get("EBAY_ENV", "sandbox").lower()

_EBAY_URLS = {
    "sandbox": {
        "auth": "https://api.sandbox.ebay.com/identity/v1/oauth2/token",
        "browse": "https://api.sandbox.ebay.com/buy/browse/v1",
    },
    "production": {
        "auth": "https://api.ebay.com/identity/v1/oauth2/token",
        "browse": "https://api.ebay.com/buy/browse/v1",
    },
}

_EBAY_AUTH_URL = _EBAY_URLS[_EBAY_ENV]["auth"]
_EBAY_BROWSE_URL = _EBAY_URLS[_EBAY_ENV]["browse"]

_token_cache: dict = {"token": None, "expires_at": 0}


def _get_ebay_token() -> str:
    if _token_cache["token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["token"]

    app_id = os.environ["EBAY_APP_ID"]
    cert_id = os.environ["EBAY_CERT_ID"]
    creds = base64.b64encode(f"{app_id}:{cert_id}".encode()).decode()

    resp = httpx.post(
        _EBAY_AUTH_URL,
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data["expires_in"]
    return _token_cache["token"]


def _ebay_headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_ebay_token()}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        "Content-Type": "application/json",
    }


def _normalize_item(item: dict) -> dict:
    price_info = item.get("price", {})
    return {
        "id": item.get("itemId", ""),
        "title": item.get("title", ""),
        "price": float(price_info.get("value", 0)),
        "currency": price_info.get("currency", "USD"),
        "category": item.get("categories", [{}])[0].get("categoryName", "") if item.get("categories") else "",
        "subcategory": "",
        "image_url": item.get("image", {}).get("imageUrl", ""),
        "url": item.get("itemWebUrl", ""),
        "condition": item.get("condition", ""),
        "seller": item.get("seller", {}).get("username", ""),
        "attributes": {},
        "tags": [],
    }


def _ebay_search(query: str, limit: int = 5, min_price: float = None, max_price: float = None) -> list[dict]:
    try:
        params = {"q": query, "limit": limit}
        filters = []
        if min_price is not None:
            filters.append(f"price:[{min_price}]")
        if max_price is not None:
            filters.append(f"price:[..{max_price}]")
        if min_price is not None and max_price is not None:
            filters = [f"price:[{min_price}..{max_price}]"]
        if filters:
            params["filter"] = ",".join(filters) + ",priceCurrency:USD"
        resp = httpx.get(
            f"{_EBAY_BROWSE_URL}/item_summary/search",
            headers=_ebay_headers(),
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        items = resp.json().get("itemSummaries", [])
        return [_normalize_item(i) for i in items]
    except httpx.HTTPStatusError:
        return []


def _ebay_get_item(item_id: str) -> dict | None:
    try:
        resp = httpx.get(
            f"{_EBAY_BROWSE_URL}/item/{item_id}",
            headers=_ebay_headers(),
            timeout=10,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return _normalize_item(resp.json())
    except httpx.HTTPStatusError:
        return None


# In-memory product cache keyed by eBay item ID (session-scoped)
_product_cache: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@tool
def search_catalog(query: str, max_results: int = 5, min_price: float = None, max_price: float = None) -> str:
    """Search eBay for products matching the query string.

    Returns up to max_results products with id, title, category, price, and condition.
    Use this for both single-product lookups and when mapping essentials to real products.
    Pass min_price and/or max_price (in USD) to filter by budget.
    """
    results = _ebay_search(query, limit=max_results, min_price=min_price, max_price=max_price)

    if not results:
        return f"No products found for '{query}'."

    lines = []
    for p in results:
        _product_cache[p["id"]] = p
        lines.append(
            f"[{p['id']}] {p['title']} — {p['currency']} {p['price']:.2f} | {p['category']} | {p['condition']}"
        )
    return "\n".join(lines)


@tool
def get_product_details(product_id: str) -> str:
    """Retrieve full details for a specific eBay item by its item ID."""
    # Check cache first
    if product_id in _product_cache:
        return json.dumps(_product_cache[product_id], indent=2)

    item = _ebay_get_item(product_id)
    if not item:
        return f"Product '{product_id}' not found."

    _product_cache[product_id] = item
    return json.dumps(item, indent=2)


@tool
def get_offers(product_ids: list[str], cart_total: float) -> str:
    """Get available offers for the given product IDs and cart total.

    Returns applicable offers and the effective total after the best discount.
    """
    if not product_ids:
        return "No products in cart."

    _BANK_OFFERS = {
        "Chase": (10, 200, "10% off up to $50 on cart ≥ $200 with Chase Sapphire"),
        "Amex": (8, 150, "8% off up to $40 on cart ≥ $150 with Amex Gold"),
        "Citi": (5, 100, "5% off up to $25 on cart ≥ $100 with Citi Double Cash"),
    }
    _CAPS = {"Chase": 50, "Amex": 40, "Citi": 25}

    applicable = []
    for card, (pct, min_val, desc) in _BANK_OFFERS.items():
        if cart_total >= min_val:
            discount = min(cart_total * pct / 100, _CAPS[card])
            applicable.append((card, discount, desc))

    if not applicable:
        return f"Cart total ${cart_total:.2f} — no offers applicable (minimum cart is $100)."

    applicable.sort(key=lambda x: x[1], reverse=True)
    lines = [f"Cart total: ${cart_total:.2f}", "", "Available offers:"]
    for card, discount, desc in applicable:
        effective = cart_total - discount
        lines.append(f"  • {card}: {desc} → saves ${discount:.2f}, effective total ${effective:.2f}")

    best_card, best_discount, _ = applicable[0]
    lines.append(f"\nBest offer: {best_card} — pay ${cart_total - best_discount:.2f} after ${best_discount:.2f} discount.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a warm, knowledgeable e-commerce consultant powered by live eBay listings.
You help users find products across all categories — travel gear, electronics, clothing, health, and more.
Prices are in USD from real eBay listings.

You operate in TWO modes depending on what the user asks:

**Mode A — Single-product consultation**
When a user asks about a specific product or need (e.g. "best sunscreen", "recommend a power bank"),
help them narrow down to the single best match. Ask clarifying questions (budget, use case, etc.)
as needed, then call search_catalog and present your top recommendation with reasoning.
If the user mentions a budget (e.g. "under $500", "budget of $300"), always pass max_price to search_catalog so results are filtered at the API level.

**Mode B — Essentials kit assembly**
When a user expresses a goal or occasion — a trip ("I'm planning a summer vacation"), an event
("throwing a birthday party"), or a setup ("I want to start trekking") — assemble a curated
multi-item essentials kit. Follow these steps:

1. Ask 1–3 focused framing questions BEFORE building the kit. For travel: destination/climate,
   trip length in days, and trip type (leisure / adventure / business / family). Keep it brief.

2. Use the gathered context to REASON about what the traveller needs — do NOT use a fixed list.
   A beach holiday, winter trek, and business trip need very different kits. Think through
   categories: Sun & Skin, Toiletries, Clothing, Electronics, Health & Safety, Documents.

3. For each purchasable essential, call search_catalog to find the closest eBay match.
   Scale quantities to trip length where it makes sense (e.g. more sunscreen for 10+ days).
   If the user has given a total budget, distribute it across items and pass max_price per item to search_catalog.

4. Present the kit GROUPED with each product's title and price. Include a running subtotal.
   Non-purchasable items (passport, tickets, boarding passes, hotel booking confirmation) go
   in a separate "Checklist — bring these yourself" section, NOT as products.

5. After presenting the kit, call get_offers on the cart total to surface any card discount.

6. Allow the user to refine the kit: "drop the electronics", "I want cheaper sunscreen",
   "add a power bank". Re-search and show the updated kit.

IMPORTANT: Never invent products. Only include items actually returned by search_catalog.
If an essential has no catalog match, add it to the checklist section instead.

Keep your tone warm, expert, and concise — like a knowledgeable friend helping you pack smart.
Avoid walls of text; use bullet points and section headers to keep things scannable."""


# ---------------------------------------------------------------------------
# LangGraph state and graph
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


_llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=4096)
_tools = [search_catalog, get_offers, get_product_details]
_llm_with_tools = _llm.bind_tools(_tools)
_tool_map = {t.name: t for t in _tools}

# Products surfaced during the current chat() call (reset each turn).
_turn_products: list[dict] = []


def _extract_item_ids(text: str) -> list[str]:
    """Extract eBay item IDs from tool result text (format: [v1|...|...] or bare ID)."""
    return re.findall(r"\[([^\]\[]+\|[^\]\[]+)\]", text)


def call_model(state: AgentState) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = _llm_with_tools.invoke(messages)
    return {"messages": [response]}


def call_tools(state: AgentState) -> dict:
    last_msg: AIMessage = state["messages"][-1]
    tool_results = []
    for tc in last_msg.tool_calls:
        fn = _tool_map[tc["name"]]
        result = fn.invoke(tc["args"])
        result_str = str(result)
        tool_results.append(
            ToolMessage(content=result_str, tool_call_id=tc["id"], name=tc["name"])
        )
        if tc["name"] in ("search_catalog", "get_product_details"):
            for pid in _extract_item_ids(result_str):
                product = _product_cache.get(pid)
                if product and not any(p["id"] == pid for p in _turn_products):
                    _turn_products.append(product)
    return {"messages": tool_results}


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return END


graph_builder = StateGraph(AgentState)
graph_builder.add_node("model", call_model)
graph_builder.add_node("tools", call_tools)
graph_builder.add_edge(START, "model")
graph_builder.add_conditional_edges("model", should_continue, {"tools": "tools", END: END})
graph_builder.add_edge("tools", "model")
graph = graph_builder.compile()


# ---------------------------------------------------------------------------
# Chat runner
# ---------------------------------------------------------------------------

def chat(user_input: str, history: list) -> tuple[str, list, list[dict]]:
    """Send a message and return (assistant_reply, updated_history, products_shown)."""
    global _turn_products
    _turn_products = []
    history = history + [HumanMessage(content=user_input)]
    result = graph.invoke({"messages": history})
    updated = result["messages"]
    reply = ""
    for msg in reversed(updated):
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            reply = msg.content
            break
    return reply, updated, list(_turn_products)


def run_cli():
    print("E-Commerce Consultant  (type 'exit' to quit)\n")
    history: list = []
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye"):
            print("Consultant: Happy shopping! Goodbye!")
            break
        reply, history, _ = chat(user_input, history)
        print(f"\nConsultant: {reply}\n")


if __name__ == "__main__":
    run_cli()
