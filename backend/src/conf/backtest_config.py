"""
回测配置管理器
支持可配置的输出路径和数据库设置
"""
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass
class BacktestConfig:
    """回测配置类"""
    # 输出路径配置
    output_base_dir: str = "../../../backtest_results"
    html_output_dir: str = "html"
    png_output_dir: str = "charts"
    excel_output_dir: str = "reports"
    
    # 数据库配置 - 统一使用项目根目录下的数据库文件
    results_db_path: str = "backtest_results.db"
    
    # 回测参数
    symbol: str = ""
    strategy_name: str = ""
    start_date: str = ""
    end_date: str = ""
    strategy_params: Dict[str, Any] = None
    
    # 生成唯一的运行ID
    run_id: str = ""
    
    def __post_init__(self):
        if not self.run_id:
            self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.strategy_params is None:
            self.strategy_params = {}
    
    def get_output_path(self, file_type: str, filename: str) -> str:
        """获取输出文件的完整路径"""
        type_mapping = {
            'html': self.html_output_dir,
            'png': self.png_output_dir,
            'excel': self.excel_output_dir
        }
        
        subdir = type_mapping.get(file_type, file_type)
        full_dir = os.path.join(self.output_base_dir, self.symbol, subdir)
        os.makedirs(full_dir, exist_ok=True)
        
        # 在文件名中加入运行ID以避免冲突
        name_parts = filename.split('.')
        if len(name_parts) > 1:
            filename = f"{name_parts[0]}_{self.run_id}.{name_parts[1]}"
        else:
            filename = f"{filename}_{self.run_id}"
        
        return os.path.join(full_dir, filename)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'output_base_dir': self.output_base_dir,
            'html_output_dir': self.html_output_dir,
            'png_output_dir': self.png_output_dir,
            'excel_output_dir': self.excel_output_dir,
            'results_db_path': self.results_db_path,
            'symbol': self.symbol,
            'strategy_name': self.strategy_name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'strategy_params': self.strategy_params,
            'run_id': self.run_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestConfig':
        """从字典创建配置对象"""
        return cls(**data)
    
    def save_to_json(self, filepath: str):
        """保存配置到JSON文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_json(cls, filepath: str) -> 'BacktestConfig':
        """从JSON文件加载配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data) 