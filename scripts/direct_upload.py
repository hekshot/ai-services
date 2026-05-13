#!/usr/bin/env python3
"""
Direct student data upload without API server
"""
import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any
from io import BytesIO

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.document_service import DocumentProcessor
from app.services.chunking_service import DocumentChunker
from app.services.qdrant_storage_service import QdrantStorageService

class DirectUploader:
    """Direct uploader that works without API server"""
    
    def __init__(self):
        self.doc_processor = DocumentProcessor()
        self.chunker = DocumentChunker()
        self.storage = QdrantStorageService()
        self.storage.connect()
    
    async def upload_content(self, content: str, filename: str, student_id: str, category: str) -> Dict[str, Any]:
        """Upload content directly"""
        try:
            # Create a mock file
            from fastapi import UploadFile
            mock_file = UploadFile(filename=filename, file=BytesIO(content.encode()))
            
            # Process document
            result = await self.doc_processor.process_uploaded_file(mock_file, student_id, category)
            
            if not result.get("success", False):
                return {
                    "success": False,
                    "error": result.get("error", "Upload failed")
                }
            
            document_id = result.get("document_id")
            
            # Create chunks
            chunk_result = self.chunker.chunk_document(student_id, document_id, category, category)
            
            return {
                "success": True,
                "document_id": document_id,
                "chunks_created": chunk_result.get("chunks_created", 0),
                "message": f"Successfully uploaded {filename}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error uploading {filename}: {str(e)}"
            }

async def upload_sample_data():
    """Upload sample student data directly"""
    print("🚀 Starting Direct Sample Data Upload")
    print("=" * 50)
    
    # Sample data
    sample_data = {
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
- **Community Involvement**: Active participation
- **Family Support**: Good family relationships
- **Extracurricular**: Balanced with academics

## Overall Wellness Score: 8.2/10
**Status**: Healthy and balanced
        """
    }
    
    # Upload configurations
    upload_configs = [
        ("academic_report.md", "STU001", "academic"),
        ("extracurricular_activities.md", "STU001", "extracurricular"),
        ("placement_readiness.md", "STU001", "placement"),
        ("wellness_report.md", "STU001", "wellness")
    ]
    
    # Initialize uploader
    uploader = DirectUploader()
    
    results = []
    
    for filename, student_id, category in upload_configs:
        content = sample_data[filename]
        print(f"\n📤 Uploading {filename}...")
        
        result = await uploader.upload_content(content, filename, student_id, category)
        
        if result["success"]:
            print(f"✅ {result['message']}")
            print(f"✅ Created {result['chunks_created']} chunks")
            results.append(f"✅ {filename}: {result['chunks_created']} chunks")
        else:
            print(f"❌ {result['error']}")
            results.append(f"❌ {filename}: {result['error']}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 UPLOAD SUMMARY")
    print("=" * 50)
    
    for result in results:
        print(result)
    
    # Check final data
    print(f"\n🔍 Verifying uploaded data...")
    try:
        collections = uploader.storage.client.get_collections()
        print(f"✅ Found {len(collections.collections)} collections")
        
        total_chunks = 0
        for collection in collections.collections:
            collection_name = collection.name
            points, _ = uploader.storage.client.scroll(
                collection_name=collection_name,
                limit=10000
            )
            chunk_count = len([p for p in points if p.payload.get("type") == "chunk"])
            total_chunks += chunk_count
            print(f"✅ {collection_name}: {chunk_count} chunks")
        
        print(f"\n🎯 Total chunks uploaded: {total_chunks}")
        
    except Exception as e:
        print(f"❌ Error verifying data: {str(e)}")

async def main():
    """Main function"""
    print("🎯 Direct Student Data Upload System")
    print("=" * 50)
    
    await upload_sample_data()
    
    print("\n🎉 Data upload completed!")
    print("💡 You can now use the RAG pipeline to analyze student data")
    print("🚀 Start the API server to test the full pipeline")

if __name__ == "__main__":
    asyncio.run(main())
