const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "ShopSmart AI";

// Palette
const NAVY    = "1E3A5F";
const BLUE    = "2563EB";
const LBLUE   = "EBF2FF";
const MID     = "93B4DC";
const WHITE   = "FFFFFF";
const GRAY    = "64748B";
const LGRAY   = "F5F8FF";
const TEXT    = "1E293B";
const BORDER  = "D1DFF5";

const makeShadow = () => ({ type: "outer", blur: 8, offset: 3, angle: 135, color: "1E3A5F", opacity: 0.08 });

// ── SLIDE 1: The Problem ────────────────────────────────────────────────────
const s1 = pres.addSlide();
s1.background = { color: LGRAY };

// Left navy sidebar
s1.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.22, h: 5.625, fill: { color: NAVY }, line: { color: NAVY } });

// Top header band
s1.addShape(pres.shapes.RECTANGLE, { x: 0.22, y: 0, w: 9.78, h: 1.25, fill: { color: WHITE }, line: { color: BORDER, pt: 0 }, shadow: makeShadow() });

// Label chip
s1.addShape(pres.shapes.RECTANGLE, { x: 0.45, y: 0.2, w: 1.3, h: 0.3, fill: { color: LBLUE }, line: { color: BLUE, pt: 1 } });
s1.addText("THE PROBLEM", { x: 0.45, y: 0.2, w: 1.3, h: 0.3, fontSize: 8, bold: true, color: BLUE, align: "center", valign: "middle", margin: 0 });

// Slide title
s1.addText("Online Shopping Has a Guidance Gap", {
  x: 0.45, y: 0.55, w: 7.8, h: 0.6,
  fontSize: 28, bold: true, color: NAVY, fontFace: "Calibri", align: "left", valign: "middle", margin: 0
});

// Subtitle
s1.addText("Users know what they want to achieve — but no platform helps them get there.", {
  x: 0.45, y: 1.02, w: 7.8, h: 0.22,
  fontSize: 12, color: GRAY, fontFace: "Calibri", align: "left", valign: "middle", margin: 0
});

// 4 problem cards  (2 × 2)
const cards = [
  { icon: "😵", title: "Decision Paralysis", body: "Searching \"best sunscreen\" returns thousands of results with no personalisation, no context, and no helpful budget filter." },
  { icon: "🧳", title: "Goal ≠ Product List",  body: "\"I'm going trekking next week\" — no platform converts that intent into a curated, ready-to-buy kit." },
  { icon: "🗂️", title: "Tab Overload",         body: "Shoppers open 15+ tabs comparing specs and prices across marketplaces. Confusion leads directly to cart abandonment." },
  { icon: "💸", title: "Missed Savings",        body: "Budget constraints and price-band deals are buried in search results — most shoppers never find the best value." },
];

const col = [0.45, 5.22];
const row = [1.55, 3.45];
const CW = 4.55, CH = 1.7;

cards.forEach((c, i) => {
  const x = col[i % 2];
  const y = row[Math.floor(i / 2)];

  s1.addShape(pres.shapes.RECTANGLE, { x, y, w: CW, h: CH, fill: { color: WHITE }, line: { color: BORDER, pt: 1 }, shadow: makeShadow() });
  // Accent left bar
  s1.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.06, h: CH, fill: { color: BLUE }, line: { color: BLUE } });

  // Icon
  s1.addText(c.icon, { x: x + 0.18, y: y + 0.18, w: 0.55, h: 0.55, fontSize: 22, align: "center", valign: "middle", margin: 0 });

  // Title
  s1.addText(c.title, { x: x + 0.78, y: y + 0.14, w: 3.6, h: 0.35, fontSize: 13, bold: true, color: NAVY, fontFace: "Calibri", align: "left", valign: "middle", margin: 0 });

  // Body
  s1.addText(c.body, { x: x + 0.78, y: y + 0.5, w: 3.6, h: 1.05, fontSize: 11, color: GRAY, fontFace: "Calibri", align: "left", valign: "top", margin: 0, wrap: true });
});

// Stat callout bottom-right
s1.addShape(pres.shapes.RECTANGLE, { x: 7.2, y: 3.45, w: 2.57, h: 1.7, fill: { color: NAVY }, line: { color: NAVY }, shadow: makeShadow() });
s1.addText("70%", { x: 7.2, y: 3.58, w: 2.57, h: 0.72, fontSize: 48, bold: true, color: WHITE, fontFace: "Calibri", align: "center", valign: "middle", margin: 0 });
s1.addText("of shoppers abandon\ntheir cart mid-session", { x: 7.2, y: 4.32, w: 2.57, h: 0.6, fontSize: 10, color: MID, fontFace: "Calibri", align: "center", valign: "top", margin: 0 });

// Footer
s1.addShape(pres.shapes.RECTANGLE, { x: 0.22, y: 5.25, w: 9.78, h: 0.375, fill: { color: NAVY }, line: { color: NAVY } });
s1.addText("ShopSmart AI", { x: 0.4, y: 5.25, w: 4, h: 0.375, fontSize: 11, bold: true, color: WHITE, fontFace: "Calibri", align: "left", valign: "middle", margin: 0 });
s1.addText("1 / 2", { x: 6, y: 5.25, w: 3.8, h: 0.375, fontSize: 10, color: MID, fontFace: "Calibri", align: "right", valign: "middle", margin: 0 });


// ── SLIDE 2: Solution · AI Role · Cost ─────────────────────────────────────
const s2 = pres.addSlide();
s2.background = { color: LGRAY };

// Left sidebar
s2.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.22, h: 5.625, fill: { color: BLUE }, line: { color: BLUE } });

// Header band
s2.addShape(pres.shapes.RECTANGLE, { x: 0.22, y: 0, w: 9.78, h: 1.25, fill: { color: WHITE }, line: { color: BORDER, pt: 0 }, shadow: makeShadow() });

s1.addShape(pres.shapes.RECTANGLE, { x: 0.45, y: 0.2, w: 1.6, h: 0.3, fill: { color: LBLUE }, line: { color: BLUE, pt: 1 } });
s2.addShape(pres.shapes.RECTANGLE, { x: 0.45, y: 0.2, w: 1.6, h: 0.3, fill: { color: LBLUE }, line: { color: BLUE, pt: 1 } });
s2.addText("THE SOLUTION", { x: 0.45, y: 0.2, w: 1.6, h: 0.3, fontSize: 8, bold: true, color: BLUE, align: "center", valign: "middle", margin: 0 });

s2.addText("ShopSmart: Your AI-Powered E-Commerce Consultant", {
  x: 0.45, y: 0.55, w: 9.0, h: 0.6,
  fontSize: 26, bold: true, color: NAVY, fontFace: "Calibri", align: "left", valign: "middle", margin: 0
});
s2.addText("Goal-driven shopping powered by LLM reasoning + live eBay product data", {
  x: 0.45, y: 1.02, w: 9.0, h: 0.22,
  fontSize: 12, color: GRAY, fontFace: "Calibri", align: "left", valign: "middle", margin: 0
});

// ── LEFT COLUMN: AI Role (flow steps) ──
s2.addText("HOW AI POWERS IT", { x: 0.45, y: 1.4, w: 4.3, h: 0.25, fontSize: 9, bold: true, color: BLUE, fontFace: "Calibri", charSpacing: 1, margin: 0 });

const steps = [
  { num: "1", title: "Understand Intent",        body: "GPT-4o-mini reads the user's goal and asks 1–3 smart clarifying questions (destination, budget, trip type)." },
  { num: "2", title: "Tool Orchestration",        body: "LangGraph agent calls search_catalog and get_product_details — bound tools that hit the live eBay API." },
  { num: "3", title: "Reason & Curate",           body: "LLM reasons over real results, groups by category, filters by budget, and surfaces only verified purchasable items." },
  { num: "4", title: "Deliver & Checkout",        body: "Streamlit renders the product grid and cart. Users add items, view totals, and complete checkout in one session." },
];

steps.forEach((st, i) => {
  const sy = 1.75 + i * 0.88;
  // Number circle
  s2.addShape(pres.shapes.OVAL, { x: 0.45, y: sy + 0.05, w: 0.38, h: 0.38, fill: { color: BLUE }, line: { color: BLUE } });
  s2.addText(st.num, { x: 0.45, y: sy + 0.05, w: 0.38, h: 0.38, fontSize: 11, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0 });
  // Title
  s2.addText(st.title, { x: 0.95, y: sy + 0.04, w: 3.6, h: 0.26, fontSize: 12, bold: true, color: NAVY, fontFace: "Calibri", align: "left", valign: "middle", margin: 0 });
  // Body
  s2.addText(st.body, { x: 0.95, y: sy + 0.32, w: 3.6, h: 0.48, fontSize: 10, color: GRAY, fontFace: "Calibri", align: "left", valign: "top", margin: 0, wrap: true });
  // Divider (skip last)
  if (i < 3) {
    s2.addShape(pres.shapes.LINE, { x: 0.45, y: sy + 0.82, w: 4.1, h: 0, line: { color: BORDER, pt: 0.75 } });
  }
});

// Vertical divider between columns
s2.addShape(pres.shapes.LINE, { x: 5.1, y: 1.38, w: 0, h: 3.72, line: { color: BORDER, pt: 1.5 } });

// ── RIGHT COLUMN: Token Usage & Cost ──
s2.addText("TOKEN USAGE & COST", { x: 5.28, y: 1.4, w: 4.5, h: 0.25, fontSize: 9, bold: true, color: BLUE, fontFace: "Calibri", charSpacing: 1, margin: 0 });

// Cost rows
const rows = [
  { label: "Model",             val: "GPT-4o-mini" },
  { label: "Input pricing",     val: "$0.15 / 1M tokens" },
  { label: "Output pricing",    val: "$0.60 / 1M tokens" },
  { label: "System prompt",     val: "~240 tokens / turn" },
  { label: "eBay tool results", val: "50–200 tokens / call" },
  { label: "Max tokens / turn", val: "4,096 (capped)" },
];

rows.forEach((r, i) => {
  const ry = 1.75 + i * 0.44;
  const bg = i % 2 === 0 ? WHITE : LGRAY;
  s2.addShape(pres.shapes.RECTANGLE, { x: 5.28, y: ry, w: 4.5, h: 0.42, fill: { color: bg }, line: { color: BORDER, pt: 0.5 } });
  s2.addText(r.label, { x: 5.38, y: ry, w: 2.5, h: 0.42, fontSize: 11, color: TEXT,  fontFace: "Calibri", align: "left",  valign: "middle", margin: 0 });
  s2.addText(r.val,   { x: 7.88, y: ry, w: 1.8, h: 0.42, fontSize: 11, bold: true, color: NAVY, fontFace: "Calibri", align: "right", valign: "middle", margin: 0 });
});

// Cost highlight box
s2.addShape(pres.shapes.RECTANGLE, { x: 5.28, y: 4.42, w: 4.5, h: 0.7, fill: { color: NAVY }, line: { color: NAVY }, shadow: makeShadow() });
s2.addText("Est. cost per user message", { x: 5.38, y: 4.42, w: 2.6, h: 0.7, fontSize: 10, color: MID, fontFace: "Calibri", align: "left", valign: "middle", margin: 0 });
s2.addText("$0.001 – $0.003", { x: 7.0, y: 4.42, w: 2.68, h: 0.7, fontSize: 18, bold: true, color: WHITE, fontFace: "Calibri", align: "right", valign: "middle", margin: 0 });

// Footer
s2.addShape(pres.shapes.RECTANGLE, { x: 0.22, y: 5.25, w: 9.78, h: 0.375, fill: { color: NAVY }, line: { color: NAVY } });
s2.addText("ShopSmart AI", { x: 0.4, y: 5.25, w: 4, h: 0.375, fontSize: 11, bold: true, color: WHITE, fontFace: "Calibri", align: "left", valign: "middle", margin: 0 });
s2.addText("2 / 2", { x: 6, y: 5.25, w: 3.8, h: 0.375, fontSize: 10, color: MID, fontFace: "Calibri", align: "right", valign: "middle", margin: 0 });

pres.writeFile({ fileName: "C:\\agent_dev_works\\ecom-consultant\\ShopSmart_AI.pptx" }).then(() => {
  console.log("Done: ShopSmart_AI.pptx");
}).catch(e => { console.error(e); process.exit(1); });
