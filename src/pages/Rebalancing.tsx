import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, TrendingUp, DollarSign, Target, BarChart3, Play } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const Rebalancing = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  
  // 보유 종목 데이터
  const [holdings] = useState([
    {
      id: "AAPL",
      name: "Apple Inc.",
      symbol: "AAPL",
      currentValue: 125000,
      currentWeight: 25.0,
      shares: 120,
      currentPrice: 185.50,
      selected: false
    },
    {
      id: "GOOGL",
      name: "Alphabet Inc.",
      symbol: "GOOGL",
      currentValue: 100000,
      currentWeight: 20.0,
      shares: 75,
      currentPrice: 142.30,
      selected: false
    },
    {
      id: "MSFT",
      name: "Microsoft Corporation",
      symbol: "MSFT",
      currentValue: 87500,
      currentWeight: 17.5,
      shares: 65,
      currentPrice: 378.85,
      selected: false
    },
    {
      id: "AMZN",
      name: "Amazon.com Inc.",
      symbol: "AMZN",
      currentValue: 75000,
      currentWeight: 15.0,
      shares: 50,
      currentPrice: 155.20,
      selected: false
    },
    {
      id: "TSLA",
      name: "Tesla Inc.",
      symbol: "TSLA",
      currentValue: 62500,
      currentWeight: 12.5,
      shares: 35,
      currentPrice: 248.42,
      selected: false
    },
    {
      id: "NVDA",
      name: "NVIDIA Corporation",
      symbol: "NVDA",
      currentValue: 50000,
      currentWeight: 10.0,
      shares: 25,
      currentPrice: 875.30,
      selected: false
    }
  ]);

  // 리밸런싱 전략 목록
  const [strategies] = useState([
    {
      id: "growth",
      name: "성장형 포트폴리오",
      description: "기술주 중심의 고성장 전략",
      targetAllocation: {
        "AAPL": 30,
        "GOOGL": 25,
        "MSFT": 20,
        "NVDA": 15,
        "TSLA": 10
      },
      expectedReturn: "24.5%",
      risk: "높음",
      selected: false
    },
    {
      id: "balanced",
      name: "균형형 포트폴리오",
      description: "안정성과 성장성의 균형",
      targetAllocation: {
        "AAPL": 25,
        "GOOGL": 20,
        "MSFT": 25,
        "AMZN": 20,
        "TSLA": 10
      },
      expectedReturn: "18.2%",
      risk: "중간",
      selected: false
    },
    {
      id: "conservative",
      name: "안정형 포트폴리오",
      description: "배당과 안정성 중심",
      targetAllocation: {
        "AAPL": 35,
        "MSFT": 30,
        "GOOGL": 20,
        "AMZN": 15
      },
      expectedReturn: "14.8%",
      risk: "낮음",
      selected: false
    }
  ]);

  const [selectedHoldings, setSelectedHoldings] = useState<string[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string>("");

  const totalPortfolioValue = holdings.reduce((sum, holding) => sum + holding.currentValue, 0);

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

    // 시뮬레이션
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <h1 className="text-2xl font-bold">리밸런싱 시작</h1>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="space-y-8">
          {/* Portfolio Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                포트폴리오 현황
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center">
                <div className="text-3xl font-bold text-primary mb-2">
                  ${totalPortfolioValue.toLocaleString()}
                </div>
                <p className="text-muted-foreground">총 포트폴리오 가치</p>
              </div>
            </CardContent>
          </Card>

          {/* Holdings Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                보유 종목 선택
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                리밸런싱할 종목들을 선택하세요
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {holdings.map((holding) => (
                  <div
                    key={holding.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                      selectedHoldings.includes(holding.id) 
                        ? 'border-primary bg-primary/5' 
                        : 'border-border'
                    }`}
                    onClick={() => handleHoldingToggle(holding.id)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold">{holding.symbol}</h3>
                        <p className="text-sm text-muted-foreground">{holding.name}</p>
                      </div>
                      <Checkbox 
                        checked={selectedHoldings.includes(holding.id)}
                        onChange={() => handleHoldingToggle(holding.id)}
                      />
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">보유량:</span>
                        <span>{holding.shares}주</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">현재가:</span>
                        <span>${holding.currentPrice}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">평가액:</span>
                        <span className="font-medium">${holding.currentValue.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">비중:</span>
                        <span className="font-medium">{holding.currentWeight}%</span>
                      </div>
                    </div>
                  </div>
                ))}
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

          {/* Strategy Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                리밸런싱 전략 선택
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                적용할 리밸런싱 전략을 선택하세요
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-4">
                {strategies.map((strategy) => (
                  <div
                    key={strategy.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                      selectedStrategy === strategy.id 
                        ? 'border-primary bg-primary/5' 
                        : 'border-border'
                    }`}
                    onClick={() => handleStrategySelect(strategy.id)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold">{strategy.name}</h3>
                        <p className="text-sm text-muted-foreground mt-1">
                          {strategy.description}
                        </p>
                      </div>
                      <Checkbox 
                        checked={selectedStrategy === strategy.id}
                        onChange={() => handleStrategySelect(strategy.id)}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">예상 수익률:</span>
                        <span className="font-medium text-green-600">{strategy.expectedReturn}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">위험도:</span>
                        <Badge variant={
                          strategy.risk === '높음' ? 'destructive' : 
                          strategy.risk === '중간' ? 'default' : 'secondary'
                        }>
                          {strategy.risk}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Execute Button */}
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
          </div>
        </div>
      </main>
    </div>
  );
};

export default Rebalancing;