"""
回测结果分析器
分析回测结果并生成可视化图表，包括资产曲线和买卖信号标记
"""
import pandas as pd
import numpy as np
import matplotlib
from streamlit.runtime import stats

matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from typing import List, Dict, Any
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
from backtest_config import BacktestConfig
from database_manager import BacktestResultsDB

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class ResultAnalyzer:
    """回测结果分析器"""
    
    def __init__(self, config: 'BacktestConfig' = None, db_manager: 'BacktestResultsDB' = None):
        """初始化分析器"""
        self.config = config
        self.db_manager = db_manager
        self.results_data = {}
        
    def analyze_results(self, stats: pd.DataFrame, trades: List, daily_results: List):
        """分析回测结果"""
        print("\n" + "="*50)
        print("回测结果分析")
        print("="*50)
        
        # 显示统计信息
        self._print_statistics(stats)
        
        # 分析交易记录
        self._analyze_trades(trades)
        
        # 分析每日收益
        self._analyze_daily_results(daily_results)
        
        # 生成可视化图表
        file_paths = self._create_charts(daily_results, trades, stats)
        
        # 保存到数据库
        if self.db_manager and self.config:
            self.db_manager.save_backtest_results(
                self.config.run_id, stats, trades, daily_results,
                file_paths.get('html'), file_paths.get('png'), file_paths.get('excel')
            )
            print(f"📊 回测结果已保存到数据库，运行ID: {self.config.run_id}")
        
    def _print_statistics(self, stats: pd.DataFrame):
        """打印统计信息"""
        print("\n📊 核心统计指标:")
        print("-" * 30)
        
        # 如果 stats 不是有效的 DataFrame，跳过
        if stats is None or not isinstance(stats, pd.DataFrame) or stats.empty:
            print("⚠️  无统计数据")
            return
        
        # 从 DataFrame 中提取数据并显示
        try:
            for index, row in stats.iterrows():
                # 假设 DataFrame 有名为 'value' 的列，如果结构不同需要调整
                if 'value' in stats.columns:
                    value = row['value']
                    if isinstance(value, (int, float)):
                        if 'rate' in str(index).lower() or 'ratio' in str(index).lower():
                            print(f"{index:<12}: {value:.2f}")
                        elif 'return' in str(index).lower() or 'drawdown' in str(index).lower():
                            print(f"{index:<12}: {value:.2f}%")
                        else:
                            print(f"{index:<12}: {value:.2f}")
                    else:
                        print(f"{index:<12}: {value}")
                else:
                    # 如果没有 'value' 列，显示所有列的值
                    print(f"{index}: {row.to_dict()}")
        except Exception as e:
            print(f"显示统计信息时出错: {e}")
            print("统计数据结构:")
            print(stats.head())
    
    def _analyze_trades(self, trades: List):
        """分析交易记录"""
        if not trades:
            print("\n⚠️  无交易记录")
            return
            
        print(f"\n📈 交易记录分析 (共{len(trades)}笔交易):")
        print("-" * 30)
        
        # 分析买卖配对并计算盈亏
        positions = {}  # 跟踪每个symbol的持仓
        trade_pairs = []  # 存储买卖配对
        
        for trade in trades:
            symbol = getattr(trade, 'symbol', 'unknown')
            direction = str(getattr(trade, 'direction', ''))
            offset = str(getattr(trade, 'offset', ''))
            price = getattr(trade, 'price', 0)
            volume = getattr(trade, 'volume', 0)
            datetime_obj = getattr(trade, 'datetime', None)
            
            if 'OPEN' in offset:  # 开仓
                if symbol not in positions:
                    positions[symbol] = []
                positions[symbol].append({
                    'entry_price': price,
                    'volume': volume,
                    'datetime': datetime_obj,
                    'direction': direction
                })
            elif 'CLOSE' in offset:  # 平仓
                if symbol in positions and positions[symbol]:
                    entry = positions[symbol].pop(0)  # FIFO
                    pnl = 0
                    if 'LONG' in entry['direction']:
                        pnl = (price - entry['entry_price']) * volume
                    else:  # SHORT
                        pnl = (entry['entry_price'] - price) * volume
                    
                    trade_pairs.append({
                        'entry_datetime': entry['datetime'],
                        'exit_datetime': datetime_obj,
                        'entry_price': entry['entry_price'],
                        'exit_price': price,
                        'direction': entry['direction'],
                        'volume': volume,
                        'pnl': pnl
                    })
        
        if trade_pairs:
            profits = [pair['pnl'] for pair in trade_pairs]
            win_trades = [p for p in profits if p > 0]
            lose_trades = [p for p in profits if p < 0]
            
            print(f"完整交易对: {len(trade_pairs)}笔")
            print(f"盈利交易: {len(win_trades)}笔, 平均盈利: {np.mean(win_trades):.2f}" if win_trades else "盈利交易: 0笔")
            print(f"亏损交易: {len(lose_trades)}笔, 平均亏损: {np.mean(lose_trades):.2f}" if lose_trades else "亏损交易: 0笔")
            print(f"最大单笔盈利: {max(profits):.2f}")
            print(f"最大单笔亏损: {min(profits):.2f}")
            print(f"总盈亏: {sum(profits):.2f}")
            
            # 胜率
            win_rate = len(win_trades) / len(trade_pairs) * 100 if trade_pairs else 0
            print(f"胜率: {win_rate:.1f}%")
        else:
            print("⚠️  无完整的交易对数据")
            
        # 显示最近5笔交易 - 使用原始交易记录
        print(f"\n📋 最近5笔交易:")
        recent_trades = trades[-5:] if len(trades) >= 5 else trades
        for i, trade in enumerate(recent_trades, 1):
            datetime_str = str(getattr(trade, 'datetime', 'N/A'))
            price = getattr(trade, 'price', 0)
            volume = getattr(trade, 'volume', 0)
            direction = getattr(trade, 'direction', 'N/A')
            offset = getattr(trade, 'offset', 'N/A')
            
            action = "开多" if "LONG" in str(direction) and "OPEN" in str(offset) else \
                    "平多" if "SHORT" in str(direction) and "CLOSE" in str(offset) else \
                    "开空" if "SHORT" in str(direction) and "OPEN" in str(offset) else \
                    "平空" if "LONG" in str(direction) and "CLOSE" in str(offset) else "未知"
            
            # 尝试找到对应的盈亏
            pnl = 0
            if trade_pairs:
                for pair in trade_pairs:
                    if pair['exit_datetime'] == getattr(trade, 'datetime', None):
                        pnl = pair['pnl']
                        break
            
            print(f"  {i}. {datetime_str} {action} "
                  f"价格:{price:.2f} 数量:{volume} 盈亏:{pnl:.2f}")
    
    def _analyze_daily_results(self, daily_results: List):
        """分析每日收益"""
        if not daily_results:
            print("\n⚠️  无每日收益数据")
            return
            
        print(f"\n📊 每日收益分析 (共{len(daily_results)}天):")
        print("-" * 30)
        
        # 提取净盈亏数据
        net_pnls = [result.net_pnl for result in daily_results if hasattr(result, 'net_pnl')]
        
        if net_pnls:
            # 计算累计资产
            initial_capital = 1000000
            cumulative_pnl = np.cumsum(net_pnls)
            final_balance = initial_capital + cumulative_pnl[-1]
            
            print(f"初始资金: {initial_capital:,.2f}")
            print(f"期末资金: {final_balance:,.2f}")
            print(f"总盈亏: {cumulative_pnl[-1]:,.2f}")
            print(f"总收益率: {(cumulative_pnl[-1] / initial_capital) * 100:.2f}%")
            print(f"平均日收益: {np.mean(net_pnls):.2f}")
            print(f"收益标准差: {np.std(net_pnls):.2f}")
            print(f"最好单日: {max(net_pnls):.2f}")
            print(f"最差单日: {min(net_pnls):.2f}")
            
            # 计算最大回撤
            cumulative_max = np.maximum.accumulate(cumulative_pnl + initial_capital)
            drawdowns = (cumulative_pnl + initial_capital - cumulative_max) / cumulative_max
            max_drawdown = np.min(drawdowns) * 100
            print(f"最大回撤: {max_drawdown:.2f}%")
            
            # 计算胜率
            winning_days = len([pnl for pnl in net_pnls if pnl > 0])
            win_rate = (winning_days / len(net_pnls)) * 100 if net_pnls else 0
            print(f"盈利天数: {winning_days}/{len(net_pnls)} ({win_rate:.1f}%)")
        else:
            print("⚠️  每日收益数据为空或全为0")
    
    def _create_charts(self, daily_results: List, trades: List, stats: pd.DataFrame = None) -> Dict[str, str]:
        """创建可视化图表并返回文件路径"""
        if not daily_results:
            print("无法创建图表：缺少每日结果数据")
            return {}
        
        file_paths = {}
        
        # 创建matplotlib图表
        png_path = self._create_matplotlib_chart(daily_results, trades)
        if png_path:
            file_paths['png'] = png_path
        
        # 创建plotly交互式图表
        html_path = self._create_plotly_chart(daily_results, trades)
        if html_path:
            file_paths['html'] = html_path
        
        # 创建Excel报告
        excel_path = self._create_excel_report(daily_results, trades, stats)
        if excel_path:
            file_paths['excel'] = excel_path
        
        return file_paths
    
    def _create_matplotlib_chart(self, daily_results: List, trades: List) -> str:
        """创建matplotlib图表"""
        try:
            # 提取数据 - 修复数据访问
            dates = []
            net_pnls = []
            
            # 从每日结果中提取数据
            for result in daily_results:
                if hasattr(result, 'date') and hasattr(result, 'net_pnl'):
                    dates.append(result.date)
                    net_pnls.append(result.net_pnl)
            
            if not dates or not net_pnls:
                print("无法创建matplotlib图表：缺少必要数据")
                return None
            
            # 计算累计资产曲线 (假设初始资金1000000)
            initial_capital = 1000000
            cumulative_pnl = np.cumsum(net_pnls)
            balances = initial_capital + cumulative_pnl
                
            # 创建图表
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # 资产曲线
            ax1.plot(dates, balances, linewidth=2, color='blue', label='账户资产')
            ax1.set_title('账户资产曲线', fontsize=14, fontweight='bold')
            ax1.set_ylabel('资产净值', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # 设置日期格式
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            
            # 每日收益
            ax2.bar(dates, net_pnls, width=1, color=['green' if x >= 0 else 'red' for x in net_pnls], alpha=0.7)
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax2.set_title('每日盈亏', fontsize=14, fontweight='bold')
            ax2.set_ylabel('盈亏', fontsize=12)
            ax2.set_xlabel('日期', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # 设置日期格式
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            
            plt.tight_layout()
            plt.xticks(rotation=45)
            
            # 保存图表到配置的路径
            if self.config:
                png_path = self.config.get_output_path('png', 'backtest_results.png')
            else:
                png_path = 'backtest_results.png'
            
            plt.savefig(png_path, dpi=300, bbox_inches='tight')
            print(f"📈 matplotlib图表已保存为 {png_path}")
            plt.close()  # 关闭图表以释放内存
            
            return png_path
            
        except Exception as e:
            print(f"创建matplotlib图表失败: {e}")
            return None
    
    def _create_plotly_chart(self, daily_results: List, trades: List) -> str:
        """创建plotly交互式图表"""
        try:
            # 提取数据
            dates = []
            net_pnls = []
            
            for result in daily_results:
                if hasattr(result, 'date') and hasattr(result, 'net_pnl'):
                    dates.append(result.date)
                    net_pnls.append(result.net_pnl)
            
            if not dates or not net_pnls:
                print("无法创建plotly图表：缺少必要数据")
                return None
            
            # 计算累计资产曲线
            initial_capital = 1000000
            cumulative_pnl = np.cumsum(net_pnls)
            balances = initial_capital + cumulative_pnl
            
            # 创建子图
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=('账户资产曲线', '每日盈亏', '累计盈亏'),
                vertical_spacing=0.08
            )
            
            # 资产曲线
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=balances,
                    mode='lines',
                    name='账户资产',
                    line=dict(color='blue', width=2)
                ),
                row=1, col=1
            )
            
            # 每日盈亏
            colors = ['green' if x >= 0 else 'red' for x in net_pnls]
            fig.add_trace(
                go.Bar(
                    x=dates,
                    y=net_pnls,
                    name='每日盈亏',
                    marker_color=colors
                ),
                row=2, col=1
            )
            
            # 累计盈亏
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=cumulative_pnl,
                    mode='lines',
                    name='累计盈亏',
                    line=dict(color='orange', width=2),
                    fill='tonexty'
                ),
                row=3, col=1
            )
            
            # 添加买卖信号标记
            self._add_trade_signals_fixed(fig, trades, dates, balances)
            
            # 更新布局
            fig.update_layout(
                title='vnpy回测结果分析',
                height=1000,
                showlegend=True,
                hovermode='x unified'
            )
            
            # 更新坐标轴
            fig.update_xaxes(title_text="日期", row=3, col=1)
            fig.update_yaxes(title_text="资产净值", row=1, col=1)
            fig.update_yaxes(title_text="每日盈亏", row=2, col=1)
            fig.update_yaxes(title_text="累计盈亏", row=3, col=1)
            
            # 保存HTML文件到配置的路径
            if self.config:
                html_path = self.config.get_output_path('html', 'backtest_results.html')
            else:
                html_path = 'backtest_results.html'
            
            fig.write_html(html_path)
            print(f"📊 plotly交互式图表已保存为 {html_path}")
            
            return html_path
            
        except Exception as e:
            print(f"创建plotly图表失败: {e}")
            return None
    
    def _add_trade_signals_fixed(self, fig, trades: List, dates: List, balances: List):
        """添加买卖信号标记 - 修复版本"""
        if not trades:
            return
            
        try:
            # 提取交易信号
            buy_dates = []
            buy_balances = []
            sell_dates = []
            sell_balances = []
            
            # 创建日期到余额的映射
            date_balance_map = dict(zip(dates, balances))
            
            for trade in trades:
                if hasattr(trade, 'datetime'):
                    trade_date = trade.datetime.date()  # 转换为日期格式
                    
                    # 查找最近的交易日期对应的余额
                    balance = None
                    for date in dates:
                        if date >= trade_date:
                            balance = date_balance_map[date]
                            break
                    
                    if balance is None:
                        balance = balances[-1]  # 使用最后一天的余额
                        
                    # 判断买卖方向
                    if hasattr(trade, 'offset'):
                        if 'OPEN' in str(trade.offset):
                            buy_dates.append(trade_date)
                            buy_balances.append(balance)
                        else:
                            sell_dates.append(trade_date)
                            sell_balances.append(balance)
            
            # 添加买入信号
            if buy_dates:
                fig.add_trace(
                    go.Scatter(
                        x=buy_dates,
                        y=buy_balances,
                        mode='markers',
                        name='买入信号',
                        marker=dict(
                            color='red',
                            size=8,
                            symbol='triangle-up'
                        )
                    ),
                    row=1, col=1
                )
            
            # 添加卖出信号
            if sell_dates:
                fig.add_trace(
                    go.Scatter(
                        x=sell_dates,
                        y=sell_balances,
                        mode='markers',
                        name='卖出信号',
                        marker=dict(
                            color='green',
                            size=8,
                            symbol='triangle-down'
                        )
                    ),
                    row=1, col=1
                )
                
        except Exception as e:
            print(f"添加交易信号失败: {e}")
    
    def _create_excel_report(self, daily_results: List, trades: List, stats: pd.DataFrame = None) -> str:
        """创建Excel报告"""
        try:
            if self.config:
                excel_path = self.config.get_output_path('excel', 'backtest_report.xlsx')
            else:
                excel_path = 'backtest_report.xlsx'
            
            # 使用openpyxl引擎创建Excel文件
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                # 检查 stats 是否为有效的 DataFrame
                has_stats = stats is not None and isinstance(stats, pd.DataFrame) and not stats.empty
                
                # 总是先创建概要页，确保至少有一个工作表
                summary_data = []
                summary_data.append(['回测报告生成时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                summary_data.append(['统计数据', '有' if has_stats else '无'])
                summary_data.append(['交易记录数量', str(len(trades)) if trades else '0'])
                summary_data.append(['每日数据数量', str(len(daily_results)) if daily_results else '0'])
                
                summary_df = pd.DataFrame(summary_data, columns=['项目', '值'])
                summary_df.to_excel(writer, sheet_name='概要', index=False)
                
                # 如果有统计数据，创建统计数据工作表
                if has_stats:
                    try:
                        # stats 是 DataFrame，直接写入
                        stats.to_excel(writer, sheet_name='统计数据', index=True)
                    except Exception as e:
                        print(f"创建统计数据工作表失败: {e}")
                        # 即使统计数据工作表创建失败，也要继续创建其他工作表
                
                # 如果有交易记录，创建交易记录工作表
                if trades and len(trades) > 0:
                    try:
                        trade_data = []
                        for trade in trades:
                            trade_data.append([
                                str(getattr(trade, 'datetime', '')),
                                str(getattr(trade, 'symbol', '')),
                                str(getattr(trade, 'direction', '')),
                                str(getattr(trade, 'offset', '')),
                                float(getattr(trade, 'price', 0)),
                                int(getattr(trade, 'volume', 0))
                            ])
                        trades_df = pd.DataFrame(trade_data, columns=['时间', '品种', '方向', '开平', '价格', '数量'])
                        trades_df.to_excel(writer, sheet_name='交易记录', index=False)
                    except Exception as e:
                        print(f"创建交易记录工作表失败: {e}")
                
                # 如果有每日结果，创建每日结果工作表
                if daily_results and len(daily_results) > 0:
                    try:
                        daily_data = []
                        for result in daily_results:
                            daily_data.append([
                                str(getattr(result, 'date', '')),
                                float(getattr(result, 'balance', 0)),
                                float(getattr(result, 'net_pnl', 0))
                            ])
                        daily_df = pd.DataFrame(daily_data, columns=['日期', '资产', '净盈亏'])
                        daily_df.to_excel(writer, sheet_name='每日结果', index=False)
                    except Exception as e:
                        print(f"创建每日结果工作表失败: {e}")
            
            print(f"📋 Excel报告已成功创建: {excel_path}")
            return excel_path
            
        except Exception as e:
            print(f"创建Excel报告失败: {e}")
            return None


if __name__ == "__main__":
    # 测试分析器
    analyzer = ResultAnalyzer()
    
    # 模拟统计数据
    mock_stats = {
        'total_return': 15.5,
        'annual_return': 12.3,
        'max_drawdown': -8.2,
        'sharpe_ratio': 1.45,
        'win_rate': 55.6,
        'total_trades': 25
    }
    
    print("测试结果分析器...")
    analyzer._print_statistics(pd.DataFrame(mock_stats)) 