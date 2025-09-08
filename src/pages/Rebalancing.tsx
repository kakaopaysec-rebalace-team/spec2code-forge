import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, TrendingUp, Target, BarChart3, Play, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { getUserHoldings, getAllStrategies } from "@/lib/api";

const Rebalancing = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  
  // 실제 데이터베이스에서 불러온 데이터
  const [holdings, setHoldings] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalValue, setTotalValue] = useState(0);
  const [selectedHoldings, setSelectedHoldings] = useState<string[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string>("");
  const [showAllStrategies, setShowAllStrategies] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        console.log('🔄 리밸런싱 페이지: DB에서 데이터를 불러오는 중...');
        
        const holdingsResponse = await getUserHoldings('mock-user-001');
        const strategiesResponse = await getAllStrategies();
        
        console.log('📊 리밸런싱 페이지 로드된 데이터:');
        console.log('- 보유 종목:', holdingsResponse.holdings?.length, '개');
        console.log('- 포트폴리오 가치: $', holdingsResponse.total_value?.toLocaleString());
        console.log('- 사용 가능 전략:', strategiesResponse.strategies?.length, '개');
        
        setHoldings(holdingsResponse.holdings || []);
        setTotalValue(holdingsResponse.total_value || 0);
        setStrategies(strategiesResponse.strategies || []);
        
      } catch (error) {
        console.error('❌ 리밸런싱 페이지 데이터 로드 실패:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handleHoldingToggle = (holdingId: string) => {
    setSelectedHoldings(prev => 
      prev.includes(holdingId) 
        ? prev.filter(id => id !== holdingId)
        : [...prev, holdingId]
    );
  };

  const handleStrategySelect = (strategyId: string) => {
    setSelectedStrategy(strategyId);
  };

  const handleSelectAllHoldings = () => {
    if (selectedHoldings.length === holdings.length) {
      setSelectedHoldings([]);
    } else {
      setSelectedHoldings(holdings.map(holding => holding.holding_id));
    }
  };

  const isAllSelected = selectedHoldings.length === holdings.length;

  const handleStartRebalancing = () => {
    if (selectedHoldings.length === 0) {
      toast({
        title: "종목 선택 필요",
        description: "리밸런싱할 종목을 최소 1개 이상 선택해주세요.",
        variant: "destructive",
      });
      return;
    }

    if (!selectedStrategy) {
      toast({
        title: "전략 선택 필요",
        description: "적용할 리밸런싱 전략을 선택해주세요.",
        variant: "destructive",
      });
      return;
    }

    toast({
      title: "리밸런싱 시작",
      description: "선택한 종목과 전략으로 리밸런싱을 실행합니다...",
    });

    setTimeout(() => {
      navigate('/results', { 
        state: { 
          selectedHoldings, 
          selectedStrategy,
          fromRebalancing: true 
        } 
      });
    }, 2000);
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
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <h1 className="text-2xl font-bold">리밸런싱 시작 (실제 DB 데이터)</h1>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="space-y-8">
          {/* 포트폴리오 현황 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                포트폴리오 현황 (실제 DB 데이터)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">
                    ${totalValue.toLocaleString()}
                  </div>
                  <p className="text-muted-foreground text-sm">총 포트폴리오 가치</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary">
                    {holdings.length}
                  </div>
                  <p className="text-muted-foreground text-sm">보유 종목</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">
                    {strategies.length}
                  </div>
                  <p className="text-muted-foreground text-sm">사용가능 전략</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 보유 종목 선택 */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    보유 종목 선택 (실제 DB 데이터)
                  </CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    리밸런싱할 종목들을 선택하세요 ({holdings.length}개 종목)
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSelectAllHoldings}
                >
                  {isAllSelected ? '전체 해제' : '전체 선택'}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {holdings.map((holding) => {
                  const totalCost = holding.purchase_price * holding.quantity;
                  const profitLoss = holding.market_value - totalCost;
                  const profitLossPercent = (profitLoss / totalCost) * 100;

                  return (
                    <div
                      key={holding.holding_id}
                      className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                        selectedHoldings.includes(holding.holding_id) 
                          ? 'border-primary bg-primary/5' 
                          : 'border-border'
                      }`}
                      onClick={() => handleHoldingToggle(holding.holding_id)}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="font-semibold">{holding.symbol}</h3>
                          <p className="text-sm text-muted-foreground">{holding.name}</p>
                        </div>
                        <Checkbox 
                          checked={selectedHoldings.includes(holding.holding_id)}
                          onChange={() => handleHoldingToggle(holding.holding_id)}
                        />
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">보유량:</span>
                          <span>{holding.quantity.toLocaleString()}주</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">현재가:</span>
                          <span>${holding.current_price.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">시장가치:</span>
                          <span className="font-medium">${holding.market_value.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">비중:</span>
                          <span className="font-medium">{holding.weight.toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">손익:</span>
                          <span className={profitLoss >= 0 ? 'text-green-600' : 'text-red-600'}>
                            ${profitLoss.toFixed(2)} ({profitLossPercent >= 0 ? '+' : ''}{profitLossPercent.toFixed(1)}%)
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
              {selectedHoldings.length > 0 && (
                <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                  <p className="text-sm font-medium">
                    선택된 종목: {selectedHoldings.length}개
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 리밸런싱 전략 선택 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                리밸런싱 전략 선택 (실제 DB 데이터)
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                적용할 리밸런싱 전략을 선택하세요 ({strategies.length}개 전략)
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {(showAllStrategies ? strategies : strategies.slice(0, 6)).map((strategy) => (
                  <div
                    key={strategy.strategy_id}
                    className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                      selectedStrategy === strategy.strategy_id 
                        ? 'border-primary bg-primary/5' 
                        : 'border-border'
                    }`}
                    onClick={() => handleStrategySelect(strategy.strategy_id)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold text-sm">{strategy.strategy_name}</h3>
                        <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                          {strategy.description}
                        </p>
                      </div>
                      <Checkbox 
                        checked={selectedStrategy === strategy.strategy_id}
                        onChange={() => handleStrategySelect(strategy.strategy_id)}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">예상 수익률:</span>
                        <span className="font-medium text-green-600">{strategy.expected_return.toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">위험도:</span>
                        <Badge variant={
                          strategy.risk_level === '높음' ? 'destructive' : 
                          strategy.risk_level === '중간' ? 'default' : 'secondary'
                        }>
                          {strategy.risk_level}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 text-center">
                <Button 
                  variant="outline" 
                  onClick={() => setShowAllStrategies(!showAllStrategies)}
                  className="flex items-center gap-2"
                >
                  {showAllStrategies ? (
                    <>
                      <ChevronUp className="h-4 w-4" />
                      전략 접기 (6개만 표시)
                    </>
                  ) : (
                    <>
                      <ChevronDown className="h-4 w-4" />
                      모든 전략 펼치기 ({strategies.length}개)
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* 실행 버튼 */}
          <div className="text-center">
            <Button 
              size="lg" 
              onClick={handleStartRebalancing}
              className="px-12 py-3"
              disabled={selectedHoldings.length === 0 || !selectedStrategy}
            >
              <Play className="h-5 w-5 mr-2" />
              리밸런싱 실행하기
            </Button>
            <p className="text-xs text-muted-foreground mt-2">
              {holdings.length}개 종목 • {strategies.length}개 전략 • ${totalValue.toLocaleString()} 포트폴리오
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Rebalancing;