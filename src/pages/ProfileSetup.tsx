import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import { Loader2, TrendingUp, Building2, PieChart, Zap, BookOpen, Upload, Link, FileText, CheckCircle, AlertCircle } from "lucide-react";
import { getUserHoldings, getAllStrategies, uploadUserText, uploadUserFile, createStrategyFromAnalysis } from "@/lib/api";

const ProfileSetup = () => {
  const navigate = useNavigate();
  const [holdings, setHoldings] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalValue, setTotalValue] = useState(0);

  // Strategy learning states
  const [urlInput, setUrlInput] = useState("");
  const [memoInput, setMemoInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<{ type: string; message: string } | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  
  // Strategy saving states
  const [lastAnalysisResult, setLastAnalysisResult] = useState<any>(null);
  const [showStrategyForm, setShowStrategyForm] = useState(false);
  const [strategyName, setStrategyName] = useState("");
  const [strategyDescription, setStrategyDescription] = useState("");
  const [isSavingStrategy, setIsSavingStrategy] = useState(false);

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

  // Strategy learning handlers
  const handleUrlUpload = async () => {
    if (!urlInput.trim()) return;
    
    setIsUploading(true);
    try {
      const result = await uploadUserText('mock-user-001', urlInput, 'url');
      setUploadStatus({ type: 'success', message: 'URL이 성공적으로 분석되었습니다!' });
      setLastAnalysisResult(result.result);
      setShowStrategyForm(true);
      setUrlInput("");
    } catch (error) {
      setUploadStatus({ type: 'error', message: 'URL 분석에 실패했습니다.' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleMemoUpload = async () => {
    if (!memoInput.trim()) return;
    
    setIsUploading(true);
    try {
      const result = await uploadUserText('mock-user-001', memoInput, 'text');
      setUploadStatus({ type: 'success', message: '투자 메모가 성공적으로 분석되었습니다!' });
      setLastAnalysisResult(result.result);
      setShowStrategyForm(true);
      setMemoInput("");
    } catch (error) {
      setUploadStatus({ type: 'error', message: '메모 분석에 실패했습니다.' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;
    
    setIsUploading(true);
    try {
      const result = await uploadUserFile('mock-user-001', selectedFile);
      setUploadStatus({ type: 'success', message: `파일 "${selectedFile.name}"이 성공적으로 분석되었습니다!` });
      setLastAnalysisResult(result.result);
      setShowStrategyForm(true);
      setSelectedFile(null);
    } catch (error) {
      setUploadStatus({ type: 'error', message: '파일 분석에 실패했습니다.' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleStrategySave = async () => {
    if (!strategyName.trim() || !lastAnalysisResult) return;
    
    setIsSavingStrategy(true);
    try {
      const result = await createStrategyFromAnalysis(
        'mock-user-001',
        strategyName,
        lastAnalysisResult,
        strategyDescription
      );
      
      setUploadStatus({ type: 'success', message: `'${strategyName}' 전략이 성공적으로 저장되었습니다!` });
      setShowStrategyForm(false);
      setStrategyName("");
      setStrategyDescription("");
      setLastAnalysisResult(null);
      
      // 전략 목록 새로고침
      const strategiesResponse = await getAllStrategies();
      setStrategies(strategiesResponse.strategies || []);
      
    } catch (error) {
      setUploadStatus({ type: 'error', message: '전략 저장에 실패했습니다.' });
    } finally {
      setIsSavingStrategy(false);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const allowedTypes = ['.pdf', '.txt', '.md'];
      const fileExt = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
      if (allowedTypes.includes(fileExt)) {
        setSelectedFile(file);
        setUploadStatus(null);
      } else {
        setUploadStatus({ type: 'error', message: '지원하지 않는 파일 형식입니다. PDF, TXT, MD 파일만 업로드 가능합니다.' });
      }
    }
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
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-6 sm:h-8 w-6 sm:w-8 text-primary" />
              <h1 className="text-xl sm:text-2xl font-bold">리밸런싱 시작하기</h1>
            </div>
            <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
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
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                <div className="text-center p-4 bg-muted rounded-lg">
                  <div className="text-2xl sm:text-3xl font-bold text-green-600">
                    ${totalValue.toLocaleString()}
                  </div>
                  <div className="text-xs sm:text-sm text-muted-foreground">총 포트폴리오 가치</div>
                </div>
                <div className="text-center p-4 bg-muted rounded-lg">
                  <div className="text-2xl sm:text-3xl font-bold">{holdings.length}</div>
                  <div className="text-xs sm:text-sm text-muted-foreground">보유 종목</div>
                </div>
                <div className="text-center p-4 bg-muted rounded-lg">
                  <div className="text-2xl sm:text-3xl font-bold">
                    {holdings.filter(h => h.market_value > h.purchase_price * h.quantity).length}
                  </div>
                  <div className="text-xs sm:text-sm text-muted-foreground">수익 종목</div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
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
                      
                      <div className="space-y-2 text-xs sm:text-sm">
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">보유량:</span>
                          <span className="font-medium">{holding.quantity.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">현재가:</span>
                          <span className="font-medium">${holding.current_price.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">시장가치:</span>
                          <span className="font-semibold">${holding.market_value.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between items-start">
                          <span className="text-muted-foreground">손익:</span>
                          <div className={`font-medium text-right ${profitLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            <div>${profitLoss.toFixed(2)}</div>
                            <div className="text-xs">({profitLossPercent >= 0 ? '+' : ''}{profitLossPercent.toFixed(1)}%)</div>
                          </div>
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
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-6 text-sm">
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-xs sm:text-sm text-muted-foreground">평균 수익률</div>
                  <div className="font-semibold text-lg sm:text-xl text-green-600">
                    {strategies.length > 0 ? (strategies.reduce((sum, s) => sum + s.expected_return, 0) / strategies.length).toFixed(1) : '0.0'}%
                  </div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-xs sm:text-sm text-muted-foreground">전체 전략 수</div>
                  <div className="font-semibold text-lg sm:text-xl">{strategies.length}개</div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-xs sm:text-sm text-muted-foreground">최고 수익률</div>
                  <div className="font-semibold text-lg sm:text-xl text-green-600">
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
                <Button variant="outline" className="w-full sm:w-auto" onClick={() => navigate('/strategies')}>
                  모든 전략 상세 비교
                </Button>
                <p className="text-xs text-muted-foreground">
                  총 {strategies.length}개 전략 사용 가능 • 실시간 DB 조회
                </p>
              </div>
            </CardContent>
          </Card>

          {/* 맞춤 전략 학습 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                맞춤 전략 학습
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                투자 문서, 웹 URL, 또는 직접 입력한 투자 철학을 분석하여 나만의 전략을 생성하세요
              </p>
            </CardHeader>
            <CardContent className="mobile-padding">
              <Tabs defaultValue="url" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="url" className="flex items-center gap-2">
                    <Link className="h-4 w-4" />
                    <span className="hidden sm:inline">웹 URL</span>
                    <span className="sm:hidden">URL</span>
                  </TabsTrigger>
                  <TabsTrigger value="file" className="flex items-center gap-2">
                    <Upload className="h-4 w-4" />
                    <span className="hidden sm:inline">파일 업로드</span>
                    <span className="sm:hidden">파일</span>
                  </TabsTrigger>
                  <TabsTrigger value="memo" className="flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    <span className="hidden sm:inline">직접 입력</span>
                    <span className="sm:hidden">메모</span>
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="url" className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="url-input">투자 관련 웹페이지 URL</Label>
                    <Input
                      id="url-input"
                      type="url"
                      placeholder="https://example.com/investment-strategy"
                      value={urlInput}
                      onChange={(e) => setUrlInput(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      투자 전략, 포트폴리오 분석 글, 전문가 의견 등의 웹페이지를 분석합니다
                    </p>
                  </div>
                  <Button 
                    onClick={handleUrlUpload} 
                    disabled={!urlInput.trim() || isUploading}
                    className="w-full sm:w-auto"
                  >
                    {isUploading ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Link className="mr-2 h-4 w-4" />
                    )}
                    URL 분석하기
                  </Button>
                </TabsContent>

                <TabsContent value="file" className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="file-input">투자 문서 업로드</Label>
                    <Input
                      id="file-input"
                      type="file"
                      accept=".pdf,.txt,.md"
                      onChange={handleFileChange}
                    />
                    <p className="text-xs text-muted-foreground">
                      PDF, TXT, MD 파일 지원 (투자 보고서, 전략 문서, 메모 등)
                    </p>
                    {selectedFile && (
                      <div className="flex items-center gap-2 p-2 bg-muted rounded-md">
                        <FileText className="h-4 w-4" />
                        <span className="text-sm">{selectedFile.name}</span>
                      </div>
                    )}
                  </div>
                  <Button 
                    onClick={handleFileUpload} 
                    disabled={!selectedFile || isUploading}
                    className="w-full sm:w-auto"
                  >
                    {isUploading ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Upload className="mr-2 h-4 w-4" />
                    )}
                    파일 분석하기
                  </Button>
                </TabsContent>

                <TabsContent value="memo" className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="memo-input">투자 철학 & 전략 메모</Label>
                    <Textarea
                      id="memo-input"
                      placeholder="나만의 투자 철학과 전략을 자유롭게 작성해주세요...
                      
예시:
- 장기 가치투자를 선호합니다
- 배당주 중심의 안정적인 수익을 추구합니다  
- ESG 투자에 관심이 있습니다
- 기술주 비중을 늘리고 싶습니다"
                      className="min-h-[120px]"
                      value={memoInput}
                      onChange={(e) => setMemoInput(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      투자 선호도, 위험 성향, 관심 섹터 등을 구체적으로 작성해주세요
                    </p>
                  </div>
                  <Button 
                    onClick={handleMemoUpload} 
                    disabled={!memoInput.trim() || isUploading}
                    className="w-full sm:w-auto"
                  >
                    {isUploading ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <FileText className="mr-2 h-4 w-4" />
                    )}
                    메모 분석하기
                  </Button>
                </TabsContent>

                {uploadStatus && (
                  <div className={`mt-4 p-3 rounded-md flex items-center gap-2 ${
                    uploadStatus.type === 'success' 
                      ? 'bg-green-50 text-green-800 border border-green-200' 
                      : 'bg-red-50 text-red-800 border border-red-200'
                  }`}>
                    {uploadStatus.type === 'success' ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      <AlertCircle className="h-4 w-4" />
                    )}
                    <span className="text-sm">{uploadStatus.message}</span>
                  </div>
                )}

                {/* Strategy Save Form */}
                {showStrategyForm && lastAnalysisResult && (
                  <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <BookOpen className="h-5 w-5 text-blue-600" />
                      분석 결과를 전략으로 저장
                    </h4>
                    
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="strategyName">전략 이름 *</Label>
                        <Input
                          id="strategyName"
                          value={strategyName}
                          onChange={(e) => setStrategyName(e.target.value)}
                          placeholder="예: 나만의 보수적 전략"
                          className="mt-1"
                        />
                      </div>
                      
                      <div>
                        <Label htmlFor="strategyDescription">전략 설명 (선택)</Label>
                        <Textarea
                          id="strategyDescription"
                          value={strategyDescription}
                          onChange={(e) => setStrategyDescription(e.target.value)}
                          placeholder="이 전략의 특징이나 목표를 간단히 설명해주세요..."
                          className="mt-1"
                          rows={3}
                        />
                      </div>

                      {/* Analysis Preview */}
                      {lastAnalysisResult?.investment_insights && (
                        <div className="bg-gray-50 p-3 rounded-md">
                          <h5 className="font-medium mb-2">분석된 투자 성향</h5>
                          <div className="text-sm space-y-1">
                            <p><strong>투자 성향:</strong> {lastAnalysisResult.investment_insights.investment_style || '정보 없음'}</p>
                            <p><strong>투자 목표:</strong> {lastAnalysisResult.investment_insights.investment_goal || '정보 없음'}</p>
                            <p><strong>리스크 점수:</strong> {lastAnalysisResult.investment_insights.risk_score || '정보 없음'}/10</p>
                          </div>
                        </div>
                      )}
                      
                      <div className="flex gap-2">
                        <Button
                          onClick={handleStrategySave}
                          disabled={!strategyName.trim() || isSavingStrategy}
                          className="flex-1"
                        >
                          {isSavingStrategy ? (
                            <>
                              <Loader2 className="h-4 w-4 animate-spin mr-2" />
                              저장 중...
                            </>
                          ) : (
                            <>
                              <CheckCircle className="h-4 w-4 mr-2" />
                              전략 저장
                            </>
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => {
                            setShowStrategyForm(false);
                            setStrategyName("");
                            setStrategyDescription("");
                          }}
                        >
                          취소
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </Tabs>
            </CardContent>
          </Card>

          {/* 분석 시작 버튼 */}
          <div className="text-center">
            <Button 
              size="lg" 
              onClick={handleAnalyze} 
              className="w-full sm:w-auto px-8 sm:px-12 py-3"
              disabled={holdings.length === 0}
            >
              <Building2 className="mr-2 h-4 sm:h-5 w-4 sm:w-5" />
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