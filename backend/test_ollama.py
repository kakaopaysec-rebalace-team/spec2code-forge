#!/usr/bin/env python3
"""
Ollama 연동 테스트 스크립트
"""
import requests
import json
from typing import Dict, Any

def test_ollama_connection():
    """Ollama 서비스 연결 테스트"""
    try:
        print("🔍 Ollama 서비스 연결 테스트...")
        
        # Health check
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama 서비스 정상 - {len(models)}개 모델 설치됨")
            for model in models:
                name = model.get('name', 'Unknown')
                size = model.get('size', 0)
                print(f"   📦 {name} ({size//1000000}MB)")
            return True
        else:
            print(f"❌ Ollama 서비스 응답 오류: {response.status_code}")
            print(f"   응답 내용: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Ollama 서비스에 연결할 수 없습니다")
        print("   해결책:")
        print("   1. systemctl start ollama")
        print("   2. ollama serve")
        print("   3. 포트 11434 확인: ss -tlnp | grep 11434")
        return False
    except requests.exceptions.Timeout:
        print("❌ Ollama 서비스 응답 시간 초과")
        print("   서비스가 시작 중이거나 과부하 상태일 수 있습니다")
        return False
    except Exception as e:
        print(f"❌ Ollama 서비스 연결 실패: {e}")
        return False

def test_ollama_generation():
    """Ollama AI 생성 테스트"""
    try:
        print("\n🤖 Ollama AI 생성 테스트...")
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.1:8b",
                "prompt": "안녕하세요. 간단한 투자 조언을 한 줄로 해주세요.",
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "max_tokens": 100
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("response", "")
            print(f"✅ AI 응답 성공: {ai_response[:100]}...")
            return True
        else:
            print(f"❌ AI 생성 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ AI 생성 테스트 실패: {e}")
        return False

def test_python_ollama_package():
    """Python ollama 패키지 테스트"""
    try:
        print("\n📦 Python ollama 패키지 테스트...")
        import ollama
        print("✅ ollama 패키지 import 성공")
        return True
    except ImportError:
        print("❌ ollama 패키지를 찾을 수 없습니다. 설치 필요:")
        print("   pip install ollama")
        return False
    except Exception as e:
        print(f"❌ ollama 패키지 오류: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Ollama 종합 테스트 시작\n")
    
    # 테스트 실행
    tests = [
        test_python_ollama_package(),
        test_ollama_connection(), 
        test_ollama_generation()
    ]
    
    # 결과 요약
    passed = sum(tests)
    total = len(tests)
    
    print(f"\n📊 테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 테스트 통과! Ollama가 정상적으로 작동합니다.")
    else:
        print("⚠️  일부 테스트 실패. 위의 오류 메시지를 확인하세요.")