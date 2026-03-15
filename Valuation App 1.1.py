import gradio as gr
import yfinance as yf

# ---------- Get Market Price ----------
def get_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if data.empty:
            return None
        return float(data["Close"].iloc[-1])
    except:
        return None

# ---------- Valuation Function ----------
def valuation(Ticker, Equity, Debt, Free_rate, Market_rate, Beta,
              Earnings, Historical_Earnings, PE_ratio, Dividend,
              Tax_rate, Rate):

    price = get_price(Ticker)
    if price is None:
        return "Ticker not found", "-", "-", "-", "-", "-", "-"

    # Cost of Equity
    ke = Free_rate + (Market_rate - Free_rate) * Beta

    # Cost of Debt
    kd = Rate * (1 - Tax_rate/100)

    # WACC
    total = Equity + Debt
    Wacc = (Equity/total)*ke + (Debt/total)*kd

    # Growth
    try:
        growth = ((Earnings/Historical_Earnings)**(1/5) - 1)
    except:
        growth = 0

    # Future Earnings
    FE = Earnings * (1 + growth)

    # PE valuation
    FMV_PE = FE * PE_ratio

    # Dividend Discount Model
    if ke/100 > growth:
        FMV_DDM = Dividend*(1+growth)/(ke/100 - growth)
    else:
        FMV_DDM = 0

    # Margin of Safety
    MOS = ((FMV_PE - price)/FMV_PE)*100 if FMV_PE != 0 else 0

    # Buy/Sell Signal
    signal = buy_sell_signal(MOS)

    return round(price,2), round(FE,2), round(FMV_PE,2), round(FMV_DDM,2), round(MOS,2), round(Wacc,2), signal

# ---------- Price Checker ----------
def check_price(ticker):
    price = get_price(ticker)
    if price is None:
        return "Ticker not found"
    return round(price,2)

# ---------- Buy/Sell Signal ----------
def buy_sell_signal(MOS):
    if MOS > 20:
        return "✅ Strong Buy"
    elif MOS > 5:
        return "🟢 Buy"
    elif MOS < 0:
        return "🔴 Sell"
    else:
        return "🟡 Hold"

# ---------- UI ----------
with gr.Blocks(title="PSX Analysis Terminal") as app:

    gr.Markdown("# 📊 PSX Stock Analysis System")

    with gr.Tabs():

        # -------- TAB 1 : VALUATION --------
        with gr.Tab("Valuation Tool"):

            ticker = gr.Textbox(label="Stock Ticker (example: SYS.KA)")
            Equity = gr.Number(label="Equity")
            Debt = gr.Number(label="Debt")
            Free_rate = gr.Number(label="Free Rate (%)")
            Market_rate = gr.Number(label="Market Rate (%)")
            Beta = gr.Number(label="Beta")
            Earnings = gr.Number(label="Current Earnings")
            Historical_Earnings = gr.Number(label="Historical Earnings (5 Years Ago)")
            PE_ratio = gr.Number(label="PE Ratio")
            Dividend = gr.Number(label="Dividend")
            Tax_rate = gr.Number(label="Tax Rate (%)")
            Rate = gr.Number(label="Interest Rate (%)")

            btn = gr.Button("Calculate")

            price = gr.Textbox(label="Current Market Price")
            FE = gr.Textbox(label="Future Earnings")
            FV_PE = gr.Textbox(label="Fair Value (PE Method)")
            FV_DDM = gr.Textbox(label="Fair Value (DDM Method)")
            MOS = gr.Textbox(label="Margin of Safety (%)")
            WACC = gr.Textbox(label="WACC (%)")
            signal = gr.Textbox(label="Buy/Sell Signal")

            btn.click(
                valuation,
                inputs=[ticker, Equity, Debt, Free_rate, Market_rate, Beta,
                        Earnings, Historical_Earnings, PE_ratio, Dividend,
                        Tax_rate, Rate],
                outputs=[price, FE, FV_PE, FV_DDM, MOS, WACC, signal]
            )

        # -------- TAB 2 : PRICE CHECKER --------
        with gr.Tab("Stock Price"):

            ticker2 = gr.Textbox(label="Stock Ticker (example: SYS.KA)")
            btn2 = gr.Button("Get Price")
            price2 = gr.Textbox(label="Current Market Price")

            btn2.click(
                check_price,
                inputs=[ticker2],
                outputs=[price2]
            )

app.launch()
