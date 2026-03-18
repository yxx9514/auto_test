import streamlit as st
import akshare as ak
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta


# --- 1. 核心量化引擎 ---
class QuantEngine:
    @staticmethod
    def calculate_all_factors(df):
        # 1. 趋势因子 (F_TRND): MA5 > MA10 > MA20
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['F_TRND'] = ((df['MA5'] > df['MA10']) & (df['MA10'] > df['MA20'])).astype(int)

        # 2. 量能因子 (F_VOL): 成交量 > 5日均量 1.2倍
        df['V_MA5'] = df['volume'].rolling(window=5).mean()
        df['F_VOL'] = (df['volume'] > df['V_MA5'] * 1.2).astype(int)

        # 3. 中期因子 (F_MID): MACD DIF > DEA
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['DIF'] = exp1 - exp2
        df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
        df['F_MID'] = (df['DIF'] > df['DEA']).astype(int)

        # 4. 短期因子 (F_SHRT): RSI(6) > 50
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=6).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=6).mean()
        df['RSI6'] = 100 - (100 / (1 + (gain / loss)))
        df['F_SHRT'] = (df['RSI6'] > 50).astype(int)

        # --- 风险过滤指标 ---
        # ATR 钝化检测
        high_low = df['high'] - df['low']
        df['ATR'] = high_low.rolling(window=14).mean()
        df['LOW_VOL'] = (df['ATR'] < df['ATR'].rolling(window=60).mean() * 0.7)

        # 顶背离检测
        df['P_HI_20'] = df['high'].rolling(window=20).max()
        df['R_HI_20'] = df['RSI6'].rolling(window=20).max()
        df['DIV_RISK'] = ((df['high'] > df['P_HI_20'].shift(1)) & (df['RSI6'] < df['R_HI_20'].shift(1))).astype(int)

        return df


# --- 2. 数据加载 ---
@st.cache_data
def load_stock_data(symbol):
    # 默认获取最近两年的数据以确保一年展示和指标计算的预热
    df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
    # akshare返回12列：日期、股票代码、开盘、收盘、最高、最低、成交量、成交额、振幅、涨跌幅、涨跌额、换手率
    df.columns = ['date', 'stock_code', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 'pct_chg', 'chg_amt', 'turnover']
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    # 删除不需要的列（保留核心交易数据）
    df = df[['open', 'close', 'high', 'low', 'volume']]  # 只保留K线所需的核心列
    return df


# --- 3. UI 界面 ---
st.set_page_config(layout="wide", page_title="A股量化辅助工具Pro")

# 侧边栏
st.sidebar.title("🔍 股票筛选")
stock_code = st.sidebar.text_input("代码 (如 600703)", "600703")
lookback_days = 365  # 默认展示1年

if stock_code:
    try:
        raw_df = load_stock_data(stock_code)
        df = QuantEngine.calculate_all_factors(raw_df)

        # 只保留最近一年的数据展示
        display_df = df.tail(lookback_days)
        last_row = display_df.iloc[-1]

        # 头部标题与实时信号
        st.title(f"📈 {stock_code} 交易辅助工具")

        # 信号预警区
        c1, c2, c3 = st.columns([1, 1, 2])
        total_score = last_row['F_TRND'] + last_row['F_VOL'] + last_row['F_MID'] + last_row['F_SHRT']

        with c1:
            if total_score == 4:
                st.error("🚨 状态：四灯全红（强共振）")
            elif total_score >= 1:
                st.warning(f"⚠️ 状态：{total_score}灯红（共振不足）")
            else:
                st.success("🟢 状态：全面回调/观望")

        with c2:
            if last_row['DIV_RISK']: st.error("🚩 风险：顶背离诱多")
            if last_row['LOW_VOL']: st.info("📉 风险：低波动钝化")

        # --- 绘图区 ---
        # 创建 5 行子图：1(K线), 2(趋势灯), 3(量能灯), 4(中期灯), 5(短期灯)
        # 不使用shared_xaxes，避免Candlestick延伸到其他子图
        fig = make_subplots(rows=5, cols=1, shared_xaxes=False,
                            vertical_spacing=0.05,
                            row_heights=[0.6, 0.08, 0.08, 0.08, 0.08],
                            specs=[[{"type": "xy"}], 
                                   [{"type": "xy"}], 
                                   [{"type": "xy"}], 
                                   [{"type": "xy"}], 
                                   [{"type": "xy"}]])

        # 1. K线图 - 第1行
        fig.add_trace(go.Candlestick(x=display_df.index, open=display_df['open'], high=display_df['high'],
                                     low=display_df['low'], close=display_df['close'], name="K线"), row=1, col=1)
        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['MA5'], name="MA5", line=dict(width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['MA20'], name="MA20", line=dict(width=1)), row=1, col=1)

        # 2-5. 四项共振色块排列
        factor_map = [
            ('F_TRND', '趋势', 2, 'red'),
            ('F_VOL', '量能', 3, 'orange'),
            ('F_MID', '中期', 4, 'blue'),
            ('F_SHRT', '短期', 5, 'purple')
        ]

        for factor_key, label, row_idx, base_color in factor_map:
            # 红色代表满足(1), 绿色代表不满足(0)
            colors = display_df[factor_key].map({1: 'red', 0: 'green'})
            # 使用Bar图显示指标，确保只在对应的row显示
            fig.add_trace(go.Bar(x=display_df.index, y=[1] * len(display_df),
                                 marker_color=colors, name=label, showlegend=True,
                                 base=0), row=row_idx, col=1)
            # 隐藏坐标轴刻度，并设置y轴范围确保只显示指标
            fig.update_yaxes(title_text=label, row=row_idx, col=1, 
                           showticklabels=False, range=[0, 1.2])
        
        # 确保K线图只在第1行显示，设置y轴范围
        fig.update_yaxes(range=[display_df['low'].min() * 0.95, display_df['high'].max() * 1.05], row=1, col=1)
        
        # 隐藏上面4个子图的x轴标签，只在最后一个显示
        for row_idx in [1, 2, 3, 4]:
            fig.update_xaxes(showticklabels=False, row=row_idx, col=1)
        
        fig.update_layout(
            height=900,
            hovermode='x unified',
            template='plotly_white'
        )
        # 只在最后一个子图（第5行）显示滑动条，设置更小的厚度避免遮挡
        fig.update_xaxes(
            rangeslider_visible=True,
            rangeslider_thickness=0.02,  # 进一步减小滑动条厚度
            row=5, col=1
        )

        st.plotly_chart(fig, use_container_width=True)

        # 底部数据详情
        with st.expander("查看原始信号数据"):
            st.write(display_df[['close', 'F_TRND', 'F_VOL', 'F_MID', 'F_SHRT', 'RSI6']].tail(10))

    except Exception as e:
        st.error(f"分析异常: {e}")
        st.info("请检查代码输入格式是否正确。")