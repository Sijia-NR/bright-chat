"""
启动脚本
"""
import uvicorn
from config import Config

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True,
        log_level="info"
    )