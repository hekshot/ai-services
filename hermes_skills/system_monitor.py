#!/usr/bin/env python3
"""
Hermes Agent Skill: System Monitoring
Monitors AI Service health, data quality, and system performance
"""
import asyncio
import sys
import httpx
from typing import Dict, List, Any
from datetime import datetime
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class SystemMonitorSkill:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def check_service_health(self) -> Dict[str, Any]:
        """Check if AI Service is healthy and responsive"""
        try:
            response = await self.client.get(f"{self.api_base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                return {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "details": health_data
                }
            else:
                return {
                    "status": "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "unreachable",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def check_qdrant_health(self) -> Dict[str, Any]:
        """Check Qdrant vector database health"""
        try:
            response = await self.client.get("http://localhost:6333/health")
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "service": "qdrant"
                }
            else:
                return {
                    "status": "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                    "service": "qdrant",
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "unreachable",
                "timestamp": datetime.now().isoformat(),
                "service": "qdrant",
                "error": str(e)
            }
    
    async def check_ollama_health(self) -> Dict[str, Any]:
        """Check Ollama LLM service health"""
        try:
            response = await self.client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "service": "ollama",
                    "models_available": len(models),
                    "models": [model.get("name") for model in models]
                }
            else:
                return {
                    "status": "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                    "service": "ollama",
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "unreachable",
                "timestamp": datetime.now().isoformat(),
                "service": "ollama",
                "error": str(e)
            }
    
    async def get_data_statistics(self) -> Dict[str, Any]:
        """Get data statistics from AI Service"""
        try:
            response = await self.client.get(f"{self.api_base_url}/api/data/statistics")
            if response.status_code == 200:
                stats = response.json()
                return {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "statistics": stats
                }
            else:
                return {
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def test_rag_pipeline(self) -> Dict[str, Any]:
        """Test RAG pipeline with a simple query"""
        try:
            response = await self.client.post(
                f"{self.api_base_url}/advanced-rag/query",
                json={"query": "Test query - how many students are in the system?"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "working",
                    "timestamp": datetime.now().isoformat(),
                    "pipeline_test": {
                        "answer_length": len(result.get("answer", "")),
                        "sources_used": result.get("sources_used", 0),
                        "processing_time": result.get("processing_time", 0)
                    }
                }
            else:
                return {
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def generate_system_report(self) -> Dict[str, Any]:
        """Generate comprehensive system health report"""
        # Check all services in parallel
        ai_service_task = self.check_service_health()
        qdrant_task = self.check_qdrant_health()
        ollama_task = self.check_ollama_health()
        data_stats_task = self.get_data_statistics()
        rag_test_task = self.test_rag_pipeline()
        
        ai_service, qdrant, ollama, data_stats, rag_test = await asyncio.gather(
            ai_service_task, qdrant_task, ollama_task, data_stats_task, rag_test_task
        )
        
        # Calculate overall health
        services = [ai_service, qdrant, ollama, rag_test]
        healthy_count = sum(1 for s in services if s.get("status") == "healthy" or s.get("status") == "working")
        overall_health = "healthy" if healthy_count == len(services) else "degraded" if healthy_count > 0 else "unhealthy"
        
        return {
            "overall_health": overall_health,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "ai_service": ai_service,
                "qdrant": qdrant,
                "ollama": ollama,
                "rag_pipeline": rag_test
            },
            "data_statistics": data_stats,
            "summary": {
                "total_services": len(services),
                "healthy_services": healthy_count,
                "health_percentage": (healthy_count / len(services)) * 100
            }
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Hermes Agent Interface Functions
async def system_health():
    """Get system health status - Hermes Agent entry point"""
    monitor = SystemMonitorSkill()
    try:
        result = await monitor.generate_system_report()
        return json.dumps(result, indent=2)
    finally:
        await monitor.close()

async def quick_health_check():
    """Quick health check - Hermes Agent entry point"""
    monitor = SystemMonitorSkill()
    try:
        ai_service = await monitor.check_service_health()
        qdrant = await monitor.check_qdrant_health()
        ollama = await monitor.check_ollama_health()
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "ai_service": ai_service.get("status"),
            "qdrant": qdrant.get("status"),
            "ollama": ollama.get("status")
        }
        
        return json.dumps(result, indent=2)
    finally:
        await monitor.close()

if __name__ == "__main__":
    # Test the monitoring skill
    async def test():
        monitor = SystemMonitorSkill()
        try:
            print("🔍 System Health Check")
            result = await monitor.generate_system_report()
            print(json.dumps(result, indent=2))
        finally:
            await monitor.close()
    
    asyncio.run(test())
