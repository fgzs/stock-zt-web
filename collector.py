#!/usr/bin/env python3
"""
股票数据采集器 - 收集各种股票数据指标
"""
import akshare as ak
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json

class StockDataCollector:
    def __init__(self, db_path='/root/stock-zt-web/stocks.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 涨停股票表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS limit_up_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                change_percent REAL,
                price REAL,
                volume REAL,
                amount REAL,
                turnover_rate REAL,
                limit_amount REAL,
                first_limit_time TEXT,
                last_limit_time TEXT,
                break_count INTEGER,
                limit_days INTEGER,
                industry TEXT,
                market_cap REAL,
                circ_cap REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, code)
            )
        ''')

        # 股票实时行情表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                price REAL,
                change_percent REAL,
                volume REAL,
                amount REAL,
                high REAL,
                low REAL,
                open REAL,
                pre_close REAL,
                market_cap REAL,
                circ_cap REAL,
                pe REAL,
                pb REAL,
                turnover_rate REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(code, timestamp)
            )
        ''')

        # 封单数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS limit_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                limit_price REAL,
                buy_orders INTEGER,
                sell_orders INTEGER,
                buy_volume REAL,
                sell_volume REAL,
               封单比 REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, code)
            )
        ''')

        # 资金流向表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS money_flow (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                main_inflow REAL,
                main_outflow REAL,
                main_net REAL,
                retail_inflow REAL,
                retail_outflow REAL,
                retail_net REAL,
                super_large_inflow REAL,
                super_large_outflow REAL,
                super_large_net REAL,
                large_inflow REAL,
                large_outflow REAL,
                large_net REAL,
                medium_inflow REAL,
                medium_outflow REAL,
                medium_net REAL,
                small_inflow REAL,
                small_outflow REAL,
                small_net REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, code)
            )
        ''')

        # 龙虎榜数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dragon_tiger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                reason TEXT,
                net_buy REAL,
                net_sell REAL,
                buy_amount REAL,
                sell_amount REAL,
                buy_seat_count INTEGER,
                sell_seat_count INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, code)
            )
        ''')

        conn.commit()
        conn.close()
        print(f"数据库初始化完成: {self.db_path}")

    def collect_limit_up_stocks(self, date=None):
        """收集涨停股票数据"""
        if date is None:
            date = datetime.now().strftime('%Y%m%d')

        try:
            print(f"获取 {date} 涨停股票数据...")
            df = ak.stock_zt_pool_em(date=date)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for idx, row in df.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO limit_up_stocks
                    (date, code, name, change_percent, price, amount, circ_cap, market_cap,
                     turnover_rate, limit_amount, first_limit_time, last_limit_time,
                     break_count, limit_days, industry)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d'),
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

            conn.commit()
            conn.close()
            print(f"✅ 成功收集 {len(df)} 只涨停股票")
            return len(df)
        except Exception as e:
            print(f"❌ 收集涨停股票失败: {e}")
            return 0

    def collect_stock_quotes(self):
        """收集实时行情数据"""
        try:
            print("获取实时行情数据...")
            df = ak.stock_zh_a_spot_em()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            count = 0
            for idx, row in df.head(100).iterrows():  # 先获取前100只
                cursor.execute('''
                    INSERT OR REPLACE INTO stock_quotes
                    (code, name, price, change_percent, amount, high, low, open, pre_close,
                     market_cap, circ_cap, pe, pb, turnover_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['代码'],
                    row['名称'],
                    float(row['最新价']),
                    float(row['涨跌幅']),
                    float(row['成交额']),
                    float(row['最高']),
                    float(row['最低']),
                    float(row['今开']),
                    float(row['昨收']),
                    float(row['总市值']),
                    float(row['流通市值']),
                    float(row['市盈率-动态']),
                    float(row['市净率']),
                    float(row['换手率'])
                ))
                count += 1

            conn.commit()
            conn.close()
            print(f"✅ 成功收集 {count} 只股票的实时行情")
            return count
        except Exception as e:
            print(f"❌ 收集实时行情失败: {e}")
            return 0

    def collect_individual_stock_detail(self, code):
        """获取个股详细信息"""
        try:
            # 个股信息
            info = ak.stock_individual_info_em(symbol=code)
            # 历史行情
            hist = ak.stock_zh_a_hist(symbol=code, period='daily', start_date='20240101', end_date=datetime.now().strftime('%Y%m%d'))
            # 资金流向
            money_flow = ak.stock_individual_fund_flow(stock=code, symbol="当日")

            return {
                'info': info,
                'history': hist,
                'money_flow': money_flow
            }
        except Exception as e:
            print(f"获取 {code} 详情失败: {e}")
            return None

    def get_market_summary(self, date=None):
        """获取市场概览"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        conn = sqlite3.connect(self.db_path)
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

if __name__ == '__main__':
    collector = StockDataCollector()

    # 收集数据
    collector.collect_limit_up_stocks()
    collector.collect_stock_quotes()

    # 获取市场概览
    summary = collector.get_market_summary()
    print("\n=== 市场概览 ===")
    print(f"涨停总数: {summary['total_limit_up']}")
    print(f"平均涨幅: {summary['avg_change']:.2f}%")
    print(f"平均成交额: {summary['avg_amount']/100000000:.2f}亿")
    print(f"平均换手率: {summary['avg_turnover']:.2f}%")
