"""
E-commerce consultant LangGraph agent.

Supports two modes:
  - Single-product consultation: recommend the best catalog item for a specific need.
  - Essentials kit assembly: for occasion/goal requests (trips, "getting started with X",
    parties, home office setup, etc.) expand the goal into a grouped multi-item basket.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Ensure UTF-8 output on Windows so ₹ and other Unicode chars render correctly
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
# Catalog & offers data
# ---------------------------------------------------------------------------

CATALOG_PATH = Path(__file__).parent / "catalog.json"
with CATALOG_PATH.open(encoding="utf-8") as _f:
    _CATALOG: list[dict] = json.load(_f)

# Simulated bank offers: card → (discount_pct, min_cart_value, description)
_BANK_OFFERS = {
    "HDFC": (10, 2000, "10% off up to ₹500 on cart ≥ ₹2,000 with HDFC Credit Card"),
    "ICICI": (8, 1500, "8% off up to ₹400 on cart ≥ ₹1,500 with ICICI Debit Card"),
    "SBI": (5, 999, "5% off up to ₹250 on cart ≥ ₹999 with SBI Card"),
}

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@tool
def search_catalog(query: str, max_results: int = 5) -> str:
    """Search the product catalog for items matching the query string.

    Returns up to max_results products with id, title, category, price, and key attributes.
    Use this for both single-product lookups and when mapping essentials to real products.
    """
    q = query.lower()
    scored: list[tuple[int, dict]] = []
    for product in _CATALOG:
        score = 0
        title_lower = product["title"].lower()
        tags: list[str] = product.get("tags", [])
        category_lower = product["category"].lower()
        subcategory_lower = product.get("subcategory", "").lower()

        if q in title_lower:
            score += 10
        for tag in tags:
            if q in tag.lower() or tag.lower() in q:
                score += 3
        # word-level partial matching
        for word in q.split():
            if word in title_lower:
                score += 2
            if word in category_lower or word in subcategory_lower:
                score += 1
            for tag in tags:
                if word in tag.lower():
                    score += 1
        if score > 0:
            scored.append((score, product))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [p for _, p in scored[:max_results]]

    if not results:
        return f"No products found for '{query}'."

    lines = []
    for p in results:
        attrs = ", ".join(f"{k}: {v}" for k, v in list(p.get("attributes", {}).items())[:3])
        lines.append(
            f"[{p['id']}] {p['title']} — ₹{p['price']} | {p['category']}/{p.get('subcategory','')} | {attrs}"
        )
    return "\n".join(lines)


@tool
def get_offers(product_ids: list[str], cart_total: float) -> str:
    """Get available bank/card offers for the given product IDs and cart total.

    Returns applicable offers and the effective total after the best discount.
    """
    if not product_ids:
        return "No products in cart."

    applicable = []
    for card, (pct, min_val, desc) in _BANK_OFFERS.items():
        if cart_total >= min_val:
            discount = min(cart_total * pct / 100, {"HDFC": 500, "ICICI": 400, "SBI": 250}[card])
            applicable.append((card, discount, desc))

    if not applicable:
        return f"Cart total ₹{cart_total:.0f} — no bank offers applicable (minimum cart is ₹999)."

    applicable.sort(key=lambda x: x[1], reverse=True)
    lines = [f"Cart total: ₹{cart_total:.0f}", "", "Available offers:"]
    for card, discount, desc in applicable:
        effective = cart_total - discount
        lines.append(f"  • {card}: {desc} → saves ₹{discount:.0f}, effective total ₹{effective:.0f}")

    best_card, best_discount, _ = applicable[0]
    lines.append(f"\nBest offer: {best_card} card — pay ₹{cart_total - best_discount:.0f} after ₹{best_discount:.0f} discount.")
    return "\n".join(lines)


@tool
def get_product_details(product_id: str) -> str:
    """Retrieve full details for a specific product by its catalog ID (e.g. 'P001')."""
    for p in _CATALOG:
        if p["id"] == product_id:
            return json.dumps(p, indent=2)
    return f"Product '{product_id}' not found in catalog."


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a warm, knowledgeable e-commerce consultant for an Indian online store.
Your catalog spans travel gear, personal care, health, electronics, clothing, and luggage — all priced in INR.

You operate in TWO modes depending on what the user asks:

**Mode A — Single-product consultation**
When a user asks about a specific product or need (e.g. "best sunscreen", "recommend a power bank"),
help them narrow down to the single best catalog match. Ask clarifying questions (budget, use case,
skin type, etc.) as needed, then call search_catalog and present your top recommendation with reasoning.

**Mode B — Essentials kit assembly**
When a user expresses a goal or occasion — a trip ("I'm planning a summer vacation"), an event
("throwing a birthday party"), or a setup ("I want to start trekking") — assemble a curated
multi-item essentials kit. Follow these steps:

1. Ask 1–3 focused framing questions BEFORE building the kit. For travel: destination/climate,
   trip length in days, and trip type (leisure / adventure / business / family). Keep it brief.

2. Use the gathered context to REASON about what the traveller needs — do NOT use a fixed list.
   A beach holiday, winter trek, and business trip need very different kits. Think through
   categories: Sun & Skin, Toiletries, Clothing, Electronics, Health & Safety, Documents.

3. For each purchasable essential, call search_catalog to find the closest catalog match.
   Scale quantities to trip length where it makes sense (e.g. more sunscreen for 10+ days).
   For multi-day trips suggest extra toiletry sizes, extra clothing, etc.

4. Present the kit GROUPED with each product's title and price. Include a running subtotal.
   Non-purchasable items (passport, tickets, boarding passes, hotel booking confirmation) go
   in a separate "Checklist — bring these yourself" section, NOT as products.

5. After presenting the kit, call get_offers on the cart total to surface any bank card discount.

6. Allow the user to refine the kit: "drop the electronics", "I want cheaper sunscreen",
   "add a power bank". Re-assemble (re-call search_catalog as needed) and show the updated kit.

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

_CATALOG_BY_ID = {p["id"]: p for p in _CATALOG}


def _extract_product_ids(text: str) -> list[str]:
    """Pull P-prefixed IDs like [P001] or P001 out of tool result text."""
    import re
    return re.findall(r"\bP\d{3}\b", text)


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
            for pid in _extract_product_ids(result_str):
                product = _CATALOG_BY_ID.get(pid)
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
            print("Consultant: Happy travels! Goodbye!")
            break
        reply, history = chat(user_input, history)
        print(f"\nConsultant: {reply}\n")


if __name__ == "__main__":
    run_cli()
