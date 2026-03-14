import gradio as gr
import yfinance as yf

def get_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")

        if data.empty:
            return None

        return float(data["Close"].iloc[-1])
    except:
        return None


def valuation(Ticker, Equity, Debt, Free_rate, Market_rate, Beta,
              Earnings, Historical_Earnings, PE_ratio, Dividend,
              Tax_rate, Rate):

    # -------- Get Market Price --------
    price = get_price(Ticker)

    if price is None:
        return "Ticker not found", "-", "-", "-", "-", "-"

    # -------- Cost of Equity --------
    ke = Free_rate + (Market_rate - Free_rate) * Beta

    # -------- Cost of Debt --------
    kd = Rate * (1 - Tax_rate/100)

    # -------- WACC --------
    total = Equity + Debt
    Wacc = (Equity/total)*ke + (Debt/total)*kd

    # -------- Growth Rate --------
    try:
        growth = ((Earnings/Historical_Earnings)**(1/5) - 1)
    except:
        growth = 0

    # -------- Future Earnings --------
    FE = Earnings * (1 + growth)

    # -------- PE Valuation --------
    FMV_PE = FE * PE_ratio

    # -------- DDM Valuation --------
    if ke/100 > growth:
        FMV_DDM = Dividend*(1+growth)/(ke/100 - growth)
    else:
        FMV_DDM = 0

    # -------- Margin of Safety --------
    MOS = ((FMV_PE - price)/FMV_PE)*100 if FMV_PE != 0 else 0

    return round(price,2), round(FE,2), round(FMV_PE,2), round(FMV_DDM,2), round(MOS,2), round(Wacc,2)


interface = gr.Interface(
    fn=valuation,

    inputs=[
        gr.Textbox(label="Stock Ticker (example: SYS.KA)"),
        gr.Number(label="Equity"),
        gr.Number(label="Debt"),
        gr.Number(label="Free Rate (%)"),
        gr.Number(label="Market Rate (%)"),
        gr.Number(label="Beta"),
        gr.Number(label="Current Earnings"),
        gr.Number(label="Historical Earnings (5 Years Ago)"),
        gr.Number(label="PE Ratio"),
        gr.Number(label="Dividend"),
        gr.Number(label="Tax Rate (%)"),
        gr.Number(label="Interest Rate (%)")
    ],

    outputs=[
        gr.Textbox(label="Current Market Price"),
        gr.Textbox(label="Future Earnings"),
        gr.Textbox(label="Fair Value (PE Method)"),
        gr.Textbox(label="Fair Value (DDM Method)"),
        gr.Textbox(label="Margin of Safety (%)"),
        gr.Textbox(label="WACC (%)")
    ],

    title="PSX Company Valuation Tool",
    description="Enter company financial data and compare intrinsic value with real-time market price."
)

interface.launch()