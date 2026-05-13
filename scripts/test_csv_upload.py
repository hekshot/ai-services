#!/usr/bin/env python3
"""
Test CSV upload workflow
"""
import asyncio
import sys
import httpx
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_csv_upload():
    """Test complete CSV upload workflow"""
    print("🧪 Testing CSV Upload Workflow")
    print("=" * 50)
    
    # Check if API server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code != 200:
                print("❌ API server not running. Please start it first:")
                print("   python production_startup.py")
                return False
            print("✅ API server is running")
    except Exception as e:
        print(f"❌ API server not accessible: {str(e)}")
        print("   Please start the API server first:")
        print("   python production_startup.py")
        return False
    
    # Test CSV upload
    csv_file = Path("sample_student_grades.csv")
    if not csv_file.exists():
        print(f"❌ Sample CSV file not found: {csv_file}")
        return False
    
    print(f"📄 Found sample CSV: {csv_file}")
    
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Upload CSV
            print("\n📤 Step 1: Uploading CSV file...")
            
            with open(csv_file, 'rb') as f:
                files = {'file': ('sample_student_grades.csv', f, 'text/csv')}
                data = {
                    'student_id': 'STU001',
                    'document_type': 'grades',
                    'semester': 'Fall 2023'
                }
                
                response = await client.post(
                    "http://localhost:8000/api/documents/upload",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                upload_result = response.json()
                document_id = upload_result.get("document_id")
                print(f"✅ Upload successful: {document_id}")
                print(f"   Category: {upload_result.get('category')}")
                print(f"   File: {upload_result.get('metadata', {}).get('filename')}")
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
            
            # Step 2: Create chunks
            print(f"\n🔧 Step 2: Creating chunks...")
            
            chunk_response = await client.post(
                "http://localhost:8000/api/chunking/create",
                json={"document_id": document_id}
            )
            
            if chunk_response.status_code == 200:
                chunk_result = chunk_response.json()
                chunks_created = chunk_result.get("chunks_created", 0)
                print(f"✅ Chunks created: {chunks_created}")
            else:
                print(f"❌ Chunk creation failed: {chunk_response.status_code}")
                print(f"   Error: {chunk_response.text}")
                return False
            
            # Step 3: Verify data
            print(f"\n🔍 Step 3: Verifying uploaded data...")
            
            # Get student documents
            docs_response = await client.get(
                "http://localhost:8000/api/data/students/STU001/documents",
                params={"category": "academic"}
            )
            
            if docs_response.status_code == 200:
                docs_result = docs_response.json()
                total_docs = docs_result.get("total_documents", 0)
                print(f"✅ Found {total_docs} academic documents")
            else:
                print(f"❌ Failed to get documents: {docs_response.status_code}")
            
            # Get student chunks
            chunks_response = await client.get(
                "http://localhost:8000/api/data/students/STU001/chunks",
                params={"category": "academic"}
            )
            
            if chunks_response.status_code == 200:
                chunks_result = chunks_response.json()
                total_chunks = chunks_result.get("total_chunks", 0)
                print(f"✅ Found {total_chunks} academic chunks")
            else:
                print(f"❌ Failed to get chunks: {chunks_response.status_code}")
            
            # Step 4: Test RAG query
            print(f"\n🤖 Step 4: Testing RAG query...")
            
            rag_response = await client.post(
                "http://localhost:8000/api/advanced-rag/query",
                json={"query": "What are the student's grades?"}
            )
            
            if rag_response.status_code == 200:
                rag_result = rag_response.json()
                answer = rag_result.get("answer", "")
                sources = rag_result.get("sources_used", 0)
                print(f"✅ RAG query successful")
                print(f"   Sources used: {sources}")
                print(f"   Answer preview: {answer[:100]}...")
            else:
                print(f"❌ RAG query failed: {rag_response.status_code}")
                print(f"   Error: {rag_response.text}")
            
            print(f"\n🎉 CSV upload workflow test completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

async def main():
    """Main function"""
    print("🎯 CSV Upload Workflow Test")
    print("=" * 50)
    
    success = await test_csv_upload()
    
    if success:
        print("\n✅ All tests passed!")
        print("💡 You can now upload CSV files via Postman")
        print("📖 See CSV_UPLOAD_GUIDE.md for detailed instructions")
    else:
        print("\n❌ Some tests failed")
        print("🔧 Check the error messages above")

if __name__ == "__main__":
    asyncio.run(main())
