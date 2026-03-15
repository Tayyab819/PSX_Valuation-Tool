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


# ---------- Buy/Sell Signal ----------
def buy_sell_signal(MOS):
    if MOS > 20:
        return "Strong Buy"
    elif MOS > 5:
        return "Buy"
    elif MOS < 0:
        return "Sell"
    else:
        return "Hold"


# ---------- Valuation Function ----------
def valuation(Ticker, Equity, Debt, Free_rate, Market_rate, Beta,
              Earnings, Historical_Earnings, PE_ratio, Dividend,
              Tax_rate, Rate):

    price = get_price(Ticker)
    if price is None:
        return "Ticker not found", "-", "-", "-", "-", "-", "-"

    ke = Free_rate + (Market_rate - Free_rate) * Beta
    kd = Rate * (1 - Tax_rate/100)

    total = Equity + Debt
    Wacc = (Equity/total)*ke + (Debt/total)*kd

    try:
        growth = ((Earnings/Historical_Earnings)**(1/5) - 1)
    except:
        growth = 0

    FE = Earnings * (1 + growth)

    FMV_PE = FE * PE_ratio

    if ke/100 > growth:
        FMV_DDM = Dividend*(1+growth)/(ke/100 - growth)
    else:
        FMV_DDM = 0

    MOS = ((FMV_PE - price)/FMV_PE)*100 if FMV_PE != 0 else 0

    signal = buy_sell_signal(MOS)

    return round(price,2), round(FE,2), round(FMV_PE,2), round(FMV_DDM,2), round(MOS,2), round(Wacc,2), signal


# ---------- Price Checker ----------
def check_price(ticker):
    price = get_price(ticker)
    if price is None:
        return "Ticker not found"
    return round(price,2)


# ---------- Tax Calculator ----------
def tax_calculator(profession, income):

    income = float(income)

    if profession == "Salary":

        if income <= 600000:
            tax = 0
        elif 600000<income <= 1200000:
            tax = income * 0.01
        elif 1200000<income <= 2200000:
            tax = income * 0.11
        elif 2200000<income <= 3200000:
            tax = income * 0.23
        elif 3200000< income <= 4100000:
            tax = income * 0.30
        else:
            tax = income * 0.35

        if income > 10000000:
            tax = tax + (tax * 0.09)


    elif profession == "Business":

        if income <= 600000:
            tax = 0
        elif 600000< income <= 1200000:
            tax = income * 0.15
        elif 1200000 < income <= 1600000:
            tax = income * 0.20
        elif  1600000<income <= 3200000:
            tax = income * 0.30
        elif 3200000< income <= 5600000:
            tax = income * 0.40
        else:
            tax = income * 0.45

    return f"Tax Payable = {round(tax,2)} PKR"


# ---------- UI ----------
with gr.Blocks(title="PSX Analysis Terminal") as app:

    gr.Markdown("# PSX Investor Toolkit")

    with gr.Tabs():

        # -------- TAB 1 : VALUATION --------
        with gr.Tab("Stock Valuation"):

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


        # -------- TAB 3 : TAX CALCULATOR --------
        with gr.Tab("Tax Calculator"):

            profession = gr.Dropdown(["Salary", "Business"], label="Profession")
            income = gr.Number(label="Annual Income")

            tax_btn = gr.Button("Calculate Tax")

            tax_output = gr.Textbox(label="Tax Result")

            tax_btn.click(
                tax_calculator,
                inputs=[profession, income],
                outputs=[tax_output]
            )


app.launch()
