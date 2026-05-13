#!/usr/bin/env python3
"""
Development startup script for AI Service
"""
import os
import sys
import uvicorn
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main development startup"""
    print("🚀 Starting AI Service in development mode")
    print("📍 Host: http://localhost:8000")
    print("📊 Environment: development")
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
