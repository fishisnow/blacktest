"""
抽象数据提供器基类
定义统一的数据提供器接口，所有具体的数据提供器都应该继承此类
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from vnpy.trader.object import BarData
from config import DataSource


class BaseDataProvider(ABC):
    """抽象数据提供器基类"""
    
    def __init__(self, data_source: DataSource):
        """
        初始化数据提供器
        
        Args:
            data_source: 数据源类型
        """
        self.data_source = data_source
        self.is_connected = False
        
    @abstractmethod
    def connect(self) -> bool:
        """
        连接到数据源
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, 
                          **kwargs) -> Optional[List[BarData]]:
        """
        获取历史K线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (格式: 'YYYY-MM-DD')
            end_date: 结束日期 (格式: 'YYYY-MM-DD')
            **kwargs: 其他参数
            
        Returns:
            BarData列表或None
        """
        pass
    
    @abstractmethod
    def get_supported_symbols(self) -> Dict[str, Dict[str, Any]]:
        """
        获取支持的股票代码列表
        
        Returns:
            Dict: 支持的股票代码映射
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        测试连接
        
        Returns:
            bool: 连接测试是否成功
        """
        pass
    
    def is_symbol_supported(self, symbol: str) -> bool:
        """
        检查是否支持指定的股票代码
        
        Args:
            symbol: 股票代码
            
        Returns:
            bool: 是否支持
        """
        supported_symbols = self.get_supported_symbols()
        return symbol in supported_symbols
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票代码信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            Dict: 股票信息或None
        """
        supported_symbols = self.get_supported_symbols()
        return supported_symbols.get(symbol)
    
    def get_data_source_name(self) -> str:
        """
        获取数据源名称
        
        Returns:
            str: 数据源名称
        """
        return self.data_source.value
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}({self.data_source.value})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__() 