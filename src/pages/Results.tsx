import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, TrendingUp, TrendingDown } from "lucide-react";
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const Results = () => {
  const navigate = useNavigate();

  // Mock data for charts
  const currentPortfolio = [
    { name: 'Apple (AAPL)', value: 35, color: '#0088FE' },
    { name: 'Microsoft (MSFT)', value: 25, color: '#00C49F' },
    { name: 'Google (GOOGL)', value: 20, color: '#FFBB28' },
    { name: 'Amazon (AMZN)', value: 10, color: '#FF8042' },
    { name: '기타', value: 10, color: '#8884D8' },
  ];

  const recommendedPortfolio = [
    { name: 'Apple (AAPL)', value: 25, color: '#0088FE' },
    { name: 'Microsoft (MSFT)', value: 20, color: '#00C49F' },
    { name: 'NVIDIA (NVDA)', value: 18, color: '#FFBB28' },
    { name: 'Google (GOOGL)', value: 15, color: '#FF8042' },
    { name: 'Tesla (TSLA)', value: 12, color: '#8884D8' },
    { name: '기타', value: 10, color: '#82CA9D' },
  ];

  const performanceData = [
    { month: '2023-01', user: 100, ai: 100, benchmark: 100 },
    { month: '2023-03', user: 105, ai: 108, benchmark: 103 },
    { month: '2023-06', user: 98, ai: 115, benchmark: 107 },
    { month: '2023-09', user: 110, ai: 125, benchmark: 112 },
    { month: '2023-12', user: 115, ai: 135, benchmark: 118 },
    { month: '2024-03', user: 108, ai: 140, benchmark: 120 },
    { month: '2024-06', user: 120, ai: 152, benchmark: 125 },
    { month: '2024-09', user: 118, ai: 158, benchmark: 130 },
  ];

  const trades = [
    { action: '매수', stock: 'NVIDIA (NVDA)', quantity: 15, price: '$850.00', impact: '+18%' },
    { action: '매수', stock: 'Tesla (TSLA)', quantity: 20, price: '$240.00', impact: '+12%' },
    { action: '매도', stock: 'Apple (AAPL)', quantity: 25, price: '$190.00', impact: '-10%' },
    { action: '매도', stock: 'Amazon (AMZN)', quantity: 30, price: '$145.00', impact: '-10%' },
    { action: '리밸런싱', stock: 'Microsoft (MSFT)', quantity: 10, price: '$420.00', impact: '-5%' },
  ];

  const metrics = [
    { label: '예상 연간 수익률', current: '12.5%', recommended: '18.7%', better: true },
    { label: '최대 낙폭 (MDD)', current: '-15.2%', recommended: '-12.8%', better: true },
    { label: '변동성', current: '22.1%', recommended: '19.4%', better: true },
    { label: '샤프 비율', current: '0.56', recommended: '0.78', better: true },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/profile')}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <h1 className="text-2xl font-bold">AI 미국 주식 포트폴리오 분석 결과</h1>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="space-y-8">
          {/* Portfolio Comparison */}
          <div className="grid lg:grid-cols-2 gap-8">
            <Card>
              <CardHeader>
                <CardTitle>현재 포트폴리오</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={currentPortfolio}
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      dataKey="value"
                    >
                      {currentPortfolio.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => `${value}%`} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>AI 추천 포트폴리오</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={recommendedPortfolio}
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      dataKey="value"
                    >
                      {recommendedPortfolio.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => `${value}%`} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* AI Strategy Explanation */}
          <Card>
            <CardHeader>
              <CardTitle>AI 전략 설명</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground leading-relaxed">
                분석 결과, 현재 포트폴리오는 전통적인 빅테크 기업에 과도하게 집중되어 있습니다. 
                AI는 급성장하는 AI/반도체 섹터(NVIDIA, Tesla) 비중 확대와 함께 기존 보유 종목의 
                적정 리밸런싱을 제안합니다. 이를 통해 연간 수익률 6.2%p 개선과 동시에 
                AI 혁명의 수혜를 받을 수 있는 포트폴리오로 전환할 수 있습니다.
              </p>
            </CardContent>
          </Card>

          {/* Trading Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle>매매 제안</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3">구분</th>
                      <th className="text-left p-3">종목</th>
                      <th className="text-left p-3">수량</th>
                      <th className="text-left p-3">가격</th>
                      <th className="text-left p-3">비중 변화</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades.map((trade, index) => (
                      <tr key={index} className="border-b">
                        <td className="p-3">
                          <span className={`px-2 py-1 rounded text-sm ${
                            trade.action === '매수' 
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                              : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                          }`}>
                            {trade.action}
                          </span>
                        </td>
                        <td className="p-3 font-medium">{trade.stock}</td>
                        <td className="p-3">{trade.quantity}주</td>
                        <td className="p-3">{trade.price}</td>
                        <td className="p-3">
                          <span className={`flex items-center gap-1 ${
                            trade.action === '매수' ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {trade.action === '매수' ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                            {trade.impact}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Performance Simulation */}
          <Card>
            <CardHeader>
              <CardTitle>시뮬레이션 분석</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value: number) => [`${value.toFixed(1)}%`, '']} />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="user" 
                    stroke="#FF8042" 
                    strokeWidth={2}
                    name="현재 포트폴리오"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="ai" 
                    stroke="#00C49F" 
                    strokeWidth={2}
                    name="AI 추천 전략"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="benchmark" 
                    stroke="#8884D8" 
                    strokeWidth={2}
                    name="S&P 500"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Performance Metrics */}
          <Card>
            <CardHeader>
              <CardTitle>주요 성과 지표</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                {metrics.map((metric, index) => (
                  <div key={index} className="text-center p-4 border rounded-lg">
                    <h3 className="text-sm text-muted-foreground mb-2">{metric.label}</h3>
                    <div className="space-y-1">
                      <div className="text-sm text-muted-foreground">현재: {metric.current}</div>
                      <div className={`text-lg font-bold ${metric.better ? 'text-green-600' : 'text-red-600'}`}>
                        AI: {metric.recommended}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex gap-4 justify-center">
            <Button variant="outline" onClick={() => navigate('/profile')}>
              다시 분석하기
            </Button>
            <Button size="lg">
              전략 적용하기
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Results;