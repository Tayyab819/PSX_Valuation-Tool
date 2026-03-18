import gradio as gr
import requests


# ═══════════════════════════════════════════════════════════════
#  MARKET PRICE  — Direct Yahoo Finance API (no yfinance)
# ═══════════════════════════════════════════════════════════════
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://finance.yahoo.com/",
    "Origin": "https://finance.yahoo.com",
}


def get_price(ticker: str):
    """
    Fetches the latest market price by calling Yahoo Finance's
    internal JSON endpoints directly — no yfinance caching layer.

    PSX tickers must use the .KA suffix  (e.g. SYS.KA, OGDC.KA).
    Global tickers work as-is            (e.g. AAPL, TSLA).
    """
    ticker = ticker.strip().upper()

    # ── Method 1 : v7/finance/quote  (real-time quote object) ──────────────
    try:
        url = (
            f"https://query1.finance.yahoo.com/v7/finance/quote"
            f"?symbols={ticker}"
            f"&fields=regularMarketPrice,previousClose,regularMarketPreviousClose"
        )
        r = requests.get(url, headers=_HEADERS, timeout=10)
        r.raise_for_status()
        results = r.json()["quoteResponse"]["result"]
        if results:
            res = results[0]
            price = (
                res.get("regularMarketPrice")
                or res.get("previousClose")
                or res.get("regularMarketPreviousClose")
            )
            if price and float(price) > 0:
                return float(price)
    except Exception:
        pass

    # ── Method 2 : v8/finance/chart  (OHLC time-series, 5-day window) ──────
    try:
        url = (
            f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?interval=1d&range=5d"
        )
        r = requests.get(url, headers=_HEADERS, timeout=10)
        r.raise_for_status()
        closes = (
            r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        )
        valid = [c for c in closes if c is not None]
        if valid:
            return float(valid[-1])
    except Exception:
        pass

    # ── Method 3 : v10/finance/quoteSummary  (fundamental summary) ─────────
    try:
        url = (
            f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"
            f"?modules=price"
        )
        r = requests.get(url, headers=_HEADERS, timeout=10)
        r.raise_for_status()
        price_module = r.json()["quoteSummary"]["result"][0]["price"]
        price = (
            price_module.get("regularMarketPrice", {}).get("raw")
            or price_module.get("regularMarketPreviousClose", {}).get("raw")
        )
        if price and float(price) > 0:
            return float(price)
    except Exception:
        pass

    return None


# ═══════════════════════════════════════════════════════════════
#  BUY / SELL SIGNAL
# ═══════════════════════════════════════════════════════════════
def buy_sell_signal(MOS: float) -> str:
    if MOS > 20:
        return "✅ Strong Buy"
    elif MOS > 5:
        return "🟢 Buy"
    elif MOS < 0:
        return "🔴 Sell"
    else:
        return "🟡 Hold"


# ═══════════════════════════════════════════════════════════════
#  STOCK VALUATION
# ═══════════════════════════════════════════════════════════════
def valuation(
    Ticker, Equity, Debt, Free_rate, Market_rate, Beta,
    Earnings, Historical_Earnings, PE_ratio, Dividend,
    Tax_rate, Rate,
):
    price = get_price(Ticker)
    if price is None:
        return (
            "❌ Ticker not found — use .KA suffix for PSX (e.g. SYS.KA)",
            "-", "-", "-", "-", "-", "-",
        )

    # Cost of Equity  (CAPM)
    ke = Free_rate + (Market_rate - Free_rate) * Beta

    # After-tax Cost of Debt
    kd = Rate * (1 - Tax_rate / 100)

    # WACC
    total = Equity + Debt
    if total == 0:
        return "❌ Equity + Debt cannot be zero", "-", "-", "-", "-", "-", "-"
    Wacc = (Equity / total) * ke + (Debt / total) * kd

    # 5-year CAGR Earnings Growth
    try:
        growth = (Earnings / Historical_Earnings) ** (1 / 5) - 1
    except Exception:
        growth = 0

    FE     = Earnings * (1 + growth)
    FMV_PE = FE * PE_ratio

    FMV_DDM = (
        Dividend * (1 + growth) / (ke / 100 - growth)
        if (ke / 100) > growth else 0
    )

    MOS    = ((FMV_PE - price) / FMV_PE) * 100 if FMV_PE != 0 else 0
    signal = buy_sell_signal(MOS)

    return (
        round(price,   2),
        round(FE,      2),
        round(FMV_PE,  2),
        round(FMV_DDM, 2),
        round(MOS,     2),
        round(Wacc,    2),
        signal,
    )


# ═══════════════════════════════════════════════════════════════
#  PRICE CHECKER
# ═══════════════════════════════════════════════════════════════
def check_price(ticker: str):
    price = get_price(ticker)
    if price is None:
        return (
            "❌ Could not fetch price.\n"
            "• PSX stocks → add .KA suffix  (e.g. SYS.KA, OGDC.KA, HBL.KA)\n"
            "• Global stocks → use plain ticker  (e.g. AAPL, TSLA)"
        )
    return f"{round(price, 2)}"


# ═══════════════════════════════════════════════════════════════
#  INCOME TAX CALCULATOR  (Pakistan — FY 2024-25)
# ═══════════════════════════════════════════════════════════════
def tax_calculator(profession, income):
    income = float(income)

    if profession == "Salary":
        if income <= 600000:
            tax = 0
        elif 600000 < income <= 1200000:
            tax = income * 0.01
        elif 1200000 < income <= 2200000:
            tax = income * 0.11
        elif 2200000 < income <= 3200000:
            tax = income * 0.23
        elif 3200000 < income <= 4100000:
            tax = income * 0.30
        else:
            tax = income * 0.35
        # Surcharge
        if income > 10000000:
            tax = tax + (tax * 0.9)

    elif profession == "Business":
        if income <= 600000:
            tax = 0
        elif 600000 < income <= 1200000:
            tax = income * 0.15
        elif 1200000 < income <= 1600000:
            tax = income * 0.20
        elif 1600000 < income <= 3200000:
            tax = income * 0.30
        elif 3200000 < income <= 5600000:
            tax = income * 0.40
        else:
            tax = income * 0.45

    else:
        return "❌ Unknown profession"

    return f"Tax Payable = {round(tax, 2)} PKR"


# ═══════════════════════════════════════════════════════════════
#  CAPITAL GAINS TAX  (Pakistan securities)
# ═══════════════════════════════════════════════════════════════
def capital_gain_tax(gain, holding_period):
    gain           = float(gain)
    holding_period = float(holding_period)

    # Tax rate based on holding period
    if holding_period <= 1:
        tax = gain * 0.15
    elif 1 < holding_period <= 2:
        tax = gain * 0.125
    elif 2 < holding_period <= 3:
        tax = gain * 0.10
    elif 3 < holding_period <= 4:
        tax = gain * 0.075
    elif 4 < holding_period <= 5:
        tax = gain * 0.05
    elif 5 < holding_period <= 6:
        tax = gain * 0.025
    else:
        tax = 0

    net_gain = gain - tax
    return round(tax, 2), round(net_gain, 2)


# ═══════════════════════════════════════════════════════════════
#  GRADIO UI
# ═══════════════════════════════════════════════════════════════
with gr.Blocks(title="PSX Investor Toolkit", theme=gr.themes.Soft()) as app:

    gr.Markdown(
        """
        # 📈 PSX Investor Toolkit
        _Real-time Prices · Valuation · Income Tax · Capital Gains Tax_

        > **PSX tickers** require the `.KA` suffix — e.g. `SYS.KA` · `OGDC.KA` · `HBL.KA` · `ENGRO.KA`  
        > **Global tickers** use the plain symbol — e.g. `AAPL` · `TSLA` · `GOOGL`
        """
    )

    with gr.Tabs():

        # ── TAB 1 : STOCK VALUATION ─────────────────────────────────────────
        with gr.Tab("📊 Stock Valuation"):
            gr.Markdown("### Enter company fundamentals to compute fair value and buy / sell signal.")

            with gr.Row():
                with gr.Column():
                    ticker      = gr.Textbox(label="Stock Ticker", placeholder="e.g. SYS.KA")
                    Equity      = gr.Number(label="Equity (PKR)")
                    Debt        = gr.Number(label="Debt (PKR)")
                    Free_rate   = gr.Number(label="Risk-Free Rate (%)",           value=15)
                    Market_rate = gr.Number(label="Expected Market Return (%)",   value=18)
                    Beta        = gr.Number(label="Beta",                         value=1.0)

                with gr.Column():
                    Earnings            = gr.Number(label="Current Earnings (EPS or Net Profit)")
                    Historical_Earnings = gr.Number(label="Earnings 5 Years Ago")
                    PE_ratio            = gr.Number(label="PE Ratio",             value=10)
                    Dividend            = gr.Number(label="Annual Dividend (PKR)")
                    Tax_rate            = gr.Number(label="Corporate Tax Rate (%)", value=29)
                    Rate                = gr.Number(label="Debt / Interest Rate (%)", value=22)

            val_btn = gr.Button("🔍 Calculate Valuation", variant="primary")

            with gr.Row():
                price_out  = gr.Textbox(label="Current Market Price")
                FE_out     = gr.Textbox(label="Forward Earnings")
                FV_PE_out  = gr.Textbox(label="Fair Value — PE Method")
                FV_DDM_out = gr.Textbox(label="Fair Value — DDM Method")
                MOS_out    = gr.Textbox(label="Margin of Safety (%)")
                WACC_out   = gr.Textbox(label="WACC (%)")
                signal_out = gr.Textbox(label="Signal")

            val_btn.click(
                valuation,
                inputs=[
                    ticker, Equity, Debt, Free_rate, Market_rate, Beta,
                    Earnings, Historical_Earnings, PE_ratio, Dividend,
                    Tax_rate, Rate,
                ],
                outputs=[price_out, FE_out, FV_PE_out, FV_DDM_out,
                         MOS_out, WACC_out, signal_out],
            )

        # ── TAB 2 : PRICE CHECKER ───────────────────────────────────────────
        with gr.Tab("💹 Stock Price"):
            gr.Markdown(
                "### Look up the current market price for any PSX or global ticker."
            )
            ticker2 = gr.Textbox(
                label="Stock Ticker",
                placeholder="e.g.  SYS.KA  |  OGDC.KA  |  AAPL",
            )
            btn2   = gr.Button("Get Current Price", variant="primary")
            price2 = gr.Textbox(label="Current Market Price")

            btn2.click(check_price, inputs=[ticker2], outputs=[price2])

        # ── TAB 3 : INCOME TAX ──────────────────────────────────────────────
        with gr.Tab("🧾 Income Tax"):
            gr.Markdown(
                "### Pakistan Income Tax Calculator — FY 2024-25\n"
                "Covers both **Salary** and **Business** income slabs, including the 90% surcharge above PKR 10M."
            )

            with gr.Row():
                with gr.Column():
                    profession = gr.Dropdown(
                        ["Salary", "Business"],
                        label="Profession / Income Type",
                    )
                    income  = gr.Number(label="Annual Income (PKR)")
                    tax_btn = gr.Button("Calculate Tax", variant="primary")

                with gr.Column():
                    tax_output = gr.Textbox(label="Tax Result", lines=3)

            tax_btn.click(tax_calculator, inputs=[profession, income], outputs=[tax_output])

        # ── TAB 4 : CAPITAL GAINS TAX ───────────────────────────────────────
        with gr.Tab("📉 Capital Gain Tax"):
            gr.Markdown(
                "### Pakistan CGT on Securities\n"
                "| Holding Period | Tax Rate |\n"
                "|---|---|\n"
                "| ≤ 1 year | 15% |\n"
                "| 1 – 2 years | 12.5% |\n"
                "| 2 – 3 years | 10% |\n"
                "| 3 – 4 years | 7.5% |\n"
                "| 4 – 5 years | 5% |\n"
                "| 5 – 6 years | 2.5% |\n"
                "| > 6 years | 0% |"
            )

            with gr.Row():
                with gr.Column():
                    gain    = gr.Number(label="Capital Gain (PKR)")
                    holding = gr.Number(label="Holding Period (Years)", value=1)
                    cg_btn  = gr.Button("Calculate CGT", variant="primary")

                with gr.Column():
                    cg_tax = gr.Textbox(label="Tax Payable (PKR)")
                    cg_net = gr.Textbox(label="Net Gain After Tax (PKR)")

            cg_btn.click(capital_gain_tax, inputs=[gain, holding], outputs=[cg_tax, cg_net])


app.launch()
