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
          {/* Learning Method Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                투자 철학 학습 방법 선택
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-8">
              <RadioGroup value={learningMethod} onValueChange={setLearningMethod}>
                <div className="grid md:grid-cols-3 gap-6">
                  {/* Document Upload Option */}
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="document" id="document" />
                      <Label htmlFor="document" className="flex items-center gap-2 font-medium">
                        <Upload className="h-4 w-4" />
                        문서 업로드
                      </Label>
                    </div>
                  </div>

                  {/* URL Option */}
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="url" id="url" />
                      <Label htmlFor="url" className="flex items-center gap-2 font-medium">
                        <Globe className="h-4 w-4" />
                        웹사이트 URL
                      </Label>
                    </div>
                  </div>

                  {/* Direct Input Option */}
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="text" id="text" />
                      <Label htmlFor="text" className="flex items-center gap-2 font-medium">
                        <PenTool className="h-4 w-4" />
                        직접 입력
                      </Label>
                    </div>
                  </div>
                </div>

                {/* Large input areas based on selection */}
                {learningMethod === "document" && (
                  <div className="mt-8">
                    <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-12 text-center hover:border-primary/50 transition-colors">
                      <Upload className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                      <p className="text-lg text-muted-foreground mb-4">
                        PDF, TXT, DOCX 파일을 업로드하세요
                      </p>
                      <p className="text-sm text-muted-foreground/80 mb-6">
                        투자 관련 문서, 포트폴리오 정보, 투자 철학이 담긴 파일을 분석합니다
                      </p>
                      <Input
                        type="file"
                        accept=".pdf,.txt,.docx"
                        onChange={handleFileUpload}
                        className="hidden"
                        id="file-upload"
                      />
                      <Button 
                        variant="outline" 
                        size="lg" 
                        type="button" 
                        className="px-8 py-3"
                        onClick={() => document.getElementById('file-upload')?.click()}
                      >
                        파일 선택하기
                      </Button>
                      {uploadedFile && (
                        <div className="mt-4 p-4 bg-muted/50 rounded-lg">
                          <p className="text-sm font-medium text-primary">
                            업로드된 파일: {uploadedFile.name}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {learningMethod === "url" && (
                  <div className="mt-8">
                    <div className="space-y-4">
                      <div className="text-center mb-6">
                        <Globe className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                        <p className="text-lg font-medium mb-2">웹사이트 URL을 입력하세요</p>
                        <p className="text-sm text-muted-foreground">
                          투자 관련 블로그, 뉴스, 분석 자료가 담긴 웹사이트를 분석합니다
                        </p>
                      </div>
                      <div className="relative max-w-2xl mx-auto">
                        <Link className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                        <Input
                          placeholder="https://example.com/investment-analysis"
                          value={philosophyUrl}
                          onChange={(e) => setPhilosophyUrl(e.target.value)}
                          className="pl-12 py-4 text-lg"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {learningMethod === "text" && (
                  <div className="mt-8">
                    <div className="space-y-4">
                      <div className="text-center mb-6">
                        <PenTool className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                        <p className="text-lg font-medium mb-2">투자 철학을 직접 입력하세요</p>
                        <p className="text-sm text-muted-foreground">
                          개인의 투자 원칙, 경험담, 선호하는 투자 전략을 자세히 작성해주세요
                        </p>
                      </div>
                      <Textarea
                        placeholder="예시: 
• 장기 투자를 선호하며 배당주에 관심이 많습니다
• 기술주보다는 안정적인 가치주를 선호합니다
• 월 100만원씩 정기 적립 투자를 하고 있습니다
• 리스크 관리를 위해 분산투자를 중요하게 생각합니다

투자 철학, 원칙, 경험담을 자유롭게 작성해주세요..."
                        value={philosophyText}
                        onChange={(e) => setPhilosophyText(e.target.value)}
                        className="min-h-48 text-base leading-relaxed"
                      />
                    </div>
                  </div>
                )}
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