#!/usr/bin/env python3
"""
Production-ready student data upload script
"""
import os
import sys
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any
import httpx
from fastapi import UploadFile
from io import BytesIO

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

class MockFile:
    """Mock file class for upload simulation"""
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self.file = BytesIO(content)
        self.content_type = self._get_content_type(filename)
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        ext = Path(filename).suffix.lower()
        if ext == '.md':
            return 'text/markdown'
        elif ext == '.csv':
            return 'text/csv'
        elif ext == '.txt':
            return 'text/plain'
        else:
            return 'application/octet-stream'

class StudentDataUploader:
    """Production-ready student data uploader"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def upload_file(self, file_path: str, student_id: str, category: str) -> Dict[str, Any]:
        """Upload a single file"""
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Create mock file
            mock_file = MockFile(Path(file_path).name, content)
            
            # Prepare upload data
            files = {
                'file': (mock_file.filename, mock_file.file, mock_file.content_type)
            }
            
            data = {
                'student_id': student_id,
                'category': category
            }
            
            # Upload file
            response = await self.client.post(
                f"{self.api_url}/api/documents/upload",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "document_id": result.get("document_id"),
                    "message": f"Successfully uploaded {Path(file_path).name}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Upload failed: {response.status_code} - {response.text}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error uploading {file_path}: {str(e)}"
            }
    
    async def create_chunks(self, document_id: str) -> Dict[str, Any]:
        """Create chunks for uploaded document"""
        try:
            response = await self.client.post(
                f"{self.api_url}/api/chunking/create",
                json={"document_id": document_id}
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "chunks_created": result.get("chunks_created", 0),
                    "message": f"Successfully created {result.get('chunks_created', 0)} chunks"
                }
            else:
                return {
                    "success": False,
                    "error": f"Chunk creation failed: {response.status_code} - {response.text}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating chunks: {str(e)}"
            }
    
    async def upload_and_chunk(self, file_path: str, student_id: str, category: str) -> Dict[str, Any]:
        """Upload file and create chunks in one step"""
        # Upload file
        upload_result = await self.upload_file(file_path, student_id, category)
        
        if not upload_result["success"]:
            return upload_result
        
        # Create chunks
        document_id = upload_result["document_id"]
        chunk_result = await self.create_chunks(document_id)
        
        return {
            "success": upload_result["success"] and chunk_result["success"],
            "document_id": document_id,
            "upload_message": upload_result.get("message"),
            "chunk_message": chunk_result.get("message"),
            "chunks_created": chunk_result.get("chunks_created", 0)
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

async def upload_sample_data():
    """Upload sample student data for demonstration"""
    print("🚀 Starting Sample Data Upload")
    print("=" * 50)
    
    # Create sample data directory
    sample_dir = Path("sample_data")
    sample_dir.mkdir(exist_ok=True)
    
    # Create sample files
    sample_files = {
        "academic_report.md": """
# Academic Report - Student STU001

## Performance Summary
- **GPA**: 3.6/4.0
- **Major**: Computer Science
- **Year**: Junior

## Course Performance
### CS301 - Data Structures
- **Grade**: A
- **Instructor**: Dr. Smith
- **Comments**: Excellent problem-solving skills

### CS303 - Computer Networks
- **Grade**: A-
- **Instructor**: Dr. Williams
- **Comments**: Strong grasp of networking protocols

### CS302 - Database Systems
- **Grade**: B+
- **Instructor**: Prof. Johnson
- **Comments**: Good understanding of database concepts

## Overall Assessment
Student demonstrates strong academic performance with particular strengths in algorithms and networking.
        """,
        
        "extracurricular_activities.md": """
# Extracurricular Activities - Student STU001

## Leadership Roles
- **Coding Club President** (2023-Present)
- **Tech Team Lead** (2022-2023)
- **Peer Tutor** (2021-Present)

## Achievements
- **Outstanding Leadership Award** (2024)
- **Technical Excellence Award** (2024)
- **Hackathon Winner** (2023)

## Skills Development
- **Programming Languages**: Python, JavaScript, Java
- **Frameworks**: React, Node.js, TensorFlow
- **Tools**: Git, Docker, AWS basics
- **Database**: SQL, MongoDB

## Time Commitment
- **Coding Club**: 10 hours/week
- **Study Groups**: 5 hours/week
- **Personal Projects**: 8 hours/week
        """,
        
        "placement_readiness.md": """
# Placement Readiness - Student STU001

## Technical Skills
- **Programming**: Advanced proficiency in Python, JavaScript
- **Frameworks**: React, Node.js, TensorFlow
- **Databases**: SQL, MongoDB, Redis
- **Cloud**: AWS basics, Docker
- **Tools**: Git, CI/CD pipelines

## Project Experience
1. **E-commerce Platform** - Full-stack development
2. **Machine Learning Model** - Predictive analytics
3. **Mobile App** - React Native development
4. **API Design** - RESTful services

## Interview Preparation
- **Technical Interviews**: Completed 15+ mock interviews
- **System Design**: Studied common patterns
- **Problem Solving**: LeetCode 200+ problems solved
- **Behavioral**: STAR method preparation

## Placement Status
- **Resume**: Finalized and optimized
- **LinkedIn**: Professional profile complete
- **Portfolio**: 5+ projects showcased
- **Target Companies**: FAANG, startups, consulting

## Readiness Score: 8.7/10
**Status**: Ready for placement
        """,
        
        "wellness_report.md": """
# Wellness Report - Student STU001

## Physical Wellness
- **Exercise**: 4 times per week
- **Sleep**: 7-8 hours nightly
- **Nutrition**: Balanced diet
- **Stress Level**: Moderate

## Mental Wellness
- **Stress Management**: Meditation and mindfulness
- **Work-Life Balance**: Good balance maintained
- **Social Support**: Strong peer network
- **Counseling**: Available if needed

## Academic Wellness
- **Study Habits**: Consistent and effective
- **Time Management**: Well-organized schedule
- **Academic Support**: Utilizes tutoring services
- **Course Load**: Manageable 15 credits

## Social Wellness
- **Friendships**: Strong social connections
- **Community Involvement Active participation
- **Family Support**: Good family relationships
- **Extracurricular**: Balanced with academics

## Overall Wellness Score: 8.2/10
**Status**: Healthy and balanced
        """
    }
    
    # Write sample files
    for filename, content in sample_files.items():
        file_path = sample_dir / filename
        with open(file_path, 'w') as f:
            f.write(content.strip())
        print(f"✅ Created sample file: {filename}")
    
    # Upload files
    uploader = StudentDataUploader()
    
    upload_configs = [
        ("academic_report.md", "STU001", "academic"),
        ("extracurricular_activities.md", "STU001", "extracurricular"),
        ("placement_readiness.md", "STU001", "placement"),
        ("wellness_report.md", "STU001", "wellness")
    ]
    
    results = []
    
    for filename, student_id, category in upload_configs:
        file_path = sample_dir / filename
        print(f"\n📤 Uploading {filename}...")
        
        result = await uploader.upload_and_chunk(str(file_path), student_id, category)
        
        if result["success"]:
            print(f"✅ {result['upload_message']}")
            print(f"✅ {result['chunk_message']}")
            results.append(f"✅ {filename}: {result['chunks_created']} chunks")
        else:
            print(f"❌ {result['error']}")
            results.append(f"❌ {filename}: {result['error']}")
    
    await uploader.close()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 UPLOAD SUMMARY")
    print("=" * 50)
    
    for result in results:
        print(result)
    
    # Cleanup sample files
    print(f"\n🧹 Cleaning up sample files...")
    for filename in sample_files:
        file_path = sample_dir / filename
        file_path.unlink()
    
    sample_dir.rmdir()
    print("✅ Cleanup completed")

async def main():
    """Main function"""
    print("🎯 Student Data Upload System")
    print("=" * 50)
    
    await upload_sample_data()
    
    print("\n🎉 Data upload completed!")
    print("💡 You can now use the RAG pipeline to analyze student data")

if __name__ == "__main__":
    asyncio.run(main())
