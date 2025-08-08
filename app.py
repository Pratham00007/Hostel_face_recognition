# app.py - Main Flask Application
from flask import Flask, render_template, jsonify, request
import cv2
import pandas as pd
import numpy as np
import os
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import face_recognition
import threading
import time

app = Flask(__name__)

class HostelManagementSystem:
    def __init__(self):
        self.student_data = None
        self.known_faces = []
        self.known_names = []
        self.known_details = []
        self.entry_records_dir = "Entry_Record"
        self.student_data_file = "hoset_student_data.xlsx"
        
        # Create Entry_Record directory if it doesn't exist
        if not os.path.exists(self.entry_records_dir):
            os.makedirs(self.entry_records_dir)
        
        # Load student data and train face recognition
        self.load_student_data()
        self.train_face_recognition()
    
    def load_student_data(self):
        """Load student data from Excel file"""
        try:
            if os.path.exists(self.student_data_file):
                self.student_data = pd.read_excel(self.student_data_file)
                print(f"Loaded {len(self.student_data)} student records")
            else:
                print(f"Student data file {self.student_data_file} not found!")
                # Create sample data file
                self.create_sample_data()
        except Exception as e:
            print(f"Error loading student data: {e}")
            self.create_sample_data()
    
    def create_sample_data(self):
        """Create sample student data file"""
        sample_data = {
            'Sno': [1, 2, 3],
            'Roll no': ['2021001', '2021002', '2021003'],
            'Erp': ['ERP001', 'ERP002', 'ERP003'],
            'Name': ['John Doe', 'Jane Smith', 'Mike Johnson'],
            'Room no': ['A101', 'A102', 'B101'],
            'Mobile no': ['9876543210', '9876543211', '9876543212'],
            'Photo': ['photos/john.jpg', 'photos/jane.jpg', 'photos/mike.jpg']
        }
        
        df = pd.DataFrame(sample_data)
        df.to_excel(self.student_data_file, index=False)
        self.student_data = df
        print("Created sample student data file")
    
    def train_face_recognition(self):
        """Train face recognition with student photos"""
        if self.student_data is None:
            return
        
        self.known_faces = []
        self.known_names = []
        self.known_details = []
        
        for index, row in self.student_data.iterrows():
            photo_path = row['Photo']
            if pd.notna(photo_path) and os.path.exists(photo_path):
                try:
                    # Load image
                    image = face_recognition.load_image_file(photo_path)
                    # Get face encodings
                    encodings = face_recognition.face_encodings(image)
                    
                    if encodings:
                        self.known_faces.append(encodings[0])
                        self.known_names.append(row['Name'])
                        self.known_details.append({
                            'roll_no': row['Roll no'],
                            'erp': row['Erp'],
                            'name': row['Name'],
                            'room_no': row['Room no'],
                            'mobile_no': row['Mobile no']
                        })
                        print(f"Loaded face data for {row['Name']}")
                except Exception as e:
                    print(f"Error loading photo for {row['Name']}: {e}")
        
        print(f"Face recognition trained with {len(self.known_faces)} faces")
    
    def recognize_face(self, image):
        """Recognize face in the given image"""
        try:
            # Convert image to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(rgb_image)
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            for face_encoding in face_encodings:
                # Compare with known faces
                matches = face_recognition.compare_faces(self.known_faces, face_encoding, tolerance=0.6)
                face_distances = face_recognition.face_distance(self.known_faces, face_encoding)
                
                if matches:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        return self.known_details[best_match_index]
            
            return None
        except Exception as e:
            print(f"Error in face recognition: {e}")
            return None
    
    def get_today_file_path(self):
        """Get today's entry record file path"""
        today = datetime.now().strftime("%d_%m_%Y")
        return os.path.join(self.entry_records_dir, f"{today}.xlsx")
    
    def create_daily_record_file(self, file_path):
        """Create daily record file if it doesn't exist"""
        if not os.path.exists(file_path):
            columns = ['rollno', 'erp', 'name', 'Exit Time', 'Entry Time', 'room no', 'phone no']
            df = pd.DataFrame(columns=columns)
            df.to_excel(file_path, index=False)
    
    def record_entry_exit(self, student_details, action_type):
        """Record entry or exit in today's file"""
        try:
            file_path = self.get_today_file_path()
            self.create_daily_record_file(file_path)
            
            # Load existing data
            df = pd.read_excel(file_path)
            
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Check if student has any record today
            student_records = df[df['rollno'] == student_details['roll_no']]
            
            if len(student_records) == 0:
                # First record of the day
                new_record = {
                    'rollno': student_details['roll_no'],
                    'erp': student_details['erp'],
                    'name': student_details['name'],
                    'Exit Time': current_time if action_type == 'exit' else '',
                    'Entry Time': current_time if action_type == 'entry' else '',
                    'room no': student_details['room_no'],
                    'phone no': student_details['mobile_no']
                }
                df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
            else:
                # Find the last record for this student
                last_record_idx = student_records.index[-1]
                last_record = df.loc[last_record_idx]
                
                if action_type == 'exit':
                    if pd.isna(last_record['Exit Time']) or last_record['Exit Time'] == '':
                        # Update exit time for existing record
                        df.loc[last_record_idx, 'Exit Time'] = current_time
                    else:
                        # Create new record for another exit
                        new_record = {
                            'rollno': student_details['roll_no'],
                            'erp': student_details['erp'],
                            'name': student_details['name'],
                            'Exit Time': current_time,
                            'Entry Time': '',
                            'room no': student_details['room_no'],
                            'phone no': student_details['mobile_no']
                        }
                        df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
                
                elif action_type == 'entry':
                    if pd.isna(last_record['Entry Time']) or last_record['Entry Time'] == '':
                        # Update entry time for existing record
                        df.loc[last_record_idx, 'Entry Time'] = current_time
                    else:
                        # Create new record for another entry
                        new_record = {
                            'rollno': student_details['roll_no'],
                            'erp': student_details['erp'],
                            'name': student_details['name'],
                            'Exit Time': '',
                            'Entry Time': current_time,
                            'room no': student_details['room_no'],
                            'phone no': student_details['mobile_no']
                        }
                        df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
            
            # Save updated data
            df.to_excel(file_path, index=False)
            return True
            
        except Exception as e:
            print(f"Error recording entry/exit: {e}")
            return False

# Initialize the system
hostel_system = HostelManagementSystem()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recognize', methods=['POST'])
def recognize():
    try:
        # Get image data from request
        image_data = request.json['image']
        action_type = request.json.get('action', 'entry')  # 'entry' or 'exit'
        
        # Decode base64 image
        image_data = image_data.split(',')[1]  # Remove data:image/jpeg;base64,
        image_bytes = base64.b64decode(image_data)
        
        # Convert to OpenCV format
        pil_image = Image.open(BytesIO(image_bytes))
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Recognize face
        student_details = hostel_system.recognize_face(cv_image)
        
        if student_details:
            # Record entry/exit
            success = hostel_system.record_entry_exit(student_details, action_type)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f"✓ {action_type.capitalize()} recorded successfully!",
                    'student': student_details,
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'date': datetime.now().strftime("%d/%m/%Y")
                })
            else:
                return jsonify({
                    'success': False,
                    'message': "Face recognized but failed to record entry/exit"
                })
        else:
            return jsonify({
                'success': False,
                'message': "Face not recognized. Please try again."
            })
            
    except Exception as e:
        print(f"Error in recognition: {e}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        })

@app.route('/records')
def view_records():
    """View today's records"""
    try:
        file_path = hostel_system.get_today_file_path()
        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
            records = df.to_dict('records')
            return render_template('records.html', records=records, date=datetime.now().strftime("%d/%m/%Y"))
        else:
            return render_template('records.html', records=[], date=datetime.now().strftime("%d/%m/%Y"))
    except Exception as e:
        return f"Error loading records: {e}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)