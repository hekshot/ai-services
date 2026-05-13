#!/usr/bin/env python3
"""
Hermes Agent Skill: Student Analytics
Interacts with AI Service RAG pipeline for student data analysis
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

class StudentAnalyticsSkill:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def query_rag_pipeline(self, query: str) -> Dict[str, Any]:
        """Query the RAG pipeline with a student-related question"""
        try:
            response = await self.client.post(
                f"{self.api_base_url}/advanced-rag/query",
                json={"query": query}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"API request failed: {response.status_code}",
                    "answer": "Unable to process query at this time"
                }
        except Exception as e:
            return {
                "error": f"Connection error: {str(e)}",
                "answer": "Service temporarily unavailable"
            }
    
    async def get_student_academic_summary(self, student_id: str = "STU001") -> Dict[str, Any]:
        """Get comprehensive academic summary for a student"""
        query = f"How is student {student_id} doing academically? Provide detailed analysis including grades, performance trends, and recommendations."
        result = await self.query_rag_pipeline(query)
        
        return {
            "student_id": student_id,
            "analysis_type": "academic_summary",
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
    
    async def get_student_wellness_status(self, student_id: str = "STU001") -> Dict[str, Any]:
        """Get wellness status for a student"""
        query = f"How is student {student_id}'s overall wellness? Include physical, mental, and social aspects."
        result = await self.query_rag_pipeline(query)
        
        return {
            "student_id": student_id,
            "analysis_type": "wellness_status",
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
    
    async def get_placement_readiness(self, student_id: str = "STU001") -> Dict[str, Any]:
        """Get placement readiness assessment"""
        query = f"Is student {student_id} ready for placement? Include technical skills, interview readiness, and career preparation."
        result = await self.query_rag_pipeline(query)
        
        return {
            "student_id": student_id,
            "analysis_type": "placement_readiness",
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
    
    async def get_comprehensive_student_profile(self, student_id: str = "STU001") -> Dict[str, Any]:
        """Get complete student profile across all dimensions"""
        # Get all analyses in parallel
        academic_task = self.get_student_academic_summary(student_id)
        wellness_task = self.get_student_wellness_status(student_id)
        placement_task = self.get_placement_readiness(student_id)
        
        academic, wellness, placement = await asyncio.gather(
            academic_task, wellness_task, placement_task
        )
        
        return {
            "student_id": student_id,
            "analysis_type": "comprehensive_profile",
            "timestamp": datetime.now().isoformat(),
            "academic": academic.get("result", {}),
            "wellness": wellness.get("result", {}),
            "placement": placement.get("result", {})
        }
    
    async def identify_students_needing_attention(self) -> Dict[str, Any]:
        """Identify students who may need attention or support"""
        query = "Which students need academic support, wellness attention, or placement assistance? List them by priority."
        result = await self.query_rag_pipeline(query)
        
        return {
            "analysis_type": "attention_required",
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
    
    async def generate_daily_summary(self) -> Dict[str, Any]:
        """Generate daily summary of all student analytics"""
        # Get attention list
        attention_result = await self.identify_students_needing_attention()
        
        # Get sample comprehensive analysis
        profile_result = await self.get_comprehensive_student_profile()
        
        return {
            "analysis_type": "daily_summary",
            "timestamp": datetime.now().isoformat(),
            "attention_required": attention_result.get("result", {}),
            "sample_analysis": profile_result,
            "system_status": "operational"
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Hermes Agent Interface Functions
async def analyze_student(student_id: str = "STU001"):
    """Analyze a specific student - Hermes Agent entry point"""
    skill = StudentAnalyticsSkill()
    try:
        result = await skill.get_comprehensive_student_profile(student_id)
        return json.dumps(result, indent=2)
    finally:
        await skill.close()

async def daily_analytics():
    """Generate daily analytics - Hermes Agent entry point"""
    skill = StudentAnalyticsSkill()
    try:
        result = await skill.generate_daily_summary()
        return json.dumps(result, indent=2)
    finally:
        await skill.close()

async def check_attention_required():
    """Check which students need attention - Hermes Agent entry point"""
    skill = StudentAnalyticsSkill()
    try:
        result = await skill.identify_students_needing_attention()
        return json.dumps(result, indent=2)
    finally:
        await skill.close()

if __name__ == "__main__":
    # Test the skill
    async def test():
        skill = StudentAnalyticsSkill()
        try:
            # Test comprehensive analysis
            result = await skill.get_comprehensive_student_profile()
            print("✅ Comprehensive Analysis Test:")
            print(json.dumps(result, indent=2))
            
            # Test attention check
            attention = await skill.identify_students_needing_attention()
            print("\n✅ Attention Check Test:")
            print(json.dumps(attention, indent=2))
            
        finally:
            await skill.close()
    
    asyncio.run(test())
