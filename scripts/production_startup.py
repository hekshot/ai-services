#!/usr/bin/env python3
"""
Production startup script for AI Service
"""
import os
import sys
import uvicorn
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main production startup"""
    # Production configuration
    config = {
        "host": os.getenv("APP_HOST", "0.0.0.0"),
        "port": int(os.getenv("APP_PORT", 8000)),
        "log_level": os.getenv("LOG_LEVEL", "info"),
        "access_log": True,
        "reload": False,  # No reload in production
    }
    
    print(f"🚀 Starting AI Service in production mode")
    print(f"📍 Host: {config['host']}:{config['port']}")
    print(f" Environment: {os.getenv('APP_ENV', 'production')}")
    
    # Start the server
    uvicorn.run(
        "main:app",
        **config
    )

if __name__ == "__main__":
    main()
