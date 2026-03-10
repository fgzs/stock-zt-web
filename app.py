from flask import Flask, render_template_string, jsonify
import akshare as ak
import json
import os
from datetime import datetime
import schedule
import time
import threading

app = Flask(__name__)

# 数据存储路径
DATA_FILE = '/root/stock-zt-web/data/zt_data.json'

# 获取今天的日期格式 YYYYMMDD
def get_today_date():
    return datetime.now().strftime('%Y%m%d')

# 获取今天的日期格式 YYYY-MM-DD
def get_today_display():
    return datetime.now().strftime('%Y-%m-%d')

# 查询涨停数据
def fetch_zt_data():
    try:
        date_str = get_today_date()
        df = ak.stock_zt_pool_em(date=date_str)

        # 转换为字典列表
        data = []
        for idx, row in df.iterrows():
            stock = {
                '序号': int(row['序号']),
                '代码': row['代码'],
                '名称': row['名称'],
                '涨跌幅': float(row['涨跌幅']),
                '最新价': float(row['最新价']),
                '成交额': float(row['成交额']),
                '流通市值': float(row['流通市值']),
                '总市值': float(row['总市值']),
                '换手率': float(row['换手率']),
                '封板资金': float(row['封板资金']),
                '首次封板时间': row['首次封板时间'],
                '最后封板时间': row['最后封板时间'],
                '炸板次数': int(row['炸板次数']),
                '涨停统计': row['涨停统计'],
                '连板数': int(row['连板数']),
                '所属行业': row['所属行业']
            }
            data.append(stock)

        # 保存到文件
        result = {
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'date': get_today_display(),
            'total_count': len(data),
            'stocks': data
        }

        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result
    except Exception as e:
        print(f"查询出错: {e}")
        return None

# 读取缓存数据
def load_cached_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

# 定时任务
def scheduled_job():
    print(f"[{datetime.now()}] 开始更新涨停数据...")
    result = fetch_zt_data()
    if result:
        print(f"成功更新 {result['total_count']} 只涨停股票")
    else:
        print("更新失败")

# 启动定时任务线程
def run_scheduler():
    # 每天 16:00 更新数据（收盘后）
    schedule.every().day.at("16:00").do(scheduled_job)
    # 每 30 分钟检查一次（已禁用）
    # schedule.every(30).minutes.do(scheduled_job)

    while True:
        schedule.run_pending()
        time.sleep(60)

# HTML 模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A股涨停股票 - {{ data.date }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .header .stats {
            margin-top: 20px;
            display: flex;
            justify-content: center;
            gap: 30px;
        }
        .header .stat-item {
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 10px;
        }
        .header .stat-value {
            font-size: 1.5em;
            font-weight: bold;
        }
        .header .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        .search-box {
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }
        .search-box input {
            width: 100%;
            padding: 12px 20px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 1em;
            transition: all 0.3s;
        }
        .search-box input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
        }
        .table-container {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        thead {
            background: #f8f9fa;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }
        th {
            font-weight: 600;
            color: #495057;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        tbody tr {
            transition: all 0.2s;
        }
        tbody tr:hover {
            background: #f8f9fa;
            transform: scale(1.01);
        }
        .up { color: #e74c3c; font-weight: bold; }
        .price { font-family: 'Monaco', 'Menlo', monospace; }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .badge-hot { background: #ff6b6b; color: white; }
        .badge-new { background: #4ecdc4; color: white; }
        .badge-normal { background: #a8e6cf; color: #2d3436; }
        .footer {
            padding: 20px;
            text-align: center;
            background: #f8f9fa;
            color: #6c757d;
            font-size: 0.9em;
        }
        .update-time {
            margin-bottom: 10px;
        }
        .loading {
            text-align: center;
            padding: 60px;
            color: #6c757d;
        }
        @media (max-width: 768px) {
            .header h1 { font-size: 1.8em; }
            .header .stats { flex-direction: column; gap: 10px; }
            th, td { padding: 8px; font-size: 0.9em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 A股涨停股票</h1>
            <div class="subtitle">{{ data.date }}</div>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value">{{ data.total_count }}</div>
                    <div class="stat-label">涨停总数</div>
                </div>
            </div>
        </div>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 搜索股票代码或名称..." onkeyup="searchTable()">
        </div>

        <div class="table-container">
            <table id="stockTable">
                <thead>
                    <tr>
                        <th>序号</th>
                        <th>代码</th>
                        <th>名称</th>
                        <th>涨跌幅</th>
                        <th>最新价</th>
                        <th>成交额</th>
                        <th>换手率</th>
                        <th>连板</th>
                        <th>封板时间</th>
                        <th>行业</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    {% for stock in data.stocks %}
                    <tr>
                        <td>{{ stock.序号 }}</td>
                        <td class="price">{{ stock.代码 }}</td>
                        <td>{{ stock.名称 }}</td>
                        <td class="up">+{{ "%.2f"|format(stock.涨跌幅) }}%</td>
                        <td class="price">{{ "%.2f"|format(stock.最新价) }}</td>
                        <td>{{ "%.2f亿"|format(stock.成交额/100000000) }}</td>
                        <td>{{ "%.2f"|format(stock.换手率) }}%</td>
                        <td>
                            {% if stock.连板数 >= 3 %}
                            <span class="badge badge-hot">{{ stock.连板数 }}板</span>
                            {% elif stock.连板数 == 2 %}
                            <span class="badge badge-new">{{ stock.连板数 }}板</span>
                            {% else %}
                            <span class="badge badge-normal">{{ stock.连板数 }}板</span>
                            {% endif %}
                        </td>
                        <td>{{ stock.首次封板时间 }}</td>
                        <td>{{ stock.所属行业 }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="footer">
            <div class="update-time">🕒 更新时间: {{ data.update_time }}</div>
            <div>数据来源: akshare | OpenClaw 自动更新</div>
        </div>
    </div>

    <script>
        function searchTable() {
            const input = document.getElementById('searchInput');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('stockTable');
            const rows = table.getElementsByTagName('tr');

            for (let i = 1; i < rows.length; i++) {
                const cells = rows[i].getElementsByTagName('td');
                let found = false;
                for (let j = 0; j < cells.length; j++) {
                    if (cells[j]) {
                        const textValue = cells[j].textContent || cells[j].innerText;
                        if (textValue.toUpperCase().indexOf(filter) > -1) {
                            found = true;
                            break;
                        }
                    }
                }
                rows[i].style.display = found ? '' : 'none';
            }
        }
    </script>
</body>
</html>
'''

@app.route('/stock')
def stock():
    data = load_cached_data()
    if not data:
        # 如果没有缓存，立即获取
        data = fetch_zt_data()
    return render_template_string(HTML_TEMPLATE, data=data)

@app.route('/stock/api')
def stock_api():
    data = load_cached_data()
    if not data:
        data = fetch_zt_data()
    return jsonify(data)

@app.route('/stock/update')
def update_now():
    result = fetch_zt_data()
    if result:
        return jsonify({'status': 'success', 'count': result['total_count']})
    else:
        return jsonify({'status': 'error', 'message': '更新失败'}), 500

if __name__ == '__main__':
    # 启动时先获取一次数据
    print("初始化数据...")
    fetch_zt_data()

    # 启动定时任务线程
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("定时任务已启动，每天16:00自动更新数据")

    # 运行 Flask 应用
    app.run(host='0.0.0.0', port=5000)
