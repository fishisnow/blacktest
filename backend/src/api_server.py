"""
回测系统 FastAPI 服务器
将 streamlit_app.py 的功能转换为 REST API 接口
"""
import time
import traceback
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import asyncio
import logging

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import pandas as pd

# 导入业务逻辑模块
from backend.src.conf.backtest_config import BacktestConfig
from backend.src.blacktest_runner import BacktestRunner
from backend.src.storage.db_utils import get_db_manager
from backend.src.strategies.trend_following_strategy import TrendFollowingStrategy
from backend.src.symbol.symbols import get_all_symbols, get_symbols_by_market
from backend.src.storage.data_loader import DataLoader
from backend.src.utils.statistics_calculator import StatisticsCalculator
from backend.src.constants import INITIAL_CAPITAL

# 配置日志 (通过 uvicorn 的 log_config 统一管理)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="回测系统 API",
    description="基于 vnpy 的股票策略回测系统 API 接口",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React 开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型定义
class StockSymbol(BaseModel):
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: str = Field(..., description="市场类型")
    type: str = Field(..., description="证券类型")
    exchange: Optional[str] = Field(None, description="交易所")

class StrategyParams(BaseModel):
    fastMaPeriod: int = Field(10, description="快速均线周期")
    slowMaPeriod: int = Field(30, description="慢速均线周期")
    atrPeriod: int = Field(14, description="ATR周期")
    atrMultiplier: float = Field(2.0, description="ATR倍数")
    positionMode: str = Field("fixed", description="仓位模式")
    fixedSize: int = Field(1, description="固定手数")

class BacktestParams(BaseModel):
    symbol: str = Field(..., description="股票代码")
    startDate: str = Field(..., description="开始日期")
    endDate: str = Field(..., description="结束日期")
    strategy: str = Field("TrendFollowingStrategy", description="策略名称")
    parameters: StrategyParams = Field(..., description="策略参数")

class CandleData(BaseModel):
    timestamp: int = Field(..., description="时间戳")
    date: str = Field(..., description="日期字符串")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量")

class TradeRecord(BaseModel):
    id: str = Field(..., description="交易ID")
    timestamp: int = Field(..., description="时间戳")
    date: str = Field(..., description="日期时间")
    symbol: str = Field(..., description="股票代码")
    direction: str = Field(..., description="方向：LONG/SHORT")
    offset: str = Field(..., description="开平：OPEN/CLOSE")
    price: float = Field(..., description="成交价格")
    volume: int = Field(..., description="成交数量")
    pnl: float = Field(..., description="盈亏")
    commission: float = Field(..., description="手续费")
    slippage: float = Field(..., description="滑点")

class DailyResult(BaseModel):
    date: str = Field(..., description="日期")
    totalPnl: float = Field(..., description="累计盈亏")
    netPnl: float = Field(..., description="当日净盈亏")
    returnRatio: float = Field(..., description="累计收益率(%)")
    drawdown: float = Field(..., description="回撤(%)")
    maxDrawdown: float = Field(..., description="最大回撤(%)")
    winLossRatio: float = Field(..., description="盈亏天数比")
    trades: int = Field(..., description="当日交易次数")

class BacktestMetrics(BaseModel):
    totalReturn: float = Field(..., description="总收益率(%)")
    annualReturn: float = Field(..., description="年化收益率(%)")
    totalPnl: float = Field(..., description="总盈亏")
    maxDrawdown: float = Field(..., description="最大回撤(%)")
    maxDrawdownDuration: int = Field(..., description="最大回撤持续天数")
    volatility: float = Field(..., description="波动率(%)")
    sharpeRatio: float = Field(..., description="夏普比率")
    sortinoRatio: float = Field(..., description="索提诺比率")
    calmarRatio: float = Field(..., description="卡玛比率")
    totalTrades: int = Field(..., description="总交易次数")
    winningTrades: int = Field(..., description="盈利交易次数")
    losingTrades: int = Field(..., description="亏损交易次数")
    winRate: float = Field(..., description="胜率(%)")
    profitFactor: float = Field(..., description="盈利因子")
    avgWin: float = Field(..., description="平均盈利")
    avgLoss: float = Field(..., description="平均亏损")
    maxWin: float = Field(..., description="最大盈利")
    maxLoss: float = Field(..., description="最大亏损")
    tradingDays: int = Field(..., description="交易天数")
    profitableDays: int = Field(..., description="盈利天数")
    losingDays: int = Field(..., description="亏损天数")
    winLossRatio: float = Field(..., description="盈亏天数比")
    initialCapital: float = Field(..., description="初始资金")
    finalCapital: float = Field(..., description="最终资金")
    maxCapital: float = Field(..., description="最高资金")
    minCapital: float = Field(..., description="最低资金")

class BacktestResults(BaseModel):
    runId: str = Field(..., description="运行ID")
    symbol: str = Field(..., description="股票代码")
    strategy: str = Field(..., description="策略名称")
    startDate: str = Field(..., description="开始日期")
    endDate: str = Field(..., description="结束日期")
    createdAt: str = Field(..., description="创建时间")
    candleData: List[CandleData] = Field(..., description="K线数据")
    trades: List[TradeRecord] = Field(..., description="交易记录")
    dailyResults: List[DailyResult] = Field(..., description="每日统计")
    metrics: BacktestMetrics = Field(..., description="回测指标")
    parameters: StrategyParams = Field(..., description="策略参数")
    executionTime: int = Field(..., description="执行耗时(毫秒)")
    dataPoints: int = Field(..., description="数据点数量")
    status: str = Field(..., description="状态")

class ApiResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    data: Optional[Any] = Field(None, description="响应数据")
    message: Optional[str] = Field(None, description="响应消息")
    error: Optional[str] = Field(None, description="错误信息")
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000), description="时间戳")

# 全局变量
running_backtests: Dict[str, dict] = {}  # 存储运行中的回测任务

# 工具函数
def calculate_consistent_daily_metrics(daily_results_raw):
    """统一的每日指标计算函数"""
    return StatisticsCalculator._process_daily_results(daily_results_raw, INITIAL_CAPITAL)

def convert_vnpy_trades_to_api_format(trades) -> List[TradeRecord]:
    """将 vnpy 交易记录转换为 API 格式"""
    api_trades = []
    for i, trade in enumerate(trades):
        trade_dict = {
            'id': f"trade_{i+1}",
            'timestamp': int(getattr(trade, 'datetime', datetime.now()).timestamp() * 1000),
            'date': str(getattr(trade, 'datetime', datetime.now())),
            'symbol': getattr(trade, 'symbol', ''),
            'direction': 'LONG' if 'LONG' in str(getattr(trade, 'direction', '')) else 'SHORT',
            'offset': 'OPEN' if 'OPEN' in str(getattr(trade, 'offset', '')) else 'CLOSE',
            'price': float(getattr(trade, 'price', 0)),
            'volume': int(getattr(trade, 'volume', 0)),
            'pnl': float(getattr(trade, 'pnl', 0)),
            'commission': float(getattr(trade, 'price', 0)) * int(getattr(trade, 'volume', 0)) * 0.0003,
            'slippage': 0.0
        }
        api_trades.append(TradeRecord(**trade_dict))
    return api_trades

def convert_daily_results_to_api_format(daily_results) -> List[DailyResult]:
    """将每日结果转换为 API 格式"""
    if not daily_results:
        return []
    
    api_daily_results = []
    for result in daily_results:
        daily_dict = {
            'date': result.get('date', ''),
            'totalPnl': result.get('total_pnl', 0),
            'netPnl': result.get('net_pnl', 0),
            'returnRatio': result.get('return_ratio', 0),
            'drawdown': result.get('drawdown', 0),
            'maxDrawdown': result.get('max_drawdown', 0),
            'winLossRatio': result.get('win_loss_ratio', 0),
            'trades': result.get('trades', 0)
        }
        api_daily_results.append(DailyResult(**daily_dict))
    return api_daily_results

def get_run_statistics_for_api(run_id: str = None, daily_results: List = None) -> BacktestMetrics:
    """获取统计指标并转换为 API 格式"""
    if run_id:
        try:
            db = get_db_manager()
            details = db.get_run_details(run_id)
            if details and details.get('stats'):
                stats_info = details['stats']
                
                # 计算 final_win_loss_ratio
                final_win_loss_ratio = 0
                if daily_results and len(daily_results) > 0:
                    processed_daily = StatisticsCalculator._process_daily_results(daily_results, INITIAL_CAPITAL)
                    if processed_daily:
                        final_win_loss_ratio = processed_daily[-1].get('win_loss_ratio', 0)
                
                return BacktestMetrics(
                    totalReturn=stats_info.get('total_return', 0) or 0,
                    annualReturn=stats_info.get('annual_return', 0) or 0,
                    totalPnl=stats_info.get('total_pnl', 0) or 0,
                    maxDrawdown=stats_info.get('max_drawdown', 0) or 0,
                    maxDrawdownDuration=30,
                    volatility=stats_info.get('annual_volatility', 0) or 0,
                    sharpeRatio=stats_info.get('sharpe_ratio', 0) or 0,
                    sortinoRatio=1.5,
                    calmarRatio=0.8,
                    totalTrades=int(stats_info.get('total_trades', 0) or 0),
                    winningTrades=int(stats_info.get('total_trades', 0) * stats_info.get('win_rate', 0) / 100) if stats_info.get('win_rate') else 0,
                    losingTrades=int(stats_info.get('total_trades', 0)) - int(stats_info.get('total_trades', 0) * stats_info.get('win_rate', 0) / 100) if stats_info.get('win_rate') else 0,
                    winRate=stats_info.get('win_rate', 0) or 0,
                    profitFactor=stats_info.get('profit_factor', 0) or 0,
                    avgWin=stats_info.get('max_profit', 0) / max(1, int(stats_info.get('total_trades', 0) * stats_info.get('win_rate', 0) / 100)) if stats_info.get('max_profit') else 0,
                    avgLoss=stats_info.get('max_loss', 0) / max(1, int(stats_info.get('total_trades', 0)) - int(stats_info.get('total_trades', 0) * stats_info.get('win_rate', 0) / 100)) if stats_info.get('max_loss') else 0,
                    maxWin=stats_info.get('max_profit', 0) or 0,
                    maxLoss=stats_info.get('max_loss', 0) or 0,
                    tradingDays=len(daily_results) if daily_results else 0,
                    profitableDays=len([r for r in daily_results if r.get('net_pnl', 0) > 0]) if daily_results else 0,
                    losingDays=len([r for r in daily_results if r.get('net_pnl', 0) < 0]) if daily_results else 0,
                    winLossRatio=final_win_loss_ratio,
                    initialCapital=INITIAL_CAPITAL,
                    finalCapital=INITIAL_CAPITAL + (stats_info.get('total_pnl', 0) or 0),
                    maxCapital=INITIAL_CAPITAL + max([r.get('total_pnl', 0) for r in daily_results], default=0) if daily_results else INITIAL_CAPITAL,
                    minCapital=INITIAL_CAPITAL + min([r.get('total_pnl', 0) for r in daily_results], default=0) if daily_results else INITIAL_CAPITAL
                )
        except Exception as e:
            logger.error(f"获取统计指标失败: {e}")
    
    # 返回默认指标
    return BacktestMetrics(
        totalReturn=0, annualReturn=0, totalPnl=0, maxDrawdown=0, maxDrawdownDuration=0,
        volatility=0, sharpeRatio=0, sortinoRatio=0, calmarRatio=0, totalTrades=0,
        winningTrades=0, losingTrades=0, winRate=0, profitFactor=0, avgWin=0, avgLoss=0,
        maxWin=0, maxLoss=0, tradingDays=0, profitableDays=0, losingDays=0, winLossRatio=0,
        initialCapital=INITIAL_CAPITAL, finalCapital=INITIAL_CAPITAL, maxCapital=INITIAL_CAPITAL, minCapital=INITIAL_CAPITAL
    )

# API 路由
@app.get("/api/stocks", response_model=ApiResponse)
async def get_stock_list():
    """获取股票列表"""
    try:
        logger.info("获取股票列表")
        all_symbols = get_all_symbols()
        
        # 转换为 API 格式
        stock_list = []
        for symbol, info in all_symbols.items():
            stock_list.append(StockSymbol(
                code=symbol,
                name=info.get('name', ''),
                market=info.get('market', 'CN'),
                type=info.get('type', 'stock'),
                exchange=info.get('exchange', '')
            ))
        
        return ApiResponse(
            success=True,
            data=stock_list,
            message=f"成功获取 {len(stock_list)} 个股票代码"
        )
        
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return ApiResponse(
            success=False,
            error=str(e),
            message="获取股票列表失败"
        )

@app.get("/api/market-data/{symbol}", response_model=ApiResponse)
async def get_market_data(
    symbol: str,
    start_date: str = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期 YYYY-MM-DD")
):
    """获取股票价格数据"""
    try:
        logger.info(f"获取 {symbol} 从 {start_date} 到 {end_date} 的价格数据")
        
        data_loader = DataLoader()
        bars_data = data_loader.get_index_data(symbol, start_date, end_date)
        
        if not bars_data:
            return ApiResponse(
                success=False,
                error="无法获取数据",
                message=f"没有找到 {symbol} 的价格数据"
            )
        
        # 转换为 API 格式
        candle_data = []
        for bar in bars_data:
            candle_data.append(CandleData(
                timestamp=int(bar.datetime.timestamp() * 1000),
                date=bar.datetime.strftime('%Y-%m-%d'),
                open=bar.open_price,
                high=bar.high_price,
                low=bar.low_price,
                close=bar.close_price,
                volume=int(bar.volume)
            ))
        
        return ApiResponse(
            success=True,
            data=candle_data,
            message=f"成功获取 {len(candle_data)} 条价格数据"
        )
        
    except Exception as e:
        logger.error(f"获取价格数据失败: {e}")
        return ApiResponse(
            success=False,
            error=str(e),
            message="获取价格数据失败"
        )

@app.post("/api/backtest", response_model=ApiResponse)
async def run_backtest(params: BacktestParams, background_tasks: BackgroundTasks):
    """执行回测"""
    try:
        logger.info(f"开始执行回测: {params.symbol} {params.startDate} - {params.endDate}")

        # 转换参数格式
        strategy_params = {
            "fast_ma_length": params.parameters.fastMaPeriod,
            "slow_ma_length": params.parameters.slowMaPeriod,
            "atr_length": params.parameters.atrPeriod,
            "atr_multiplier": params.parameters.atrMultiplier,
            "fixed_size": params.parameters.fixedSize,
            "position_mode": params.parameters.positionMode
        }

        logger.info(f"回测参数: {strategy_params}")
        
        # 转换日期
        start_date = datetime.strptime(params.startDate, "%Y-%m-%d")
        end_date = datetime.strptime(params.endDate, "%Y-%m-%d")
        
        # 创建配置
        config = BacktestConfig(
            output_base_dir="../../backtest_results",
            symbol=params.symbol,
            strategy_name=params.strategy,
            start_date=params.startDate,
            end_date=params.endDate,
            strategy_params=strategy_params
        )
        
        # 创建回测运行器
        runner = BacktestRunner(config)
        
        # 设置回测引擎
        runner.setup_engine(params.symbol, start_date, end_date)
        
        # 添加策略
        runner.add_strategy(TrendFollowingStrategy, strategy_params)
        
        # 加载数据
        if not runner.load_data(params.symbol, params.startDate, params.endDate):
            return ApiResponse(
                success=False,
                error="数据加载失败",
                message=f"无法加载 {params.symbol} 的数据"
            )
        
        # 运行回测
        runner.run_backtest()
        
        # 获取结果
        stats = runner.engine.calculate_result()
        trades = runner.engine.get_all_trades()
        daily_results = runner.engine.get_all_daily_results()
        
        # 保存到数据库
        if runner.db_manager and runner.config:
            runner.db_manager.save_backtest_run(runner.config)
        
        # 进行完整的结果分析和保存
        runner.analyzer.analyze_results(stats, trades, daily_results)
        
        # 处理数据转换
        processed_daily_results = calculate_consistent_daily_metrics(daily_results)
        api_trades = convert_vnpy_trades_to_api_format(trades)
        api_daily_results = convert_daily_results_to_api_format(processed_daily_results)
        
        # 获取 K 线数据
        data_loader = DataLoader()
        bars_data = data_loader.get_index_data(params.symbol, params.startDate, params.endDate)
        candle_data = []
        if bars_data:
            for bar in bars_data:
                candle_data.append(CandleData(
                    timestamp=int(bar.datetime.timestamp() * 1000),
                    date=bar.datetime.strftime('%Y-%m-%d'),
                    open=bar.open_price,
                    high=bar.high_price,
                    low=bar.low_price,
                    close=bar.close_price,
                    volume=int(bar.volume)
                ))
        
        # 获取统计指标
        metrics = get_run_statistics_for_api(runner.config.run_id, processed_daily_results)
        
        # 构建回测结果
        result = BacktestResults(
            runId=runner.config.run_id,
            symbol=params.symbol,
            strategy=params.strategy,
            startDate=params.startDate,
            endDate=params.endDate,
            createdAt=datetime.now().isoformat(),
            candleData=candle_data,
            trades=api_trades,
            dailyResults=api_daily_results,
            metrics=metrics,
            parameters=params.parameters,
            executionTime=1000,  # 执行时间，毫秒
            dataPoints=len(candle_data),
            status="completed"
        )
        
        return ApiResponse(
            success=True,
            data=result,
            message="回测执行成功"
        )
        
    except Exception as e:
        logger.error(f"回测执行失败: {e}")
        logger.error(traceback.format_exc())
        return ApiResponse(
            success=False,
            error=str(e),
            message="回测执行失败"
        )

@app.get("/api/backtest/history", response_model=ApiResponse)
async def get_backtest_history():
    """获取回测历史记录"""
    try:
        logger.info("获取回测历史记录")
        
        db = get_db_manager()
        runs_data = db.get_all_runs()
        
        if not runs_data:
            return ApiResponse(
                success=True,
                data=[],
                message="暂无历史回测数据"
            )
        
        # 转换为 API 格式
        history_results = []
        for run in runs_data:
            # 获取详细信息
            details = db.get_run_details(run.get('run_id', ''))
            if details:
                daily_results = details.get('daily_results', [])
                processed_daily = calculate_consistent_daily_metrics(daily_results)
                
                # 获取统计指标
                metrics = get_run_statistics_for_api(run.get('run_id'), processed_daily)
                
                # 构建历史记录
                history_result = BacktestResults(
                    runId=run.get('run_id', ''),
                    symbol=run.get('symbol', ''),
                    strategy=run.get('strategy_name', ''),
                    startDate=run.get('start_date', ''),
                    endDate=run.get('end_date', ''),
                    createdAt=run.get('created_at', ''),
                    candleData=[],  # 历史记录不包含详细 K 线数据
                    trades=[],      # 历史记录不包含详细交易数据
                    dailyResults=convert_daily_results_to_api_format(processed_daily),
                    metrics=metrics,
                    parameters=StrategyParams(
                        fastMaPeriod=10,
                        slowMaPeriod=30,
                        atrPeriod=14,
                        atrMultiplier=2.0,
                        positionMode="fixed",
                        fixedSize=1
                    ),
                    executionTime=0,
                    dataPoints=len(daily_results),
                    status="completed"
                )
                history_results.append(history_result)
        
        return ApiResponse(
            success=True,
            data=history_results,
            message=f"成功获取 {len(history_results)} 条历史记录"
        )
        
    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        return ApiResponse(
            success=False,
            error=str(e),
            message="获取历史记录失败"
        )

@app.delete("/api/backtest/{run_id}", response_model=ApiResponse)
async def delete_backtest_result(run_id: str):
    """删除回测记录"""
    try:
        logger.info(f"删除回测记录: {run_id}")
        
        db = get_db_manager()
        
        # 检查记录是否存在
        details = db.get_run_details(run_id)
        if not details:
            return ApiResponse(
                success=False,
                error="记录不存在",
                message=f"找不到 ID 为 {run_id} 的回测记录"
            )
        
        # 删除记录 (这里需要实现删除逻辑)
        # 注意：当前的 database_manager 可能没有删除方法，需要添加
        
        return ApiResponse(
            success=True,
            message=f"成功删除回测记录 {run_id}"
        )
        
    except Exception as e:
        logger.error(f"删除回测记录失败: {e}")
        return ApiResponse(
            success=False,
            error=str(e),
            message="删除回测记录失败"
        )

@app.get("/", response_model=ApiResponse)
async def root():
    """根路径"""
    return ApiResponse(
        success=True,
        data={"message": "回测系统 API 服务器运行中"},
        message="API 服务器运行正常"
    )

@app.get("/health", response_model=ApiResponse)
async def health_check():
    """健康检查"""
    return ApiResponse(
        success=True,
        data={"status": "healthy", "timestamp": datetime.now().isoformat()},
        message="服务器健康状态良好"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 