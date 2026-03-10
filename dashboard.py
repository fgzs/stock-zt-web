#!/usr/bin/env python3
"""
股票分析仪表盘 - 基于 Dash
"""
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import sqlite3
from datetime import datetime
import json

from collector import StockDataCollector

# 初始化 Dash 应用
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "股票分析仪表盘"

# 数据库路径
DB_PATH = '/root/stock-zt-web/stocks.db'

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

def get_market_summary(date=None):
    """获取市场概览"""
    collector = StockDataCollector()
    return collector.get_market_summary(date)

def get_stock_detail(code):
    """获取股票详情"""
    collector = StockDataCollector()
    return collector.collect_individual_stock_detail(code)

# ============ 布局 ============
app.layout = dbc.Container([
    # 标题栏
    dbc.Row([
        dbc.Col([
            html.H1("📊 股票分析仪表盘", className="text-center mb-4"),
            html.P(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", className="text-center text-muted")
        ])
    ]),

    # 顶部统计卡片
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='total-limit-up', className="card-title text-primary"),
                    html.P("涨停总数", className="card-text text-muted")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='avg-change', className="card-title text-danger"),
                    html.P("平均涨幅", className="card-text text-muted")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='avg-amount', className="card-title text-info"),
                    html.P("平均成交额(亿)", className="card-text text-muted")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='avg-turnover', className="card-title text-warning"),
                    html.P("平均换手率", className="card-text text-muted")
                ])
            ])
        ], width=3),
    ], className="mb-4"),

    # 主要内容区域
    dbc.Row([
        # 左侧：涨停股票列表
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("🔥 涨停股票")),
                dbc.CardBody([
                    html.Div(id='limit-up-table')
                ])
            ])
        ], width=4),

        # 右侧：图表分析
        dbc.Col([
            # 连板分布
            dbc.Card([
                dbc.CardHeader(html.H5("📈 连板分布")),
                dbc.CardBody([
                    dcc.Graph(id='limit-days-chart')
                ])
            ], className="mb-3"),

            # 行业分布
            dbc.Card([
                dbc.CardHeader(html.H5("🏢 行业分布")),
                dbc.CardBody([
                    dcc.Graph(id='industry-chart')
                ])
            ])
        ], width=8),
    ], className="mb-4"),

    # 底部：详情分析区域
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("📊 涨幅分布")),
                dbc.CardBody([
                    dcc.Graph(id='change-distribution-chart')
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("💰 成交额 Top10")),
                dbc.CardBody([
                    dcc.Graph(id='top-amount-chart')
                ])
            ])
        ], width=6),
    ]),

    # 自动刷新
    dcc.Interval(
        id='interval-component',
        interval=30*60*1000,  # 30分钟
        n_intervals=0
    ),

], fluid=True)

# ============ 回调函数 ============

@app.callback(
    [Output('total-limit-up', 'children'),
     Output('avg-change', 'children'),
     Output('avg-amount', 'children'),
     Output('limit-days-chart', 'figure'),
     Output('industry-chart', 'figure'),
     Output('change-distribution-chart', 'figure'),
     Output('top-amount-chart', 'figure'),
     Output('limit-up-table', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    """更新仪表盘数据"""
    # 获取数据
    df = get_limit_up_data()
    summary = get_market_summary()

    # 更新统计卡片
    total = summary['total_limit_up']
    avg_change = f"{summary['avg_change']:.2f}%"
    avg_amount = f"{summary['avg_amount']/100000000:.2f}"
    avg_turnover = f"{summary['avg_turnover']:.2f}%"

    # 连板分布图
    limit_days_df = pd.DataFrame(summary['limit_days'], columns=['limit_days', 'count'])
    fig_limit_days = px.bar(
        limit_days_df,
        x='limit_days',
        y='count',
        title='连板分布',
        color='limit_days',
        color_continuous_scale='Reds'
    )
    fig_limit_days.update_xaxis(title_text='连板天数')
    fig_limit_days.update_yaxis(title_text='股票数量')

    # 行业分布图
    industry_df = pd.DataFrame(summary['top_industries'], columns=['industry', 'count'])
    fig_industry = px.bar(
        industry_df.head(10),
        x='count',
        y='industry',
        orientation='h',
        title='行业分布 Top10',
        color='count',
        color_continuous_scale='Blues'
    )

    # 涨幅分布图
    fig_change = px.histogram(
        df,
        x='change_percent',
        nbins=20,
        title='涨幅分布',
        color_discrete_sequence=['#ff6b6b']
    )
    fig_change.update_xaxis(title_text='涨幅 (%)')
    fig_change.update_yaxis(title_text='股票数量')

    # 成交额 Top10
    top_amount = df.nlargest(10, 'amount')
    fig_top_amount = px.bar(
        top_amount,
        x='amount/100000000',
        y='name',
        orientation='h',
        title='成交额 Top10',
        color='amount',
        color_continuous_scale='Greens'
    )
    fig_top_amount.update_xaxis(title_text='成交额 (亿)')

    # 涨停股票表格
    table_data = []
    for _, row in df.iterrows():
        table_data.append(
            dbc.TableRow([
                dbc.Td(row['code']),
                dbc.Td(row['name']),
                dbc.Td(f"{row['change_percent']:.2f}%", style={'color': 'red', 'font-weight': 'bold'}),
                dbc.Td(f"{row['price']:.2f}"),
                dbc.Td(f"{row['amount']/100000000:.2f}亿"),
                dbc.Td(f"{row['turnover_rate']:.2f}%"),
                dbc.Td(f"{row['limit_days']}板"),
            ])
        )

    table = dbc.Table.from_dataframe(
        df[['code', 'name', 'change_percent', 'price', 'amount', 'turnover_rate', 'limit_days']].head(20),
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        size='sm'
    )

    return total, avg_change, avg_amount, fig_limit_days, fig_industry, fig_change, fig_top_amount, table

# 添加额外的输出
@app.callback(
    Output('avg-turnover', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_avg_turnover(n):
    """更新平均换手率"""
    summary = get_market_summary()
    return f"{summary['avg_turnover']:.2f}%"

if __name__ == '__main__':
    # 初始化数据库
    collector = StockDataCollector()
    collector.collect_limit_up_stocks()
    collector.collect_stock_quotes()

    # 运行应用
    app.run_server(host='0.0.0.0', port=5001, debug=False)
