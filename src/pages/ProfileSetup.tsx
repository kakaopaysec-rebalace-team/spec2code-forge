import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useNavigate } from "react-router-dom";
import { Upload, Link, FileText, ArrowLeft } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";

const ProfileSetup = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [investmentStyle, setInvestmentStyle] = useState("");
  const [investmentGoal, setInvestmentGoal] = useState("");
  const [investmentPeriod, setInvestmentPeriod] = useState("");
  const [portfolio, setPortfolio] = useState([{ stock: "", weight: "" }]);
  const [philosophyText, setPhilosophyText] = useState("");
  const [philosophyUrl, setPhilosophyUrl] = useState("");

  const addPortfolioRow = () => {
    setPortfolio([...portfolio, { stock: "", weight: "" }]);
  };

  const updatePortfolio = (index: number, field: string, value: string) => {
    const updated = [...portfolio];
    updated[index][field as keyof typeof updated[0]] = value;
    setPortfolio(updated);
  };

  const handleAnalyze = () => {
    if (!investmentStyle || !investmentGoal || !investmentPeriod) {
      toast({
        title: "입력 오류",
        description: "투자 프로필을 모두 입력해주세요.",
        variant: "destructive",
      });
      return;
    }

    toast({
      title: "분석 시작",
      description: "AI가 포트폴리오를 분석하고 있습니다...",
    });

    // Simulate API call
    setTimeout(() => {
      navigate('/results');
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
            <h1 className="text-2xl font-bold">투자 프로필 설정</h1>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="space-y-8">
          {/* Investment Profile */}
          <Card>
            <CardHeader>
              <CardTitle>투자 프로필</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <Label>투자 성향</Label>
                  <Select value={investmentStyle} onValueChange={setInvestmentStyle}>
                    <SelectTrigger>
                      <SelectValue placeholder="선택하세요" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="conservative">보수적</SelectItem>
                      <SelectItem value="moderate">중도</SelectItem>
                      <SelectItem value="aggressive">공격적</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>투자 목표</Label>
                  <Select value={investmentGoal} onValueChange={setInvestmentGoal}>
                    <SelectTrigger>
                      <SelectValue placeholder="선택하세요" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="retirement">은퇴 준비</SelectItem>
                      <SelectItem value="wealth">자산 증식</SelectItem>
                      <SelectItem value="income">배당 수익</SelectItem>
                      <SelectItem value="growth">성장 투자</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>투자 기간</Label>
                  <Select value={investmentPeriod} onValueChange={setInvestmentPeriod}>
                    <SelectTrigger>
                      <SelectValue placeholder="선택하세요" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="short">1년 이하</SelectItem>
                      <SelectItem value="medium">1-5년</SelectItem>
                      <SelectItem value="long">5년 이상</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Current Portfolio */}
          <Card>
            <CardHeader>
              <CardTitle>현재 포트폴리오</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {portfolio.map((item, index) => (
                  <div key={index} className="grid md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>종목명</Label>
                      <Input
                        placeholder="예: 삼성전자"
                        value={item.stock}
                        onChange={(e) => updatePortfolio(index, 'stock', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>비중 (%)</Label>
                      <Input
                        type="number"
                        placeholder="예: 30"
                        value={item.weight}
                        onChange={(e) => updatePortfolio(index, 'weight', e.target.value)}
                      />
                    </div>
                  </div>
                ))}
                <Button variant="outline" onClick={addPortfolioRow}>
                  종목 추가
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Investment Philosophy Learning */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                나만의 투자 철학 학습시키기
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* File Upload */}
              <div className="space-y-2">
                <Label>문서 업로드</Label>
                <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center hover:border-primary/50 transition-colors cursor-pointer">
                  <Upload className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground mb-2">
                    PDF, TXT, DOCX 파일을 드래그하거나 클릭하여 업로드
                  </p>
                  <Button variant="outline" size="sm">
                    파일 선택
                  </Button>
                </div>
              </div>

              {/* URL Input */}
              <div className="space-y-2">
                <Label htmlFor="philosophy-url">웹사이트 URL</Label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Link className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="philosophy-url"
                      placeholder="투자 관련 블로그나 웹사이트 URL을 입력하세요"
                      value={philosophyUrl}
                      onChange={(e) => setPhilosophyUrl(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  <Button variant="outline">분석</Button>
                </div>
              </div>

              {/* Text Input */}
              <div className="space-y-2">
                <Label htmlFor="philosophy-text">투자 원칙 직접 입력</Label>
                <Textarea
                  id="philosophy-text"
                  placeholder="본인만의 투자 철학, 원칙, 경험담을 자유롭게 입력해주세요..."
                  value={philosophyText}
                  onChange={(e) => setPhilosophyText(e.target.value)}
                  className="min-h-32"
                />
              </div>
            </CardContent>
          </Card>

          {/* Analyze Button */}
          <div className="text-center">
            <Button size="lg" onClick={handleAnalyze} className="px-12 py-3">
              전략 분석하기
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ProfileSetup;