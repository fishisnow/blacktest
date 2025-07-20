"""
数据源配置管理
支持 tushare 和 futu openapi 两种数据源
"""
import os
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("警告: python-dotenv未安装，无法从.env文件读取配置")


class DataSource(Enum):
    """数据源枚举"""
    TUSHARE = "tushare"
    FUTU = "futu"


@dataclass
class DataSourceConfig:
    """数据源配置"""
    source: DataSource
    enabled: bool = True
    priority: int = 1  # 优先级，数字越小优先级越高
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.data_sources = self._load_data_source_configs()
        
    def _load_data_source_configs(self) -> Dict[DataSource, DataSourceConfig]:
        """加载数据源配置"""
        configs = {}
        
        # Tushare 配置
        tushare_token = os.getenv('TUSHARE_TOKEN')
        tushare_enabled = bool(tushare_token)
        configs[DataSource.TUSHARE] = DataSourceConfig(
            source=DataSource.TUSHARE,
            enabled=tushare_enabled,
            priority=int(os.getenv('TUSHARE_PRIORITY', '2')),
            config={
                'token': tushare_token,
                'timeout': int(os.getenv('TUSHARE_TIMEOUT', '30')),
                'retry_count': int(os.getenv('TUSHARE_RETRY_COUNT', '3'))
            }
        )
        
        # Futu 配置
        futu_host = os.getenv('FUTU_HOST', '127.0.0.1')
        futu_port = int(os.getenv('FUTU_PORT', '11111'))
        futu_enabled = os.getenv('FUTU_ENABLED', 'false').lower() == 'true'
        configs[DataSource.FUTU] = DataSourceConfig(
            source=DataSource.FUTU,
            enabled=futu_enabled,
            priority=int(os.getenv('FUTU_PRIORITY', '1')),
            config={
                'host': futu_host,
                'port': futu_port,
                'timeout': int(os.getenv('FUTU_TIMEOUT', '30')),
                'retry_count': int(os.getenv('FUTU_RETRY_COUNT', '3')),
                'session': os.getenv('FUTU_SESSION', 'ALL')  # ALL, REGULAR, AFTER_HOURS
            }
        )
        
        return configs
    
    def get_primary_data_source(self) -> Optional[DataSource]:
        """获取主要数据源（优先级最高且启用的）"""
        enabled_sources = [
            (source, config) for source, config in self.data_sources.items() 
            if config.enabled
        ]
        
        if not enabled_sources:
            return None
            
        # 按优先级排序
        enabled_sources.sort(key=lambda x: x[1].priority)
        return enabled_sources[0][0]
    
    def get_fallback_sources(self) -> list[DataSource]:
        """获取备用数据源列表（按优先级排序）"""
        primary = self.get_primary_data_source()
        if primary is None:
            return []
            
        fallback_sources = [
            source for source, config in self.data_sources.items()
            if config.enabled and source != primary
        ]
        
        # 按优先级排序
        fallback_sources.sort(key=lambda x: self.data_sources[x].priority)
        return fallback_sources
    
    def get_data_source_config(self, source: DataSource) -> Optional[DataSourceConfig]:
        """获取指定数据源的配置"""
        return self.data_sources.get(source)
    
    def is_source_enabled(self, source: DataSource) -> bool:
        """检查数据源是否启用"""
        config = self.get_data_source_config(source)
        return config is not None and config.enabled
    
    def get_all_enabled_sources(self) -> list[DataSource]:
        """获取所有启用的数据源"""
        return [
            source for source, config in self.data_sources.items()
            if config.enabled
        ]
    
    def print_config_summary(self):
        """打印配置摘要"""
        print("=== 数据源配置摘要 ===")
        primary = self.get_primary_data_source()
        fallbacks = self.get_fallback_sources()
        
        print(f"主要数据源: {primary.value if primary else '无'}")
        if fallbacks:
            print(f"备用数据源: {', '.join([s.value for s in fallbacks])}")
        else:
            print("备用数据源: 无")
            
        print("\n详细配置:")
        for source, config in self.data_sources.items():
            status = "启用" if config.enabled else "禁用"
            print(f"  {source.value}: {status} (优先级: {config.priority})")
            
            if source == DataSource.TUSHARE and config.enabled:
                token = config.config.get('token', '')
                masked_token = token[:4] + '*' * (len(token) - 8) + token[-4:] if len(token) > 8 else token
                print(f"    Token: {masked_token}")
                
            elif source == DataSource.FUTU and config.enabled:
                print(f"    连接: {config.config.get('host')}:{config.config.get('port')}")
                print(f"    会话: {config.config.get('session')}")


# 全局配置实例
config_manager = ConfigManager()


if __name__ == "__main__":
    # 测试配置管理器
    config_manager.print_config_summary() 