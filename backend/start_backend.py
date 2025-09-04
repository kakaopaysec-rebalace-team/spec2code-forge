#!/usr/bin/env python3
"""
AI Asset Rebalancing System - Backend Startup Script
자동화된 환경 설정 및 서버 시작 스크립트
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path
from typing import Optional, List
import signal
import psutil
import asyncio
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BackendManager:
    """백엔드 서버 관리 클래스"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent
        self.venv_path = self.base_dir / "venv"
        self.python_exe = self._get_python_executable()
        self.requirements_file = self.base_dir / "requirements.txt"
        self.env_file = self.base_dir / ".env"
        self.env_example_file = self.base_dir / ".env.example"
        self.logs_dir = self.base_dir / "logs"
        self.uploads_dir = self.base_dir / "uploads"
        self.process = None
        
    def _get_python_executable(self) -> Path:
        """가상환경의 Python 실행파일 경로 반환"""
        if os.name == 'nt':  # Windows
            return self.venv_path / "Scripts" / "python.exe"
        else:  # Unix/Linux/macOS
            return self.venv_path / "bin" / "python"
    
    def _get_pip_executable(self) -> Path:
        """가상환경의 pip 실행파일 경로 반환"""
        if os.name == 'nt':  # Windows
            return self.venv_path / "Scripts" / "pip.exe"
        else:  # Unix/Linux/macOS
            return self.venv_path / "bin" / "pip"
    
    def create_directories(self):
        """필요한 디렉토리 생성"""
        directories = [self.logs_dir, self.uploads_dir]
        
        for directory in directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"디렉토리 생성: {directory}")
    
    def check_python_version(self) -> bool:
        """Python 버전 확인 (3.8 이상)"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            logger.info(f"Python 버전 확인: {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            logger.error(f"Python 3.8 이상이 필요합니다. 현재 버전: {version.major}.{version.minor}.{version.micro}")
            return False
    
    def create_virtual_environment(self):
        """가상환경 생성"""
        if self.venv_path.exists():
            logger.info("가상환경이 이미 존재합니다.")
            return True
        
        try:
            logger.info("가상환경을 생성하고 있습니다...")
            subprocess.run([
                sys.executable, "-m", "venv", str(self.venv_path)
            ], check=True, capture_output=True, text=True)
            logger.info("가상환경 생성 완료")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"가상환경 생성 실패: {e}")
            return False
    
    def install_dependencies(self):
        """의존성 패키지 설치"""
        if not self.requirements_file.exists():
            logger.error("requirements.txt 파일이 없습니다.")
            return False
        
        try:
            logger.info("의존성 패키지를 설치하고 있습니다...")
            pip_exe = self._get_pip_executable()
            
            # pip 업그레이드
            subprocess.run([
                str(pip_exe), "install", "--upgrade", "pip"
            ], check=True, capture_output=True, text=True)
            
            # 의존성 설치
            subprocess.run([
                str(pip_exe), "install", "-r", str(self.requirements_file)
            ], check=True, capture_output=True, text=True)
            
            logger.info("의존성 패키지 설치 완료")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"의존성 설치 실패: {e}")
            return False
    
    def setup_environment_file(self):
        """환경 변수 파일 설정"""
        if not self.env_file.exists():
            if self.env_example_file.exists():
                logger.info(".env 파일이 없어 .env.example을 복사합니다...")
                import shutil
                shutil.copy(self.env_example_file, self.env_file)
                logger.warning("⚠️  .env 파일의 API 키들을 실제 값으로 설정해주세요!")
            else:
                logger.warning(".env.example 파일이 없습니다.")
                return False
        else:
            logger.info(".env 파일이 존재합니다.")
        
        return True
    
    def check_database_connection(self) -> bool:
        """데이터베이스 연결 확인"""
        try:
            logger.info("데이터베이스 연결을 확인하고 있습니다...")
            # 간단한 데이터베이스 연결 테스트
            import sqlite3
            db_path = self.base_dir / "asset_rebalancing.db"
            conn = sqlite3.connect(str(db_path))
            conn.close()
            logger.info("데이터베이스 연결 확인 완료")
            return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            return False
    
    def check_dependencies(self) -> List[str]:
        """의존성 패키지 확인"""
        missing_packages = []
        required_packages = [
            'fastapi', 'uvicorn', 'pydantic', 'pandas', 'numpy',
            'yfinance', 'requests', 'beautifulsoup4', 'python-multipart',
            'aiofiles', 'python-dotenv', 'httpx', 'PyPDF2', 'arxiv', 'anthropic'
        ]
        
        try:
            pip_exe = self._get_pip_executable()
            result = subprocess.run([
                str(pip_exe), "list", "--format=freeze"
            ], capture_output=True, text=True, check=True)
            
            installed_packages = result.stdout.lower()
            
            for package in required_packages:
                if package.lower() not in installed_packages:
                    missing_packages.append(package)
            
            if missing_packages:
                logger.warning(f"누락된 패키지: {', '.join(missing_packages)}")
            else:
                logger.info("모든 의존성 패키지가 설치되어 있습니다.")
                
        except Exception as e:
            logger.error(f"의존성 확인 실패: {e}")
        
        return missing_packages
    
    def check_environment_variables(self) -> bool:
        """필수 환경 변수 확인"""
        from dotenv import load_dotenv
        load_dotenv(self.env_file)
        
        required_vars = [
            'ANTHROPIC_API_KEY',
        ]
        
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            if not value or value.startswith('your_'):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"⚠️  다음 환경 변수를 설정해주세요: {', '.join(missing_vars)}")
            logger.warning("   .env 파일을 편집하여 실제 API 키를 입력하세요.")
            return False
        else:
            logger.info("필수 환경 변수가 설정되어 있습니다.")
            return True
    
    def is_port_in_use(self, port: int) -> bool:
        """포트 사용 여부 확인"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0
        except Exception:
            return False
    
    def find_available_port(self, start_port: int = 8000, max_port: int = 8010) -> int:
        """사용 가능한 포트 찾기"""
        for port in range(start_port, max_port + 1):
            if not self.is_port_in_use(port):
                return port
        return start_port  # 기본값 반환
    
    def start_server(self, host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
        """서버 시작"""
        try:
            # 포트 확인 및 조정
            if self.is_port_in_use(port):
                available_port = self.find_available_port(port)
                if available_port != port:
                    logger.warning(f"포트 {port}가 사용 중입니다. 포트 {available_port}를 사용합니다.")
                    port = available_port
            
            logger.info(f"서버를 시작합니다... http://{host}:{port}")
            logger.info("API 문서: http://localhost:8000/docs")
            logger.info("서버를 중지하려면 Ctrl+C를 누르세요")
            
            # uvicorn으로 서버 시작
            python_exe = self._get_python_executable()
            cmd = [
                str(python_exe), "-m", "uvicorn",
                "app:app",
                f"--host={host}",
                f"--port={port}",
                "--log-level=info"
            ]
            
            if reload:
                cmd.append("--reload")
            
            self.process = subprocess.Popen(
                cmd,
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # 실시간 로그 출력
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    print(line.rstrip())
                if self.process.poll() is not None:
                    break
                    
        except KeyboardInterrupt:
            logger.info("서버를 종료하고 있습니다...")
            self.stop_server()
        except Exception as e:
            logger.error(f"서버 시작 실패: {e}")
    
    def stop_server(self):
        """서버 중지"""
        if self.process:
            logger.info("서버를 중지하고 있습니다...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
            logger.info("서버가 중지되었습니다.")
    
    def run_tests(self):
        """테스트 실행"""
        try:
            logger.info("테스트를 실행하고 있습니다...")
            python_exe = self._get_python_executable()
            
            # 기본 테스트: 모듈 임포트 확인
            test_script = """
import sys
sys.path.append('.')

try:
    from app import app
    from data_processor import DataProcessor
    from ai_model_trainer import AIModelTrainer
    from simulation_analyzer import SimulationAnalyzer
    from database_manager import get_database_manager
    from user_data_processor import get_user_data_processor
    print("✅ 모든 모듈 임포트 성공")
except Exception as e:
    print(f"❌ 모듈 임포트 실패: {e}")
    sys.exit(1)
            """
            
            result = subprocess.run([
                str(python_exe), "-c", test_script
            ], capture_output=True, text=True, cwd=self.base_dir)
            
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
                
            if result.returncode == 0:
                logger.info("✅ 기본 테스트 통과")
                return True
            else:
                logger.error("❌ 기본 테스트 실패")
                return False
                
        except Exception as e:
            logger.error(f"테스트 실행 실패: {e}")
            return False
    
    def setup_and_start(self, run_tests: bool = True, host: str = "0.0.0.0", port: int = 8000):
        """전체 설정 및 서버 시작"""
        logger.info("=== AI Asset Rebalancing System Backend 시작 ===")
        logger.info(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 기본 검증
        if not self.check_python_version():
            return False
        
        # 2. 디렉토리 생성
        self.create_directories()
        
        # 3. 가상환경 생성
        if not self.create_virtual_environment():
            return False
        
        # 4. 의존성 설치
        missing_packages = self.check_dependencies()
        if missing_packages:
            if not self.install_dependencies():
                return False
        
        # 5. 환경 파일 설정
        if not self.setup_environment_file():
            return False
        
        # 6. 환경 변수 확인
        env_ok = self.check_environment_variables()
        if not env_ok:
            logger.warning("일부 환경 변수가 설정되지 않았지만 계속 진행합니다...")
        
        # 7. 테스트 실행
        if run_tests:
            if not self.run_tests():
                logger.warning("테스트에서 오류가 발생했지만 계속 진행합니다...")
        
        # 8. 서버 시작
        logger.info("=== 설정 완료, 서버 시작 ===")
        self.start_server(host=host, port=port)

def signal_handler(signum, frame):
    """시그널 핸들러"""
    print("\n서버를 종료합니다...")
    sys.exit(0)

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Asset Rebalancing Backend Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Port number (default: 8000)')
    parser.add_argument('--no-reload', action='store_true', help='Disable auto-reload')
    parser.add_argument('--skip-tests', action='store_true', help='Skip running tests')
    parser.add_argument('--setup-only', action='store_true', help='Only run setup, do not start server')
    
    args = parser.parse_args()
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 백엔드 매니저 초기화
    manager = BackendManager()
    
    try:
        if args.setup_only:
            # 설정만 수행
            logger.info("설정만 수행하고 종료합니다...")
            manager.create_directories()
            manager.create_virtual_environment()
            manager.install_dependencies()
            manager.setup_environment_file()
            if not args.skip_tests:
                manager.run_tests()
            logger.info("설정 완료!")
        else:
            # 전체 설정 및 서버 시작
            manager.setup_and_start(
                run_tests=not args.skip_tests,
                host=args.host,
                port=args.port
            )
    except KeyboardInterrupt:
        logger.info("사용자가 프로그램을 중단했습니다.")
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)