import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { TrendingUp, BarChart3, Target, Shield } from "lucide-react";

const Index = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-8 w-8 text-primary" />
            <h1 className="text-2xl font-bold">AI 자산 리밸런싱 시스템</h1>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <h2 className="text-5xl font-bold mb-6 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            나만의 투자 철학을<br />AI와 함께 완성하세요
          </h2>
          <p className="text-xl text-muted-foreground mb-12 max-w-2xl mx-auto">
            복잡한 투자 분석을 단순화하여, AI가 제안하는 최적의 리밸런싱 전략을 
            한눈에 이해하고 신뢰할 수 있는 시뮬레이션 결과를 확인하세요.
          </p>
          
          <Button 
            size="lg" 
            className="text-lg px-8 py-6 mb-16"
            onClick={() => navigate('/profile')}
          >
            나의 전략 분석하기
          </Button>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-8 mt-16">
            <div className="text-center p-6 rounded-lg border bg-card">
              <BarChart3 className="h-12 w-12 text-primary mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">데이터 기반 분석</h3>
              <p className="text-muted-foreground">
                과거 데이터를 바탕으로 한 정확한 시뮬레이션과 성과 분석
              </p>
            </div>
            <div className="text-center p-6 rounded-lg border bg-card">
              <Target className="h-12 w-12 text-primary mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">개인화된 전략</h3>
              <p className="text-muted-foreground">
                투자 성향과 목표에 맞춘 AI 맞춤형 포트폴리오 제안
              </p>
            </div>
            <div className="text-center p-6 rounded-lg border bg-card">
              <Shield className="h-12 w-12 text-primary mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">리스크 관리</h3>
              <p className="text-muted-foreground">
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
