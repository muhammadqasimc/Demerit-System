import base64
import io
import uuid
from flask import abort, current_app
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
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas  # Add this import statement
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from werkzeug.utils import secure_filename
from PIL import Image as PILImage



from fpdf import FPDF




app = Flask(__name__)

# Constants for file paths

PENDING_SUBMISSIONS_CSV = 'pending_submissions.csv'

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Lists to store submissions
submissions_pending_approval = []
approved_submissions = []


# Use the correct path to your 'namewithid.csv' file
NAMWITHID_CSV = 'namewithid.csv'

# Global variable to store the dataframe
df = None

@app.route('/get_names_by_grade/<int:selected_grade>')
def get_names_by_grade(selected_grade):
    # Make sure to load the data if it's not already loaded
    if df is None:
        load_data()
    
    # Filter the dataframe by the selected grade and return the required fields
    filtered_data = df[df['Grade'] == selected_grade][['Learnerid', 'Name']]
    # Convert the filtered data to a list of dictionaries
    names_with_ids = filtered_data.to_dict(orient='records')
    return jsonify(names_with_ids)

def load_data():
    global df
    # Load the data from the CSV file
    df = pd.read_csv(NAMWITHID_CSV)

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
        fieldnames = ["Name", "Grade", "Date", "Notes", 'Username', "Offenses", "LearnerId", "StudentSignature", "TeacherSignature", "WitnessSignature", "offenseId",  # This seems to be repeated for different values, you likely want to use different keys
    "offenseLevel",
    "offenseCode",
    "offenseType",
    "offensePoint"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for submission in submissions:
            writer.writerow(submission)

# Load pending submissions when the app starts
submissions_pending_approval = load_pending_submissions()

# Dummy user data for demonstration purposes
users = {
    'JAMESON A -4': {
        'password': 'password123',
        'is_admin': True
    },
    'KGONGWANA E -20': {
        'password': 'userpassword',
        'is_admin': False
    },
    'VARGHESE S -16': {
        'password': 'randompassword1',
        'is_admin': False
    },
    'JOHN B -14': {
        'password': 'randompassword2',
        'is_admin': False
    },
    'JOUBERT R -2': {
        'password': 'randompassword3',
        'is_admin': False
    },
    'JAMESON C -12': {
        'password': 'randompassword4',
        'is_admin': False
    },
    'BESTER N -17': {
        'password': 'randompassword5',
        'is_admin': False
    },
    'CLAASSENS CH -22': {
        'password': 'randompassword6',
        'is_admin': False
    },
    'VAN EEDEN B -38': {
        'password': 'randompassword7',
        'is_admin': False
    },
    'GELDENHUYS SM -44': {
        'password': 'randompassword8',
        'is_admin': False
    },
    'MOSENTHAL V D -46': {
        'password': 'randompassword9',
        'is_admin': False
    },
    'BEZUIDENHOUT M -47': {
        'password': 'randompassword10',
        'is_admin': False
    },
    'STRYDOM F -48': {
        'password': 'randompassword11',
        'is_admin': False
    },
    'BRUWER B -51': {
        'password': 'randompassword12',
        'is_admin': False
    },
    'FOURIE L -49': {
        'password': 'randompassword13',
        'is_admin': False
    },
    'JANKOWITZ J -52': {
        'password': 'randompassword14',
        'is_admin': False
    },
    'TAYOB N -53': {
        'password': 'randompassword15',
        'is_admin': False
    },
    'PATTASSERIL BABU B -55': {
        'password': 'randompassword16',
        'is_admin': False
    },
    'GELDENHUYS H D -56': {
        'password': 'randompassword17',
        'is_admin': False
    },
    'GOOSEN C -57': {
        'password': 'randompassword18',
        'is_admin': False
    },
    'REDIKER L -58': {
        'password': 'randompassword19',
        'is_admin': False
    },
    'JONKER F -59': {
        'password': 'randompassword20',
        'is_admin': False
    },
    'DU TOIT WD -60': {
        'password': 'randompassword21',
        'is_admin': False
    },
    'admin': {
        'password': '123',
        'is_admin': True
    }
}

# Set a secret key for session management
app.secret_key = os.urandom(24)

def is_logged_in():
    return 'username' in session


@app.route('/')
def index():
    if 'username' in session:
        df['Grade'] = df['Grade'].astype(int)
        
        # Get unique grade values
        grades = sorted(df['Grade'].unique())
        
        # Create a dictionary to store names grouped by grade
        names_by_grade = {}
        for grade in grades:
            names_by_grade[grade] = df[df['Grade'] == grade]['Name'].tolist()
        
        return render_template('index.html', grades=grades, namesByGrade=names_by_grade)
    else:
        # Redirect to the login page if the user is not logged in
        return redirect(url_for('login'))

@app.route('/green')
def green():
    if 'username' in session:
        df['Grade'] = df['Grade'].astype(int)
        
        # Get unique grade values
        grades = sorted(df['Grade'].unique())
        
        # Create a dictionary to store names grouped by grade
        names_by_grade = {}
        for grade in grades:
            names_by_grade[grade] = df[df['Grade'] == grade]['Name'].tolist()
        return render_template('green.html', grades=grades, namesByGrade=names_by_grade)
    else:
        return redirect(url_for('login'))

@app.route('/yellow')
def yellow():
    if 'username' in session:
        df['Grade'] = df['Grade'].astype(int)
        
        # Get unique grade values
        grades = sorted(df['Grade'].unique())
        
        # Create a dictionary to store names grouped by grade
        names_by_grade = {}
        for grade in grades:
            names_by_grade[grade] = df[df['Grade'] == grade]['Name'].tolist()

        # Read the offenses from the CSV file
        offenses_df = pd.read_csv('yellowcodes.csv')
        
        # Convert the DataFrame to a list of dictionaries for easy handling in the template
        offenses_list = offenses_df.to_dict(orient='records')

        return render_template('yellow.html', grades=grades, offenses=offenses_list, namesByGrade=names_by_grade)
    else:
        return redirect(url_for('login'))
    

@app.route('/pink')
def pink():
    if 'username' in session:
        df['Grade'] = df['Grade'].astype(int)
        
        # Get unique grade values
        grades = sorted(df['Grade'].unique())
        
        # Create a dictionary to store names grouped by grade
        names_by_grade = {}
        for grade in grades:
            names_by_grade[grade] = df[df['Grade'] == grade]['Name'].tolist()
        return render_template('pink.html', grades=grades, namesByGrade=names_by_grade)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and password == users[username]['password']:
            session['username'] = username
            return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/select_name', methods=['POST'])
def select_name():
    selected_name = request.form['name']
    
    # Filter data by the selected name and non-empty Date and Offenses
    filtered_data = df[(df['Name'] == selected_name) & ~df['Date'].isnull() & ~df['Offenses'].isnull()]
    
    return render_template('select_name.html', data=filtered_data)


# Define the directory where signature images will be saved
signature_folder = 'signatures'

@app.route('/submit_form', methods=["GET", 'POST'])
def submit_form():
        if request.method == "POST":
            photo = request.files["photo"]

            if photo:
                # Retrieve the selected name from the form data
                selected_name = request.form["name"]

                # Get the current date in the format YYYY-MM-DD
                current_date = datetime.now().strftime("%d-%m-%y")

                # Combine the selected name and current date to create the filename
                raw_filename = f"{selected_name}_{current_date}.jpg"
                filename = secure_filename(raw_filename)

                photo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

                # Save the uploaded photo to the specified directory
                photo.save(photo_path)

                
        selected_grade = request.form['grade']
        selected_name = request.form['name']
        selected_offenses = request.form.getlist('offense')
        current_date = datetime.now().strftime('%d-%m-%y')
        notes = request.form['notes']  # Retrieve the notes from the form
        username = session['username']
        selected_learnerid = request.form['learner_id']

        offense_id = request.form.get('Id')
        offense_level = request.form.get('Level')
        offense_code = request.form.get('Code')
        offense_type = request.form.get('Type')
        offense_point = request.form.get('Point')
        
        # # Handle the student's signature
        # student_signature_data_url = request.form['student_signature']
        # if student_signature_data_url:
        #     # Generate a unique filename for the student's signature image
        #     student_signature_filename = f'{selected_name}_{current_date}.png'
        #     student_signature_path = os.path.join(signature_folder, student_signature_filename)

        #     # Convert the data URL back to an image and save it as a PNG
        #     student_signature_image_data = student_signature_data_url.split(',')[1]
        #     student_signature_image_binary = base64.b64decode(student_signature_image_data)
        #     with open(student_signature_path, 'wb') as student_signature_file:
        #         student_signature_file.write(student_signature_image_binary)

        # Generate a unique filename for the digital signature image
        student_signature_filename = f'{selected_name}.png'
        signature_path1 = os.path.join(signature_folder, student_signature_filename)

        # Create an image with the selected name as signature
        img1 = Image.new('RGB', (650, 250), color = (255, 255, 255))
        d = ImageDraw.Draw(img1)
        font = ImageFont.truetype("static/Andina Demo.otf", 48)  # Specify the path to a signature-style font file
        d.text((10,10), selected_name, font=font, fill=(0,0,0))

        # Generate a unique filename for the teacher digital signature image
        teacher_signature_filename = f'{username}.png'
        signature_path = os.path.join(signature_folder, teacher_signature_filename)

        # Create an image with the selected name as signature
        img = Image.new('RGB', (650, 250), color = (255, 255, 255))
        d1 = ImageDraw.Draw(img)
        font = ImageFont.truetype("static/Andina Demo.otf", 48)  # Specify the path to a signature-style font file
        d1.text((10,10), username, font=font, fill=(0,0,0))

        # Save the signature image

        img1.save(signature_path1)
        img.save(signature_path)

        # Handle the teacher's signature (similar code as above)
        teacher_signature_data_url = request.form['teacher_signature']
        if teacher_signature_data_url:
            teacher_signature_filename = f'{username}_{current_date}.png'
            teacher_signature_path = os.path.join(signature_folder, teacher_signature_filename)
            teacher_signature_image_data = teacher_signature_data_url.split(',')[1]
            teacher_signature_image_binary = base64.b64decode(teacher_signature_image_data)
            with open(teacher_signature_path, 'wb') as teacher_signature_file:
                teacher_signature_file.write(teacher_signature_image_binary)


        # Handle the witness's signature (similar code as above)
        witness_signature_data_url = request.form['witness_signature']
        if witness_signature_data_url:
            witness_signature_filename = f'witness_signature_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
            witness_signature_path = os.path.join(signature_folder, witness_signature_filename)
            witness_signature_image_data = witness_signature_data_url.split(',')[1]
            witness_signature_image_binary = base64.b64decode(witness_signature_image_data)
            with open(witness_signature_path, 'wb') as witness_signature_file:
                witness_signature_file.write(witness_signature_image_binary)


        # Create a new submission dictionary
        new_submission = {
            'Name': selected_name,
            'Grade': selected_grade,
            'Date': current_date,
            'Offenses': ', '.join(selected_offenses),
            'Notes': notes,
            'Username' : username,
            'LearnerId' : selected_learnerid,
            'offenseId' : offense_id,
            "offenseLevel": offense_level,
            "offenseCode": offense_code,
            "offenseType": offense_type,
            "offensePoint": offense_point


        }

        # Append the submission to the pending approval list
        submissions_pending_approval.append(new_submission)

        # Save pending submissions to the CSV file
        save_pending_submissions(submissions_pending_approval)

        # Notify with a sound
        playsound('static/ding.mp3')

        return redirect(url_for('index'))
    
    


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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

        # Get the current time in HH:MM format
        current_time = datetime.now().strftime("%H:%M")

        logo_image = Image.open('static/Logo.png')
        logo_image = logo_image.convert('RGB')  # Convert to RGB format (optional)
        logo_image.save('static/Logo_non_interlaced1.png', 'PNG', optimize=True)

        logo_filename = 'static/Logo_non_interlaced1.png'
        logo_width = 130  # Width of the logo in millimeters
        logo_height = 40  # Height of the logo in millimeters


        # Use the current time in the filename
        pdf_filename = f'{submission["Name"].replace(" ", "_")}_{submission["Date"]}_{current_time}.pdf'

        pdf_path = os.path.join(grade_folder, pdf_filename)

        # Create a PDF with A4 size (210x297 mm) in landscape mode
        pdf = FPDF(format='A4', unit='mm')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)  # Automatic page break with a 15mm margin
        pdf.set_font("Arial", size=12)
        
        # Calculate the x-coordinate to center the logo horizontally
        logo_x = (pdf.w - logo_width) / 2

        # Load and embed the logo image
        pdf.image(logo_filename, x=logo_x, y=pdf.get_y(), w=logo_width, h=logo_height)  # Adjust position and size

        # Move down to create space for the logo
        pdf.ln(logo_height)


        # Adjusted positions and sizes for A4 portrait
        pdf.cell(0, 10, txt="Demerits Form", ln=True, align='C')  # Background fill
        pdf.ln(10)  # Add some space

        # Left Column
        pdf.set_fill_color(200, 200, 200)  # Background fill color
        column_width = 90  # Adjust the column width as needed
        column_width1 = 25  # Adjust the column width as needed

        pdf.cell(column_width1, 10, txt="Name:", fill=True)
        pdf.cell(column_width, 10, txt=submission['Name'], ln=True)

        pdf.cell(column_width1, 10, txt="Grade:", fill=True)
        pdf.cell(column_width, 10, txt=str(submission['Grade']), ln=True)

        pdf.cell(column_width1, 10, txt="Date:", fill=True)
        pdf.cell(column_width, 10, txt=submission['Date'], ln=True)

        pdf.cell(column_width1, 10, txt="Notes:", fill=True)
        pdf.cell(column_width, 10, txt=submission['Notes'], ln=True)

        pdf.cell(column_width1, 10, txt="Educator:", fill=True)
        pdf.cell(column_width, 10, txt=submission['Username'], ln=True)

        pdf.cell(column_width1, 10, txt="Offenses:", fill=True)
        pdf.cell(column_width, 10, txt=submission['Offenses'], ln=True)  # Multiline cell for offenses

        pdf.ln(10)  # Add some space

        # Title for the student's signature cell
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(0, 10, txt="Student Signature", ln=True, align='C')

        # Create a cell for the student's signature
        pdf.set_fill_color(255, 255, 255)  # White background
        pdf.cell(0, 30, txt="", border=1, ln=True)  # Cell for the signature with borders

        # Load and embed the student's signature image within the cell
        student_signature_filename = f'{submission["Name"]}.png'
        student_signature_path = os.path.join(signature_folder, student_signature_filename)
        pdf.image(student_signature_path, x=pdf.get_x() + 5, y=pdf.get_y() - 25, w=0, h=20)  # Adjust position and size

        # Title for the teacher's signature cell
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(0, 10, txt="Teacher Signature", ln=True, align='C')

        # Create a cell for the teacher's signature
        pdf.set_fill_color(255, 255, 255)  # White background
        pdf.cell(0, 30, txt="", border=1, ln=True)  # Cell for the signature with borders

        # Load and embed the teacher's signature image within the cell
        teacher_signature_filename = f'{submission["Username"]}.png'
        teacher_signature_path = os.path.join(signature_folder, teacher_signature_filename)
        pdf.image(teacher_signature_path, x=pdf.get_x() + 5, y=pdf.get_y() - 25, w=0, h=20)  # Adjust position and size


        # # Title for the witness's signature
        # pdf.set_font("Arial", style='B', size=12)
        # pdf.cell(20190, 10, txt="Witness Signature", ln=True, align='C')

        # # Create a box for the witness's signature
        # pdf.set_fill_color(255, 255, 255)  # White background
        # pdf.rect(10, pdf.get_y(), 190, 40, style='F')  # Rectangle for the signature

        # # Load and embed the witness's signature image in the box
        # witness_signature_filename = f'witness_signature_{submission["Date"]}.png'
        # witness_signature_path = os.path.join(signature_folder, witness_signature_filename)
        # pdf.image(witness_signature_path, x=15, y=pdf.get_y() + 5, w=180, h=30)  # Adjust position and size


        # Extract the image filename from the submission data
        image_filename = f'{submission["Name"].replace(" ", "_")}_{submission["Date"]}.jpg'
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], image_filename)


        # Check if the image exists (it's good to have a safety check)
        if os.path.exists(image_path):
            # Add a new page to the PDF
            pdf.add_page()

            # Use PIL to get image dimensions
            with PILImage.open(image_path) as img:
                img_width, img_height = img.size

            # A4 dimensions in points
            a4_width_mm = 210
            a4_height_mm = 297

            # Calculate the scaling factor
            width_scale = a4_width_mm / img_width
            height_scale = a4_height_mm / img_height
            scale_factor = min(width_scale, height_scale)

            # Calculate the new image dimensions
            new_img_width = img_width * scale_factor
            new_img_height = img_height * scale_factor

            # Embed the image in the new page
            pdf.image(image_path, x=(a4_width_mm - new_img_width) / 2, y=(a4_height_mm - new_img_height) / 2, w=new_img_width, h=new_img_height)

        # Save the PDF to the file
        pdf.output(pdf_path)

        # Parse the original date assuming it's in the format "dd/mm/yy"
        original_date = datetime.strptime(submission['Date'], '%d-%m-%y')

        # Format the date into the required formats
        formatted_date = original_date.strftime('%d/%m/%y') + ' 00:00:00'  # Adding the '00:00:00' part manually
        formatted_month = original_date.strftime('%m')
        formatted_year = original_date.strftime('%Y')

        # Now, map the submission data to your new CSV headers
        mapped_submission = {
            'id': '',  # Assuming you need to generate or have an ID
            'Learnerid': submission['LearnerId'],  # Replace with actual key if exists
            'Date': formatted_date,
            'Comment': submission['Notes'],
            'LevelMisconduct': submission['offenseLevel'],
            'MisconductCode': submission['offenseCode'],
            'MisconductDescription': submission['Offenses'],
            'ActionLevel' : '',
            'ActionCode' : '',
            'ActionDescription': '',
            'DisciplinedBy': '',
            'AuthorisedBy': submission['Username'],
            'Agency': '',
            'Suspension': '0',
            'Option': '',
            'ExpulsionDate': '',
            'Month': formatted_month,
            'RecommendedExpulsion': '',
            'Datayear': formatted_year,
            'Demerit' : submission['offensePoint'],
            'Merit': '0',
            'Type': 'Demerit'
        }

        # Define the path to the CSV file
        csv_file_path = 'mdb-import.csv'

        # Check if the file exists and if not, write the header
        file_exists = os.path.isfile(csv_file_path)

        with open(csv_file_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=mapped_submission.keys())
            
            # Write the header only if the file does not exist
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(mapped_submission)

        # Save pending submissions to the CSV file
        save_pending_submissions(submissions_pending_approval)

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

@app.route('/reset_mdb', methods=['POST'])
def reset_mdb():
    # Define the path to the CSV file
    csv_file_path = 'mdb-import.csv'
    
    # Open the file in write mode to clear its contents
    with open(csv_file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write the headers to the CSV file
        writer.writerow([
            'id', 'Learnerid', 'Date', 'Comment', 'LevelMisconduct', 'MisconductCode',
            'MisconductDescription', 'ActionLevel', 'ActionCode', 'ActionDescription',
            'DisciplinedBy', 'AuthorisedBy', 'Agency', 'Suspension', 'Option',
            'ExpulsionDate', 'Month', 'RecommendedExpulsion', 'Datayear',
            'Demerit', 'Merit', 'Type'
        ])
    
    # Redirect to the admin page or another appropriate page
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from the session
    return redirect(url_for('login'))


@app.route('/get_directory_data', methods=['GET'])
def get_directory_data():
    base_directory = os.path.join(os.getcwd(), 'Demerits')
    
    grades = set()
    names = set()

    # Walk through the directory to gather grade folders and names from filenames
    for root, dirs, files in os.walk(base_directory):
        for dir in dirs:
            if dir.startswith('Grade_'):
                grades.add(dir)
        for file in files:
            if file.endswith('.pdf'):
                # Assuming the filename format is 'Name_Date.pdf'
                name = file.split('_')[0]  # This gets the name part of the file
                names.add(name)

    return jsonify({
        'grades': list(grades),
        'names': list(names)
    })

def filter_pdfs():
    # Extract query parameters from the request
    grade = request.args.get('grade')
    name = request.args.get('name')
    date = request.args.get('date')

    # Base directory where the PDFs are stored
    base_directory = os.path.join(os.getcwd(), 'Demerits')

    # Filter PDFs based on the provided parameters
    filtered_pdfs = []
    for root, dirs, files in os.walk(base_directory):
        for file in files:
            if file.endswith('.pdf'):
                if grade and f"Grade_{grade}" not in root:
                    continue
                if name and name not in file:
                    continue
                if date and date not in file:
                    continue
                filtered_pdfs.append(file)

    return jsonify(filtered_pdfs)

@app.route('/directory')
def directory():
    # This will render a template called 'directory.html'
    # You need to create this HTML template and include the necessary JavaScript for filtering and downloading
    return render_template('directory.html')


@app.route('/get_pdfs', methods=['POST'])
def get_pdfs():
    # This will handle the AJAX request from the frontend to get the list of PDFs
    # You can pass filtering parameters from the frontend to this function
    data = request.json
    grade_filter = data.get('grade')
    name_filter = data.get('name')
    date_filter = data.get('date')
    
    pdfs = []
    base_dir = 'Demerits'  # Base directory where PDFs are stored

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.pdf'):
                file_path = os.path.join(root, file)
                file_stats = os.stat(file_path)
                file_date = datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d')
                file_grade = root.split('_')[-1]  # Assumes the format 'Demerits/Grade_X'

                # Apply filters if they are provided
                if grade_filter and grade_filter not in file_grade:
                    continue
                if name_filter and name_filter not in file:
                    continue
                if date_filter and date_filter != file_date:
                    continue
                
                pdf_info = {
                    'name': file,
                    'date': file_date,
                    'grade': file_grade,
                    'path': file_path
                }
                pdfs.append(pdf_info)
    
    return jsonify(pdfs)


@app.route('/download_pdf/<path:filename>')
def download_pdf(filename):
    # Log the requested filename for debugging
    print(f"Requested filename: {filename}")

    # This is the correct path to the Demerits directory
    demerits_directory = os.path.join(current_app.root_path, 'Demerits')
    print(f"Demerits directory: {demerits_directory}")

    # The filename should be a relative path like 'Grade_12/Ahmed_SHALABI_2023-10-07.pdf'
    # Make sure the 'filename' parameter does not include 'Demerits/' as it is already in 'demerits_directory'
    if filename.startswith('Demerits/'):
        # If it does, strip it from the filename
        filename = filename[len('Demerits/'):]

    expected_path = os.path.join(demerits_directory, filename)
    print(f"Expected path: {expected_path}")

    if not os.path.exists(expected_path):
        print("File does not exist.")
        abort(404)

    try:
        # Now we pass the correct directory and filename to send_from_directory
        return send_from_directory(directory=demerits_directory, path=filename, as_attachment=True)
    except FileNotFoundError:
        print(f"File not found: {filename}")
        abort(404)


if __name__ == '__main__':
    app.run(host='192.168.10.38', port=8080)