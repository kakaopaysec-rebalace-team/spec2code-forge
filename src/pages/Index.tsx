import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useNavigate } from "react-router-dom";
import { TrendingUp, BarChart3, Target, Shield, Database, CheckCircle, AlertCircle } from "lucide-react";
import { useState, useEffect } from "react";
import { healthCheck, getAllStrategies, getUserHoldings } from "@/lib/api";

const Index = () => {
  const navigate = useNavigate();
  const [systemStatus, setSystemStatus] = useState({
    api: 'checking',
    strategies: 0,
    holdings: 0,
    lastCheck: null as Date | null
  });

  useEffect(() => {
    const checkSystemStatus = async () => {
      try {
        console.log('Index: Checking system status...');
        
        // Check API health
        await healthCheck();
        
        // Check strategies count
        const strategiesResponse = await getAllStrategies();
        
        // Check holdings count
        const holdingsResponse = await getUserHoldings('mock-user-001');
        
        setSystemStatus({
          api: 'healthy',
          strategies: strategiesResponse.strategies.length,
          holdings: holdingsResponse.holdings.length,
          lastCheck: new Date()
        });
        
        console.log('Index: System status check complete', {
          strategies: strategiesResponse.strategies.length,
          holdings: holdingsResponse.holdings.length
        });
        
      } catch (error) {
        console.error('Index: System status check failed:', error);
        setSystemStatus(prev => ({
          ...prev,
          api: 'error',
          lastCheck: new Date()
        }));
      }
    };

    checkSystemStatus();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-6 w-6 sm:h-8 sm:w-8 text-primary" />
              <h1 className="text-lg sm:text-2xl font-bold leading-tight">
                AI 해외 주식 리밸런싱 시스템
              </h1>
            </div>
            
            {/* System Status */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4" />
                <span className="text-sm">DB 상태:</span>
                {systemStatus.api === 'checking' && (
                  <Badge variant="outline" className="text-yellow-600 text-xs">
                    확인 중...
                  </Badge>
                )}
                {systemStatus.api === 'healthy' && (
                  <Badge variant="default" className="bg-green-600 text-xs">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    정상
                  </Badge>
                )}
                {systemStatus.api === 'error' && (
                  <Badge variant="destructive" className="text-xs">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    오류
                  </Badge>
                )}
              </div>
              
              {systemStatus.api === 'healthy' && (
                <div className="text-xs text-muted-foreground">
                  전략: {systemStatus.strategies}개 • 종목: {systemStatus.holdings}개
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="container mx-auto px-4 py-8 sm:py-16">
        <div className="text-center max-w-4xl mx-auto">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 sm:mb-6 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent leading-tight">
            해외 주식 포트폴리오를<br className="hidden sm:block" />
            <span className="sm:hidden"> </span>AI와 함께 최적화하세요
          </h2>
          <p className="text-base sm:text-lg lg:text-xl text-muted-foreground mb-8 sm:mb-12 max-w-2xl mx-auto px-4">
            글로벌 최고 기업들로 구성된 해외 주식 포트폴리오를 AI가 분석하여
            최적의 리밸런싱 전략과 신뢰할 수 있는 시뮬레이션 결과를 제공합니다.
          </p>
          
          {/* Primary Action */}
          <div className="mb-6 sm:mb-8 px-4">
            <Button 
              size="lg" 
              className="w-full sm:w-auto text-base sm:text-lg px-6 sm:px-8 py-6 sm:py-8 bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 sm:min-w-[280px]"
              onClick={() => navigate('/rebalancing')}
            >
              <TrendingUp className="mr-2 sm:mr-3 h-4 w-4 sm:h-5 sm:w-5" />
              리밸런싱 시작
            </Button>
          </div>

          {/* Secondary Actions */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12 sm:mb-16 px-4">
            <Button 
              variant="outline"
              size="lg" 
              className="text-lg px-8 py-8 min-w-[280px] shadow-md hover:shadow-lg border-2 transform hover:scale-105 transition-all duration-200 bg-background/50 backdrop-blur-sm"
              onClick={() => navigate('/profile')}
            >
              리밸런싱 전략 생성
            </Button>
            <Button 
              variant="outline"
              size="lg" 
              className="text-lg px-8 py-8 min-w-[280px] shadow-md hover:shadow-lg border-2 transform hover:scale-105 transition-all duration-200 bg-background/50 backdrop-blur-sm"
              onClick={() => navigate('/strategies')}
            >
              리밸런싱 전략 비교
            </Button>
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8 mt-8 sm:mt-16 px-4">
            <div className="text-center p-4 sm:p-6 rounded-lg border bg-card shadow-sm">
              <BarChart3 className="h-10 w-10 sm:h-12 sm:w-12 text-primary mx-auto mb-3 sm:mb-4" />
              <h3 className="text-lg sm:text-xl font-semibold mb-2">데이터 기반 분석</h3>
              <p className="text-sm sm:text-base text-muted-foreground">
                과거 데이터를 바탕으로 한 정확한 시뮬레이션과 성과 분석
              </p>
            </div>
            <div className="text-center p-4 sm:p-6 rounded-lg border bg-card shadow-sm">
              <Target className="h-10 w-10 sm:h-12 sm:w-12 text-primary mx-auto mb-3 sm:mb-4" />
              <h3 className="text-lg sm:text-xl font-semibold mb-2">개인화된 전략</h3>
              <p className="text-sm sm:text-base text-muted-foreground">
                투자 성향과 목표에 맞춘 AI 맞춤형 포트폴리오 제안
              </p>
            </div>
            <div className="text-center p-4 sm:p-6 rounded-lg border bg-card shadow-sm sm:col-span-2 lg:col-span-1">
              <Shield className="h-10 w-10 sm:h-12 sm:w-12 text-primary mx-auto mb-3 sm:mb-4" />
              <h3 className="text-lg sm:text-xl font-semibold mb-2">리스크 관리</h3>
              <p className="text-sm sm:text-base text-muted-foreground">
                최대낙폭과 변동성을 고려한 안전한 투자 전략 수립
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
