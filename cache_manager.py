"""
数据缓存管理工具
用于管理本地SQLite数据库中的指数数据缓存
"""
import sqlite3
import argparse
from datetime import datetime
from data_loader import DataLoader

class CacheManager:
    """数据缓存管理器"""
    
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self.loader = DataLoader(db_path=db_path)
    
    def show_cache_info(self):
        """显示缓存信息"""
        print(f"数据库文件: {self.db_path}")
        cache_info = self.loader.get_cache_info()
        
        if not cache_info:
            print("缓存为空")
            return
        
        print(f"缓存中共有 {len(cache_info)} 个指数的数据:\n")
        
        total_records = 0
        for symbol, info in cache_info.items():
            print(f"指数代码: {symbol}")
            print(f"指数名称: {info['name']}")
            print(f"数据条数: {info['count']}")
            print(f"日期范围: {info['start_date']} ~ {info['end_date']}")
            print("-" * 40)
            total_records += info['count']
        
        print(f"总计: {total_records} 条记录")
    
    def clear_cache(self, symbol: str = None):
        """清空缓存"""
        if symbol:
            if symbol not in self.loader.symbol_mapping:
                print(f"不支持的指数代码: {symbol}")
                return
            
            confirm = input(f"确定要清空 {symbol} 的缓存数据吗？(y/N): ")
            if confirm.lower() == 'y':
                self.loader.clear_cache(symbol)
            else:
                print("操作已取消")
        else:
            confirm = input("确定要清空所有缓存数据吗？(y/N): ")
            if confirm.lower() == 'y':
                self.loader.clear_cache()
            else:
                print("操作已取消")
    
    def export_data(self, symbol: str, start_date: str, end_date: str, output_file: str):
        """导出数据到CSV文件"""
        if symbol not in self.loader.symbol_mapping:
            print(f"不支持的指数代码: {symbol}")
            return
        
        print(f"正在导出 {symbol} 的数据...")
        bars = self.loader.get_index_data(symbol, start_date, end_date)
        
        if bars:
            self.loader.save_data_to_csv(bars, output_file)
            print(f"数据已导出到: {output_file}")
        else:
            print("导出失败，未获取到数据")
    
    def check_data_integrity(self):
        """检查数据完整性"""
        print("检查数据完整性...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查是否有重复数据
        cursor.execute('''
            SELECT symbol, trade_date, COUNT(*) as count
            FROM index_data
            GROUP BY symbol, trade_date
            HAVING COUNT(*) > 1
        ''')
        
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"发现 {len(duplicates)} 条重复数据:")
            for dup in duplicates:
                print(f"  {dup[0]} - {dup[1]}: {dup[2]} 条重复记录")
        else:
            print("未发现重复数据")
        
        # 检查数据缺失（简单的日期连续性检查）
        cache_info = self.loader.get_cache_info()
        for symbol, info in cache_info.items():
            cursor.execute('''
                SELECT COUNT(*) FROM index_data 
                WHERE symbol = ?
            ''', (symbol,))
            actual_count = cursor.fetchone()[0]
            
            if actual_count != info['count']:
                print(f"数据不一致: {symbol} 预期{info['count']}条，实际{actual_count}条")
        
        conn.close()
        print("数据完整性检查完成")
    
    def vacuum_database(self):
        """压缩数据库文件"""
        print("正在压缩数据库...")
        conn = sqlite3.connect(self.db_path)
        conn.execute('VACUUM')
        conn.close()
        print("数据库压缩完成")

def main():
    parser = argparse.ArgumentParser(description='数据缓存管理工具')
    parser.add_argument('--db', default='market_data.db', help='数据库文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 显示缓存信息
    subparsers.add_parser('info', help='显示缓存信息')
    
    # 清空缓存
    clear_parser = subparsers.add_parser('clear', help='清空缓存')
    clear_parser.add_argument('--symbol', help='指定要清空的指数代码（不指定则清空全部）')
    
    # 导出数据
    export_parser = subparsers.add_parser('export', help='导出数据到CSV')
    export_parser.add_argument('symbol', help='指数代码')
    export_parser.add_argument('start_date', help='开始日期 (YYYY-MM-DD)')
    export_parser.add_argument('end_date', help='结束日期 (YYYY-MM-DD)')
    export_parser.add_argument('output', help='输出文件名')
    
    # 检查数据完整性
    subparsers.add_parser('check', help='检查数据完整性')
    
    # 压缩数据库
    subparsers.add_parser('vacuum', help='压缩数据库文件')
    
    # 显示支持的指数
    subparsers.add_parser('symbols', help='显示支持的指数代码')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = CacheManager(args.db)
    
    if args.command == 'info':
        manager.show_cache_info()
    elif args.command == 'clear':
        manager.clear_cache(args.symbol)
    elif args.command == 'export':
        manager.export_data(args.symbol, args.start_date, args.end_date, args.output)
    elif args.command == 'check':
        manager.check_data_integrity()
    elif args.command == 'vacuum':
        manager.vacuum_database()
    elif args.command == 'symbols':
        print("支持的指数代码:")
        for code, info in manager.loader.symbol_mapping.items():
            print(f"  {code}: {info['name']}")

if __name__ == "__main__":
    main() 