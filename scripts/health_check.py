#!/usr/bin/env python3
"""
Health check script for production monitoring
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def check_services():
    """Check all service health"""
    print("🔍 Health Check Starting")
    print("=" * 40)
    
    checks = {}
    
    # Check Qdrant
    try:
        from app.services.qdrant_storage_service import QdrantStorageService
        storage = QdrantStorageService()
        storage.connect()
        collections = storage.client.get_collections()
        checks['qdrant'] = "✅ Healthy"
        print(f"✅ Qdrant: {len(collections.collections)} collections")
    except Exception as e:
        checks['qdrant'] = f"❌ Error: {str(e)}"
        print(f"❌ Qdrant: {str(e)}")
    
    # Check Ollama
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            if response.status_code == 200:
                models = response.json().get('models', [])
                checks['ollama'] = "✅ Healthy"
                print(f"✅ Ollama: {len(models)} models available")
            else:
                checks['ollama'] = f"❌ Status: {response.status_code}"
                print(f"❌ Ollama: Status {response.status_code}")
    except Exception as e:
        checks['ollama'] = f"❌ Error: {str(e)}"
        print(f"❌ Ollama: {str(e)}")
    
    # Check Redis (if available)
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        checks['redis'] = "✅ Healthy"
        print("✅ Redis: Connected")
    except Exception as e:
        checks['redis'] = f"❌ Error: {str(e)}"
        print(f"❌ Redis: {str(e)}")
    
    # Check RAG Pipeline
    try:
        from app.services.advanced_rag_service import AdvancedRAGService
        rag_service = AdvancedRAGService()
        result = await rag_service.advanced_rag_pipeline("Health check query")
        checks['rag_pipeline'] = "✅ Healthy"
        print("✅ RAG Pipeline: Working")
    except Exception as e:
        checks['rag_pipeline'] = f"❌ Error: {str(e)}"
        print(f"❌ RAG Pipeline: {str(e)}")
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 HEALTH CHECK SUMMARY")
    print("=" * 40)
    
    healthy = sum(1 for status in checks.values() if "✅" in status)
    total = len(checks)
    
    for service, status in checks.items():
        print(f"{status} {service}")
    
    print(f"\n🎯 Overall Health: {healthy}/{total} services healthy")
    
    if healthy == total:
        print("🎉 All systems operational!")
        return True
    else:
        print("⚠️ Some services need attention")
        return False

async def main():
    """Main health check"""
    healthy = await check_services()
    sys.exit(0 if healthy else 1)

if __name__ == "__main__":
    asyncio.run(main())
