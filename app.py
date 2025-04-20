from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

# Import your existing bill parsing functions
from src.imageprocessing import extract_text
from src.billparsing import extract_invoice_data

# Create Flask app with correct template folder
template_dir = os.path.abspath('templates')
app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'bill_splitter_secret_key'  # Required for session

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Check if file extension is allowed


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload_bill():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'bill_image' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['bill_image']

        # If user does not select file, browser also
        # submits an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # Secure the filename and save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Extract text from the bill image
            try:
                bill_text = extract_text(file_path)
                # Parse the bill to extract items, taxes, and total
                bill_data = extract_invoice_data(bill_text)

                # Ensure bill_data has the correct structure
                if not isinstance(bill_data, dict):
                    bill_data = {'items': {}, 'taxes': {}, 'total': 0}

                # Ensure 'items' is a dictionary
                if 'items' not in bill_data or not isinstance(bill_data['items'], dict):
                    bill_data['items'] = {}

                # Ensure 'taxes' is a dictionary
                if 'taxes' not in bill_data or not isinstance(bill_data['taxes'], dict):
                    bill_data['taxes'] = {}

                # Ensure 'total' exists
                if 'total' not in bill_data or bill_data['total'] is None:
                    bill_data['total'] = 0

                # Store the bill data in session
                session['bill_data'] = bill_data
                session['bill_text'] = bill_text
                session['file_path'] = file_path

                # Redirect to the assign people page
                return redirect(url_for('assign_people'))
            except Exception as e:
                flash(f'Error processing bill: {str(e)}')
                return redirect(request.url)

    return render_template('upload.html')


@app.route('/add_people', methods=['GET', 'POST'])
def assign_people():
    if 'bill_data' not in session:
        flash('Please upload a bill first')
        return redirect(url_for('upload_bill'))

    bill_data = session['bill_data']

    # Double-check the bill data structure here as well
    if not isinstance(bill_data, dict):
        bill_data = {'items': {}, 'taxes': {}, 'total': 0}
        session['bill_data'] = bill_data

    # Ensure 'items' is a dictionary
    if 'items' not in bill_data or not isinstance(bill_data['items'], dict):
        bill_data['items'] = {}
        session['bill_data'] = bill_data

    # Ensure 'taxes' is a dictionary
    if 'taxes' not in bill_data or not isinstance(bill_data['taxes'], dict):
        bill_data['taxes'] = {}
        session['bill_data'] = bill_data

    if request.method == 'POST':
        # Get list of people from form
        people = [person.strip() for person in request.form.get(
            'people', '').split(',') if person.strip()]

        if not people:
            flash('Please add at least one person')
            return redirect(request.url)

        # Store people in session
        session['people'] = people

        # Initialize the assignments dictionary - this will track who's assigned to each item
        assignments = {item: [] for item in bill_data['items']}
        session['assignments'] = assignments

        return redirect(url_for('assign_items'))

    return render_template('add_people.html', bill_data=bill_data)


@app.route('/assign_items', methods=['GET', 'POST'])
def assign_items():
    if 'bill_data' not in session or 'people' not in session:
        flash('Please upload a bill and add people first')
        return redirect(url_for('upload_bill'))

    bill_data = session['bill_data']
    people = session['people']
    assignments = session.get('assignments', {})

    # Ensure bill_data structure is correct
    if not isinstance(bill_data, dict) or 'items' not in bill_data or not isinstance(bill_data['items'], dict):
        flash('Invalid bill data format')
        return redirect(url_for('upload_bill'))

    if request.method == 'POST':
        # Update assignments based on form submission
        for item in bill_data['items']:
            # Get list of people assigned to this item
            assigned_people = request.form.getlist(f'item_{item}')
            assignments[item] = assigned_people

        # Store updated assignments in session
        session['assignments'] = assignments

        # Redirect to results page
        return redirect(url_for('results'))

    return render_template('assign_items.html',
                           bill_data=bill_data,
                           people=people,
                           assignments=assignments)


@app.route('/results')
def results():
    if 'bill_data' not in session or 'people' not in session or 'assignments' not in session:
        flash('Please complete all previous steps first')
        return redirect(url_for('upload_bill'))

    bill_data = session['bill_data']
    people = session['people']
    assignments = session['assignments']

    # Ensure bill_data structure is correct
    if not isinstance(bill_data, dict) or 'items' not in bill_data or not isinstance(bill_data['items'], dict):
        flash('Invalid bill data format')
        return redirect(url_for('upload_bill'))

    # Calculate how much each person owes
    amounts = {person: 0 for person in people}

    # Calculate base costs from food items
    for item, assigned_people in assignments.items():
        # Make sure item exists in bill_data['items']
        if assigned_people and item in bill_data['items']:
            item_cost = bill_data['items'][item]['amount']
            cost_per_person = item_cost / len(assigned_people)

            for person in assigned_people:
                amounts[person] += cost_per_person

    # Calculate tax and distribute proportionally
    total_before_tax = sum(bill_data['items'][item]['amount']
                           for item in bill_data['items'])

    # Fix for TypeError: Check if taxes is a dictionary and has values before trying to sum
    total_tax = 0
    if 'taxes' in bill_data and isinstance(bill_data['taxes'], dict):
        total_tax = sum(bill_data['taxes'].values())

    # Distribute tax proportionally
    if total_before_tax > 0:
        for person in amounts:
            tax_ratio = amounts[person] / total_before_tax
            amounts[person] += tax_ratio * total_tax

    # Round the amounts to 2 decimal places
    amounts = {person: round(amount, 2) for person, amount in amounts.items()}

    return render_template('results.html',
                           bill_data=bill_data,
                           people=people,
                           assignments=assignments,
                           amounts=amounts,
                           total_before_tax=total_before_tax,
                           total_tax=total_tax)


@app.route('/start_new')
def start_new():
    # Clear session data
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
