# CSV Upload Guide for Postman

## Overview
This guide shows how to upload CSV files containing student data to the AI Service using Postman.

## API Endpoint
```
POST /api/documents/upload
```

## Prerequisites
1. AI Service running on `http://localhost:8000`
2. Qdrant database running on `http://localhost:6333`
3. Sample CSV file ready for upload

## Step-by-Step Guide

### Step 1: Start the AI Service
```bash
python production_startup.py
```

### Step 2: Open Postman
1. Create a new request
2. Set method to `POST`
3. Set URL to `http://localhost:8000/api/documents/upload`

### Step 3: Configure Request
1. Go to **Body** tab
2. Select **form-data**
3. Add the following fields:

#### Field 1: File Upload
- **Key**: `file`
- **Type**: `File`
- **Value**: Select your CSV file

#### Field 2: Student ID
- **Key**: `student_id`
- **Type**: `Text`
- **Value**: `STU001` (or your student ID)

#### Field 3: Document Type
- **Key**: `document_type`
- **Type**: `Text`
- **Value**: One of the following:
  - `grades` (for grade data)
  - `academic_report` (for academic reports)
  - `wellness_report` (for wellness data)
  - `activities` (for extracurricular activities)
  - `placement_report` (for placement data)

#### Field 4: Semester (Optional)
- **Key**: `semester`
- **Type**: `Text`
- **Value**: `Fall 2023` (or current semester)

### Step 4: Send Request
Click **Send** to upload the CSV file.

## Expected Response
```json
{
  "success": true,
  "document_id": "doc_12345678",
  "metadata": {
    "filename": "sample_student_grades.csv",
    "file_size": 1024,
    "file_type": "csv",
    "student_id": "STU001",
    "category": "academic",
    "upload_timestamp": "2024-01-15T10:30:00Z"
  },
  "extracted_text_preview": true,
  "file_path": "/uploads/academic/sample_student_grades.csv",
  "category": "academic"
}
```

## Step 5: Create Chunks
After uploading, you need to create chunks for the document:

### Endpoint
```
POST /api/chunking/create
```

### Request Body
```json
{
  "document_id": "doc_12345678"
}
```

### Response
```json
{
  "success": true,
  "document_id": "doc_12345678",
  "chunks_created": 8,
  "message": "Successfully created 8 chunks"
}
```

## Sample CSV File Format

### Academic Grades CSV
```csv
student_id,course_code,course_name,instructor,semester,grade,credits,attendance,assignment_score,midterm_score,final_score,gpa_points
STU001,CS301,Data Structures,Dr. Smith,Fall 2023,A,4,95,92,88,94,4.0
STU001,CS303,Computer Networks,Dr. Williams,Fall 2023,A-,4,93,89,85,87,3.7
STU001,CS302,Database Systems,Prof. Johnson,Fall 2023,B+,4,88,85,82,84,3.3
```

### Wellness Metrics CSV
```csv
student_id,date,metric_type,value,category,notes
STU001,2024-01-01,sleep_hours,7.5,physical,Good sleep quality
STU001,2024-01-01,exercise_minutes,45,physical,Morning run
STU001,2024-01-01,stress_level,3,mental,Moderate stress
```

### Extracurricular Activities CSV
```csv
student_id,activity_name,role,start_date,end_date,hours_per_week,description
STU001,Coding Club,President,2023-09-01,2024-05-31,10,Leading coding club activities
STU001,Basketball Team,Member,2023-09-01,2024-05-31,6,Regular practice and games
```

## Troubleshooting

### Common Errors

#### 1. "Invalid document type"
**Solution**: Ensure `document_type` matches one of the allowed types:
- `grades`, `academic_report`, `wellness_report`, `activities`, `placement_report`

#### 2. "Unsupported file type"
**Solution**: Only CSV, PDF, TXT, and MD files are supported.

#### 3. "Student ID not found"
**Solution**: Ensure the CSV contains a `student_id` column with valid values.

#### 4. "File too large"
**Solution**: Keep CSV files under 10MB for optimal performance.

### Error Response Example
```json
{
  "detail": "Invalid document type: invalid_type"
}
```

## Complete Workflow Example

### 1. Upload Grades CSV
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@sample_student_grades.csv" \
  -F "student_id=STU001" \
  -F "document_type=grades" \
  -F "semester=Fall 2023"
```

### 2. Create Chunks
```bash
curl -X POST "http://localhost:8000/api/chunking/create" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "doc_12345678"}'
```

### 3. Query RAG Pipeline
```bash
curl -X POST "http://localhost:8000/api/advanced-rag/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "How is the student doing academically?"}'
```

## Data Management Endpoints

### Get Student Documents
```
GET /api/data/students/{student_id}/documents?category=academic
```

### Get Student Chunks
```
GET /api/data/students/{student_id}/chunks?category=academic
```

### Delete Document
```
DELETE /api/data/documents/{document_id}
```

### Get Statistics
```
GET /api/data/statistics
```

## Best Practices

1. **File Naming**: Use descriptive names like `student_grades_fall2023.csv`
2. **Data Validation**: Ensure CSV has required columns for your document type
3. **Batch Upload**: Use the batch upload endpoint for multiple files
4. **Regular Cleanup**: Delete old documents to maintain performance
5. **Monitoring**: Check `/api/data/statistics` for system overview

## Testing with Sample Data

Use the provided `sample_student_grades.csv` file to test the upload process:

1. Download the sample file
2. Follow the Postman steps above
3. Verify the upload was successful
4. Create chunks for the document
5. Test the RAG pipeline with queries about the uploaded data
