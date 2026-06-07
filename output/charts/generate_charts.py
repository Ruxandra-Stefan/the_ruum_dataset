import duckdb
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import pandas as pd
import numpy as np
from pathlib import Path

con = duckdb.connect("dev.duckdb")
OUT = Path("output/charts")

# ── Shared style ──────────────────────────────────────────────────────────────
BG      = "#0f1117"
PANEL   = "#1a1d27"
ACCENT  = "#6c63ff"
WARN    = "#ff6b6b"
OK      = "#43d9ad"
MID     = "#f7c948"
TEXT    = "#e2e8f0"
MUTED   = "#64748b"
PALETTE = [ACCENT, OK, MID, WARN, "#60a5fa", "#fb923c", "#a78bfa"]

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": PANEL,
    "axes.edgecolor": MUTED, "axes.labelcolor": TEXT,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "text.color": TEXT, "grid.color": "#2d3448",
    "grid.linestyle": "--", "grid.alpha": 0.5,
    "font.family": "DejaVu Sans", "font.size": 11,
})

def fmt_k(x, _=None):
    return f"${x/1000:.0f}K" if x >= 1000 else f"${x:.0f}"

def save(fig, name):
    path = OUT / name
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  saved → {path}")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 1 — Revenue trend (monthly) with 3-month rolling average
# Level 4: shows revenue momentum, flags the Jan 2026 spike
# ══════════════════════════════════════════════════════════════════════════════
df_monthly = con.execute("""
    SELECT DATE_TRUNC('month', o.order_date)::date AS month,
           COUNT(DISTINCT o.order_id)              AS orders,
           ROUND(SUM(oi.line_total), 2)            AS revenue
    FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY 1 ORDER BY 1
""").df()
df_monthly["rolling"] = df_monthly["revenue"].rolling(3, min_periods=1).mean()
# drop partial last month
df_monthly = df_monthly[df_monthly["month"] < df_monthly["month"].max()]

fig, ax = plt.subplots(figsize=(14, 5))
ax.bar(df_monthly["month"], df_monthly["revenue"], width=20,
       color=ACCENT, alpha=0.55, label="Monthly revenue")
ax.plot(df_monthly["month"], df_monthly["rolling"],
        color=OK, linewidth=2.5, label="3-month avg")

# annotate Jan 2026 spike
peak = df_monthly.loc[df_monthly["revenue"].idxmax()]
ax.annotate(f"Peak ${peak.revenue/1000:.1f}K\n(Jan 2026)",
            xy=(peak.month, peak.revenue),
            xytext=(0, 18), textcoords="offset points",
            ha="center", color=MID, fontsize=9,
            arrowprops=dict(arrowstyle="-", color=MID, lw=1.2))

ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax.set_title("Monthly Revenue + 3-Month Rolling Average", fontsize=14, pad=14, color=TEXT)
ax.set_xlabel("Month"), ax.set_ylabel("Revenue (USD)")
ax.legend(facecolor=PANEL, edgecolor=MUTED, labelcolor=TEXT)
ax.grid(axis="y")

total = df_monthly["revenue"].sum()
ax.text(0.01, 0.95, f"Total gross revenue  ${total/1000:.1f}K  |  {len(df_monthly)} months",
        transform=ax.transAxes, fontsize=9, color=MUTED, va="top")
fig.tight_layout()
save(fig, "01_revenue_trend.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 — Order status financial impact (Level 4 — The Economist)
# "Cancelled orders cost the business $208K — 24.8% of gross revenue"
# ══════════════════════════════════════════════════════════════════════════════
df_status = con.execute("""
    SELECT o.order_status,
           COUNT(DISTINCT o.order_id) AS orders,
           ROUND(SUM(oi.line_total), 2) AS revenue
    FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY 1 ORDER BY revenue DESC
""").df()

gross = df_status["revenue"].sum()
df_status["pct"] = df_status["revenue"] / gross * 100
colors = {
    "delivered": OK, "shipped": ACCENT, "pending": MID, "cancelled": WARN,
    "pending_refund": "#fb923c"
}
bar_colors = [colors.get(s, MUTED) for s in df_status["order_status"]]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5),
                                gridspec_kw={"width_ratios": [1.4, 1]})

# Bar chart
bars = ax1.barh(df_status["order_status"], df_status["revenue"],
                color=bar_colors, height=0.55)
for bar, rev, pct in zip(bars, df_status["revenue"], df_status["pct"]):
    ax1.text(bar.get_width() + 2000, bar.get_y() + bar.get_height() / 2,
             f"${rev/1000:.0f}K  ({pct:.1f}%)",
             va="center", fontsize=10, color=TEXT)
ax1.set_xlim(0, df_status["revenue"].max() * 1.35)
ax1.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax1.set_title("Revenue by Order Status", fontsize=13, color=TEXT)
ax1.set_xlabel("Revenue (USD)")
ax1.grid(axis="x")

# Level 4 callout box
cancelled_rev = df_status.loc[df_status["order_status"] == "cancelled", "revenue"].values[0]
cancelled_pct = cancelled_rev / gross * 100
confirmed_rev = df_status.loc[df_status["order_status"] == "delivered", "revenue"].values[0]

ax2.axis("off")
callout = (
    f"Level 4 — Business Impact\n\n"
    f"[LOST]  Cancellations cost\n"
    f"    ${cancelled_rev/1000:.1f}K  ({cancelled_pct:.1f}% of gross)\n\n"
    f"[CONF]  Confirmed revenue\n"
    f"    ${confirmed_rev/1000:.1f}K  (only {confirmed_rev/gross*100:.1f}%)\n\n"
    f"[RISK]  Pending + Shipped\n"
    f"    ${(gross - cancelled_rev - confirmed_rev)/1000:.1f}K  at risk\n\n"
    f"Gross GMV:  ${gross/1000:.1f}K\n"
    f"Net confirmed:  ${confirmed_rev/1000:.1f}K"
)
ax2.text(0.05, 0.95, callout, transform=ax2.transAxes,
         fontsize=10.5, va="top", linespacing=1.7,
         bbox=dict(facecolor=PANEL, edgecolor=WARN, linewidth=1.5, pad=12))
fig.suptitle("Order Status Financial Impact", fontsize=15, y=1.01, color=TEXT)
fig.tight_layout()
save(fig, "02_order_status_impact.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 3 — Customer LTV Pareto (Level 4/5)
# "1,621 single-purchase customers drove 83% of revenue and never came back"
# ══════════════════════════════════════════════════════════════════════════════
df_ltv = con.execute("""
    SELECT o.user_id,
           COUNT(DISTINCT o.order_id) AS order_count,
           ROUND(SUM(oi.line_total), 2) AS ltv
    FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY o.user_id
    ORDER BY ltv DESC
""").df()

df_ltv["cumrev"] = df_ltv["ltv"].cumsum()
df_ltv["cumrev_pct"] = df_ltv["cumrev"] / df_ltv["ltv"].sum() * 100
df_ltv["cust_pct"] = (np.arange(1, len(df_ltv) + 1)) / len(df_ltv) * 100

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Pareto curve
ax1.plot(df_ltv["cust_pct"], df_ltv["cumrev_pct"], color=ACCENT, linewidth=2.5)
ax1.fill_between(df_ltv["cust_pct"], df_ltv["cumrev_pct"], alpha=0.15, color=ACCENT)
ax1.axhline(80, color=MID, linestyle="--", linewidth=1.2, alpha=0.7)
# find 80% point
idx_80 = (df_ltv["cumrev_pct"] >= 80).idxmax()
pct_80 = df_ltv.loc[idx_80, "cust_pct"]
ax1.axvline(pct_80, color=MID, linestyle="--", linewidth=1.2, alpha=0.7)
ax1.text(pct_80 + 1, 30, f"Top {pct_80:.0f}% of customers\ngenerate 80% of revenue",
         color=MID, fontsize=9)
ax1.set_xlabel("Cumulative % of Customers")
ax1.set_ylabel("Cumulative % of Revenue")
ax1.set_title("Customer Revenue Concentration (Pareto)", fontsize=13, color=TEXT)
ax1.grid()

# LTV segmentation bar
seg_labels = ["1 order\n(1,621 customers)", "2 orders\n(141 customers)", "3+ orders\n(5 customers)"]
seg_rev = [
    df_ltv.loc[df_ltv["order_count"] == 1, "ltv"].sum(),
    df_ltv.loc[df_ltv["order_count"] == 2, "ltv"].sum(),
    df_ltv.loc[df_ltv["order_count"] >= 3, "ltv"].sum(),
]
seg_colors = [WARN, MID, OK]
bars = ax2.bar(seg_labels, seg_rev, color=seg_colors, width=0.5)
for bar, rev in zip(bars, seg_rev):
    pct = rev / sum(seg_rev) * 100
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3000,
             f"${rev/1000:.0f}K\n({pct:.1f}%)", ha="center", fontsize=10, color=TEXT)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax2.set_title("Revenue by Purchase Frequency", fontsize=13, color=TEXT)
ax2.set_ylabel("Total Revenue (USD)")
ax2.grid(axis="y")

# Level 5 annotation
ax2.text(0.5, -0.22,
         "Level 5 — Action: Re-engage 1,621 single-purchase customers.\n"
         "Converting 5% to repeat buyers = ~$21K additional revenue.",
         transform=ax2.transAxes, ha="center", fontsize=9,
         color=OK, style="italic",
         bbox=dict(facecolor=PANEL, edgecolor=OK, linewidth=1, pad=8))
fig.suptitle("Customer Lifetime Value Analysis", fontsize=15, y=1.02, color=TEXT)
fig.tight_layout()
save(fig, "03_customer_ltv.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 4 — Product category revenue + avg order value
# ══════════════════════════════════════════════════════════════════════════════
df_cat = con.execute("""
    SELECT p.category,
           COUNT(oi.order_item_id) AS items_sold,
           ROUND(SUM(oi.line_total), 2) AS revenue,
           ROUND(AVG(oi.unit_price), 2) AS avg_unit_price,
           ROUND(AVG(oi.discount) * 100, 1) AS avg_discount_pct
    FROM order_items oi JOIN products p ON oi.product_id = p.id
    GROUP BY 1 ORDER BY revenue DESC
""").df()

fig, axes = plt.subplots(1, 3, figsize=(14, 5))

# Revenue
bars = axes[0].bar(df_cat["category"], df_cat["revenue"],
                   color=[OK, ACCENT, MID], width=0.5)
for bar, rev in zip(bars, df_cat["revenue"]):
    axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2000,
                 fmt_k(rev), ha="center", fontsize=10)
axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
axes[0].set_title("Revenue by Category", color=TEXT)
axes[0].set_ylabel("Revenue (USD)")
axes[0].grid(axis="y")

# Avg unit price
bars2 = axes[1].bar(df_cat["category"], df_cat["avg_unit_price"],
                    color=[OK, ACCENT, MID], width=0.5)
for bar, val in zip(bars2, df_cat["avg_unit_price"]):
    axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                 f"${val:.0f}", ha="center", fontsize=10)
axes[1].set_title("Avg Unit Price by Category", color=TEXT)
axes[1].set_ylabel("Avg Price (USD)")
axes[1].grid(axis="y")

# Avg discount
bars3 = axes[2].bar(df_cat["category"], df_cat["avg_discount_pct"],
                    color=[OK, ACCENT, MID], width=0.5)
for bar, val in zip(bars3, df_cat["avg_discount_pct"]):
    axes[2].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                 f"{val}%", ha="center", fontsize=10)
axes[2].set_title("Avg Discount % by Category", color=TEXT)
axes[2].set_ylabel("Discount (%)")
axes[2].grid(axis="y")

fig.suptitle("Product Category Performance", fontsize=15, y=1.02, color=TEXT)
fig.tight_layout()
save(fig, "04_category_performance.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 5 — Top 15 states by revenue (supply chain exclusions flagged)
# Level 4: flags AK revenue that may need compliance routing
# ══════════════════════════════════════════════════════════════════════════════
df_state = con.execute("""
    SELECT l.state,
           CASE WHEN l.state IN ('AK','HI') THEN true ELSE false END AS excluded,
           COUNT(DISTINCT o.order_id) AS orders,
           ROUND(SUM(oi.line_total), 2) AS revenue
    FROM orders o
    JOIN users u ON o.user_id = u.user_id
    JOIN locations l ON u.location_id = l.location_id
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY 1, 2 ORDER BY revenue DESC
    LIMIT 15
""").df()

state_colors = [WARN if exc else ACCENT for exc in df_state["excluded"]]

fig, ax = plt.subplots(figsize=(13, 6))
bars = ax.barh(df_state["state"], df_state["revenue"], color=state_colors, height=0.6)
for bar, rev in zip(bars, df_state["revenue"]):
    ax.text(bar.get_width() + 400, bar.get_y() + bar.get_height() / 2,
            fmt_k(rev), va="center", fontsize=9, color=TEXT)
ax.set_xlim(0, df_state["revenue"].max() * 1.2)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax.set_title("Top 15 States by Revenue  (red = Supply Chain Excluded)", fontsize=13, color=TEXT)
ax.set_xlabel("Revenue (USD)")
ax.invert_yaxis()
ax.grid(axis="x")

legend = [
    mpatches.Patch(color=ACCENT, label="Standard fulfillment"),
    mpatches.Patch(color=WARN,   label="Supply chain excluded (AK / HI)"),
]
ax.legend(handles=legend, facecolor=PANEL, edgecolor=MUTED, labelcolor=TEXT, loc="lower right")
fig.tight_layout()
save(fig, "05_state_revenue.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 6 — AOV distribution + payment method breakdown
# ══════════════════════════════════════════════════════════════════════════════
df_aov = con.execute("""
    SELECT o.order_id, o.payment_method,
           ROUND(SUM(oi.line_total), 2) AS order_value
    FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY 1, 2
""").df()

df_pay = df_aov.groupby("payment_method").agg(
    orders=("order_id", "count"),
    revenue=("order_value", "sum")
).reset_index()
df_pay["avg_order"] = df_pay["revenue"] / df_pay["orders"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# AOV histogram
ax1.hist(df_aov["order_value"], bins=40, color=ACCENT, edgecolor=BG, alpha=0.85)
median_aov = df_aov["order_value"].median()
mean_aov = df_aov["order_value"].mean()
ax1.axvline(median_aov, color=OK, linewidth=2, linestyle="--",
            label=f"Median ${median_aov:.0f}")
ax1.axvline(mean_aov, color=MID, linewidth=2, linestyle="--",
            label=f"Mean ${mean_aov:.0f}")
ax1.set_title("Order Value Distribution (AOV)", fontsize=13, color=TEXT)
ax1.set_xlabel("Order Value (USD)")
ax1.set_ylabel("Number of Orders")
ax1.legend(facecolor=PANEL, edgecolor=MUTED, labelcolor=TEXT)
ax1.grid(axis="y")

# Payment method
wedges, texts, autotexts = ax2.pie(
    df_pay["revenue"], labels=df_pay["payment_method"],
    colors=[ACCENT, OK, MID],
    autopct="%1.1f%%", startangle=140,
    textprops={"color": TEXT},
    wedgeprops={"edgecolor": BG, "linewidth": 2}
)
for at in autotexts:
    at.set_fontsize(10)
ax2.set_title("Revenue by Payment Method", fontsize=13, color=TEXT)

fig.suptitle("Order Value & Payment Analysis", fontsize=15, y=1.02, color=TEXT)
fig.tight_layout()
save(fig, "06_aov_payment.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 7 — Metric map (connected system — Level 5 Strategist view)
# Shows how metrics influence each other across the funnel
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(14, 7))
ax.set_xlim(0, 10), ax.set_ylim(0, 6)
ax.axis("off")
ax.set_facecolor(BG)
fig.patch.set_facecolor(BG)

metrics = {
    # (x, y, label, value, color)
    "users":     (1.1, 4.8, "Total Users",       "12,483",   ACCENT),
    "purchasers":(1.1, 3.0, "Purchasing Users",   "1,767",    ACCENT),
    "repeat":    (1.1, 1.2, "Repeat Purchasers",  "146",      WARN),
    "orders":    (4.0, 4.8, "Total Orders",       "1,918",    MID),
    "aov":       (4.0, 3.0, "Avg Order Value",    f"${mean_aov:.0f}", MID),
    "cancelled": (4.0, 1.2, "Cancellation Rate",  "24.1%",    WARN),
    "revenue":   (7.5, 4.5, "Gross GMV",          "$838K",    OK),
    "confirmed": (7.5, 3.0, "Confirmed Revenue",  "$197K",    OK),
    "ltv":       (7.5, 1.5, "Avg Customer LTV",   f"${df_ltv['ltv'].mean():.0f}", MID),
}

boxes = {}
for key, (x, y, label, val, color) in metrics.items():
    box = ax.text(x, y, f"{label}\n{val}", ha="center", va="center",
                  fontsize=10, color=BG, fontweight="bold",
                  bbox=dict(facecolor=color, edgecolor=color,
                            boxstyle="round,pad=0.5", alpha=0.92))
    boxes[key] = (x, y)

arrows = [
    ("users",     "purchasers", "converts"),
    ("purchasers","repeat",     "retention"),
    ("purchasers","orders",     "places"),
    ("orders",    "aov",        "drives"),
    ("orders",    "cancelled",  "risk"),
    ("aov",       "revenue",    "× volume"),
    ("cancelled", "confirmed",  "reduces"),
    ("revenue",   "confirmed",  "net of cancel"),
    ("orders",    "revenue",    "feeds"),
    ("aov",       "ltv",        "builds"),
]

for src, dst, label in arrows:
    x1, y1 = boxes[src]
    x2, y2 = boxes[dst]
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=MUTED,
                                lw=1.3, connectionstyle="arc3,rad=0.08"))
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    ax.text(mx, my + 0.12, label, ha="center", fontsize=7.5, color=MUTED)

ax.set_title("Metric Map — How Key Metrics Connect  (Level 5: Strategist View)",
             fontsize=14, color=TEXT, pad=16)
ax.text(0.5, -0.03,
        "Action priorities: (1) Reduce cancellation rate  (2) Re-engage 1,621 single-purchase customers  (3) Grow AOV through category mix",
        transform=ax.transAxes, ha="center", fontsize=9.5, color=OK,
        bbox=dict(facecolor=PANEL, edgecolor=OK, linewidth=1.2, pad=8))
save(fig, "07_metric_map.png")

print("\nAll charts generated.")
