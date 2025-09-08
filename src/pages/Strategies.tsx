import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, TrendingUp, Shield, Zap, DollarSign, Brain, Target, Loader2 } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { getAllStrategies, RebalancingStrategy } from "@/lib/api";

const Strategies = () => {
  const navigate = useNavigate();
  const [strategies, setStrategies] = useState<RebalancingStrategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 실제 백엔드에서 전략 데이터 가져오기
  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        setLoading(true);
        const response = await getAllStrategies();
        setStrategies(response.strategies);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch strategies:', err);
        setError('전략을 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchStrategies();
  }, []);

  // 로딩 상태
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background to-muted flex items-center justify-center">
        <div className="flex items-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <p className="text-lg">전략을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background to-muted flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-red-600 mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>다시 시도</Button>
        </div>
      </div>
    );
  }

  // 아이콘 매핑 함수 (실제 전략 데이터용)
  const getStrategyIcon = (strategyName: string, tags: string[]) => {
    if (tags.includes('AI') || tags.includes('혁신기술') || tags.includes('AI생성')) return Brain;
    if (tags.includes('기술주') || tags.includes('디지털전환')) return Zap;
    if (tags.includes('배당') || tags.includes('인컴') || tags.includes('현금흐름')) return DollarSign;
    if (tags.includes('안정성') || tags.includes('보수적') || tags.includes('저위험')) return Shield;
    if (tags.includes('성장') || tags.includes('고성장') || tags.includes('고수익')) return TrendingUp;
    return Target;
  };

  // 색상 매핑 함수
  const getStrategyColor = (riskLevel: string) => {
    switch (riskLevel) {
      case '높음': return 'rgb(239, 68, 68)'; // red-500
      case '중간': return 'rgb(59, 130, 246)'; // blue-500
      case '낮음': return 'rgb(34, 197, 94)'; // green-500
      default: return 'rgb(107, 114, 128)'; // gray-500
    }
  };

  // Generate performance simulation data based on actual strategies
  const performanceData = (() => {
    const months = [
      '2023-01', '2023-03', '2023-06', '2023-09', 
      '2023-12', '2024-03', '2024-06', '2024-09'
    ];
    
    return months.map((month, index) => {
      const dataPoint: any = { month, sp500: 100 + (index * 3) }; // S&P 500 benchmark
      
      // Generate performance data for each strategy based on their expected returns
      strategies.slice(0, 6).forEach((strategy) => {
        const monthlyReturn = strategy.expected_return / 12; // Convert annual return to monthly
        const volatility = strategy.volatility / Math.sqrt(12); // Monthly volatility
        
        // Add some randomness to simulate market conditions
        const randomFactor = (Math.random() - 0.5) * volatility * 0.3;
        
        // Calculate cumulative performance with some realistic simulation
        const basePerformance = 100 * Math.pow(1 + (monthlyReturn + randomFactor) / 100, index + 1);
        const strategyKey = strategy.strategy_name.replace(' 포트폴리오', '').replace(' ', '').toLowerCase();
        
        dataPoint[strategyKey] = Math.round(basePerformance * 100) / 100;
      });
      
      return dataPoint;
    });
  })();

  // Risk-Return comparison data
  const riskReturnData = strategies.map(strategy => ({
    name: strategy.strategy_name.replace(' 포트폴리오', ''),
    return: strategy.expected_return,
    risk: strategy.volatility,
    riskLevel: strategy.risk_level
  }));

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <h1 className="text-2xl font-bold">AI 리밸런싱 전략 비교</h1>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="space-y-8">
          {/* Strategy Cards */}
          <div className="grid lg:grid-cols-3 md:grid-cols-2 gap-6">
            {strategies.map((strategy) => {
              const IconComponent = getStrategyIcon(strategy.strategy_name, strategy.tags);
              const strategyColor = getStrategyColor(strategy.risk_level);
              
              return (
                <Card key={strategy.strategy_id} className="hover:shadow-lg transition-shadow cursor-pointer">
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div 
                        className="p-2 rounded-lg"
                        style={{ backgroundColor: `${strategyColor}20`, color: strategyColor }}
                      >
                        <IconComponent className="h-6 w-6" />
                      </div>
                      <div className="flex-1">
                        <CardTitle className="text-lg">{strategy.strategy_name}</CardTitle>
                        <div className="flex gap-1 mt-2 flex-wrap">
                          {strategy.tags.slice(0, 3).map((tag: string) => (
                            <Badge key={tag} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                          {strategy.strategy_type === 'ai_generated' && (
                            <Badge variant="outline" className="text-xs border-purple-500 text-purple-600">
                              AI 생성
                            </Badge>
                          )}
                          {strategy.user_id && (
                            <Badge variant="outline" className="text-xs border-blue-500 text-blue-600">
                              내 전략
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground text-sm mb-4">
                      {strategy.description}
                    </p>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <div className="text-muted-foreground">예상 수익률</div>
                        <div className="font-semibold text-green-600">{strategy.expected_return.toFixed(1)}%</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">변동성</div>
                        <div className="font-semibold">{strategy.volatility.toFixed(1)}%</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">최대 낙폭</div>
                        <div className="font-semibold text-red-600">{strategy.max_drawdown.toFixed(1)}%</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">샤프 비율</div>
                        <div className="font-semibold">{strategy.sharpe_ratio.toFixed(2)}</div>
                      </div>
                    </div>
                    
                    {/* 포트폴리오 구성 미리보기 */}
                    <div className="mt-4 pt-4 border-t">
                      <div className="text-xs text-muted-foreground mb-2">주요 구성</div>
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(strategy.target_allocation)
                          .sort(([,a], [,b]) => (b as number) - (a as number))
                          .slice(0, 3)
                          .map(([symbol, weight]) => (
                            <span key={symbol} className="text-xs px-2 py-1 bg-muted rounded">
                              {symbol} {(weight as number).toFixed(0)}%
                            </span>
                          ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Performance Comparison Chart */}
          <Card>
            <CardHeader>
              <CardTitle>전략별 성과 비교 (누적 수익률)</CardTitle>
              <p className="text-sm text-muted-foreground">
                실제 전략 데이터를 기반으로 한 시뮬레이션 결과입니다
              </p>
            </CardHeader>
            <CardContent>
              {strategies.length === 0 ? (
                <div className="flex items-center gap-2 py-8 justify-center">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>전략 데이터를 로딩 중...</span>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={500}>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip formatter={(value: number) => [`${(value - 100).toFixed(1)}%`, '']} />
                    <Legend />
                    {/* Dynamic lines based on actual strategies */}
                    {strategies.slice(0, 6).map((strategy, index) => {
                      const strategyKey = strategy.strategy_name.replace(' 포트폴리오', '').replace(' ', '').toLowerCase();
                      const colors = [
                        'rgb(34, 197, 94)', 'rgb(59, 130, 246)', 'rgb(168, 85, 247)', 
                        'rgb(249, 115, 22)', 'rgb(20, 184, 166)', 'rgb(236, 72, 153)'
                      ];
                      
                      return (
                        <Line 
                          key={strategy.strategy_id}
                          type="monotone" 
                          dataKey={strategyKey} 
                          stroke={colors[index % colors.length]} 
                          strokeWidth={2} 
                          name={strategy.strategy_name.replace(' 포트폴리오', '')} 
                        />
                      );
                    })}
                    <Line type="monotone" dataKey="sp500" stroke="#8884D8" strokeWidth={2} strokeDasharray="5 5" name="S&P 500" />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Risk-Return Scatter Plot */}
          <Card>
            <CardHeader>
              <CardTitle>위험 대비 수익률 분석</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={riskReturnData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                  <YAxis yAxisId="left" orientation="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="return" fill="#10b981" name="예상 수익률 (%)" />
                  <Bar yAxisId="right" dataKey="risk" fill="#f59e0b" name="변동성 (%)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

        </div>
      </main>
    </div>
  );
};

export default Strategies;