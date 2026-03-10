# 📊 股票分析仪表盘

一个基于 Python + Dash 的 A股涨停股票分析仪表盘，实时监控市场涨停情况，提供多维度的数据可视化。

## ✨ 功能特性

### 🔥 核心功能
- **实时涨停监控** - 每日自动收集涨停股票数据
- **动态数据存储** - 使用 SQLite 轻量级数据库存储历史数据
- **可视化仪表盘** - 基于 Dash + Plotly 的交互式图表
- **自动更新** - 每30分钟自动刷新数据，支持手动立即更新

### 📈 数据分析
- **涨停统计** - 涨停总数、平均涨幅、平均成交额、平均换手率
- **连板分析** - 连板天数分布、最高连板天数
- **行业分析** - 行业分布排名
- **涨幅分布** - 涨幅区间统计
- **成交排名** - 成交额 Top10 榜单

### 🎯 股票指标
- 基本信息：代码、名称、最新价
- 涨跌幅、涨跌额
- 成交量、成交额
- 换手率
- 市值（总市值、流通市值）
- 市盈率、市净率
- 封板资金
- 封板时间（首次、最后）
- 炸板次数
- 连板天数
- 所属行业

## 🚀 快速开始

### 环境要求
- Python 3.8+
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
# 初始化数据库并收集数据
python3 collector.py

# 启动仪表盘
python3 simple_dashboard.py
```

访问地址：
```
http://localhost:5001
```

### 系统集成

如果需要通过 Nginx 部署，参考 `nginx.conf` 配置文件。

## 📁 项目结构

```
stock-zt-web/
├── app.py                  # 旧版 Flask 应用（简单版本）
├── simple_dashboard.py     # 新版仪表盘（推荐使用）
├── collector.py           # 数据采集器
├── requirements.txt       # Python 依赖
├── stocks.db             # SQLite 数据库（自动生成）
├── data/                 # 数据缓存目录
├── nginx.conf            # Nginx 配置示例
└── README.md             # 项目文档
```

## 🎨 技术栈

- **后端**: Python 3 + Flask + Dash
- **数据库**: SQLite3
- **数据源**: AKShare（东方财富）
- **可视化**: Plotly
- **UI 框架**: Dash + Bootstrap Components

## 📊 数据来源

所有股票数据来源于 [AKShare](https://github.com/akfamily/akshare) 开源财经数据接口库。

### 主要接口
- `stock_zt_pool_em` - 涨停股池
- `stock_zh_a_spot_em` - 实时行情
- `stock_individual_info_em` - 个股信息

## 🔧 配置说明

### 数据库
默认路径：`/root/stock-zt-web/stocks.db`

如需修改，编辑 `collector.py` 中的 `DB_PATH` 变量。

### 自动更新
仪表盘每30分钟自动刷新一次数据，可点击"🔄 立即更新"按钮手动刷新。

### 数据采集策略
- 启动时自动收集当日数据
- 每30分钟检查并更新
- 支持手动触发更新

## 🎯 使用场景

### 适合人群
- 股票投资者
- 量化交易者
- 财经分析师
- 市场研究员

### 应用场景
- 日常盯盘
- 涨停板复盘
- 连板股追踪
- 行业热点分析
- 市场情绪判断

## 📝 未来计划

- [ ] 历史数据回看功能
- [ ] 个股详细分析页面
- [ ] 龙虎榜数据集成
- [ ] 资金流向分析
- [ ] 自定义股票关注列表
- [ ] 数据导出功能
- [ ] 邮件/消息通知
- [ ] 用户认证系统

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## ⚠️ 免责声明

本工具仅供学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎。

---

**Made with ❤️ by OpenClaw**
