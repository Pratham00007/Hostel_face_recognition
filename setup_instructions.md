
# Hostel Management System Setup Instructions

## Prerequisites
- Python 3.7 or higher
- Webcam/Camera
- Windows/Linux/MacOS

## Installation Steps

### 1. Create Project Directory
```bash
mkdir hostel_management
cd hostel_management
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv hostel_env
# On Windows:
hostel_env\Scripts\activate
# On Linux/Mac:
source hostel_env/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create Directory Structure
```
hostel_management/
├── app.py
├── requirements.txt
├── templates/
│   ├── index.html
│   └── records.html
├── photos/
├── Entry_Record/
└── hoset_student_data.xlsx
```

### 5. Create Templates Directory
```bash
mkdir templates
```

### 6. Create Photos Directory
```bash
mkdir photos
```

### 7. Add Student Photos
- Place student photos in the `photos/` directory
- Update the `Photo` column in `hoset_student_data.xlsx` with correct paths
- Supported formats: JPG, JPEG, PNG

### 8. Prepare Student Data
Create `hoset_student_data.xlsx` with columns:
- Sno
- Roll no
- Erp
- Name
- Room no
- Mobile no
- Photo (path to student photo)

Example:
| Sno | Roll no | Erp    | Name      | Room no | Mobile no  | Photo           |
|-----|---------|--------|-----------|---------|------------|-----------------|
| 1   | 2021001 | ERP001 | John Doe  | A101    | 9876543210 | photos/john.jpg |
| 2   | 2021002 | ERP002 | Jane Smith| A102    | 9876543211 | photos/jane.jpg |

## Running the Application

### 1. Start the Flask Application
```bash
python app.py
```

### 2. Access the Web Interface
- Open web browser
- Go to: `http://localhost:5000`
- Allow camera permissions when prompted

### 3. Using the System
- **For Entry**: Click "Record Entry" button, show face to camera
- **For Exit**: Click "Record Exit" button, show face to camera
- **View Records**: Click "View Records" to see today's entries/exits

## Important Notes

### Face Recognition Setup
- Each student needs at least one clear photo
- Photos should be well-lit and show the face clearly
- Recommended image size: 300x300 pixels or larger
- Face should be the primary focus in the image

### Data Storage
- Daily records are automatically created in `Entry_Record/` folder
- Files are named with date format: `DD_MM_YYYY.xlsx`
- Each record contains: rollno, erp, name, Exit Time, Entry Time, room no, phone no

### Troubleshooting

#### Camera Issues
- Ensure camera permissions are granted
- Check if camera is being used by other applications
- Try refreshing the web page

#### Face Recognition Issues
- Ensure good lighting conditions
- Position face clearly in the camera frame
- Check if student photo exists and path is correct
- Verify face-recognition library is properly installed

#### Installation Issues
- On Linux: Install cmake and dlib dependencies
  ```bash
  sudo apt-get install cmake
  sudo apt-get install libopenblas-dev liblapack-dev
  ```
- On Windows: Install Visual Studio Build Tools
- For dlib issues: `pip install dlib` might need cmake

### Performance Tips
- Use good lighting for better face recognition accuracy
- Keep student photos updated
- Restart the application daily for optimal performance
- Monitor Entry_Record folder size regularly

### Security Considerations
- Run on internal network only
- Regularly backup student data and records
- Keep student photos secure and private
- Update dependencies regularly for security patches

## File Descriptions

### app.py
Main Flask application with face recognition logic

### templates/index.html
Web interface for camera capture and recognition

### templates/records.html
Interface to view daily entry/exit records

### hoset_student_data.xlsx
Master file containing all student information

### Entry_Record/
Directory containing daily entry/exit records

### photos/
Directory containing student photos for face recognition

## Support
For issues or questions, check:
1. Camera permissions in browser
2. Student photo paths in Excel file
3. All required packages are installed
4. Python version compatibility