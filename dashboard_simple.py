#!/usr/bin/env python3
"""
股票分析仪表盘 - 纯HTML版本（无CDN依赖）
"""
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import sqlite3
from datetime import datetime
import akshare as ak
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 Dash 应用（不使用Bootstrap）
app = dash.Dash(__name__)
app.title = "股票分析仪表盘"

# 数据库路径
DB_PATH = '/root/stock-zt-web/stocks.db'

def init_database():
    """初始化数据库"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS limit_up_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                change_percent REAL,
                price REAL,
                amount REAL,
                circ_cap REAL,
                market_cap REAL,
                turnover_rate REAL,
                limit_amount REAL,
                first_limit_time TEXT,
                last_limit_time TEXT,
                break_count INTEGER,
                limit_days INTEGER,
                industry TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, code)
            )
        ''')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False

def collect_and_store_data():
    """收集并存储数据"""
    try:
        logger.info("开始收集涨停数据...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        date_str = datetime.now().strftime('%Y%m%d')
        df = ak.stock_zt_pool_em(date=date_str)

        count = 0
        for idx, row in df.iterrows():
            cursor.execute('''
                INSERT OR REPLACE INTO limit_up_stocks
                (date, code, name, change_percent, price, amount, circ_cap, market_cap,
                 turnover_rate, limit_amount, first_limit_time, last_limit_time,
                 break_count, limit_days, industry)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d'),
                row['代码'],
                row['名称'],
                float(row['涨跌幅']),
                float(row['最新价']),
                float(row['成交额']),
                float(row['流通市值']),
                float(row['总市值']),
                float(row['换手率']),
                float(row['封板资金']),
                row['首次封板时间'],
                row['最后封板时间'],
                int(row['炸板次数']),
                int(row['连板数']),
                row['所属行业']
            ))
            count += 1

        conn.commit()
        conn.close()
        logger.info(f"✅ 成功收集 {count} 只涨停股票")
        return count
    except Exception as e:
        logger.error(f"❌ 收集数据失败: {e}")
        return 0

def get_limit_up_data(date=None):
    """获取涨停股票数据"""
    try:
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql('''
            SELECT * FROM limit_up_stocks WHERE date = ?
            ORDER BY limit_days DESC, change_percent DESC
        ''', conn, params=(date,))
        conn.close()
        return df
    except Exception as e:
        logger.error(f"获取数据失败: {e}")
        return pd.DataFrame()

# 自定义样式
styles = {
    'container': {
        'fontFamily': 'Arial, sans-serif',
        'maxWidth': '1400px',
        'margin': '0 auto',
        'padding': '20px',
        'backgroundColor': '#f8f9fa'
    },
    'header': {
        'textAlign': 'center',
        'marginBottom': '30px'
    },
    'title': {
        'fontSize': '36px',
        'fontWeight': 'bold',
        'marginBottom': '10px',
        'color': '#333'
    },
    'subtitle': {
        'fontSize': '16px',
        'color': '#666'
    },
    'statCard': {
        'backgroundColor': 'white',
        'padding': '20px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'textAlign': 'center'
    },
    'statValue': {
        'fontSize': '32px',
        'fontWeight': 'bold',
        'marginBottom': '5px'
    },
    'statLabel': {
        'fontSize': '14px',
        'color': '#666'
    },
    'chartCard': {
        'backgroundColor': 'white',
        'padding': '20px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'marginBottom': '20px'
    },
    'updateButton': {
        'backgroundColor': '#007bff',
        'color': 'white',
        'border': 'none',
        'padding': '10px 20px',
        'borderRadius': '5px',
        'cursor': 'pointer',
        'fontSize': '16px',
        'width': '100%'
    }
}

# ============ 布局 ============
app.layout = html.Div([
    # 容器
    html.Div([
        # 标题栏
        html.Div([
            html.H1("📊 A股涨停分析仪表盘", style=styles['title']),
            html.P(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style=styles['subtitle'])
        ], style=styles['header']),

        # 顶部统计卡片
        html.Div([
            html.Div([
                html.H2("0", id='total-limit-up', style={**styles['statValue'], 'color': '#007bff'}),
                html.P("涨停总数", style=styles['statLabel'])
            ], style={**styles['statCard'], 'width': '19%', 'display': 'inline-block', 'margin': '0.5%'}),

            html.Div([
                html.H2("0%", id='avg-change', style={**styles['statValue'], 'color': '#dc3545'}),
                html.P("平均涨幅", style=styles['statLabel'])
            ], style={**styles['statCard'], 'width': '19%', 'display': 'inline-block', 'margin': '0.5%'}),

            html.Div([
                html.H2("0", id='avg-amount', style={**styles['statValue'], 'color': '#17a2b8'}),
                html.P("平均成交额(亿)", style=styles['statLabel'])
            ], style={**styles['statCard'], 'width': '19%', 'display': 'inline-block', 'margin': '0.5%'}),

            html.Div([
                html.H2("0%", id='avg-turnover', style={**styles['statValue'], 'color': '#ffc107'}),
                html.P("平均换手率", style=styles['statLabel'])
            ], style={**styles['statCard'], 'width': '19%', 'display': 'inline-block', 'margin': '0.5%'}),

            html.Div([
                html.H2("0", id='max-limit-days', style={**styles['statValue'], 'color': '#28a745'}),
                html.P("最高连板", style=styles['statLabel'])
            ], style={**styles['statCard'], 'width': '19%', 'display': 'inline-block', 'margin': '0.5%'}),
        ], style={'marginBottom': '20px'}),

        # 更新按钮
        html.Div([
            html.Button("🔄 立即更新", id="update-btn", n_clicks=0, style=styles['updateButton']),
            html.Div(id="update-status", style={'textAlign': 'center', 'marginTop': '10px', 'color': '#666'})
        ], style={'marginBottom': '20px'}),

        # 主图表区域
        html.Div([
            # 连板分布
            html.Div([
                html.H5("📈 连板分布", style={'marginBottom': '10px'}),
                dcc.Graph(id='limit-days-chart', style={'height': '300px'})
            ], style={**styles['chartCard'], 'width': '49%', 'display': 'inline-block', 'marginRight': '1%'}),

            # 行业分布
            html.Div([
                html.H5("🏢 行业分布", style={'marginBottom': '10px'}),
                dcc.Graph(id='industry-chart', style={'height': '300px'})
            ], style={**styles['chartCard'], 'width': '49%', 'display': 'inline-block', 'marginLeft': '1%'}),
        ]),

        # 第二行图表
        html.Div([
            # 涨幅分布
            html.Div([
                html.H5("📊 涨幅分布", style={'marginBottom': '10px'}),
                dcc.Graph(id='change-distribution-chart', style={'height': '300px'})
            ], style={**styles['chartCard'], 'width': '100%'}),
        ], style={'marginBottom': '20px'}),

        # 涨停股票表格
        html.Div([
            html.H5("🔥 涨停股票列表", style={'marginBottom': '10px'}),
            html.Div(id='limit-up-table-container', style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'maxHeight': '400px', 'overflowY': 'auto'})
        ], style={**styles['chartCard']}),

        # 自动刷新
        dcc.Interval(
            id='interval-component',
            interval=30*60*1000,  # 30分钟
            n_intervals=0
        ),

    ], style=styles['container'])

# ============ 回调函数 ============

@app.callback(
    [Output('total-limit-up', 'children'),
     Output('avg-change', 'children'),
     Output('avg-amount', 'children'),
     Output('avg-turnover', 'children'),
     Output('max-limit-days', 'children'),
     Output('limit-days-chart', 'figure'),
     Output('industry-chart', 'figure'),
     Output('change-distribution-chart', 'figure'),
     Output('limit-up-table-container', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('update-btn', 'n_clicks')]
)
def update_dashboard(n, n_clicks):
    """更新仪表盘数据"""
    try:
        logger.info("开始更新仪表盘...")

        # 收集最新数据
        count = collect_and_store_data()

        # 获取数据
        df = get_limit_up_data()

        if len(df) == 0:
            logger.warning("没有数据")
            return "0", "0%", "0", "0%", "0", {}, {}, {}, html.Div("暂无数据")

        # 计算统计
        total = len(df)
        avg_change = f"{df['change_percent'].mean():.2f}%"
        avg_amount = f"{df['amount'].mean()/100000000:.2f}"
        avg_turnover = f"{df['turnover_rate'].mean():.2f}%"
        max_limit_days = int(df['limit_days'].max())

        # 连板分布图
        limit_days_df = df.groupby('limit_days').size().reset_index(name='count')
        fig_limit_days = px.bar(
            limit_days_df,
            x='limit_days',
            y='count',
            title='连板分布',
            color='limit_days',
            color_continuous_scale='Reds',
            text='count'
        )
        fig_limit_days.update_layout(margin=dict(t=50, b=50, l=50, r=50), height=300)

        # 行业分布图
        industry_df = df.groupby('industry').size().nlargest(10).reset_index(name='count')
        fig_industry = px.bar(
            industry_df,
            x='count',
            y='industry',
            orientation='h',
            title='行业分布 Top10',
            color='count',
            color_continuous_scale='Blues',
            text='count'
        )
        fig_industry.update_layout(margin=dict(t=50, b=50, l=100, r=50), height=300)

        # 涨幅分布图
        fig_change = px.histogram(
            df,
            x='change_percent',
            nbins=20,
            title='涨幅分布',
            color_discrete_sequence=['#ff6b6b']
        )
        fig_change.update_layout(margin=dict(t=50, b=50, l=50, r=50), height=300)

        # 涨停股票表格
        display_df = df[['code', 'name', 'change_percent', 'price', 'amount', 'turnover_rate', 'limit_days', 'industry']].copy()
        display_df['amount'] = display_df['amount'].apply(lambda x: f"{x/100000000:.2f}亿")
        display_df['change_percent'] = display_df['change_percent'].apply(lambda x: f"{x:.2f}%")
        display_df['turnover_rate'] = display_df['turnover_rate'].apply(lambda x: f"{x:.2f}%")

        # 创建简单的HTML表格
        table_rows = []
        for _, row in display_df.iterrows():
            table_rows.append(
                html.Tr([
                    html.Td(row['code'], style={'padding': '8px'}),
                    html.Td(row['name'], style={'padding': '8px'}),
                    html.Td(row['change_percent'], style={'padding': '8px', 'color': 'red', 'fontWeight': 'bold'}),
                    html.Td(row['price'], style={'padding': '8px'}),
                    html.Td(row['amount'], style={'padding': '8px'}),
                    html.Td(row['turnover_rate'], style={'padding': '8px'}),
                    html.Td(f"{row['limit_days']}板", style={'padding': '8px'}),
                    html.Td(row['industry'], style={'padding': '8px'}),
                ])
            )

        table = html.Table([
            html.Thead([
                html.Tr([
                    html.Th("代码", style={'padding': '10px', 'textAlign': 'left'}),
                    html.Th("名称", style={'padding': '10px', 'textAlign': 'left'}),
                    html.Th("涨幅", style={'padding': '10px', 'textAlign': 'left'}),
                    html.Th("价格", style={'padding': '10px', 'textAlign': 'left'}),
                    html.Th("成交额", style={'padding': '10px', 'textAlign': 'left'}),
                    html.Th("换手率", style={'padding': '10px', 'textAlign': 'left'}),
                    html.Th("连板", style={'padding': '10px', 'textAlign': 'left'}),
                    html.Th("行业", style={'padding': '10px', 'textAlign': 'left'}),
                ], style={'backgroundColor': '#f8f9fa'})
            ]),
            html.Tbody(table_rows)
        ], style={'width': '100%', 'borderCollapse': 'collapse'})

        logger.info(f"仪表盘更新完成，共 {total} 只股票")

        return total, avg_change, avg_amount, avg_turnover, max_limit_days, fig_limit_days, fig_industry, fig_change, table

    except Exception as e:
        logger.error(f"更新仪表盘失败: {e}")
        return "0", "0%", "0", "0%", "0", {}, {}, {}, html.Div(f"加载失败: {str(e)}")

@app.callback(
    Output('update-status', 'children'),
    [Input('update-btn', 'n_clicks')]
)
def show_update_status(n_clicks):
    if n_clicks > 0:
        return "✅ 已更新 " + datetime.now().strftime('%H:%M:%S')
    return ""

if __name__ == '__main__':
    # 初始化数据库
    logger.info("初始化数据库...")
    init_database()

    # 收集数据
    logger.info("收集初始数据...")
    collect_and_store_data()

    # 运行应用
    logger.info("启动仪表盘服务...")
    app.run_server(host='0.0.0.0', port=5002, debug=False)
