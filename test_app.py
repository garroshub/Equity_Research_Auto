import os
from os import environ
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.dates as mdates

from app_utility import settings
from app_utility import company_valuation as cv
from app_utility import stock_time_series as sts

from matplotlib.font_manager import FontProperties
fontP = FontProperties()
fontP.set_size('small')

# 设置页面配置
st.set_page_config(layout="wide")

# 定义日期相关变量
today = datetime.today()
todaystr = today.strftime("%Y-%m-%d")
two_years_ago = today - timedelta(days=2*365)
two_years_ago_str = two_years_ago.strftime("%Y-%m-%d")

# 辅助函数：创建高亮标题
def create_section_header(title):
    st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; font-size: 20px; font-weight: bold; margin-top: 20px;'>{title}</div>", unsafe_allow_html=True)

# 辅助函数：设置图表日期格式
def set_date_format(ax):
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))  # 每三个月显示一个刻度
    plt.xticks(rotation=45, ha='right')

# 计算移动平均线
def calculate_ma(data, window):
    return data['close'].rolling(window=window).mean()

# 生成买入/卖出信号
def generate_signals(data, short_window, long_window):
    short_ma = f'{short_window}_day_ma'
    long_ma = f'{long_window}_day_ma'
    buy_signals = (data[short_ma] > data[long_ma]) & (data[short_ma].shift(1) <= data[long_ma].shift(1))
    sell_signals = (data[short_ma] < data[long_ma]) & (data[short_ma].shift(1) >= data[long_ma].shift(1))
    return buy_signals, sell_signals

# 主应用代码
st.title('Equity Research')

# 添加间隔
st.markdown("<br>", unsafe_allow_html=True)

st.sidebar.title("Setup")
st.sidebar.write("Please get your FMP API key here [link](https://financialmodelingprep.com/developer)")
api_key = st.sidebar.text_input('API Key', 'UNoMCpdclG9U2ZJ7x34eWBzTRXrV85oE', type="password")

try:
    if environ.get('fmp_key') is not None:
        settings.set_apikey(os.environ['fmp_key'])
except:
    settings.set_apikey(api_key)

symbol_search = st.sidebar.text_input('Symbol', 'AMZN')

# MA设置在侧边栏
short_window = st.sidebar.number_input("Short-term MA period", min_value=1, max_value=100, value=10)
long_window = st.sidebar.number_input("Long-term MA period", min_value=1, max_value=200, value=20)

if st.sidebar.button("Start"):
    try:
        symbol = symbol_search

        # 添加高亮横幅显示股票代码
        create_section_header(f"Stock - {symbol}")

        # 获取数据
        df_prices_ = sts.historical_stock_data(symbol, dailytype='line', start=two_years_ago_str, end=todaystr)
        df_prices = df_prices_.reset_index()
        df_ratios = cv.financial_ratios(ticker=symbol, period='annual', ttm=False)
        df_metrics = cv.key_metrics(ticker=symbol, period='annual')
        df_income = cv.income_statement(ticker=symbol, period='annual', ftype='full')
        df_cashflow = cv.cash_flow_statement(ticker=symbol, period='annual', ftype='full')

        # 价格趋势 with Buy/Sell Signals
        create_section_header('Price Trend with Buy/Sell Signals')

        # 计算移动平均线
        df_prices[f'{short_window}_day_ma'] = calculate_ma(df_prices, short_window)
        df_prices[f'{long_window}_day_ma'] = calculate_ma(df_prices, long_window)

        # 生成买入/卖出信号
        buy_signals, sell_signals = generate_signals(df_prices, short_window, long_window)

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df_prices['date'], df_prices['close'], label='Closing Price', color='blue')
        ax.plot(df_prices['date'], df_prices[f'{short_window}_day_ma'], label=f'{short_window}-day MA', color='lightblue', alpha=0.8)
        ax.plot(df_prices['date'], df_prices[f'{long_window}_day_ma'], label=f'{long_window}-day MA', color='red', alpha=0.8)

        # 标记买入和卖出信号
        ax.scatter(df_prices.loc[buy_signals, 'date'], df_prices.loc[buy_signals, 'close'], 
                   color='green', label='Buy Signal', marker='^', s=100)
        ax.scatter(df_prices.loc[sell_signals, 'date'], df_prices.loc[sell_signals, 'close'], 
                   color='red', label='Sell Signal', marker='v', s=100)

        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax.legend(loc='upper left')
        set_date_format(ax)
        fig.tight_layout()
        st.pyplot(fig)

        st.write(f"This chart shows the stock's closing price along with {short_window}-day and {long_window}-day moving averages for the past 2 years.")
        st.write(f"Buy signals are generated when the {short_window}-day MA crosses above the {long_window}-day MA, and sell signals when it crosses below.")

        # 财务比率部分
        create_section_header('Financial Ratios')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Price to Book Ratio")
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(df_ratios['date'], df_ratios['priceToBookRatio'], marker='o')
            ax.set_xlabel('Date')
            ax.set_ylabel('P/B Ratio')
            set_date_format(ax)
            fig.tight_layout()
            st.pyplot(fig)
            st.write(f"Current P/B Ratio: {df_ratios.loc[0, 'priceToBookRatio']:.2f}")
            st.write("The Price to Book Ratio is calculated by dividing the company's stock price per share by its book value per share.")

        with col2:
            st.subheader("Price to Sales Ratio")
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(df_ratios['date'], df_ratios['priceToSalesRatio'], marker='o')
            ax.set_xlabel('Date')
            ax.set_ylabel('P/S Ratio')
            set_date_format(ax)
            fig.tight_layout()
            st.pyplot(fig)
            st.write(f"Current P/S Ratio: {df_ratios.loc[0, 'priceToSalesRatio']:.2f}")
            st.write("The Price to Sales Ratio is calculated by dividing the company's market cap by its total sales.")

        col3, col4 = st.columns(2)

        with col3:
            st.subheader("Return on Equity")
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(df_ratios['date'], df_ratios['returnOnEquity'], marker='o')
            ax.set_xlabel('Date')
            ax.set_ylabel('ROE')
            set_date_format(ax)
            fig.tight_layout()
            st.pyplot(fig)
            st.write(f"Current ROE: {df_ratios.loc[0, 'returnOnEquity']*100:.2f}%")
            st.write("Return on Equity (ROE) measures a company's profitability in relation to shareholders' equity.")

        with col4:
            st.subheader("Debt to Equity Ratio")
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(df_metrics['date'], df_metrics['debtToEquity'], marker='o')
            ax.set_xlabel('Date')
            ax.set_ylabel('D/E Ratio')
            set_date_format(ax)
            fig.tight_layout()
            st.pyplot(fig)
            st.write(f"Current D/E Ratio: {df_metrics.loc[0, 'debtToEquity']:.2f}")
            st.write("The Debt to Equity Ratio measures a company's financial leverage.")

        # 利润率部分
        create_section_header('Profitability Ratios')
        
        col5, col6 = st.columns(2)
        
        with col5:
            st.subheader("Gross Profit Margin")
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(df_ratios['date'], df_ratios['grossProfitMargin'], marker='o')
            ax.set_xlabel('Date')
            ax.set_ylabel('Gross Profit Margin')
            set_date_format(ax)
            fig.tight_layout()
            st.pyplot(fig)
            st.write(f"Current Gross Profit Margin: {df_ratios.loc[0, 'grossProfitMargin']*100:.2f}%")
            st.write("Gross Profit Margin is the percentage of revenue left after subtracting the cost of goods sold.")

        with col6:
            st.subheader("Net Profit Margin")
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(df_ratios['date'], df_ratios['netProfitMargin'], marker='o')
            ax.set_xlabel('Date')
            ax.set_ylabel('Net Profit Margin')
            set_date_format(ax)
            fig.tight_layout()
            st.pyplot(fig)
            st.write(f"Current Net Profit Margin: {df_ratios.loc[0, 'netProfitMargin']*100:.2f}%")
            st.write("Net Profit Margin is the percentage of revenue left after all expenses have been deducted from sales.")

        # 现金流和收益部分
        create_section_header('Cash Flow and Earnings')
        
        col7, col8 = st.columns(2)
        
        with col7:
            st.subheader("Cash Flow")
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(df_cashflow['date'], df_cashflow['operatingCashFlow'], label='Operating')
            ax.plot(df_cashflow['date'], df_cashflow['netCashUsedForInvestingActivites'], label='Investing')
            ax.plot(df_cashflow['date'], df_cashflow['netCashUsedProvidedByFinancingActivities'], label='Financing')
            ax.set_xlabel('Date')
            ax.set_ylabel('Cash Flow')
            ax.legend(fontsize='x-small')
            set_date_format(ax)
            fig.tight_layout()
            st.pyplot(fig)
            st.write("This chart shows the company's cash flows from operating, investing, and financing activities over time.")

        with col8:
            st.subheader("Earnings per Share")
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(df_income['date'], df_income['eps'], label='EPS')
            ax.plot(df_income['date'], df_income['epsdiluted'], label='Diluted EPS')
            ax.set_xlabel('Date')
            ax.set_ylabel('EPS')
            ax.legend(fontsize='x-small')
            set_date_format(ax)
            fig.tight_layout()
            st.pyplot(fig)
            st.write(f"Current EPS: ${df_income.loc[0, 'eps']:.2f}")
            st.write(f"Current Diluted EPS: ${df_income.loc[0, 'epsdiluted']:.2f}")
            st.write("Earnings per Share (EPS) is the portion of a company's profit allocated to each outstanding share of common stock.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.write("Please check your API key and ensure you have access to the required data.")

st.sidebar.markdown("---")
st.sidebar.subheader("About")
st.sidebar.info("This app provides a comprehensive equity research dashboard using data from Financial Modeling Prep API.")