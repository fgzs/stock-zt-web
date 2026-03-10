#!/usr/bin/env python3
"""
简化版仪表盘 - 先展示涨停数据
"""
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import sqlite3
from datetime import datetime
import akshare as ak

# 初始化 Dash 应用
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "股票分析仪表盘"

# 数据库路径
DB_PATH = '/root/stock-zt-web/stocks.db'

def init_and_collect_data():
    """初始化数据库并收集数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建表
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

    # 收集数据
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
    return count

def get_limit_up_data(date=None):
    """获取涨停股票数据"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('''
        SELECT * FROM limit_up_stocks WHERE date = ?
        ORDER BY limit_days DESC, change_percent DESC
    ''', conn, params=(date,))
    conn.close()
    return df

# ============ 布局 ============
app.layout = dbc.Container([
    # 标题栏
    dbc.Row([
        dbc.Col([
            html.H1("📊 A股涨停分析仪表盘", className="text-center mb-3"),
            html.P(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", className="text-center text-muted mb-4")
        ])
    ]),

    # 顶部统计卡片
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(id='total-limit-up', className="card-title text-primary"),
                    html.P("涨停总数", className="card-text text-muted")
                ])
            ])
        ], width=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(id='avg-change', className="card-title text-danger"),
                    html.P("平均涨幅", className="card-text text-muted")
                ])
            ])
        ], width=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(id='avg-amount', className="card-title text-info"),
                    html.P("平均成交额(亿)", className="card-text text-muted")
                ])
            ])
        ], width=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(id='avg-turnover', className="card-title text-warning"),
                    html.P("平均换手率", className="card-text text-muted")
                ])
            ])
        ], width=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(id='max-limit-days', className="card-title text-success"),
                    html.P("最高连板", className="card-text text-muted")
                ])
            ])
        ], width=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Button("🔄 立即更新", id="update-btn", n_clicks=0, className="btn btn-primary w-100"),
                    html.Div(id="update-status", className="text-center mt-2 small text-muted")
                ])
            ])
        ], width=2),
    ], className="mb-4"),

    # 主图表区域
    dbc.Row([
        # 连板分布
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("📈 连板分布")),
                dbc.CardBody([
                    dcc.Graph(id='limit-days-chart')
                ])
            ])
        ], width=4),

        # 行业分布
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("🏢 行业分布")),
                dbc.CardBody([
                    dcc.Graph(id='industry-chart')
                ])
            ])
        ], width=4),

        # 涨幅分布
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("📊 涨幅分布")),
                dbc.CardBody([
                    dcc.Graph(id='change-distribution-chart')
                ])
            ])
        ], width=4),
    ], className="mb-4"),

    # 详细数据区域
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("🔥 涨停股票列表")),
                dbc.CardBody([
                    dbc.Table.from_dataframe(
                        pd.DataFrame(),  # 初始为空，由回调填充
                        striped=True,
                        bordered=True,
                        hover=True,
                        responsive=True,
                        size='sm',
                        id='limit-up-table'
                    )
                ])
            ])
        ], width=12),
    ], className="mb-4"),

    # 成交额 Top10
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("💰 成交额 Top10")),
                dbc.CardBody([
                    dcc.Graph(id='top-amount-chart')
                ])
            ])
        ], width=12),
    ]),

    # 自动刷新
    dcc.Interval(
        id='interval-component',
        interval=30*60*1000,  # 30分钟
        n_intervals=0
    ),

], fluid=True, style={'backgroundColor': '#f8f9fa', 'padding': '20px'})

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
     Output('top-amount-chart', 'figure'),
     Output('limit-up-table', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('update-btn', 'n_clicks')]
)
def update_dashboard(n, n_clicks):
    """更新仪表盘数据"""
    # 每次都尝试收集最新数据
    count = init_and_collect_data()

    # 获取数据
    df = get_limit_up_data()

    if len(df) == 0:
        return 0, "0%", "0", "0%", "0", {}, {}, {}, {}, dbc.Table.from_dataframe(pd.DataFrame())

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
    fig_limit_days.update_traces(texttemplate='%{text}', textposition='outside')
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
    fig_industry.update_traces(texttemplate='%{text}', textposition='outside')
    fig_industry.update_layout(margin=dict(t=50, b=50, l=150, r=50), height=300)

    # 涨幅分布图
    fig_change = px.histogram(
        df,
        x='change_percent',
        nbins=20,
        title='涨幅分布',
        color_discrete_sequence=['#ff6b6b']
    )
    fig_change.update_layout(margin=dict(t=50, b=50, l=50, r=50), height=300)

    # 成交额 Top10
    top_amount = df.nlargest(10, 'amount')
    fig_top_amount = px.bar(
        top_amount,
        x='amount/100000000',
        y='name',
        orientation='h',
        title='成交额 Top10 (亿)',
        color='amount',
        color_continuous_scale='Greens',
        text='amount/100000000'
    )
    fig_top_amount.update_traces(texttemplate='%{text:.2f}亿', textposition='outside')
    fig_top_amount.update_layout(margin=dict(t=50, b=50, l=150, r=50), height=400)

    # 涨停股票表格
    display_df = df[['code', 'name', 'change_percent', 'price', 'amount', 'turnover_rate', 'limit_days', 'industry']].copy()
    display_df['amount'] = display_df['amount'].apply(lambda x: f"{x/100000000:.2f}亿")
    display_df['change_percent'] = display_df['change_percent'].apply(lambda x: f"{x:.2f}%")
    display_df['turnover_rate'] = display_df['turnover_rate'].apply(lambda x: f"{x:.2f}%")

    table = dbc.Table.from_dataframe(
        display_df,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        size='sm'
    )

    return total, avg_change, avg_amount, avg_turnover, max_limit_days, fig_limit_days, fig_industry, fig_change, fig_top_amount, table

@app.callback(
    Output('update-status', 'children'),
    [Input('update-btn', 'n_clicks')]
)
def show_update_status(n_clicks):
    if n_clicks > 0:
        return "✅ 已更新 " + datetime.now().strftime('%H:%M:%S')
    return ""

if __name__ == '__main__':
    # 初始化数据
    print("初始化数据...")
    count = init_and_collect_data()
    print(f"✅ 初始化完成，共 {count} 只涨停股票")

    # 运行应用
    app.run_server(host='0.0.0.0', port=5001, debug=False)
