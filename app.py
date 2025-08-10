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

app = Flask(__name__)

class HostelManagementSystem:
    def __init__(self):
        self.student_data = None
        self.known_faces = []
        self.known_names = []
        self.known_details = []
        self.entry_records_dir = "Entry_Record"
        self.student_data_file = "hoset_student_data.xlsx"
        
        if not os.path.exists(self.entry_records_dir):
            os.makedirs(self.entry_records_dir)
        
        self.load_student_data()
        self.train_face_recognition()
    
    def load_student_data(self):
        try:
            if os.path.exists(self.student_data_file):
                self.student_data = pd.read_excel(self.student_data_file)
                print(f"Loaded {len(self.student_data)} student records")
            else:
                print(f"Student data file {self.student_data_file} not found!")
                self.create_sample_data()
        except Exception as e:
            print(f"Error loading student data: {e}")
            self.create_sample_data()
    
    def create_sample_data(self):
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
        if self.student_data is None:
            return
        
        self.known_faces = []
        self.known_names = []
        self.known_details = []
        
        for index, row in self.student_data.iterrows():
            photo_path = row['Photo']
            if pd.notna(photo_path) and os.path.exists(photo_path):
                try:
                    image = face_recognition.load_image_file(photo_path)
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
        try:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_image)
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            for face_encoding in face_encodings:
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
        today = datetime.now().strftime("%d_%m_%Y")
        return os.path.join(self.entry_records_dir, f"{today}.xlsx")
    
    def create_daily_record_file(self, file_path):
        if not os.path.exists(file_path):
            columns = ['rollno', 'erp', 'name', 'Exit Time', 'Entry Time', 'room no', 'phone no']
            df = pd.DataFrame(columns=columns)
            df.to_excel(file_path, index=False)
    
    def record_entry_exit(self, student_details, action_type):
        """
        Clean pairing logic:
        - If no record today for student: first action must be EXIT (creates new row).
        - If last row has Exit Time set and Entry Time empty: next allowed action is ENTRY (fills same row).
        - If last row has both Exit & Entry set: next allowed action is EXIT (creates new row).
        - Prevents double exit/entry in a row. Returns True on success or an error message string.
        """
        try:
            file_path = self.get_today_file_path()
            self.create_daily_record_file(file_path)
            
            # Load today's file
            df = pd.read_excel(file_path)
            current_time = datetime.now().strftime("%H:%M:%S")

            # helper to detect if a cell is filled
            def filled(val):
                return not (pd.isna(val) or str(val).strip() == "")

            # get student's rows
            student_records = df[df['rollno'] == student_details['roll_no']]

            # No record today -> only EXIT allowed (first action)
            if student_records.empty:
                if action_type == 'entry':
                    return "❌ First action today must be EXIT. Please record EXIT first."
                
                # create new row with Exit Time
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
                df.to_excel(file_path, index=False)
                return True

            # There is at least one row for this student today
            last_idx = student_records.index[-1]
            last_row = df.loc[last_idx]
            exit_filled = filled(last_row.get('Exit Time', ''))
            entry_filled = filled(last_row.get('Entry Time', ''))

            # Case A: last row has Exit filled but Entry empty -> last action was EXIT -> only ENTRY allowed (fills same row)
            if exit_filled and not entry_filled:
                if action_type != 'entry':
                    return "❌ You must record ENTRY next to complete the last EXIT."
                # fill Entry Time in same row
                df.at[last_idx, 'Entry Time'] = current_time
                df.to_excel(file_path, index=False)
                return True

            # Case B: last row has both Exit and Entry filled -> last action was ENTRY -> only EXIT allowed (start new pair/row)
            if exit_filled and entry_filled:
                if action_type != 'exit':
                    return "❌ You must record EXIT."
                # create new row with Exit Time
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
                df.to_excel(file_path, index=False)
                return True

            # Case C: last row has neither Exit nor Entry filled (malformed) -> treat EXIT as start, ENTRY invalid until EXIT exists
            if (not exit_filled) and (not entry_filled):
                if action_type == 'exit':
                    df.at[last_idx, 'Exit Time'] = current_time
                    df.to_excel(file_path, index=False)
                    return True
                else:
                    return "❌ Invalid state: please record EXIT first."

            # Case D: last row has Entry filled but Exit empty (unexpected with our logic) -> allow EXIT to fill it
            if (not exit_filled) and entry_filled:
                if action_type == 'exit':
                    df.at[last_idx, 'Exit Time'] = current_time
                    df.to_excel(file_path, index=False)
                    return True
                else:
                    return "❌ Cannot record ENTRY now. Please record EXIT first."

            # Fallback
            return "❌ Invalid action or state. Please contact admin."

        except Exception as e:
            print(f"Error recording entry/exit: {e}")
            return f"❌ Error recording entry/exit: {e}"


# Initialize the system
hostel_system = HostelManagementSystem()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recognize', methods=['POST'])
def recognize():
    try:
        image_data = request.json['image']
        action_type = request.json.get('action', 'entry')
        
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        
        pil_image = Image.open(BytesIO(image_bytes))
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        student_details = hostel_system.recognize_face(cv_image)
        
        if student_details:
            result = hostel_system.record_entry_exit(student_details, action_type)
            
            if result is True:
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
                    'message': result
                })
        else:
            return jsonify({
                'success': False,
                'message': "❌ Face not recognized. Please try again."
            })
            
    except Exception as e:
        print(f"Error in recognition: {e}")
        return jsonify({
            'success': False,
            'message': f"❌ Error: {str(e)}"
        })

@app.route('/records')
def view_records():
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
