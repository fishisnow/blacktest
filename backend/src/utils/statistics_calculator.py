"""
统计指标计算器
统一的回测统计指标计算逻辑，确保database_manager和streamlit_app使用相同的计算方法
"""
from typing import List, Dict, Any, Union

from backend.src.constants import TRADING_DAYS_PER_YEAR, PROFIT_THRESHOLD, LOSS_THRESHOLD


class StatisticsCalculator:
    """回测统计指标计算器"""
    
    @staticmethod
    def calculate_backtest_statistics(
        daily_results: List[Union[Dict, Any]], 
        trades: List[Union[Dict, Any]], 
        initial_capital: float = 1_000_000
    ) -> Dict[str, float]:
        """
        根据每日结果和交易记录计算统计指标
        
        Args:
            daily_results: 每日结果数据（可以是字典列表或对象列表）
            trades: 交易记录数据（可以是字典列表或对象列表）
            initial_capital: 初始资金
            
        Returns:
            Dict: 包含所有统计指标的字典
        """
        if not daily_results or len(daily_results) == 0:
            return StatisticsCalculator._get_default_stats()
        
        # 1. 处理每日结果数据，转换为统一格式
        processed_results = StatisticsCalculator._process_daily_results(daily_results, initial_capital)
        
        # 2. 计算基础指标
        final_return_ratio = processed_results[-1]['return_ratio']
        total_pnl = processed_results[-1]['total_pnl']
        final_win_loss_ratio = processed_results[-1].get('win_loss_ratio', 0)
        
        # 3. 计算最大回撤
        max_drawdown = StatisticsCalculator._calculate_max_drawdown(processed_results, initial_capital)
        
        # 4. 计算年化指标
        annual_return, annual_volatility, sharpe_ratio = StatisticsCalculator._calculate_annual_metrics(
            processed_results, initial_capital
        )
        
        # 5. 计算交易相关统计
        trade_stats = StatisticsCalculator._calculate_trade_statistics(trades)
        
        # 6. 合并所有统计指标
        return {
            'total_return': final_return_ratio,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'profit_factor': trade_stats['profit_factor'],
            'win_rate': trade_stats['win_rate'],
            'total_trades': trade_stats['total_trades'],
            'total_pnl': total_pnl,
            'max_profit': trade_stats['max_profit'],
            'max_loss': trade_stats['max_loss'],
            'final_win_loss_ratio': final_win_loss_ratio,
            'annual_volatility': annual_volatility
        }
    
    @staticmethod
    def _process_daily_results(daily_results: List, initial_capital: float) -> List[Dict]:
        """处理每日结果数据，转换为统一格式"""
        processed_results = []
        cumulative_pnl = 0
        win_count = 0
        loss_count = 0
        
        # 用于计算回撤
        max_capital = initial_capital
        current_drawdown = 0
        max_drawdown = 0
        
        for result in daily_results:
            # 统一获取net_pnl，处理对象和字典两种格式
            if isinstance(result, dict):
                net_pnl = result.get('net_pnl', 0)
                date = result.get('date', '')
            else:
                net_pnl = getattr(result, 'net_pnl', 0)
                date = str(getattr(result, 'date', ''))
            
            # 确保数值类型正确
            net_pnl = float(net_pnl) if net_pnl is not None else 0.0
            
            # 累积总盈亏
            cumulative_pnl += net_pnl
            
            # 计算当前资金
            current_capital = initial_capital + cumulative_pnl
            
            # 更新最大资金
            if current_capital > max_capital:
                max_capital = current_capital
                current_drawdown = 0
            else:
                # 计算当前回撤
                current_drawdown = (max_capital - current_capital) / max_capital * 100
                max_drawdown = max(max_drawdown, current_drawdown)
            
            # 统计盈亏天数（设置阈值避免浮点数精度问题）
            if net_pnl > PROFIT_THRESHOLD:  # 盈利阈值
                win_count += 1
            elif net_pnl < LOSS_THRESHOLD:  # 亏损阈值
                loss_count += 1
            
            # 计算盈亏比（避免除零错误）
            if loss_count > 0:
                win_loss_ratio = win_count / loss_count
            else:
                win_loss_ratio = float(win_count) if win_count > 0 else 0.0
            
            # 计算收益率（相对于初始资金）
            return_ratio = (cumulative_pnl / initial_capital) * 100
            
            processed_results.append({
                'date': date,
                'net_pnl': net_pnl,
                'total_pnl': cumulative_pnl,
                'return_ratio': return_ratio,
                'win_loss_ratio': win_loss_ratio,
                'drawdown': current_drawdown,
                'max_drawdown': max_drawdown
            })
        
        return processed_results
    
    @staticmethod
    def _calculate_max_drawdown(processed_results: List[Dict], initial_capital: float) -> float:
        """计算最大回撤"""
        cumulative_assets = [initial_capital + d['total_pnl'] for d in processed_results]
        cumulative_max = []
        current_max = cumulative_assets[0]
        
        for asset in cumulative_assets:
            if asset > current_max:
                current_max = asset
            cumulative_max.append(current_max)
        
        drawdowns = [(asset - max_val) / max_val for asset, max_val in zip(cumulative_assets, cumulative_max)]
        max_drawdown = abs(min(drawdowns) * 100) if drawdowns else 0
        
        return max_drawdown
    
    @staticmethod
    def _calculate_annual_metrics(processed_results: List[Dict], initial_capital: float) -> tuple:
        """计算年化指标：年化收益率、年化波动率、夏普比率"""
        # 计算日收益率
        daily_returns = []
        for i in range(1, len(processed_results)):
            prev_pnl = processed_results[i-1]['total_pnl']
            curr_pnl = processed_results[i]['total_pnl']
            daily_return = (curr_pnl - prev_pnl) / initial_capital
            daily_returns.append(daily_return)
        
        if daily_returns and len(daily_returns) > 0:
            avg_daily_return = sum(daily_returns) / len(daily_returns)
            # 计算标准差
            variance = sum([(r - avg_daily_return) ** 2 for r in daily_returns]) / len(daily_returns)
            std_daily_return = variance ** 0.5
            
            # 年化指标（假设252个交易日）
            annual_return = avg_daily_return * TRADING_DAYS_PER_YEAR * 100
            annual_volatility = std_daily_return * (TRADING_DAYS_PER_YEAR ** 0.5) * 100
            sharpe_ratio = (avg_daily_return * TRADING_DAYS_PER_YEAR) / (std_daily_return * (TRADING_DAYS_PER_YEAR ** 0.5)) if std_daily_return > 0 else 0
        else:
            annual_return = 0
            annual_volatility = 0
            sharpe_ratio = 0
        
        return annual_return, annual_volatility, sharpe_ratio
    
    @staticmethod
    def _calculate_trade_statistics(trades: List) -> Dict[str, float]:
        """计算交易相关统计，手动计算交易盈亏"""
        if not trades or len(trades) == 0:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'max_profit': 0,
                'max_loss': 0
            }
        
        # 按时间排序交易
        sorted_trades = sorted(trades, key=lambda t: t.get('trade_datetime') if isinstance(t, dict) else getattr(t, 'datetime'))
        
        # 手动计算交易盈亏
        position_stack = []  # 持仓栈，存储开仓交易
        completed_trades = []  # 完成的交易（有盈亏的配对交易）
        
        for trade in sorted_trades:
            if isinstance(trade, dict):
                direction = str(trade.get('direction', ''))
                offset = str(trade.get('offset', ''))
                price = float(trade.get('price', 0))
                volume = int(trade.get('volume', 0))
            else:
                direction = str(getattr(trade, 'direction', ''))
                offset = str(getattr(trade, 'offset', ''))
                price = float(getattr(trade, 'price', 0))
                volume = int(getattr(trade, 'volume', 0))
            
            is_open = 'OPEN' in offset.upper() or '开仓' in offset
            is_close = 'CLOSE' in offset.upper() or '平仓' in offset
            is_long = 'LONG' in direction.upper() or '多' in direction
            is_short = 'SHORT' in direction.upper() or '空' in direction
            
            if is_open:
                # 开仓交易，压入栈中
                position_stack.append({
                    'direction': 'LONG' if is_long else 'SHORT',
                    'price': price,
                    'volume': volume,
                    'trade': trade
                })
            elif is_close and position_stack:
                # 平仓交易，与最近的开仓配对计算盈亏
                open_position = position_stack.pop()
                
                # 计算盈亏：(平仓价 - 开仓价) * 数量 * 方向
                if open_position['direction'] == 'LONG':
                    # 多头：平仓价高于开仓价盈利
                    pnl = (price - open_position['price']) * min(volume, open_position['volume'])
                else:
                    # 空头：平仓价低于开仓价盈利
                    pnl = (open_position['price'] - price) * min(volume, open_position['volume'])
                
                completed_trades.append({
                    'open_price': open_position['price'],
                    'close_price': price,
                    'direction': open_position['direction'],
                    'volume': min(volume, open_position['volume']),
                    'pnl': pnl
                })
        
        # 总交易次数：所有交易记录
        total_trades = len(sorted_trades)
        
        # 基于配对完成的交易计算胜率等指标
        if completed_trades:
            trade_pnls = [t['pnl'] for t in completed_trades]
            winning_trades = len([p for p in trade_pnls if p > 0])
            win_rate = (winning_trades / len(completed_trades) * 100) if len(completed_trades) > 0 else 0
            
            # 计算profit factor
            total_profit = sum([p for p in trade_pnls if p > 0])
            total_loss = abs(sum([p for p in trade_pnls if p < 0]))
            profit_factor = total_profit / total_loss if total_loss > 0 else 0
            
            # 最大单笔盈利和亏损
            max_profit = max(trade_pnls) if trade_pnls else 0
            max_loss = min(trade_pnls) if trade_pnls else 0
            
        else:
            # 如果没有配对完成的交易，胜率相关指标为0
            win_rate = 0
            profit_factor = 0
            max_profit = 0
            max_loss = 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_profit': max_profit,
            'max_loss': max_loss
        }
    
    @staticmethod
    def _get_default_stats() -> Dict[str, float]:
        """获取默认统计数据"""
        return {
            'total_return': 0.0,
            'annual_return': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'profit_factor': 0.0,
            'win_rate': 0.0,
            'total_trades': 0,
            'total_pnl': 0.0,
            'max_profit': 0.0,
            'max_loss': 0.0,
            'final_win_loss_ratio': 0.0,
            'annual_volatility': 0.0
        } 