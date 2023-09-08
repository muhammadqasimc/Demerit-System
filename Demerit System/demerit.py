import base64
import io
from zipfile import ZipFile
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, send_from_directory
import pandas as pd
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from playsound import playsound
import csv  # Added for CSV file operations
from flask import send_file, request
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

app = Flask(__name__)

# Constants for file paths
STUDENT_DATA_CSV = 'student_data.csv'
PENDING_SUBMISSIONS_CSV = 'pending_submissions.csv'

# Lists to store submissions
submissions_pending_approval = []
approved_submissions = []

# Declare the df variable as global
df = None

def load_data():
    global df
    df = pd.read_csv(STUDENT_DATA_CSV)

# Call the load_data function to load the CSV data when the app starts
load_data()

# Function to load pending submissions from a CSV file
def load_pending_submissions():
    pending_submissions = []
    try:
        with open(PENDING_SUBMISSIONS_CSV, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                pending_submissions.append(row)
    except FileNotFoundError:
        # If the file doesn't exist, start with an empty list
        pass
    return pending_submissions

# Function to save pending submissions to a CSV file
def save_pending_submissions(submissions):
    with open(PENDING_SUBMISSIONS_CSV, mode='w', newline='') as file:
        fieldnames = ['Name', 'Grade', 'Date', 'Offenses']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for submission in submissions:
            writer.writerow(submission)

# Load pending submissions when the app starts
submissions_pending_approval = load_pending_submissions()

# Dummy user data for demonstration purposes
users = {
    'admin': {
        'password': 'password123',  # You should hash passwords in a real app
        'is_admin': True
    },
    'user1': {
        'password': 'userpassword',
        'is_admin': False
    }
}

# Set a secret key for session management
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    df['Grade'] = df['Grade'].astype(int)
    
    # Get unique grade values
    grades = sorted(df['Grade'].unique())
    
    # Create a dictionary to store names grouped by grade
    names_by_grade = {}
    for grade in grades:
        names_by_grade[grade] = df[df['Grade'] == grade]['Name'].tolist()
    
    return render_template('index.html', grades=grades, namesByGrade=names_by_grade)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and password == users[username]['password']:
            session['username'] = username
            return redirect(url_for('admin'))

    return render_template('login.html')

@app.route('/select_name', methods=['POST'])
def select_name():
    selected_name = request.form['name']
    
    # Filter data by the selected name and non-empty Date and Offenses
    filtered_data = df[(df['Name'] == selected_name) & ~df['Date'].isnull() & ~df['Offenses'].isnull()]
    
    return render_template('select_name.html', data=filtered_data)

@app.route('/get_names_by_grade/<int:selected_grade>')
def get_names_by_grade(selected_grade):
    names = df[df['Grade'] == selected_grade]['Name'].tolist()
    return jsonify(names)

@app.route('/submit_form', methods=['POST'])
def submit_form():
    selected_grade = request.form['grade']
    selected_name = request.form['name']
    selected_offenses = request.form.getlist('offense')
    current_date = datetime.now().strftime('%Y-%m-%d')
    

    
    # Create a new submission dictionary
    new_submission = {
        'Name': selected_name,
        'Grade': selected_grade,
        'Date': current_date,
        'Offenses': ', '.join(selected_offenses)
    }

    # Append the submission to the pending approval list
    submissions_pending_approval.append(new_submission)

    # Save pending submissions to the CSV file
    save_pending_submissions(submissions_pending_approval)

    # Notify with a sound
    playsound('static/ding.mp3')

    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if 'username' in session:
        username = session['username']
        if users[username]['is_admin']:
            return render_template('admin.html', submissions=submissions_pending_approval)
        else:
            return 'You are not authorized to access this page.'
    return redirect(url_for('login'))

@app.route('/approve_submission/<int:index>')
def approve_submission(index):
    if 0 <= index < len(submissions_pending_approval):
        submission = submissions_pending_approval.pop(index)
        approved_submissions.append(submission)
        
        # Create directory structure for the grade
        grade_folder = os.path.join('Demerits', f'Grade_{submission["Grade"]}')
        os.makedirs(grade_folder, exist_ok=True)

        # Generate a unique filename based on name and date
        base_filename = f'{submission["Name"]}_{submission["Date"]}.csv'
        filename = base_filename
        counter = 1

        # Check if the file already exists and generate a new filename if needed
        while os.path.exists(os.path.join(grade_folder, filename)):
            filename = f'{submission["Name"]}_{submission["Date"]}_{counter}.csv'
            counter += 1

        # Save the submission to the unique CSV file in the grade folder
        with open(os.path.join(grade_folder, filename), mode='w', newline='') as file:
            fieldnames = ['Name', 'Grade', 'Date', 'Offenses']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(submission)
        
        # Save pending submissions to the CSV file
        save_pending_submissions(submissions_pending_approval)
        
        # Notify with a sound
        # Start of the code snippet for saving to XLSX with styling
        # Save the submission to an XLSX file with styling
        xlsx_filename = os.path.join(grade_folder, filename.replace('.csv', '.xlsx'))

        # Create a Pandas DataFrame from the submission data
        submission_df = pd.DataFrame([submission])

        # Create a Pandas ExcelWriter using openpyxl as the engine
        excel_writer = pd.ExcelWriter(xlsx_filename, engine='openpyxl')

        # Write the DataFrame to the Excel file with styling
        submission_df.to_excel(excel_writer, index=False, header=False)

        # Get the xlsxwriter workbook and worksheet objects from the Pandas ExcelWriter
        workbook  = excel_writer.book
        worksheet = workbook.active  # Use the default (first) worksheet

        # Create a header row with styling
        header_format = Font(bold=True)
        header_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
        for col_num, value in enumerate(submission_df.columns.values):
            cell = worksheet.cell(row=1, column=col_num+1)
            cell.value = value
            cell.font = header_format
            cell.fill = header_fill

        # Save the Excel file
        excel_writer.save()
        # End of the code snippet for saving to XLSX with styling


    return redirect(url_for('admin'))

@app.route('/reject_submission/<int:index>')
def reject_submission(index):
    if 0 <= index < len(submissions_pending_approval):
        submission = submissions_pending_approval.pop(index)
        # Perform any rejection action here (e.g., delete the submission)
        # Save pending submissions to the CSV file
        save_pending_submissions(submissions_pending_approval)
        # Notify with a sound

    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from the session
    return redirect(url_for('login'))

@app.route('/csv_files', methods=['GET', 'POST'])
def csv_files():
    # Create a list to store the available CSV files
    csv_file_list = []

    # Specify the directory where the CSV files are located
    csv_directory = 'Demerits'

    # Loop through the grade directories and list CSV files
    for grade_folder in os.listdir(csv_directory):
        if os.path.isdir(os.path.join(csv_directory, grade_folder)):
            grade_path = os.path.join(csv_directory, grade_folder)
            for csv_file in os.listdir(grade_path):
                if csv_file.endswith('.csv'):
                    # Construct the full file path
                    file_path = os.path.join(grade_path, csv_file)
                    # Create a dictionary with file information
                    csv_info = {
                        'grade_folder': grade_folder,
                        'file_name': csv_file,
                        'file_path': file_path,
                    }
                    csv_file_list.append(csv_info)

    # Get unique grade values for the grade filter dropdown
    grades = sorted(set(info['grade_folder'] for info in csv_file_list))

    # Get unique student names for the student filter dropdown
    students = sorted(set(info['file_name'].split('_')[0] for info in csv_file_list))

    # Initialize the filtered file list
    filtered_csv_files = csv_file_list

    if request.method == 'POST':
        selected_grade = request.form.get('selected_grade')
        selected_student = request.form.get('selected_student')

        # Apply grade filter
        if selected_grade:
            filtered_csv_files = [info for info in filtered_csv_files if info['grade_folder'] == selected_grade]

        # Apply student filter
        if selected_student:
            filtered_csv_files = [info for info in filtered_csv_files if info['file_name'].startswith(selected_student)]

    return render_template('csv_files.html', csv_files=csv_file_list, grades=grades, students=students,
                           filtered_csv_files=filtered_csv_files)

@app.route('/filter_by_grade', methods=['POST'])
def filter_by_grade():
    selected_grade = request.form.get('selected_grade')

    # Specify the directory where the CSV files are located
    csv_directory = 'Demerits'

    # Create a list to store the available CSV files
    csv_file_list = []

    # Loop through the grade directories and list CSV files
    for grade_folder in os.listdir(csv_directory):
        if os.path.isdir(os.path.join(csv_directory, grade_folder)):
            grade_path = os.path.join(csv_directory, grade_folder)
            for csv_file in os.listdir(grade_path):
                if csv_file.endswith('.csv'):
                    # Construct the full file path
                    file_path = os.path.join(grade_path, csv_file)
                    # Create a dictionary with file information
                    csv_info = {
                        'grade_folder': grade_folder,
                        'file_name': csv_file,
                        'file_path': file_path,
                    }
                    csv_file_list.append(csv_info)

    # Get unique grade values for the grade filter dropdown
    grades = sorted(set(info['grade_folder'] for info in csv_file_list))

    # Get unique student names for the student filter dropdown
    students = sorted(set(info['file_name'].split('_')[0] for info in csv_file_list))

    # Apply grade filter
    if selected_grade:
        csv_file_list = [info for info in csv_file_list if info['grade_folder'] == selected_grade]

    return render_template('csv_files.html', csv_files=csv_file_list, grades=grades, students=students,
                           filtered_csv_files=csv_file_list)


@app.route('/filter_by_student', methods=['POST'])
def filter_by_student():
    selected_student = request.form.get('selected_student')

    # Specify the directory where the CSV files are located
    csv_directory = 'Demerits'

    # Create a list to store the available CSV files
    csv_file_list = []

    # Loop through the grade directories and list CSV files
    for grade_folder in os.listdir(csv_directory):
        if os.path.isdir(os.path.join(csv_directory, grade_folder)):
            grade_path = os.path.join(csv_directory, grade_folder)
            for csv_file in os.listdir(grade_path):
                if csv_file.endswith('.csv'):
                    # Construct the full file path
                    file_path = os.path.join(grade_path, csv_file)
                    # Create a dictionary with file information
                    csv_info = {
                        'grade_folder': grade_folder,
                        'file_name': csv_file,
                        'file_path': file_path,
                    }
                    csv_file_list.append(csv_info)

    # Get unique grade values for the grade filter dropdown
    grades = sorted(set(info['grade_folder'] for info in csv_file_list))

    # Get unique student names for the student filter dropdown
    students = sorted(set(info['file_name'].split('_')[0] for info in csv_file_list))

    # Apply student filter
    if selected_student:
        csv_file_list = [info for info in csv_file_list if info['file_name'].startswith(selected_student)]

    return render_template('csv_files.html', csv_files=csv_file_list, grades=grades, students=students,
                           filtered_csv_files=csv_file_list)


@app.route('/filter_by_date', methods=['POST'])
def filter_by_date():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    # Specify the directory where the CSV files are located
    csv_directory = 'Demerits'

    # Create a list to store the available CSV files
    csv_file_list = []

    # Loop through the grade directories and list CSV files
    for grade_folder in os.listdir(csv_directory):
        if os.path.isdir(os.path.join(csv_directory, grade_folder)):
            grade_path = os.path.join(csv_directory, grade_folder)
            for csv_file in os.listdir(grade_path):
                if csv_file.endswith('.csv'):
                    # Construct the full file path
                    file_path = os.path.join(grade_path, csv_file)
                    # Check if the file matches the date range
                    file_date = csv_file.split('_')[1]
                    if start_date <= file_date <= end_date:
                        # Create a dictionary with file information
                        csv_info = {
                            'grade_folder': grade_folder,
                            'file_name': csv_file,
                            'file_path': file_path,
                        }
                        csv_file_list.append(csv_info)

    # Get unique grade values for the grade filter dropdown
    grades = sorted(set(info['grade_folder'] for info in csv_file_list))

    # Get unique student names for the student filter dropdown
    students = sorted(set(info['file_name'].split('_')[0] for info in csv_file_list))

    return render_template('csv_files.html', csv_files=csv_file_list, grades=grades, students=students,
                           filtered_csv_files=csv_file_list)

@app.route('/bulk_download_csv', methods=['POST'])
def bulk_download_csv():
    selected_files = request.form.getlist('selected_files')

    # Check if any files are selected for download
    if not selected_files:
        return "No files selected for download."

    # Create a zip file containing the selected CSV files
    zip_filename = 'bulk_download.zip'
    with ZipFile(zip_filename, 'w') as zipf:
        for file_path in selected_files:
            # Make sure the selected file exists and is allowed for download
            if os.path.exists(file_path):
                zipf.write(file_path, os.path.basename(file_path))

    # Send the zip file for download
    return send_file(zip_filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host='192.168.10.43', port=8082)
