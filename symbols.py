"""
统一的股票代码管理
从symbol文件夹中的CSV文件加载股票代码到内存中
"""
import os
import csv
from typing import Dict, List, Tuple
from vnpy.trader.object import Exchange


class SymbolManager:
    """股票代码管理器"""

    def __init__(self, symbol_dir: str = "symbol"):
        """
        初始化股票代码管理器
        
        Args:
            symbol_dir: 股票代码文件夹路径
        """
        self.symbol_dir = symbol_dir
        self.symbols = {}  # 存储所有股票代码 {code: {name, market, type, exchange}}
        self._load_symbols()

    def _load_symbols(self):
        """从CSV文件加载股票代码"""
        if not os.path.exists(self.symbol_dir):
            print(f"警告: 股票代码文件夹 {self.symbol_dir} 不存在")
            return

        # 定义文件映射
        file_mappings = {
            "A_stock.txt": {"market": "CN", "type": "stock"},
            "A_index.txt": {"market": "CN", "type": "index"},
            "HK_stock.txt": {"market": "HK", "type": "stock"},
            "US_stock.txt": {"market": "US", "type": "stock"},
        }

        for filename, info in file_mappings.items():
            filepath = os.path.join(self.symbol_dir, filename)
            if os.path.exists(filepath):
                self._load_file(filepath, info["market"], info["type"])
            else:
                print(f"警告: 文件 {filepath} 不存在")

    def _load_file(self, filepath: str, market: str, symbol_type: str):
        """加载单个CSV文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split(',')
                    if len(parts) != 2:
                        print(f"警告: {filepath} 第{line_num}行格式错误: {line}")
                        continue

                    code, name = parts[0].strip(), parts[1].strip()
                    exchange = self._get_exchange(code, market)

                    self.symbols[code] = {
                        "name": name,
                        "market": market,
                        "type": symbol_type,
                        "exchange": exchange
                    }

            print(
                f"从 {filepath} 加载了 {len([s for s in self.symbols.values() if s['market'] == market and s['type'] == symbol_type])} 个{market}市场{symbol_type}代码")

        except Exception as e:
            print(f"加载文件 {filepath} 失败: {e}")

    def _get_exchange(self, code: str, market: str) -> Exchange:
        """根据代码和市场确定交易所"""
        if market == "CN":
            if code.endswith(".SH"):
                return Exchange.SSE
            elif code.endswith(".SZ"):
                return Exchange.SZSE
        elif market == "HK":
            return Exchange.HKFE
        elif market == "US":
            return Exchange.NASDAQ

        return Exchange.SSE  # 默认值

    def get_symbol_info(self, symbol: str) -> dict:
        """获取股票代码信息"""
        return self.symbols.get(symbol)

    def is_symbol_supported(self, symbol: str) -> bool:
        """检查是否支持指定的股票代码"""
        return symbol in self.symbols

    def get_symbols_by_market(self, market: str) -> Dict[str, dict]:
        """获取指定市场的所有股票代码"""
        return {symbol: info for symbol, info in self.symbols.items()
                if info['market'] == market}

    def get_symbols_by_type(self, symbol_type: str) -> Dict[str, dict]:
        """获取指定类型的所有股票代码"""
        return {symbol: info for symbol, info in self.symbols.items()
                if info['type'] == symbol_type}

    def get_all_symbols(self) -> Dict[str, dict]:
        """获取所有支持的股票代码"""
        return self.symbols.copy()

    def reload_symbols(self):
        """重新加载股票代码"""
        self.symbols.clear()
        self._load_symbols()


# 全局实例
_symbol_manager = SymbolManager()


def get_symbol_info(symbol: str) -> dict:
    """获取股票代码信息"""
    return _symbol_manager.get_symbol_info(symbol)


def get_symbols_by_market(market: str) -> Dict[str, dict]:
    """获取指定市场的所有股票代码"""
    return _symbol_manager.get_symbols_by_market(market)


def get_symbols_by_type(symbol_type: str) -> Dict[str, dict]:
    """获取指定类型的所有股票代码"""
    return _symbol_manager.get_symbols_by_type(symbol_type)


def get_all_symbols() -> Dict[str, dict]:
    """获取所有支持的股票代码"""
    return _symbol_manager.get_all_symbols()


def reload_symbols():
    """重新加载股票代码"""
    _symbol_manager.reload_symbols()


if __name__ == "__main__":
    # 测试函数
    print("所有支持的股票代码:")
    for symbol, info in get_all_symbols().items():
        print(f"  {symbol}: {info['name']} ({info['market']}-{info['type']})")

    print(f"\n总共支持 {len(get_all_symbols())} 个股票代码")

    # 按市场分组显示
    for market in ['CN', 'HK', 'US']:
        symbols = get_symbols_by_market(market)
        print(f"\n{market} 市场股票 ({len(symbols)} 个):")
        for symbol, info in symbols.items():
            print(f"  {symbol}: {info['name']} ({info['type']})")
