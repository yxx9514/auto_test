"""
量化炒股辅助软件 - 使用示例
"""

from transaction_review import (
    StockAnalyzer, 
    analyze_stock, 
    analyze_multiple_stocks, 
    print_report
)


def example_single_stock():
    """示例1: 分析单只股票"""
    print("="*60)
    print("示例1: 分析单只股票")
    print("="*60)
    
    stock_code = "600519"  # 贵州茅台
    report = analyze_stock(stock_code)
    print_report(report)


def example_batch_analysis():
    """示例2: 批量分析多只股票"""
    print("\n" + "="*60)
    print("示例2: 批量分析多只股票")
    print("="*60)
    
    stock_list = [
        "600519",  # 贵州茅台
        "600703",  # 三安光电
        "000001",  # 平安银行
        "000002",  # 万科A
    ]
    
    df_results = analyze_multiple_stocks(stock_list)
    
    # 按综合评分排序
    df_results = df_results.sort_values('综合评分', ascending=False)
    
    print("\n分析结果（按综合评分排序）:")
    print(df_results.to_string(index=False))
    
    # 筛选买入信号
    buy_signals = df_results[df_results['信号'].str.contains('BUY', case=False)]
    if not buy_signals.empty:
        print("\n买入信号股票:")
        print(buy_signals[['股票代码', '当前价格', '信号', '综合评分']].to_string(index=False))


def example_custom_analysis():
    """示例3: 自定义分析"""
    print("\n" + "="*60)
    print("示例3: 自定义分析（使用StockAnalyzer类）")
    print("="*60)
    
    analyzer = StockAnalyzer("600703", period_days=180)
    
    # 只计算需要的指标
    analyzer.fetch_data()
    analyzer.calculate_ma([5, 20, 60])
    analyzer.calculate_rsi()
    
    # 获取特定分析
    trend = analyzer.analyze_trend()
    momentum = analyzer.analyze_momentum()
    
    print(f"\n趋势分析: {trend['trend']} (评分: {trend['score']:.2f})")
    print(f"动量分析: RSI={momentum['rsi']:.2f}, MACD={momentum['macd']:.4f}")
    
    # 生成信号
    signal = analyzer.generate_signal()
    print(f"\n交易信号: {signal['signal']} ({signal['strength']})")
    print(f"综合评分: {signal['total_score']:.2f}/100")


def example_screen_stocks():
    """示例4: 股票筛选（找出买入信号股票）"""
    print("\n" + "="*60)
    print("示例4: 股票筛选")
    print("="*60)
    
    # 这里可以扩展为从文件或数据库读取股票列表
    stock_pool = [
        "600519", "600703", "000001", "000002",
        "600036", "000858", "002415", "300750"
    ]
    
    print(f"正在分析 {len(stock_pool)} 只股票...")
    df_results = analyze_multiple_stocks(stock_pool)
    
    # 筛选条件：综合评分 > 70 且信号为买入
    buy_candidates = df_results[
        (df_results['综合评分'] > 70) & 
        (df_results['信号'].str.contains('BUY', case=False))
    ].sort_values('综合评分', ascending=False)
    
    if not buy_candidates.empty:
        print(f"\n找到 {len(buy_candidates)} 只符合条件的股票:")
        print(buy_candidates[['股票代码', '当前价格', '信号', '综合评分', '趋势评分', '动量评分']].to_string(index=False))
    else:
        print("\n未找到符合条件的股票")


if __name__ == "__main__":
    # 运行所有示例
    example_single_stock()
    example_batch_analysis()
    example_custom_analysis()
    example_screen_stocks()