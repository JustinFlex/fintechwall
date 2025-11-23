#!/usr/bin/env python3
"""
A股市场大屏启动脚本
Startup script for A-shares market wallboard
"""

import os
import sys
import uvicorn
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('a_shares_wallboard.log')
    ]
)

logger = logging.getLogger(__name__)


def setup_environment():
    """Setup environment variables for A-shares wallboard."""
    # Set data mode to Wind
    os.environ.setdefault('DATA_MODE', 'wind')

    # Redis configuration (optional)
    os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
    os.environ.setdefault('REDIS_ENABLED', 'false')  # Start without Redis for simplicity

    # Cache settings
    os.environ.setdefault('SNAPSHOT_CACHE_TTL', '15')  # 15 seconds

    # API settings
    os.environ.setdefault('API_TITLE', 'Wind A-Shares Market Wallboard')
    os.environ.setdefault('API_VERSION', '1.0.0')

    logger.info("Environment configured for A-shares wallboard")


def check_wind_api():
    """Check if Wind API is available."""
    try:
        from WindPy import w
        result = w.start()
        if result.ErrorCode == 0:
            logger.info("Wind API connection successful")
            w.stop()
            return True
        else:
            logger.warning(f"Wind API connection failed: {result.Data}")
            return False
    except ImportError:
        logger.warning("WindPy not installed - running in demo mode")
        return False
    except Exception as e:
        logger.warning(f"Wind API check failed: {e}")
        return False


def main():
    """Main startup function."""
    logger.info("Starting A-shares Market Wallboard...")

    # Setup environment
    setup_environment()

    # Check Wind API availability
    wind_available = check_wind_api()
    if wind_available:
        logger.info("Wind API available - using real market data")
    else:
        logger.info("Wind API not available - using demo data")

    # Start the FastAPI server
    try:
        logger.info("Starting FastAPI server...")
        logger.info("Market wallboard will be available at:")
        logger.info("  - API: http://localhost:8000")
        logger.info("  - Main Wallboard: http://localhost:8000/static/wallboard.html")
        logger.info("  - A-shares View: http://localhost:8000/static/a-shares.html")
        logger.info("  - API Docs: http://localhost:8000/docs")

        uvicorn.run(
            "backend.app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )

    except KeyboardInterrupt:
        logger.info("Shutting down A-shares wallboard...")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()