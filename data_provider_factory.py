"""
数据提供器工厂
统一管理和创建不同的数据提供器实例
"""
from typing import Optional, Dict, List
from base_data_provider import BaseDataProvider
from tushare_data_provider import TushareDataProvider
from futu_data_provider import FutuDataProvider
from config import DataSource, config_manager


class DataProviderFactory:
    """数据提供器工厂"""
    
    def __init__(self):
        """初始化工厂"""
        self._providers: Dict[DataSource, BaseDataProvider] = {}
        self._initialized = False
    
    def initialize(self):
        """初始化所有可用的数据提供器"""
        if self._initialized:
            return
        
        print("初始化数据提供器...")
        
        # 初始化 Tushare 提供器
        if config_manager.is_source_enabled(DataSource.TUSHARE):
            try:
                config = config_manager.get_data_source_config(DataSource.TUSHARE)
                token = config.config.get('token') if config else None
                
                if token:
                    provider = TushareDataProvider(token)
                    self._providers[DataSource.TUSHARE] = provider
                    print(f"✓ Tushare 数据提供器已初始化")
                else:
                    print("✗ Tushare Token 未配置，跳过初始化")
            except Exception as e:
                print(f"✗ Tushare 数据提供器初始化失败: {e}")
        
        # 初始化 Futu 提供器
        if config_manager.is_source_enabled(DataSource.FUTU):
            try:
                config = config_manager.get_data_source_config(DataSource.FUTU)
                if config:
                    provider = FutuDataProvider(
                        host=config.config.get('host', '127.0.0.1'),
                        port=config.config.get('port', 11111),
                        timeout=config.config.get('timeout', 30)
                    )
                    self._providers[DataSource.FUTU] = provider
                    print(f"✓ Futu 数据提供器已初始化")
                else:
                    print("✗ Futu 配置未找到，跳过初始化")
            except Exception as e:
                print(f"✗ Futu 数据提供器初始化失败: {e}")
        
        self._initialized = True
        print(f"数据提供器初始化完成，共 {len(self._providers)} 个可用")
    
    def get_provider(self, data_source: DataSource) -> Optional[BaseDataProvider]:
        """
        获取指定数据源的提供器
        
        Args:
            data_source: 数据源类型
            
        Returns:
            数据提供器实例或None
        """
        if not self._initialized:
            self.initialize()
        
        return self._providers.get(data_source)
    
    def get_all_providers(self) -> Dict[DataSource, BaseDataProvider]:
        """
        获取所有可用的数据提供器
        
        Returns:
            数据提供器字典
        """
        if not self._initialized:
            self.initialize()
        
        return self._providers.copy()
    
    def get_providers_by_priority(self) -> List[BaseDataProvider]:
        """
        按优先级获取数据提供器列表
        
        Returns:
            按优先级排序的数据提供器列表
        """
        if not self._initialized:
            self.initialize()
        
        # 获取启用的数据源，按优先级排序
        enabled_sources = []
        for source, provider in self._providers.items():
            config = config_manager.get_data_source_config(source)
            if config and config.enabled:
                enabled_sources.append((source, provider, config.priority))
        
        # 按优先级排序（数字越小优先级越高）
        enabled_sources.sort(key=lambda x: x[2])
        
        return [provider for _, provider, _ in enabled_sources]
    
    def get_primary_provider(self) -> Optional[BaseDataProvider]:
        """
        获取主要数据提供器（优先级最高的）
        
        Returns:
            主要数据提供器或None
        """
        providers = self.get_providers_by_priority()
        return providers[0] if providers else None
    
    def get_fallback_providers(self) -> List[BaseDataProvider]:
        """
        获取备用数据提供器列表
        
        Returns:
            备用数据提供器列表
        """
        providers = self.get_providers_by_priority()
        return providers[1:] if len(providers) > 1 else []
    
    def test_all_providers(self) -> Dict[DataSource, bool]:
        """
        测试所有数据提供器的连接
        
        Returns:
            测试结果字典
        """
        if not self._initialized:
            self.initialize()
        
        results = {}
        print("测试所有数据提供器连接...")
        
        for source, provider in self._providers.items():
            print(f"\n测试 {source.value} 连接...")
            try:
                result = provider.test_connection()
                results[source] = result
                status = "✓ 成功" if result else "✗ 失败"
                print(f"{source.value} 连接测试: {status}")
            except Exception as e:
                results[source] = False
                print(f"{source.value} 连接测试异常: {e}")
        
        return results
    
    def get_supported_symbols_all(self) -> Dict[str, List[DataSource]]:
        """
        获取所有数据源支持的股票代码汇总
        
        Returns:
            股票代码到支持的数据源列表的映射
        """
        if not self._initialized:
            self.initialize()
        
        symbol_sources = {}
        
        for source, provider in self._providers.items():
            try:
                symbols = provider.get_supported_symbols()
                for symbol in symbols.keys():
                    if symbol not in symbol_sources:
                        symbol_sources[symbol] = []
                    symbol_sources[symbol].append(source)
            except Exception as e:
                print(f"获取 {source.value} 支持的股票代码失败: {e}")
        
        return symbol_sources
    
    def find_providers_for_symbol(self, symbol: str) -> List[BaseDataProvider]:
        """
        查找支持指定股票代码的数据提供器
        
        Args:
            symbol: 股票代码
            
        Returns:
            支持该股票代码的数据提供器列表（按优先级排序）
        """
        if not self._initialized:
            self.initialize()
        
        supporting_providers = []
        providers_by_priority = self.get_providers_by_priority()
        
        for provider in providers_by_priority:
            if provider.is_symbol_supported(symbol):
                supporting_providers.append(provider)
        
        return supporting_providers
    
    def cleanup(self):
        """清理所有数据提供器连接"""
        for provider in self._providers.values():
            try:
                provider.disconnect()
            except Exception as e:
                print(f"断开 {provider.get_data_source_name()} 连接失败: {e}")
        
        print("所有数据提供器连接已清理")


# 全局工厂实例
data_provider_factory = DataProviderFactory()


if __name__ == "__main__":
    # 测试数据提供器工厂
    factory = DataProviderFactory()
    
    # 初始化
    factory.initialize()
    
    # 显示所有提供器
    providers = factory.get_all_providers()
    print(f"\n可用的数据提供器:")
    for source, provider in providers.items():
        print(f"  {source.value}: {provider}")
    
    # 显示优先级顺序
    priority_providers = factory.get_providers_by_priority()
    print(f"\n数据提供器优先级顺序:")
    for i, provider in enumerate(priority_providers, 1):
        print(f"  {i}. {provider}")
    
    # 测试所有连接
    test_results = factory.test_all_providers()
    print(f"\n连接测试结果:")
    for source, result in test_results.items():
        status = "✓" if result else "✗"
        print(f"  {source.value}: {status}")
    
    # 显示支持的股票代码汇总
    symbol_sources = factory.get_supported_symbols_all()
    print(f"\n支持的股票代码汇总:")
    for symbol, sources in symbol_sources.items():
        source_names = [s.value for s in sources]
        print(f"  {symbol}: {', '.join(source_names)}")
    
    # 测试查找特定股票的提供器
    test_symbols = ["AAPL", "000300", "00700"]
    for symbol in test_symbols:
        providers = factory.find_providers_for_symbol(symbol)
        if providers:
            provider_names = [p.get_data_source_name() for p in providers]
            print(f"\n{symbol} 支持的数据源: {', '.join(provider_names)}")
        else:
            print(f"\n{symbol} 没有可用的数据源")
    
    # 清理
    factory.cleanup() 