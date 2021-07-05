import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from datetime import date, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import os
API_KEY = os.environ.get("API_KEY")
password = os.environ.get("password")

#find and catergorize data
yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
yesterday_30age = (date.today() - timedelta(days=20)).strftime('%Y-%m-%d')
stocks = "TSM,AAPL,SPY,AMZN,FB,GOOGL,TSLA"
stock_dict = {}
para = {
    "access_key": API_KEY,
    "symbols": stocks,
    "date_from": yesterday_30age,
    "date_to": yesterday,
}
response = requests.get(url="http://api.marketstack.com/v1/eod", params=para)
all_data = response.json()["data"]
stocks = stocks.split(",")
for stock in stocks:
    list_tmp = []
    for data in all_data:
        if data["symbol"] == stock:
            list_tmp.append(data)
    stock_dict[stock] = list_tmp

#stock plot
plots_dict = {}
for stock in stocks:
    trade_date = []
    trade_open = []
    trade_close = []
    trade_high = []
    trade_low = []
    trade_volumne = []
    trade_data = {}
    one_stock_data = stock_dict[stock]
    for one_data in one_stock_data:
        # date = ((one_data["date"].split("T")[0]).replace("-", "/")).split("/", 1)[1]
        date = one_data["date"].split("T")[0]
        trade_date.append(date)
        trade_open.append(one_data["open"])
        trade_close.append(one_data["close"])
        trade_high.append(one_data["high"])
        trade_low.append(one_data["low"])
        trade_volumne.append(one_data["volume"])

    # trade_data["Date"] = trade_date
    trade_data["Open"] = trade_open
    trade_data["High"] = trade_high
    trade_data["Low"] = trade_low
    trade_data["Close"] = trade_close
    trade_data["Volume"] = trade_volumne

    stock_df = pd.DataFrame(index=pd.to_datetime(trade_date,format='%Y-%m-%d'), data=trade_data)
    stock_df.reset_index().rename({'index':'Date'}, axis='columns')

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, subplot_titles=('OHLC', 'Volume'),
                        row_width=[0.2, 0.7])
    fig.add_trace(go.Candlestick(x=stock_df.index,
                                 open=stock_df['Open'],
                                 high=stock_df['High'],
                                 low=stock_df['Low'],
                                 close=stock_df['Close'],
                                 increasing={"fillcolor":'red', "line":{"color":'red'}},
                                 decreasing={"fillcolor":'green',"line":{"color":'green'}},
                                 name="OHLC"),
                  row=1, col=1)

    fig.add_trace(go.Bar(x=stock_df.index, y=stock_df['Volume'], showlegend=False), row=2, col=1)
    fig.update(layout_xaxis_rangeslider_visible=True)
    fig.update_layout(
        width=800, height=600,
        title=f"{stock}",)
    fig.update_xaxes(tickangle=45,nticks=20)
    img_bytes = fig.to_image(format="png")
    plots_dict[stock] = base64.b64encode(img_bytes).decode("ascii")



#send email
#email messages
template = (''
    '<img src="data:image/png;base64,{graph_url}">'        # Use the ".png" magic url so that the latest, most-up-to-date image is included
    '{caption}'                              # Optional caption to include below the graph
    '<br>'                                   # Line break
    '<br>'
    '<hr>'                                   # horizontal line
'')


email_body = ''
for stock in stocks:
    _ = template
    _ = _.format(graph_url=plots_dict[stock], caption='')
    email_body += _


msg = MIMEMultipart('alternative')
msg['From'] = "duanhsinyi@gmail.com"
msg['To'] = "kusumia@hotmail.com"
msg['Subject'] = "America STOCK Info near month"
msg.attach(MIMEText(email_body, 'html'))
server = smtplib.SMTP("smtp.gmail.com", port=587)
server.ehlo()
server.starttls()
server.login(user=msg['From'], password=password)
server.sendmail(msg['From'], msg['To'], msg.as_string())
server.close()
