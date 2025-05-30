"""
使用tushare数据加载器的示例（支持本地缓存和.env配置）
"""
from data_loader import DataLoader

def main():
    # 创建数据加载器，指定数据库路径
    # Token会自动从.env文件中的TUSHARE_TOKEN读取
    # 如果需要手动指定token：loader = DataLoader(token="your_token_here")
    loader = DataLoader(db_path="market_data.db")
    
    # 支持的指数代码
    print("支持的指数代码:")
    for code, info in loader.symbol_mapping.items():
        print(f"  {code}: {info['name']}")
    
    # 显示当前缓存信息
    print("\n当前缓存信息:")
    cache_info = loader.get_cache_info()
    if cache_info:
        for symbol, info in cache_info.items():
            print(f"  {symbol} ({info['name']}): {info['count']}条数据 "
                  f"({info['start_date']} ~ {info['end_date']})")
    else:
        print("  缓存为空")
    
    # 获取数据示例
    symbol = "000300"  # 沪深300
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    
    print(f"\n开始获取{symbol}数据...")
    bars = loader.get_index_data(symbol, start_date, end_date)
    
    if bars:
        print(f"获取数据成功，共 {len(bars)} 条记录")
        
        # 统计数据来源
        cache_count = sum(1 for bar in bars if bar.gateway_name == "CACHE")
        tushare_count = sum(1 for bar in bars if bar.gateway_name == "TUSHARE")
        print(f"数据来源统计: 缓存({cache_count}条), Tushare({tushare_count}条)")
        
        # 显示前几条数据
        print("\n前5条数据:")
        for bar in bars[:5]:
            print(f"  {bar.datetime.strftime('%Y-%m-%d')}: "
                  f"开盘={bar.open_price:.2f}, "
                  f"最高={bar.high_price:.2f}, "
                  f"最低={bar.low_price:.2f}, "
                  f"收盘={bar.close_price:.2f} "
                  f"[来源: {bar.gateway_name}]")
        
        # 保存到CSV文件
        filename = f"{symbol}_{start_date}_{end_date}.csv"
        loader.save_data_to_csv(bars, filename)
        
        # 再次显示缓存信息，看看是否有更新
        print("\n更新后的缓存信息:")
        cache_info = loader.get_cache_info()
        for symbol_key, info in cache_info.items():
            print(f"  {symbol_key} ({info['name']}): {info['count']}条数据 "
                  f"({info['start_date']} ~ {info['end_date']})")
        
    else:
        print("获取数据失败！")
        print("可能的原因:")
        print("1. 网络连接问题")
        print("2. Tushare token未配置或无效")
        print("3. 日期范围无效")
        print("4. 指数代码不正确")
        print("\n请检查.env文件中的TUSHARE_TOKEN配置")

def demo_cache_management():
    """演示缓存管理功能"""
    print("\n=== 缓存管理演示 ===")
    loader = DataLoader()
    
    # 查看缓存信息
    cache_info = loader.get_cache_info()
    print(f"当前缓存中有 {len(cache_info)} 个指数的数据")
    
    # 清空特定指数的缓存（演示用，注释掉以免误删）
    # loader.clear_cache("000300")
    # print("已清空沪深300的缓存数据")
    
    # 清空所有缓存（演示用，注释掉以免误删）
    # loader.clear_cache()
    # print("已清空所有缓存数据")

def demo_incremental_data():
    """演示增量数据获取"""
    print("\n=== 增量数据获取演示 ===")
    loader = DataLoader()
    
    symbol = "000016"  # 上证50
    
    # 第一次获取部分数据
    print("第一次获取2023年上半年数据...")
    bars1 = loader.get_index_data(symbol, "2023-01-01", "2023-06-30")
    if bars1:
        print(f"获取到 {len(bars1)} 条数据")
    
    # 第二次获取扩展范围的数据（包含已有数据）
    print("\n第二次获取2023年全年数据...")
    bars2 = loader.get_index_data(symbol, "2023-01-01", "2023-12-31")
    if bars2:
        print(f"获取到 {len(bars2)} 条数据")
        # 统计数据来源
        cache_count = sum(1 for bar in bars2 if bar.gateway_name == "CACHE")
        tushare_count = sum(1 for bar in bars2 if bar.gateway_name == "TUSHARE")
        print(f"数据来源: 缓存({cache_count}条), Tushare({tushare_count}条)")

def check_env_setup():
    """检查环境配置"""
    print("\n=== 环境配置检查 ===")
    import os
    
    token = os.getenv('TUSHARE_TOKEN')
    if token:
        # 只显示token的前几位和后几位，中间用*代替
        masked_token = token[:4] + '*' * (len(token) - 8) + token[-4:] if len(token) > 8 else token
        print(f"✓ 已找到Tushare Token: {masked_token}")
    else:
        print("✗ 未找到Tushare Token")
        print("  请创建.env文件并设置TUSHARE_TOKEN")
        print("  参考env_example.txt文件")
    
    # 检查.env文件是否存在
    if os.path.exists('.env'):
        print("✓ 找到.env配置文件")
    else:
        print("✗ 未找到.env配置文件")
        print("  请将env_example.txt重命名为.env并配置您的token")

if __name__ == "__main__":
    check_env_setup()
    main()
    demo_cache_management()
    demo_incremental_data() 