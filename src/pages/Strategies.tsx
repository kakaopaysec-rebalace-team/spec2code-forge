import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, TrendingUp, Shield, Zap, DollarSign, Brain, Target } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

const Strategies = () => {
  const navigate = useNavigate();

  const strategies = [
    {
      id: 'growth',
      name: '성장형 전략',
      description: '고성장 기업에 집중 투자하여 장기적 자본 증식을 추구',
      icon: TrendingUp,
      color: 'rgb(34, 197, 94)', // green-500
      expectedReturn: '22.8%',
      volatility: '24.5%',
      maxDrawdown: '-18.3%',
      sharpe: '0.82',
      tags: ['고수익', '고변동성', '장기투자']
    },
    {
      id: 'value',
      name: '가치형 전략',
      description: '저평가된 우량 기업을 발굴하여 안정적 수익을 추구',
      icon: Shield,
      color: 'rgb(59, 130, 246)', // blue-500
      expectedReturn: '16.4%',
      volatility: '18.2%',
      maxDrawdown: '-12.7%',
      sharpe: '0.74',
      tags: ['안정성', '저변동성', '배당']
    },
    {
      id: 'dividend',
      name: '배당 중심 전략',
      description: '높은 배당 수익률을 제공하는 기업들로 구성된 포트폴리오',
      icon: DollarSign,
      color: 'rgb(168, 85, 247)', // purple-500
      expectedReturn: '14.2%',
      volatility: '15.8%',
      maxDrawdown: '-10.4%',
      sharpe: '0.68',
      tags: ['배당수익', '현금흐름', '안정성']
    },
    {
      id: 'tech',
      name: '기술주 집중 전략',
      description: '혁신 기술 기업들에 집중하여 디지털 전환 수혜를 추구',
      icon: Zap,
      color: 'rgb(249, 115, 22)', // orange-500
      expectedReturn: '26.7%',
      volatility: '28.9%',
      maxDrawdown: '-22.1%',
      sharpe: '0.85',
      tags: ['기술주', '혁신', '고성장']
    },
    {
      id: 'conservative',
      name: '안정형 전략',
      description: '위험을 최소화하면서 꾸준한 수익을 추구하는 보수적 접근',
      icon: Target,
      color: 'rgb(20, 184, 166)', // teal-500
      expectedReturn: '12.1%',
      volatility: '12.4%',
      maxDrawdown: '-7.8%',
      sharpe: '0.65',
      tags: ['저위험', '안정수익', '보수적']
    },
    {
      id: 'ai',
      name: 'AI 혁신 전략',
      description: 'AI와 머신러닝 기술을 활용한 차세대 투자 전략',
      icon: Brain,
      color: 'rgb(236, 72, 153)', // pink-500
      expectedReturn: '29.3%',
      volatility: '26.1%',
      maxDrawdown: '-19.7%',
      sharpe: '0.94',
      tags: ['AI', '머신러닝', '혁신기술']
    }
  ];

  // Performance simulation data for all strategies
  const performanceData = [
    { month: '2023-01', growth: 100, value: 100, dividend: 100, tech: 100, conservative: 100, ai: 100, sp500: 100 },
    { month: '2023-03', growth: 108, value: 104, dividend: 103, tech: 112, conservative: 102, ai: 115, sp500: 103 },
    { month: '2023-06', growth: 115, value: 108, dividend: 106, tech: 98, conservative: 104, ai: 128, sp500: 107 },
    { month: '2023-09', growth: 125, value: 112, dividend: 110, tech: 135, conservative: 106, ai: 142, sp500: 112 },
    { month: '2023-12', growth: 135, value: 118, dividend: 115, tech: 148, conservative: 108, ai: 158, sp500: 118 },
    { month: '2024-03', growth: 142, value: 122, dividend: 118, tech: 156, conservative: 110, ai: 165, sp500: 120 },
    { month: '2024-06', growth: 158, value: 128, dividend: 122, tech: 172, conservative: 112, ai: 185, sp500: 125 },
    { month: '2024-09', growth: 164, value: 132, dividend: 125, tech: 178, conservative: 114, ai: 195, sp500: 130 },
  ];

  // Risk-Return comparison data
  const riskReturnData = strategies.map(strategy => ({
    name: strategy.name,
    return: parseFloat(strategy.expectedReturn),
    risk: parseFloat(strategy.volatility),
    color: strategy.color
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
              const IconComponent = strategy.icon;
              return (
                <Card key={strategy.id} className="hover:shadow-lg transition-shadow cursor-pointer">
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div 
                        className="p-2 rounded-lg"
                        style={{ backgroundColor: `${strategy.color}20`, color: strategy.color }}
                      >
                        <IconComponent className="h-6 w-6" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{strategy.name}</CardTitle>
                        <div className="flex gap-1 mt-2">
                          {strategy.tags.map((tag) => (
                            <Badge key={tag} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
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
                        <div className="font-semibold text-green-600">{strategy.expectedReturn}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">변동성</div>
                        <div className="font-semibold">{strategy.volatility}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">최대 낙폭</div>
                        <div className="font-semibold text-red-600">{strategy.maxDrawdown}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">샤프 비율</div>
                        <div className="font-semibold">{strategy.sharpe}</div>
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
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={500}>
                <LineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value: number) => [`${(value - 100).toFixed(1)}%`, '']} />
                  <Legend />
                  <Line type="monotone" dataKey="growth" stroke="rgb(34, 197, 94)" strokeWidth={2} name="성장형 전략" />
                  <Line type="monotone" dataKey="value" stroke="rgb(59, 130, 246)" strokeWidth={2} name="가치형 전략" />
                  <Line type="monotone" dataKey="dividend" stroke="rgb(168, 85, 247)" strokeWidth={2} name="배당 중심 전략" />
                  <Line type="monotone" dataKey="tech" stroke="rgb(249, 115, 22)" strokeWidth={2} name="기술주 집중 전략" />
                  <Line type="monotone" dataKey="conservative" stroke="rgb(20, 184, 166)" strokeWidth={2} name="안정형 전략" />
                  <Line type="monotone" dataKey="ai" stroke="rgb(236, 72, 153)" strokeWidth={2} name="AI 혁신 전략" />
                  <Line type="monotone" dataKey="sp500" stroke="#8884D8" strokeWidth={2} strokeDasharray="5 5" name="S&P 500" />
                </LineChart>
              </ResponsiveContainer>
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

          {/* Strategy Selection */}
          <Card>
            <CardHeader>
              <CardTitle>전략 선택 가이드</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold mb-3">투자 성향별 추천</h3>
                  <div className="space-y-2 text-sm">
                    <div><span className="font-medium">공격적 투자자:</span> AI 혁신 전략, 기술주 집중 전략</div>
                    <div><span className="font-medium">균형 투자자:</span> 성장형 전략, 가치형 전략</div>
                    <div><span className="font-medium">보수적 투자자:</span> 안정형 전략, 배당 중심 전략</div>
                  </div>
                </div>
                <div>
                  <h3 className="font-semibold mb-3">투자 기간별 추천</h3>
                  <div className="space-y-2 text-sm">
                    <div><span className="font-medium">장기 (5년+):</span> 성장형, AI 혁신, 기술주 집중</div>
                    <div><span className="font-medium">중기 (2-5년):</span> 가치형, 배당 중심</div>
                    <div><span className="font-medium">단기 (1-2년):</span> 안정형, 배당 중심</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex gap-4 justify-center">
            <Button variant="outline" onClick={() => navigate('/profile')}>
              프로필 설정하기
            </Button>
            <Button size="lg" onClick={() => navigate('/results')}>
              맞춤 분석 받기
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Strategies;