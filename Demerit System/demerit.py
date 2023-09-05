import base64
import io
from flask import Flask, jsonify, render_template, request, redirect, url_for
import pandas as pd
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from playsound import playsound

app = Flask(__name__)

# Declare the df variable as global
df = None

def load_data():
    global df
    df = pd.read_csv('student_data.csv')

# Call the load_data function to load the CSV data when the app starts
load_data()

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
    
    

    # Create a new DataFrame for the submission
    new_entry = pd.DataFrame({'Name': [selected_name],
                              'Grade': [selected_grade],
                              'Date': [current_date],
                              'Offenses': [', '.join(selected_offenses)]})

    # Create directory structure for the grade
    grade_folder = os.path.join('Demerits', f'Grade_{selected_grade}')
    os.makedirs(grade_folder, exist_ok=True)

    # Generate a unique filename based on name and date
    base_filename = f'{selected_name}_{current_date}.csv'
    filename = base_filename
    counter = 1

    # Check if the file already exists and generate a new filename if needed
    while os.path.exists(os.path.join(grade_folder, filename)):
        filename = f'{selected_name}_{current_date}_{counter}.csv'
        counter += 1

    # Save the submission to the unique CSV file
    new_entry.to_csv(os.path.join(grade_folder, filename), index=False)

    # Append the submission to a separate CSV file
    new_entry.to_csv('submission.csv', mode='a', header=not os.path.exists('submission.csv'), index=False)
    playsound('static/ding.mp3')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
