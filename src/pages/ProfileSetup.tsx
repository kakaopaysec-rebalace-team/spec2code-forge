import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useNavigate } from "react-router-dom";
import { Upload, Link, FileText, ArrowLeft, Globe, PenTool } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const ProfileSetup = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [investmentStyle, setInvestmentStyle] = useState("");
  const [investmentGoal, setInvestmentGoal] = useState("");
  const [investmentPeriod, setInvestmentPeriod] = useState("");
  const [learningMethod, setLearningMethod] = useState("");
  const [philosophyText, setPhilosophyText] = useState("");
  const [philosophyUrl, setPhilosophyUrl] = useState("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      toast({
        title: "파일 업로드 완료",
        description: `${file.name} 파일이 업로드되었습니다.`,
      });
    }
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

    if (!learningMethod) {
      toast({
        title: "학습 방법 선택",
        description: "투자 철학 학습 방법을 선택해주세요.",
        variant: "destructive",
      });
      return;
    }

    // Validate based on selected method
    if (learningMethod === "document" && !uploadedFile) {
      toast({
        title: "파일 업로드",
        description: "분석할 문서를 업로드해주세요.",
        variant: "destructive",
      });
      return;
    }

    if (learningMethod === "url" && !philosophyUrl) {
      toast({
        title: "URL 입력",
        description: "분석할 웹사이트 URL을 입력해주세요.",
        variant: "destructive",
      });
      return;
    }

    if (learningMethod === "text" && !philosophyText) {
      toast({
        title: "투자 원칙 입력",
        description: "투자 원칙을 입력해주세요.",
        variant: "destructive",
      });
      return;
    }

    toast({
      title: "분석 시작",
      description: "AI가 데이터를 분석하고 포트폴리오를 생성하고 있습니다...",
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
            <h1 className="text-2xl font-bold">AI 투자 전략 분석</h1>
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

          {/* Learning Method Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                투자 철학 학습 방법 선택
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <RadioGroup value={learningMethod} onValueChange={setLearningMethod}>
                <div className="grid md:grid-cols-3 gap-4">
                  {/* Document Upload Option */}
                  <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="document" id="document" />
                      <Label htmlFor="document" className="flex items-center gap-2 font-medium">
                        <Upload className="h-4 w-4" />
                        문서 업로드
                      </Label>
                    </div>
                    {learningMethod === "document" && (
                      <div className="space-y-2">
                        <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-6 text-center hover:border-primary/50 transition-colors">
                          <Upload className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                          <p className="text-sm text-muted-foreground mb-2">
                            PDF, TXT, DOCX 파일 업로드
                          </p>
                          <Input
                            type="file"
                            accept=".pdf,.txt,.docx"
                            onChange={handleFileUpload}
                            className="hidden"
                            id="file-upload"
                          />
                          <Label htmlFor="file-upload" className="cursor-pointer">
                            <Button variant="outline" size="sm" type="button">
                              파일 선택
                            </Button>
                          </Label>
                          {uploadedFile && (
                            <p className="text-xs text-primary mt-2">
                              {uploadedFile.name}
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* URL Option */}
                  <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="url" id="url" />
                      <Label htmlFor="url" className="flex items-center gap-2 font-medium">
                        <Globe className="h-4 w-4" />
                        웹사이트 URL
                      </Label>
                    </div>
                    {learningMethod === "url" && (
                      <div className="space-y-2">
                        <div className="relative">
                          <Link className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            placeholder="투자 관련 웹사이트 URL"
                            value={philosophyUrl}
                            onChange={(e) => setPhilosophyUrl(e.target.value)}
                            className="pl-10"
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Direct Input Option */}
                  <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="text" id="text" />
                      <Label htmlFor="text" className="flex items-center gap-2 font-medium">
                        <PenTool className="h-4 w-4" />
                        직접 입력
                      </Label>
                    </div>
                    {learningMethod === "text" && (
                      <div className="space-y-2">
                        <Textarea
                          placeholder="투자 철학, 원칙, 경험담을 입력하세요..."
                          value={philosophyText}
                          onChange={(e) => setPhilosophyText(e.target.value)}
                          className="min-h-24"
                        />
                      </div>
                    )}
                  </div>
                </div>
              </RadioGroup>

              <div className="text-sm text-muted-foreground bg-muted/50 p-4 rounded-lg">
                <p className="font-medium mb-2">AI가 다음 정보를 분석합니다:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>업로드된 문서나 URL에서 포트폴리오 정보 자동 추출</li>
                  <li>투자 성향 및 철학 분석</li>
                  <li>개인화된 리밸런싱 전략 생성</li>
                </ul>
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