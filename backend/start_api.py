#!/usr/bin/env python3
"""
启动回测系统 FastAPI 服务器
"""
import os
import sys
import logging
import uvicorn

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# 配置日志格式
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "detailed": {
            "formatter": "detailed",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["default"],
    },
    "loggers": {
        "uvicorn": {
            "level": "INFO",
            "handlers": ["default"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["default"], 
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["detailed"],
            "propagate": False,
        },
        "backend.src.api_server": {
            "level": "INFO",
            "handlers": ["detailed"],
            "propagate": False,
        },
        "backend": {
            "level": "INFO", 
            "handlers": ["detailed"],
            "propagate": False,
        },
    },
}

def main():
    """启动 FastAPI 服务器"""
    print("🚀 启动回测系统 API 服务器...")
    print(f"📁 项目根目录: {project_root}")
    print(f"📍 工作目录: {os.getcwd()}")
    print("🌐 API 文档地址: http://localhost:8000/api/docs")
    print("📝 Redoc 文档地址: http://localhost:8000/api/redoc")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "backend.src.api_server:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True,
            log_config=LOGGING_CONFIG
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 