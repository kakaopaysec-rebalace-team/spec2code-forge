import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, TrendingUp, Building2, PieChart, Zap } from "lucide-react";
import { getUserHoldings, getAllStrategies } from "@/lib/api";

const ProfileSetup = () => {
  const navigate = useNavigate();
  const [holdings, setHoldings] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalValue, setTotalValue] = useState(0);

  useEffect(() => {
    const loadData = async () => {
      try {
        console.log('🔄 DB에서 데이터를 불러오는 중...');
        
        const holdingsResponse = await getUserHoldings('mock-user-001');
        const strategiesResponse = await getAllStrategies();
        
        console.log('📊 로드된 데이터:');
        console.log('- 보유 종목:', holdingsResponse.holdings?.length, '개');
        console.log('- 포트폴리오 가치: $', holdingsResponse.total_value?.toLocaleString());
        console.log('- 사용 가능 전략:', strategiesResponse.strategies?.length, '개');
        
        setHoldings(holdingsResponse.holdings || []);
        setTotalValue(holdingsResponse.total_value || 0);
        setStrategies(strategiesResponse.strategies || []);
        
      } catch (error) {
        console.error('❌ 데이터 로드 실패:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handleAnalyze = () => {
    sessionStorage.setItem('userProfile', JSON.stringify({
      investment_style: 'moderate',
      investment_goal: 'growth',
      investment_period: 'long'
    }));
    
    sessionStorage.setItem('currentPortfolio', JSON.stringify(
      holdings.map(holding => ({
        stock: holding.symbol,
        weight: holding.weight
      }))
    ));
    
    navigate('/results');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
          <p className="text-muted-foreground">데이터베이스에서 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted">
      <header className="border-b bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-8 w-8 text-primary" />
              <h1 className="text-2xl font-bold">리밸런싱 시작하기</h1>
            </div>
            <Button variant="ghost" onClick={() => navigate('/')}>
              돌아가기
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="space-y-8">
          {/* 포트폴리오 개요 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5" />
                현재 포트폴리오 (실제 DB 데이터)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="text-center p-4 bg-muted rounded-lg">
                  <div className="text-3xl font-bold text-green-600">
                    ${totalValue.toLocaleString()}
                  </div>
                  <div className="text-sm text-muted-foreground">총 포트폴리오 가치</div>
                </div>
                <div className="text-center p-4 bg-muted rounded-lg">
                  <div className="text-3xl font-bold">{holdings.length}</div>
                  <div className="text-sm text-muted-foreground">보유 종목</div>
                </div>
                <div className="text-center p-4 bg-muted rounded-lg">
                  <div className="text-3xl font-bold">
                    {holdings.filter(h => h.market_value > h.purchase_price * h.quantity).length}
                  </div>
                  <div className="text-sm text-muted-foreground">수익 종목</div>
                </div>
              </div>

              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {holdings.map((holding) => {
                  const totalCost = holding.purchase_price * holding.quantity;
                  const profitLoss = holding.market_value - totalCost;
                  const profitLossPercent = (profitLoss / totalCost) * 100;
                  
                  return (
                    <div key={holding.holding_id} className="p-4 border rounded-lg bg-card">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-semibold">{holding.symbol}</h3>
                          <p className="text-sm text-muted-foreground">{holding.name}</p>
                        </div>
                        <Badge variant="outline">{holding.weight.toFixed(1)}%</Badge>
                      </div>
                      
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span>보유량:</span>
                          <span>{holding.quantity.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>현재가:</span>
                          <span>${holding.current_price.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>시장가치:</span>
                          <span className="font-medium">${holding.market_value.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>손익:</span>
                          <span className={profitLoss >= 0 ? 'text-green-600' : 'text-red-600'}>
                            ${profitLoss.toFixed(2)} ({profitLossPercent >= 0 ? '+' : ''}{profitLossPercent.toFixed(1)}%)
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* 사용 가능한 전략 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                사용 가능한 리밸런싱 전략 (실제 DB 데이터)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 mb-6 text-sm">
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-muted-foreground">평균 수익률</div>
                  <div className="font-semibold text-lg text-green-600">
                    {strategies.length > 0 ? (strategies.reduce((sum, s) => sum + s.expected_return, 0) / strategies.length).toFixed(1) : '0.0'}%
                  </div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-muted-foreground">전체 전략 수</div>
                  <div className="font-semibold text-lg">{strategies.length}개</div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-muted-foreground">최고 수익률</div>
                  <div className="font-semibold text-lg text-green-600">
                    {strategies.length > 0 ? Math.max(...strategies.map(s => s.expected_return)).toFixed(1) : '0.0'}%
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                {strategies.slice(0, 6).map((strategy) => (
                  <div key={strategy.strategy_id} className="p-4 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer bg-card">
                    <div className="space-y-3">
                      <div>
                        <h3 className="font-semibold text-sm">{strategy.strategy_name}</h3>
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                          {strategy.description}
                        </p>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-muted-foreground">수익률:</span>
                          <span className="font-medium text-green-600 ml-1">
                            {strategy.expected_return.toFixed(1)}%
                          </span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">위험도:</span>
                          <span className={`font-medium ml-1 ${
                            strategy.risk_level === '높음' ? 'text-red-600' : 
                            strategy.risk_level === '중간' ? 'text-yellow-600' : 'text-green-600'
                          }`}>
                            {strategy.risk_level}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex flex-wrap gap-1">
                        {strategy.tags.slice(0, 2).map((tag) => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 text-center space-y-2">
                <Button variant="outline" onClick={() => navigate('/strategies')}>
                  모든 전략 상세 비교
                </Button>
                <p className="text-xs text-muted-foreground">
                  총 {strategies.length}개 전략 사용 가능 • 실시간 DB 조회
                </p>
              </div>
            </CardContent>
          </Card>

          {/* 분석 시작 버튼 */}
          <div className="text-center">
            <Button 
              size="lg" 
              onClick={handleAnalyze} 
              className="px-12 py-3"
              disabled={holdings.length === 0}
            >
              <Building2 className="mr-2 h-5 w-5" />
              리밸런싱 전략 생성하기
            </Button>
            <p className="text-xs text-muted-foreground mt-2">
              {holdings.length}개 종목 • ${totalValue.toLocaleString()} 포트폴리오
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ProfileSetup;