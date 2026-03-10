#!/usr/bin/env python3
"""
股票分析仪表盘 - 本地化版本（无CDN依赖）
纯HTML+内联CSS，加载速度极快
"""
import sqlite3
import pandas as pd
from datetime import datetime
import akshare as ak
from flask import Flask, request, jsonify
import schedule
import time
import threading

app = Flask(__name__)

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
        print(f"数据库初始化失败: {e}")
        return False

def collect_and_store_data():
    """收集并存储数据"""
    try:
        print("开始收集涨停数据...")
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        print(f"✅ 成功收集 {count} 只涨停股票")
        return count
    except Exception as e:
        print(f"❌ 收集数据失败: {e}")
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
        print(f"获取数据失败: {e}")
        return pd.DataFrame()

def get_market_summary(date=None):
    """获取市场概览"""
    try:
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 涨停统计
        cursor.execute('''
            SELECT COUNT(*), AVG(change_percent), AVG(amount), AVG(turnover_rate)
            FROM limit_up_stocks WHERE date = ?
        ''', (date,))
        result = cursor.fetchone()

        # 连板统计
        cursor.execute('''
            SELECT limit_days, COUNT(*) as count
            FROM limit_up_stocks WHERE date = ?
            GROUP BY limit_days
            ORDER BY limit_days DESC
        ''', (date,))
        limit_days = cursor.fetchall()

        # 行业统计
        cursor.execute('''
            SELECT industry, COUNT(*) as count
            FROM limit_up_stocks WHERE date = ?
            GROUP BY industry
            ORDER BY count DESC
            LIMIT 10
        ''', (date,))
        industries = cursor.fetchall()

        conn.close()

        return {
            'total_limit_up': result[0] if result else 0,
            'avg_change': result[1] if result else 0,
            'avg_amount': result[2] if result else 0,
            'avg_turnover': result[3] if result else 0,
            'limit_days': limit_days,
            'top_industries': industries
        }
    except Exception as e:
        print(f"获取概览失败: {e}")
        return {}

def scheduled_job():
    """定时任务"""
    print(f"[{datetime.now()}] 开始更新涨停数据...")
    result = collect_and_store_data()
    if result:
        print(f"成功更新 {result} 只涨停股票")
    else:
        print("更新失败")

def run_scheduler():
    """启动定时任务线程"""
    schedule.every().day.at("16:00").do(scheduled_job)

    while True:
        schedule.run_pending()
        time.sleep(60)

@app.route('/')
def index():
    """主页"""
    date = datetime.now().strftime('%Y-%m-%d')
    df = get_limit_up_data()
    summary = get_market_summary()

    # 连板分布HTML
    limit_days_html = ""
    for limit_days, count in summary['limit_days']:
        bar_width = min(count * 5, 100)
        limit_days_html += f'''
            <tr>
                <td width="100">{limit_days}板</td>
                <td width="300">
                    <div style="background: linear-gradient(to right, #ff6b6b, #ee5a24); width: {bar_width}%; height: 20px; border-radius: 4px;"></div>
                </td>
                <td width="100">{count}只</td>
            </tr>
        '''

    # 行业分布HTML
    industry_html = ""
    for industry, count in summary['top_industries']:
        bar_width = min(count * 2, 100)
        industry_html += f'''
            <tr>
                <td width="400">{industry}</td>
                <td width="300">
                    <div style="background: linear-gradient(to right, #4ecdc4, #17a2b8); width: {bar_width}%; height: 20px; border-radius: 4px;"></div>
                </td>
                <td width="100">{count}只</td>
            </tr>
        '''

    # 涨停股票表格HTML
    table_rows = ""
    for _, row in df.iterrows():
        table_rows += f'''
            <tr>
                <td>{row['code']}</td>
                <td>{row['name']}</td>
                <td style="color: #e74c3c; font-weight: bold;">+{row['change_percent']:.2f}%</td>
                <td>{row['price']:.2f}</td>
                <td>{row['amount']/100000000:.2f}亿</td>
                <td>{row['turnover_rate']:.2f}%</td>
                <td>{row['limit_days']}板</td>
                <td>{row['industry']}</td>
            </tr>
        '''

    # 涨幅分布HTML
    bins = [9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0, 19.5, 20.0, 30.0]
    histogram = {}
    for _, row in df.iterrows():
        for i in range(len(bins) - 1):
            if row['change_percent'] >= bins[i] and row['change_percent'] < bins[i+1]:
                key = f"{bins[i]}-{bins[i+1]}%"
                histogram[key] = histogram.get(key, 0) + 1
                break

    change_dist_html = ""
    for range_, (key, count) in enumerate(histogram.items()):
        bar_width = min(count * 3, 100)
        change_dist_html += f'''
            <div style="display: inline-block; margin-right: 5px;">
                <div style="background: #ff6b6b; width: {bar_width}px; height: 100px; display: inline-block; vertical-align: bottom; margin: 2px 0;">
                    <div style="text-align: center; color: white; font-size: 12px; padding-top: 5px;">{key}</div>
                </div>
                <div style="text-align: center; color: #666; font-size: 11px;">{count}</div>
            </div>
        '''

    html_template = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A股涨停分析仪表盘 - {date}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 30px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .title {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }}
        .subtitle {{
            font-size: 16px;
            color: #666;
            margin-bottom: 20px;
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            flex: 1;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
            color: #007bff;
        }}
        .stat-label {{
            font-size: 14px;
            color: #666;
        }}
        .section {{
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .section-title {{
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }}
        th {{
            background: #e9ecef;
            font-weight: 600;
            color: #495057;
        }}
        tbody tr:hover {{
            background: #f8f9fa;
        }}
        .refresh-btn {{
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            margin-bottom: 20px;
            width: 100%;
        }}
        .refresh-btn:hover {{
            background: #0056b3;
        }}
        .update-status {{
            text-align: center;
            color: #28a745;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        .chart-container {{
            margin-top: 15px;
            height: 120px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 A股涨停分析仪表盘</h1>
            <div class="subtitle">更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{summary['total_limit_up']}</div>
                <div class="stat-label">涨停总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #e74c3c;">{summary['avg_change']:.2f}%</div>
                <div class="stat-label">平均涨幅</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #17a2b8;">{summary['avg_amount']/100000000:.2f}亿</div>
                <div class="stat-label">平均成交额</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #ffc107;">{summary['avg_turnover']:.2f}%</div>
                <div class="stat-label">平均换手率</div>
            </div>
        </div>

        <div class="update-status">✅ 数据已本地化存储，加载速度极快！</div>

        <button class="refresh-btn" onclick="location.reload()">🔄 立即更新</button>

        <div class="section">
            <div class="section-title">📈 连板分布</div>
            <table>
                <thead>
                    <tr>
                        <th>连板天数</th>
                        <th>数量分布</th>
                        <th>股票数量</th>
                    </tr>
                </thead>
                <tbody>
                    {limit_days_html}
                </tbody>
            </table>
        </div>

        <div class="section">
            <div class="section-title">🏢 行业分布 Top10</div>
            <table>
                <thead>
                    <tr>
                        <th>行业</th>
                        <th>数量分布</th>
                        <th>股票数量</th>
                    </tr>
                </thead>
                <tbody>
                    {industry_html}
                </tbody>
            </table>
        </div>

        <div class="section">
            <div class="section-title">📊 涨幅分布</div>
            <div class="chart-container">
                {change_dist_html}
            </div>
        </div>

        <div class="section">
            <div class="section-title">🔥 涨停股票列表</div>
            <table>
                <thead>
                    <tr>
                        <th>代码</th>
                        <th>名称</th>
                        <th>涨幅</th>
                        <th>价格</th>
                        <th>成交额</th>
                        <th>换手率</th>
                        <th>连板</th>
                        <th>行业</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
    '''
    return html_template

@app.route('/api')
def api():
    """API接口"""
    date = datetime.now().strftime('%Y-%m-%d')
    df = get_limit_up_data()

    data = {
        'date': date,
        'total_count': len(df),
        'stocks': df.to_dict('records'),
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(data)

@app.route('/update')
def update():
    """更新数据"""
    count = collect_and_store_data()
    return jsonify({'status': 'success', 'count': count})

if __name__ == '__main__':
    # 初始化数据库
    print("初始化数据库...")
    init_database()

    # 收集数据
    print("收集初始数据...")
    collect_and_store_data()

    # 启动定时任务线程
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("定时任务已启动，每天16:00自动更新")

    # 运行应用
    print("启动本地化仪表盘服务...")
    app.run(host='0.0.0.0', port=5003, debug=False)
