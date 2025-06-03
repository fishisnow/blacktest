"""
vnpy趋势跟踪策略回测系统 - Streamlit版本
集成股票选择、参数设置、回测执行和结果展示
"""
import time
import traceback
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.conf.backtest_config import BacktestConfig
from src.blacktest_runner import BacktestRunner, INITIAL_CAPITAL
from src.storage.database_manager import BacktestResultsDB
from src.storage.db_utils import get_db_manager
from src.strategies.trend_following_strategy import TrendFollowingStrategy
# 导入回测相关模块
from src.symbol.symbols import get_all_symbols, get_symbols_by_market
from src.storage.data_loader import DataLoader

# 页面配置
st.set_page_config(
    page_title="回测结果分析系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 全局状态管理
if 'backtest_running' not in st.session_state:
    st.session_state.backtest_running = False
if 'backtest_progress' not in st.session_state:
    st.session_state.backtest_progress = 0
if 'current_symbol' not in st.session_state:
    st.session_state.current_symbol = None
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = None

# 在文件开头添加字段转换函数
def convert_trade_fields(trade_dict):
    """转换交易记录字段为通俗易懂的中文术语"""
    # 方向转换
    direction_map = {
        'Direction.LONG': '做多',
        'Direction.SHORT': '做空',
    }
    
    # 开平转换
    offset_map = {
        'Offset.OPEN': '开仓',
        'Offset.CLOSE': '平仓',
    }
    
    # 转换方向
    direction = trade_dict.get('direction', '')
    if direction in direction_map:
        direction = direction_map[direction]
    elif 'LONG' in str(direction).upper():
        direction = '做多'
    elif 'SHORT' in str(direction).upper():
        direction = '做空'
    
    # 转换开平
    offset = trade_dict.get('offset', '')
    if offset in offset_map:
        offset = offset_map[offset]
    elif 'OPEN' in str(offset).upper():
        offset = '开仓'
    elif 'CLOSE' in str(offset).upper():
        offset = '平仓'
    
    return direction, offset

class BacktestExecutor:
    """回测执行器"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
    
    def run_backtest_async(self, symbol: str, strategy_params: dict, date_range: tuple):
        """异步执行回测"""
        try:
            st.session_state.backtest_running = True
            st.session_state.backtest_progress = 10
            
            # 确保日期是datetime对象而不是date对象
            from datetime import datetime, date
            start_date = date_range[0]
            end_date = date_range[1]
            
            # 如果是date对象，转换为datetime对象
            if isinstance(start_date, date) and not isinstance(start_date, datetime):
                start_date = datetime.combine(start_date, datetime.min.time())
            if isinstance(end_date, date) and not isinstance(end_date, datetime):
                end_date = datetime.combine(end_date, datetime.min.time())
            
            # 创建配置
            config = BacktestConfig(
                output_base_dir="../backtest_results",
                symbol=symbol,
                strategy_name="TrendFollowingStrategy",
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                strategy_params=strategy_params
            )
            
            st.session_state.backtest_progress = 30
            
            # 创建回测运行器
            runner = BacktestRunner(config)
            
            # 设置回测引擎 - 现在传递datetime对象
            runner.setup_engine(symbol, start_date, end_date)
            st.session_state.backtest_progress = 50
            
            # 添加策略
            runner.add_strategy(TrendFollowingStrategy, strategy_params)
            st.session_state.backtest_progress = 60
            
            # 加载数据
            if runner.load_data(symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")):
                st.session_state.backtest_progress = 80
                
                # 运行回测
                runner.run_backtest()
                st.session_state.backtest_progress = 90
                
                # 获取结果
                stats = runner.engine.calculate_result()
                trades = runner.engine.get_all_trades()
                daily_results = runner.engine.get_all_daily_results()
                
                # 保存结果 - 先调用show_results保存基本配置信息
                runner.show_results()
                
                # 然后进行详细分析（这会保存完整的回测结果）
                runner.analyzer.analyze_results(stats, trades, daily_results)
                
                # 转换为可序列化的格式
                serializable_trades = []
                for trade in trades:
                    trade_dict = {
                        'datetime': str(getattr(trade, 'datetime', '')),
                        'symbol': getattr(trade, 'symbol', ''),
                        'direction': str(getattr(trade, 'direction', '')),
                        'offset': str(getattr(trade, 'offset', '')),
                        'price': float(getattr(trade, 'price', 0)),
                        'volume': float(getattr(trade, 'volume', 0)),
                        'pnl': float(getattr(trade, 'pnl', 0))
                    }
                    serializable_trades.append(trade_dict)
                
                serializable_daily_results = []
                cumulative_pnl = 0
                win_count = 0  # 盈利天数
                loss_count = 0  # 亏损天数
                
                for result in daily_results:
                    # 累积总盈亏
                    net_pnl = getattr(result, 'net_pnl', 0)
                    cumulative_pnl += net_pnl
                    
                    # 统计盈亏天数
                    if net_pnl > 0:
                        win_count += 1
                    elif net_pnl < 0:
                        loss_count += 1
                    
                    # 计算盈亏比（避免除零错误）
                    if loss_count > 0:
                        win_loss_ratio = win_count / loss_count
                    else:
                        win_loss_ratio = win_count if win_count > 0 else 0
                    
                    # 计算收益率（相对于初始资金）
                    return_ratio = (cumulative_pnl / INITIAL_CAPITAL) * 100 if INITIAL_CAPITAL > 0 else 0
                    
                    result_dict = {
                        'date': str(getattr(result, 'date', '')),
                        'net_pnl': float(getattr(result, 'net_pnl', 0)),
                        'pnl': float(getattr(result, 'pnl', 0)),
                        'total_pnl': float(cumulative_pnl),  # 累积总盈亏
                        'return_ratio': float(return_ratio),  # 收益率（%）
                        'win_count': int(win_count),  # 盈利天数
                        'loss_count': int(loss_count),  # 亏损天数
                        'win_loss_ratio': float(win_loss_ratio)  # 盈利天数/亏损天数比
                    }
                    serializable_daily_results.append(result_dict)
                
                st.session_state.backtest_progress = 100
                st.session_state.backtest_results = {
                    'stats': stats,
                    'trades': serializable_trades,
                    'daily_results': serializable_daily_results,
                    'symbol': symbol
                }
                
                return True
            else:
                st.error(f"无法加载 {symbol} 数据")
                return False
                
        except Exception as e:
            st.error(f"回测执行失败: {str(e)}")
            traceback.print_exc()
            return False
        finally:
            st.session_state.backtest_running = False

def create_stock_kline_chart(symbol: str, start_date: str, end_date: str) -> go.Figure:
    """创建股票K线图"""
    try:
        # 使用DataLoader直接获取数据
        data_loader = DataLoader()
        
        # 获取历史数据
        print(f"正在获取 {symbol} 从 {start_date} 到 {end_date} 的历史数据...")
        bars_data = data_loader.get_index_data(symbol, start_date, end_date)
        
        if bars_data and len(bars_data) > 0:
            # 转换数据格式
            dates = []
            opens = []
            highs = []
            lows = []
            closes = []
            volumes = []
            
            for bar in bars_data:
                dates.append(bar.datetime)
                opens.append(bar.open_price)
                highs.append(bar.high_price)
                lows.append(bar.low_price)
                closes.append(bar.close_price)
                volumes.append(bar.volume)
            
            # 创建K线图
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=(f'{symbol} - 股价走势', '成交量'),
                vertical_spacing=0.1,
                row_heights=[0.7, 0.3],
                shared_xaxes=True
            )
            
            # K线图
            fig.add_trace(
                go.Candlestick(
                    x=dates,
                    open=opens,
                    high=highs,
                    low=lows,
                    close=closes,
                    name='K线',
                    increasing_line_color='red',
                    decreasing_line_color='green'
                ),
                row=1, col=1
            )
            
            # 成交量
            volume_colors = ['red' if c >= o else 'green' for c, o in zip(closes, opens)]
            fig.add_trace(
                go.Bar(
                    x=dates,
                    y=volumes,
                    name='成交量',
                    marker_color=volume_colors,
                    opacity=0.7
                ),
                row=2, col=1
            )
            
            # 更新布局
            fig.update_layout(
                title=f'{symbol} 历史走势图',
                height=600,
                showlegend=False,
                xaxis_rangeslider_visible=False,
                font=dict(size=12)
            )
            
            fig.update_yaxes(title_text="股价", row=1, col=1)
            fig.update_yaxes(title_text="成交量", row=2, col=1)
            fig.update_xaxes(title_text="日期", row=2, col=1)
            
            print(f"成功生成包含 {len(bars_data)} 条数据的K线图")
            return fig
        else:
            # 返回空图表
            fig = go.Figure()
            fig.add_annotation(
                text=f"无法获取 {symbol} 的历史数据\n请检查股票代码是否正确或数据源连接",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(height=400, title=f"{symbol} K线图")
            return fig
            
    except Exception as e:
        # 返回错误信息图表
        fig = go.Figure()
        fig.add_annotation(
            text=f"K线图生成失败: {str(e)}\n\n可能的原因：\n- 数据源连接问题\n- 股票代码格式错误\n- 网络连接异常",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14)
        )
        fig.update_layout(height=400, title="K线图生成失败")
        print(f"K线图生成异常: {e}")
        return fig

def create_performance_chart(daily_results) -> go.Figure:
    """创建性能图表"""
    if not daily_results or len(daily_results) == 0:
        return go.Figure()
    
    # 转换为DataFrame
    if isinstance(daily_results, list) and len(daily_results) > 0:
        # 检查是字典列表还是对象列表
        if isinstance(daily_results[0], dict):
            # 字典格式（序列化后的数据）
            df_data = []
            for result in daily_results:
                df_data.append({
                    'date': result.get('date', ''),
                    'total_pnl': result.get('total_pnl', 0),
                    'return_ratio': result.get('return_ratio', 0),
                    'net_pnl': result.get('net_pnl', 0),
                    'win_loss_ratio': result.get('win_loss_ratio', 0)
                })
            df = pd.DataFrame(df_data)
        else:
            # 对象格式（原始vnpy对象）
            df_data = []
            cumulative_pnl = 0
            for daily_result in daily_results:
                net_pnl = getattr(daily_result, 'net_pnl', 0)
                cumulative_pnl += net_pnl
                # 计算收益率
                return_ratio = (cumulative_pnl / INITIAL_CAPITAL) * 100 if INITIAL_CAPITAL > 0 else 0
                df_data.append({
                    'date': getattr(daily_result, 'date', ''),
                    'total_pnl': cumulative_pnl,
                    'return_ratio': return_ratio,
                    'net_pnl': net_pnl,
                    'win_loss_ratio': 0  # 这里需要重新计算，暂时设为0
                })
            df = pd.DataFrame(df_data)
    else:
        # DataFrame格式
        df = daily_results
    
    if df.empty:
        return go.Figure()
    
    # 调试信息：打印数据状态
    print(f"图表数据状态: {len(df)} 行数据")
    print(f"收益率范围: {df['return_ratio'].min():.4f} ~ {df['return_ratio'].max():.4f}")
    print(f"日期范围: {df['date'].min()} ~ {df['date'].max()}")
    
    # 确定x轴显示模式
    data_length = len(df)
    if data_length > 500:
        print(f"应用长期模式: {data_length}天数据，显示季度刻度")
    elif data_length > 250:
        print(f"应用中期模式: {data_length}天数据，显示月度刻度")
    else:
        print(f"应用短期模式: {data_length}天数据，显示详细刻度")
    
    # 确保date列是datetime类型
    try:
        df['date'] = pd.to_datetime(df['date'])
    except:
        # 如果转换失败，使用索引作为x轴
        df['date'] = range(len(df))
    
    df = df.sort_values('date')
    
    # 创建子图
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('累积收益率与总盈亏', '每日盈亏', '盈利天数/亏损天数比'),
        vertical_spacing=0.08,
        row_heights=[0.4, 0.35, 0.25],
        specs=[[{"secondary_y": True}],
               [{"secondary_y": False}],
               [{"secondary_y": False}]]
    )
    
    # 第一个子图：双y轴显示收益率和总盈亏
    # 左轴：收益率曲线
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['return_ratio'],
            mode='lines',
            name='累积收益率 (%)',
            line=dict(color='green', width=2),
            hovertemplate='%{y:.2f}%<extra></extra>'
        ),
        row=1, col=1, secondary_y=False
    )
    
    # 右轴：总盈亏曲线
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['total_pnl'],
            mode='lines',
            name='累积总盈亏',
            line=dict(color='blue', width=2, dash='dot'),
            hovertemplate='%{y:,.0f}<extra></extra>'
        ),
        row=1, col=1, secondary_y=True
    )
    
    # 添加零线（左轴）
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)
    
    # 每日盈亏
    colors = ['green' if x >= 0 else 'red' for x in df['net_pnl']]
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['net_pnl'],
            name='每日盈亏',
            marker_color=colors,
            opacity=0.7,
            hovertemplate='%{y:,.0f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # 盈利天数/亏损天数比走势
    if 'win_loss_ratio' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['win_loss_ratio'],
                mode='lines+markers',
                name='盈利天数/亏损天数比',
                line=dict(color='purple', width=2),
                marker=dict(size=4),
                hovertemplate='%{y:.2f}<extra></extra>'
            ),
            row=3, col=1
        )
        
        # 添加比值=1的参考线
        fig.add_hline(y=1, line_dash="dash", line_color="orange", row=3, col=1)
    
    # 更新布局
    fig.update_layout(
        title='回测性能分析',
        height=900,
        showlegend=True,
        hovermode='x unified',  # 恢复统一悬停模式以显示日期
        font=dict(size=12)
    )
    
    # 设置x轴标题
    fig.update_xaxes(title_text="日期", row=3, col=1)
    
    # 设置y轴标题
    fig.update_yaxes(title_text="收益率 (%)", secondary_y=False, row=1, col=1)
    fig.update_yaxes(title_text="累积总盈亏", secondary_y=True, row=1, col=1)
    fig.update_yaxes(title_text="每日盈亏", row=2, col=1)
    fig.update_yaxes(title_text="盈利天数/亏损天数比", row=3, col=1)
    
    # 优化x轴显示：根据数据长度智能调整
    if data_length > 500:  # 数据超过500天（约2年）
        # 长期数据：只显示季度标记
        fig.update_xaxes(
            showticklabels=True,
            tickmode='auto',
            nticks=8,  # 限制为8个刻度点
            tickangle=0,  # 水平显示
            tickformat='%Y-%m'  # 只显示年月
        )
    elif data_length > 250:  # 数据超过250天（约1年）
        # 中期数据：显示月度标记
        fig.update_xaxes(
            showticklabels=True,
            tickmode='auto', 
            nticks=12,  # 限制为12个刻度点
            tickangle=0,
            tickformat='%Y-%m'
        )
    else:
        # 短期数据：正常显示
        fig.update_xaxes(
            showticklabels=True,
            tickmode='auto',
            tickangle=45,
            tickformat='%m-%d'  # 只显示月日
        )
    
    return fig

def show_backtest_interface():
    """显示回测界面"""
    st.header("📈 vnpy趋势跟踪策略回测系统")
    
    # 加载股票代码
    try:
        all_symbols = get_all_symbols()
        cn_stocks = get_symbols_by_market('CN')
    except Exception as e:
        st.error(f"加载股票代码失败: {e}")
        all_symbols = {}
        cn_stocks = {}
    
    # 左侧边栏 - 股票选择
    with st.sidebar:
        st.title("🎯 股票选择")
        
        # 市场筛选
        market_filter = st.selectbox(
            "选择市场",
            ["全部", "CN", "HK", "US"],
            index=1
        )
        
        # 类型筛选
        type_filter = st.selectbox(
            "选择类型", 
            ["全部", "stock", "index"],
            index=0
        )
        
        # 根据筛选条件获取股票列表
        filtered_symbols = {}
        for symbol, info in all_symbols.items():
            if market_filter != "全部" and info['market'] != market_filter:
                continue
            if type_filter != "全部" and info['type'] != type_filter:
                continue
            filtered_symbols[symbol] = info
        
        # 股票选择
        if filtered_symbols:
            symbol_options = [f"{symbol} - {info['name']}" for symbol, info in filtered_symbols.items()]
            selected_option = st.selectbox(
                "选择股票",
                symbol_options,
                index=0
            )
            selected_symbol = selected_option.split(' - ')[0] if selected_option else None
        else:
            selected_symbol = None
            st.warning("未找到符合条件的股票")
        
        # 默认股票（如果没有加载到股票列表）
        if not all_symbols:
            st.warning("股票代码文件加载失败，使用默认股票")
            default_symbols = {
                "688981.SH": "中芯国际",
                "000001.SH": "上证指数", 
                "000300.SH": "沪深300",
                "399006.SZ": "创业板指"
            }
            symbol_options = [f"{symbol} - {name}" for symbol, name in default_symbols.items()]
            selected_option = st.selectbox(
                "选择股票（默认列表）",
                symbol_options,
                index=0
            )
            selected_symbol = selected_option.split(' - ')[0] if selected_option else None

    # 主页面
    if selected_symbol:
        st.session_state.current_symbol = selected_symbol
        
        # 显示选中的股票信息
        col1, col2 = st.columns([2, 1])
        with col1:
            symbol_info = all_symbols.get(selected_symbol)
            if symbol_info:
                st.info(f"已选择: {selected_symbol} - {symbol_info['name']} ({symbol_info['market']}市场 {symbol_info['type']})")
            else:
                st.info(f"已选择: {selected_symbol}")
        
        with col2:
            if st.button("🔄 刷新股票列表"):
                try:
                    from src.symbol.symbols import reload_symbols
                    reload_symbols()
                    st.success("股票列表已刷新")
                    st.rerun()
                except Exception as e:
                    st.error(f"刷新失败: {e}")
        
        # 回测参数设置
        st.subheader("⚙️ 回测参数设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📅 时间范围**")
            start_date = st.date_input(
                "开始日期",
                value=datetime(2023, 1, 1),
                min_value=datetime(2020, 1, 1),
                max_value=datetime.now()
            )
            end_date = st.date_input(
                "结束日期", 
                value=datetime.now(),
                min_value=start_date,
                max_value=datetime.now()
            )
            
            # 验证日期范围
            if start_date >= end_date:
                st.error("开始日期必须小于结束日期")
        
        with col2:
            st.markdown("**📊 策略参数**")
            fast_ma = st.slider("快速均线周期", 5, 20, 10, help="用于生成交易信号的短期均线")
            slow_ma = st.slider("慢速均线周期", 20, 60, 30, help="用于确定趋势方向的长期均线")
            atr_length = st.slider("ATR周期", 10, 30, 14, help="计算真实波幅的周期")
            atr_multiplier = st.slider("ATR倍数", 1.0, 4.0, 2.0, 0.1, help="止损和止盈的ATR倍数")
            fixed_size = st.number_input("固定交易手数", 1, 10, 1, help="每次交易的固定手数")
        
        # 策略参数
        strategy_params = {
            "fast_ma_length": fast_ma,
            "slow_ma_length": slow_ma,
            "atr_length": atr_length,
            "atr_multiplier": atr_multiplier,
            "fixed_size": fixed_size
        }
        
        # 显示参数摘要
        st.markdown("**📋 参数摘要**")
        param_col1, param_col2, param_col3 = st.columns(3)
        with param_col1:
            st.write(f"股票: {selected_symbol}")
            st.write(f"快/慢均线: {fast_ma}/{slow_ma}")
        with param_col2:
            st.write(f"时间: {start_date} 至 {end_date}")
            st.write(f"ATR: {atr_length}期 {atr_multiplier}倍")
        with param_col3:
            st.write(f"交易手数: {fixed_size}")
            days = (end_date - start_date).days
            st.write(f"回测天数: {days}天")
        
        st.markdown("---")
        
        # 回测控制
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            start_backtest = st.button(
                "🚀 开始回测",
                type="primary",
                disabled=st.session_state.backtest_running or start_date >= end_date,
                use_container_width=True
            )
        
        with col2:
            if st.session_state.backtest_running:
                st.button("⏸️ 运行中...", disabled=True, use_container_width=True)
            else:
                clear_results = st.button("🗑️ 清除结果", use_container_width=True)
                if clear_results:
                    st.session_state.backtest_results = None
                    st.success("结果已清除")
        
        with col3:
            if st.session_state.backtest_running:
                progress = st.progress(st.session_state.backtest_progress / 100)
                st.write(f"进度: {st.session_state.backtest_progress}%")
        
        # 执行回测
        if start_backtest and not st.session_state.backtest_running:
            executor = BacktestExecutor()
            
            with st.spinner("正在执行回测，请稍候..."):
                # 模拟进度更新
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 执行回测（这里简化为同步执行）
                try:
                    status_text.text("正在初始化回测引擎...")
                    progress_bar.progress(20)
                    time.sleep(0.5)
                    
                    status_text.text("正在加载市场数据...")
                    progress_bar.progress(40)
                    time.sleep(0.5)
                    
                    status_text.text("正在运行回测策略...")
                    progress_bar.progress(70)
                    
                    # 实际执行回测
                    success = executor.run_backtest_async(
                        selected_symbol, 
                        strategy_params, 
                        (start_date, end_date)
                    )
                    
                    progress_bar.progress(100)
                    status_text.text("回测完成!")
                    
                    if success:
                        st.success("🎉 回测执行成功！")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ 回测执行失败")
                        
                except Exception as e:
                    st.error(f"回测执行出错: {str(e)}")
                finally:
                    progress_bar.empty()
                    status_text.empty()
        
        # 显示回测结果
        if st.session_state.backtest_results:
            st.markdown("---")
            st.subheader("📊 回测结果")
            
            results = st.session_state.backtest_results
            
            # 关键指标 - 从daily_results计算得出，而不是从stats获取
            metric_col1, metric_col2, metric_col3, metric_col4, metric_col5, metric_col6 = st.columns(6)
            
            # 计算策略综合指标
            strategy_metrics = {}
            if results['daily_results'] and len(results['daily_results']) > 0:
                daily_data = results['daily_results']
                
                # 基础数据
                final_return_ratio = daily_data[-1].get('return_ratio', 0)
                total_pnl = daily_data[-1].get('total_pnl', 0)
                final_win_loss_ratio = daily_data[-1].get('win_loss_ratio', 0)
                
                # 计算最大回撤
                cumulative_assets = [INITIAL_CAPITAL + d.get('total_pnl', 0) for d in daily_data]
                cumulative_max = []
                current_max = cumulative_assets[0]
                for asset in cumulative_assets:
                    if asset > current_max:
                        current_max = asset
                    cumulative_max.append(current_max)
                
                drawdowns = [(asset - max_val) / max_val for asset, max_val in zip(cumulative_assets, cumulative_max)]
                max_drawdown = min(drawdowns) * 100 if drawdowns else 0
                
                # 计算日收益率统计
                daily_returns = []
                for i in range(1, len(daily_data)):
                    prev_pnl = daily_data[i-1].get('total_pnl', 0)
                    curr_pnl = daily_data[i].get('total_pnl', 0)
                    daily_return = (curr_pnl - prev_pnl) / INITIAL_CAPITAL
                    daily_returns.append(daily_return)
                
                # 计算年化指标（假设252个交易日）
                if daily_returns:
                    avg_daily_return = sum(daily_returns) / len(daily_returns)
                    std_daily_return = (sum([(r - avg_daily_return) ** 2 for r in daily_returns]) / len(daily_returns)) ** 0.5
                    
                    annual_return = avg_daily_return * 252 * 100
                    annual_volatility = std_daily_return * (252 ** 0.5) * 100
                    sharpe_ratio = (avg_daily_return * 252) / (std_daily_return * (252 ** 0.5)) if std_daily_return > 0 else 0
                else:
                    annual_return = 0
                    annual_volatility = 0
                    sharpe_ratio = 0
                
                # 计算交易统计
                total_trades = len(results['trades']) if results['trades'] else 0
                winning_trades = len([t for t in results['trades'] if t.get('pnl', 0) > 0]) if results['trades'] else 0
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                
                strategy_metrics = {
                    'final_return_ratio': final_return_ratio,
                    'total_pnl': total_pnl,
                    'max_drawdown': max_drawdown,
                    'final_win_loss_ratio': final_win_loss_ratio,
                    'total_trades': total_trades,
                    'win_rate': win_rate,
                    'annual_return': annual_return,
                    'annual_volatility': annual_volatility,
                    'sharpe_ratio': sharpe_ratio
                }
            else:
                # 如果没有daily_results数据，使用默认值
                strategy_metrics = {
                    'final_return_ratio': 0,
                    'total_pnl': 0,
                    'max_drawdown': 0,
                    'final_win_loss_ratio': 0,
                    'total_trades': 0,
                    'win_rate': 0,
                    'annual_return': 0,
                    'annual_volatility': 0,
                    'sharpe_ratio': 0
                }
            
            with metric_col1:
                st.metric("策略收益率", f"{strategy_metrics['final_return_ratio']:.2f}%")
            
            with metric_col2:
                st.metric("年化收益率", f"{strategy_metrics['annual_return']:.2f}%")
            
            with metric_col3:
                st.metric("总盈亏", f"{strategy_metrics['total_pnl']:,.0f}")
            
            with metric_col4:
                st.metric("最大回撤", f"{strategy_metrics['max_drawdown']:.2f}%")
            
            with metric_col5:
                st.metric("夏普比率", f"{strategy_metrics['sharpe_ratio']:.2f}")
            
            with metric_col6:
                st.metric("胜率", f"{strategy_metrics['win_rate']:.1f}%")
            
            # 性能图表
            st.subheader("📈 性能图表")
            if results['daily_results']:
                fig = create_performance_chart(results['daily_results'])
                st.plotly_chart(fig, use_container_width=True)
            
            # 标的走势分析
            st.subheader("📊 标的走势分析")
            st.write("对比策略表现与标的股票走势，分析策略的有效性")
            
            # 获取回测的时间范围
            if results['daily_results'] and len(results['daily_results']) > 0:
                start_date = results['daily_results'][0]['date'][:10]  # 取日期部分
                end_date = results['daily_results'][-1]['date'][:10]   # 取日期部分
                
                try:
                    # 创建K线图
                    kline_fig = create_stock_kline_chart(results['symbol'], start_date, end_date)
                    st.plotly_chart(kline_fig, use_container_width=True)
                except Exception as e:
                    st.error(f"K线图生成失败: {str(e)}")
                    st.write("无法显示标的走势图，可能的原因：")
                    st.write("- 数据源连接问题")
                    st.write("- 股票代码格式不正确")
                    st.write("- 时间范围超出数据范围")
            else:
                st.warning("无法获取回测时间范围，无法生成K线图")
            
            # 详细统计
            st.subheader("📋 策略指标详情")
            
            # 显示真正的策略综合指标
            try:
                # 构建策略指标展示数据
                important_metrics = {
                    '策略收益率': (strategy_metrics['final_return_ratio'], '策略期间的总体收益表现'),
                    '年化收益率': (strategy_metrics['annual_return'], '将策略收益换算为年化表现'),
                    '年化波动率': (strategy_metrics['annual_volatility'], '策略收益的年化标准差'),
                    '夏普比率': (strategy_metrics['sharpe_ratio'], '风险调整后的收益指标，越高越好'),
                    '最大回撤': (strategy_metrics['max_drawdown'], '从最高点到最低点的最大损失'),
                    '交易胜率': (strategy_metrics['win_rate'], '盈利交易占总交易数量的比例'),
                    '总交易次数': (strategy_metrics['total_trades'], '策略期间的总交易笔数'),
                    '盈利天数比': (strategy_metrics['final_win_loss_ratio'], '盈利天数与亏损天数的比值')
                }
                
                display_data = []
                for key, (value, description) in important_metrics.items():
                    try:
                        if isinstance(value, (int, float)):
                            if '率' in key or '比' in key:
                                if '胜率' in key or '收益率' in key:
                                    value_str = f"{value:.2f}%"
                                else:
                                    value_str = f"{value:.2f}"
                            elif '次数' in key:
                                value_str = f"{int(value)}"
                            else:
                                value_str = f"{value:.2f}%"
                        else:
                            value_str = str(value)
                    except:
                        value_str = "无法解析"
                    
                    display_data.append({
                        "指标": key,
                        "数值": value_str,
                        "说明": description
                    })
                
                if display_data:
                    display_df = pd.DataFrame(display_data)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info("没有可显示的策略指标")
                    
            except Exception as e:
                st.error(f"显示策略指标失败: {str(e)}")
                st.info("策略指标数据解析出现问题，正在从正确的数据源(daily_results)重新计算指标")
            
            # 交易记录（分页显示）
            if results['trades'] and len(results['trades']) > 0:
                st.subheader("📝 交易记录")
                
                # 转换交易记录为DataFrame并优化字段显示
                trades_data = []
                for trade in results['trades']:
                    # 转换方向和开平字段
                    direction, offset = convert_trade_fields(trade)
                    
                    # 格式化时间显示
                    datetime_str = trade['datetime']
                    if len(datetime_str) > 19:  # 如果包含毫秒
                        datetime_str = datetime_str[:19]
                    
                    trades_data.append({
                        '时间': datetime_str,
                        '股票': trade['symbol'],
                        '方向': direction,
                        '开平': offset,
                        '价格': f"{trade['price']:.2f}",
                        '数量': int(trade['volume']),
                        '盈亏': f"{trade['pnl']:.2f}"
                    })
                
                if trades_data:
                    trades_df = pd.DataFrame(trades_data)
                    
                    # 分页设置
                    page_size = 10
                    total_records = len(trades_df)
                    total_pages = (total_records + page_size - 1) // page_size  # 向上取整
                    
                    # 初始化页面状态
                    if 'current_page' not in st.session_state:
                        st.session_state.current_page = 1
                    
                    # 确保当前页面在有效范围内
                    if st.session_state.current_page > total_pages:
                        st.session_state.current_page = total_pages
                    if st.session_state.current_page < 1:
                        st.session_state.current_page = 1
                    
                    # 计算当前页面的数据范围
                    start_idx = (st.session_state.current_page - 1) * page_size
                    end_idx = min(start_idx + page_size, total_records)
                    page_trades = trades_df.iloc[start_idx:end_idx]
                    
                    # 显示当前页面的交易记录
                    st.dataframe(page_trades, use_container_width=True, hide_index=True)
                    
                    # 分页控制 - 只在有多页时显示
                    if total_pages > 1:
                        # 分页信息和按钮
                        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                        
                        with col1:
                            if st.button("⬅️ 上一页", disabled=(st.session_state.current_page <= 1)):
                                st.session_state.current_page -= 1
                                st.rerun()

                        with col2:
                            st.write(f"**第 {st.session_state.current_page} 页 / 共 {total_pages} 页** | **总计 {total_records} 条交易记录**")
                        
                        with col3:
                            if st.button("➡️ 下一页", disabled=(st.session_state.current_page >= total_pages)):
                                st.session_state.current_page += 1
                                st.rerun()
                        

                    
                    # 显示当前页面记录范围
                    if total_pages > 1:
                        st.caption(f"显示第 {start_idx + 1} - {end_idx} 条记录")
                    
                    # 添加交易统计摘要
                    with st.expander("📊 交易统计摘要"):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        # 统计各类交易
                        long_trades = len([t for t in results['trades'] if '多' in convert_trade_fields(t)[0]])
                        short_trades = len([t for t in results['trades'] if '空' in convert_trade_fields(t)[0]])
                        open_trades = len([t for t in results['trades'] if '开仓' in convert_trade_fields(t)[1]])
                        close_trades = len([t for t in results['trades'] if '平仓' in convert_trade_fields(t)[1]])
                        
                        with col1:
                            st.metric("做多交易", long_trades)
                        with col2:
                            st.metric("做空交易", short_trades)
                        with col3:
                            st.metric("开仓交易", open_trades)
                        with col4:
                            st.metric("平仓交易", close_trades)

def show_historical_results():
    """显示历史回测结果"""
    st.header("📚 历史回测结果")
    
    try:
        db = get_db_manager()
        runs_data = db.get_all_runs()  # 这是一个字典列表，不是DataFrame
        
        # 检查是否有数据 - 修复：检查列表是否为空
        if not runs_data or len(runs_data) == 0:
            st.info("暂无历史回测数据")
            return
        
        # 将字典列表转换为DataFrame用于显示
        runs_df = pd.DataFrame(runs_data)
        
        # 显示历史记录表格
        display_columns = ['run_id', 'symbol', 'strategy_name', 'total_return', 
                          'max_drawdown', 'sharpe_ratio', 'win_rate', 'total_trades', 'created_at']
        
        # 确保所有列都存在，如果不存在则用默认值填充
        for col in display_columns:
            if col not in runs_df.columns:
                runs_df[col] = 0 if col in ['total_return', 'max_drawdown', 'sharpe_ratio', 'win_rate', 'total_trades'] else ''
        
        # 显示数据表格，对数值列进行四舍五入
        display_df = runs_df[display_columns].copy()
        numeric_columns = ['total_return', 'max_drawdown', 'sharpe_ratio', 'win_rate']
        for col in numeric_columns:
            if col in display_df.columns:
                display_df[col] = pd.to_numeric(display_df[col], errors='coerce').round(2)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # 选择查看详情
        if len(runs_df) > 0:
            run_options = {}
            for _, row in runs_df.iterrows():
                # 安全地获取数值，处理可能的None值
                total_return = row.get('total_return', 0)
                if total_return is None:
                    total_return = 0
                
                label = f"{row.get('symbol', 'Unknown')} - {str(row.get('created_at', ''))[:16]} (收益率: {total_return:.2f}%)"
                run_options[label] = row.get('run_id', '')
            
            selected_run = st.selectbox("选择查看详情", ["选择一个回测结果"] + list(run_options.keys()))
            
            if selected_run != "选择一个回测结果":
                run_id = run_options[selected_run]
                details = db.get_run_details(run_id)
                
                if details:
                    st.subheader("📊 回测详情")
                    
                    # 基本信息
                    run_info = details['run_info']
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**股票代码:** {run_info.get('symbol', 'Unknown')}")
                        st.write(f"**策略名称:** {run_info.get('strategy_name', 'Unknown')}")
                        st.write(f"**回测期间:** {run_info.get('start_date', '')} 至 {run_info.get('end_date', '')}")
                    
                    with col2:
                        # 安全地获取统计数据，处理可能的None值
                        stats_info = details.get('stats', {})
                        total_return = stats_info.get('total_return', 0) or 0
                        max_drawdown = stats_info.get('max_drawdown', 0) or 0
                        sharpe_ratio = stats_info.get('sharpe_ratio', 0) or 0
                        
                        st.write(f"**总收益率:** {total_return:.2f}%")
                        st.write(f"**最大回撤:** {max_drawdown:.2f}%")
                        st.write(f"**夏普比率:** {sharpe_ratio:.2f}")
                    
                    # 性能图表
                    daily_results = details.get('daily_results', [])
                    if not daily_results or len(daily_results) == 0:
                        st.warning("没有可用的每日结果数据")
                    else:
                        # 修复：检查是否为列表而不是DataFrame
                        if isinstance(daily_results, list):
                            fig = create_performance_chart(daily_results)
                            st.plotly_chart(fig, use_container_width=True)
                        elif hasattr(daily_results, 'empty') and daily_results.empty:
                            st.warning("每日结果数据为空")
                        else:
                            fig = create_performance_chart(daily_results)
                            st.plotly_chart(fig, use_container_width=True)
                    
    except Exception as e:
        st.error(f"加载历史数据失败: {e}")
        import traceback
        st.error(f"详细错误信息: {traceback.format_exc()}")

def main():
    """主函数"""
    # 导航
    page = st.sidebar.radio(
        "📋 导航菜单",
        ["🚀 回测执行", "📚 历史结果"],
        index=0
    )
    
    if page == "🚀 回测执行":
        show_backtest_interface()
    elif page == "📚 历史结果":
        show_historical_results()

if __name__ == "__main__":
    main() 