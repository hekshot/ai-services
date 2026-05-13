# Data Directory Structure

## Overview
This directory contains all data-related files for the AI Service.

## Directory Structure

```
data/
├── samples/          # Sample data files for testing
│   ├── sample_student_grades.csv
│   ├── sample_wellness_metrics.csv
│   ├── sample_extracurricular_activities.csv
│   └── sample_placement_data.csv
└── uploads/          # User uploaded files (created automatically)
```

## Sample Data Files

### Academic Data
- **sample_student_grades.csv**: Student grade information with course details, scores, and GPA

### Wellness Data
- **sample_wellness_metrics.csv**: Student wellness metrics including sleep, exercise, and stress levels

### Extracurricular Data
- **sample_extracurricular_activities.csv**: Student activities, roles, and time commitments

### Placement Data
- **sample_placement_data.csv**: Job applications, interviews, and placement status

## File Formats

### CSV Files
All CSV files follow these conventions:
- Use UTF-8 encoding
- Include headers in the first row
- Use comma as delimiter
- Include student_id column for data association

### Required Columns
- **student_id**: Unique identifier for each student
- Other columns vary by data type

## Usage

### Testing
Use sample files for testing the RAG pipeline:
```bash
python scripts/direct_upload.py
```

### API Upload
Upload CSV files via API:
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@data/samples/sample_student_grades.csv" \
  -F "student_id=STU001" \
  -F "document_type=grades"
```

## Data Categories

Supported document types for upload:
- `grades`: Academic grade data
- `wellness_report`: Wellness metrics
- `activities`: Extracurricular activities
- `placement_report`: Placement and career data

## Best Practices

1. **File Naming**: Use descriptive names with dates
2. **Data Validation**: Ensure required columns are present
3. **File Size**: Keep files under 10MB for optimal performance
4. **Regular Cleanup**: Remove old files from uploads directory

## Data Privacy

- All sample data is fictional and for testing purposes only
- User uploads should follow data privacy regulations
- Consider implementing data retention policies
