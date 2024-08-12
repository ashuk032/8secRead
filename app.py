from flask import Flask, render_template, redirect, url_for, request, session, send_from_directory,jsonify,flash
from application.database import db, User, Admin, Book, BookRequest, Section
from functools import wraps
from sqlalchemy import or_ , func, distinct
from flask_restful import Api
from werkzeug.utils import secure_filename
import logging
from datetime import datetime,timedelta
import os
import matplotlib
matplotlib.use('Agg')  # Use Agg backend which doesn't require a GUI
import matplotlib.pyplot as plt
import numpy as np
import bcrypt
from collections import defaultdict
 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///8secRead.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['STATIC_FOLDER'] = 'sec_images'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GRAPH_FOLDER'] = 'graph'
api = Api(app)

# Initialize database
db.init_app(app)

def create_tables():
    with app.app_context():
        db.create_all()

create_tables()  
# debug log
logging.basicConfig(filename='debug.log',
                    level=logging.DEBUG,
                    format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


@app.route('/graph/<path:filename>')
def graph_file(filename):
    clean_filename = filename.replace('\\', '/')
    
    # Extract basename
    clean_filename = os.path.basename(clean_filename)
    
    # Send file from specified directory
    return send_from_directory(app.config['GRAPH_FOLDER'], clean_filename)

@app.route('/sec_images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['STATIC_FOLDER'], filename)

# book upload
@app.route('/create_uploads_folder')
def create_uploads_folder():
    uploads_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)
        return 'Uploads folder created successfully!'
    else:
        return 'Uploads folder already exists.'
    
# Graph folder
def graph_folder():
    graph_folder = app.config['GRAPH_FOLDER']
    if not os.path.exists(graph_folder):
        os.makedirs(graph_folder)
    

# book connect img connect route
@app.route('/uploads/<path:filename>')
def book_con(filename):
    # Extract filename without directory path
    clean_filename = os.path.basename(filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'], clean_filename)


# User login route
@app.route('/', methods=['GET', 'POST'])
def login():
    error = request.args.get('error')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            error = 'Please fill in both username and password.'
        else:
            user = User.query.filter_by(username=username).first()
            if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                session['username'] = username
                session['logged_in'] = True
                return redirect(url_for('loading'))
            else:
                error = 'Invalid username or password. Please try again.'

    return render_template('login.html', error=error)



# Login required decorator
def login_required(user_type='user'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if user_type == 'admin':
                if 'admin_logged_in' not in session:
                    return redirect(url_for('admin_login', error='You need to log in first.'))
            else:
                if 'logged_in' not in session:
                    return redirect(url_for('login', error='You need to log in first.'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# user route
@app.route('/user/<username>') 
@login_required(user_type='user')
def user(username):
    if 'logged_in' in session:
        logged_in = session['logged_in']
        # Fetch user-specific data based on username
        user = User.query.filter_by(username=username).first()


        if user:
          session['user_id'] = user.user_id  # user_id primary key of User model
          session['logged_in'] = True

        pass  

        if user:
            # Fetch all books from the database in descending order of upload date
            books = Book.query.order_by(Book.upload_date.desc()).all()
            # Fetch most recent books
            recent_books = books[:4]  # Get the first 4 books
            return render_template('user_dashboard.html', logged_in=logged_in, user=user, recent_books=recent_books, user_id=session.get('user_id'), book_already_requested=book_already_requested, book_request_status=book_request_status, all_book=all_book)
        else:
            return render_template('error.html', error='User not found'), 404
        
# display all book to user 
@app.route('/all_books')        
def all_book():
    books = Book.query.order_by(Book.upload_date.desc()).all()
    recent_books_all = books

    user_id = session.get('user_id')  # user ID is stored in session
    user = User.query.get(user_id) 

    return render_template('all_book.html', recent_books_all=recent_books_all, book_already_requested=book_already_requested, book_request_status=book_request_status, user=user)

# Logout route
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)  
    return redirect(url_for('login')) 

# Registration route
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        u_email = request.form['email']
        password = request.form['password']
        con_password = request.form['con_password']

        error = None

        if password != con_password:
            error = 'Passwords do not match!'
        else:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                error = 'Username already exists!'
            else:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                new_user = User(username=username, u_email=u_email, password=hashed_password.decode('utf-8'))
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))

        if error:
            return render_template('register.html', error=error)
        else:
            return render_template('register.html')

    return render_template('register.html')



# Admin login route
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    error = request.args.get('error')
    if request.method == 'POST':
        admin_username = request.form['admin_username']
        admin_password = request.form['admin_password']

        admin = Admin.query.filter_by(username=admin_username, password=admin_password).first()
        if admin:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid admin username or password. Please try again.'

    return render_template('admin_login.html', error=error)

# Admin logout route
@app.route('/admin/logout', methods=['POST'])
def logout_admin():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))



# Admin dashboard route
@app.route('/admin/dashboard')
@login_required(user_type='admin')
def admin_dashboard():
    if 'admin_logged_in' in session:
        sections = Section.query.all()
        # Calculate admin statistics
        total_books_issued = calculate_book_issued()
        section_distribution = calculate_section_distribution()

        # Generate admin stats graph
        generate_admin_stats_graph(total_books_issued, section_distribution)

        # Pass the URL of the generated graph image to the template
        graph_url = url_for('static', filename='admin_stats_graph.png')

        return render_template('admin_dashboard.html', graph_url=graph_url, sections=sections)
    else:
        return redirect(url_for('admin_login', error='You need to log in as an admin first.'))



# User search route
@app.route('/user_search')
@login_required(user_type='user')
def user_search():
    query = request.args.get('query')
    results = []

    # Fetch user information
    user_id = session.get('user_id')  # user ID is stored in the session
    user = User.query.get(user_id)  # Fetch user object from the database

    # Fetch user's books
    my_books = []  # Fetch the user's books from the database

    if query:
        # Search for books
        results = Book.query.join(Section).filter(
            or_(
                Book.name.ilike(f'%{query}%'),  # Search in book name
                Section.sec_name.ilike(f'%{query}%'),  # Search in section name
                Book.author.ilike(f'%{query}%')  # Search in author
            )
        ).all()

    return render_template('user_search.html', query=query, results=results, user=user, my_books=my_books)


# admin search 
@app.route('/admin_search', methods=['GET'])
@login_required(user_type='admin')
def admin_search():
    search_query = request.args.get('query')
    section_results = []
    book_results = []

    if search_query:
        # Search for sections
        section_results = Section.query.filter(
            (Section.sec_name.ilike(f'%{search_query}%')) |  # Search in section name
            (Section.description.ilike(f'%{search_query}%'))  # Search in section description
        ).all()

        # Search for books
        book_results = Book.query.filter(
            (Book.name.ilike(f'%{search_query}%')) |  # Search in book name
            (Book.author.ilike(f'%{search_query}%'))  # Search in book author
        ).all()

    return render_template('admin_search.html', search_query=search_query, section_results=section_results, book_results=book_results)



# Add section route
@app.route('/admin/add_section', methods=['GET', 'POST'])
@login_required(user_type='admin')
def add_section():
    if request.method == 'POST':
        sec_name = request.form['sec_name'].strip().upper()  # Normalize the section name
        description = request.form['description'].strip()
        sec_image = request.files['sec_image']

        # Check if the section name already exists
        existing_section = Section.query.filter_by(sec_name=sec_name).first()
        if existing_section:
            flash('Section name already exists!', 'error')
            return redirect(url_for('add_section'))

        # Check if the upload folder exists, if not, create it
        if not os.path.exists(app.config['STATIC_FOLDER']):
            os.makedirs(app.config['STATIC_FOLDER'])

        # Save the uploaded image to the upload folder
        filename = secure_filename(sec_image.filename)
        filepath = os.path.join(app.config['STATIC_FOLDER'], filename)
        sec_image.save(filepath)

        try:
            # Create a new Section object and add it to the database
            new_section = Section(sec_name=sec_name, description=description, sec_image=filename)
            db.session.add(new_section)
            db.session.commit()
            flash('Section added successfully!', 'success')
        except Exception as e:
            # Rollback the session if there was an error
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
            if os.path.exists(filepath):
                os.remove(filepath)  # Optionally remove the uploaded file if DB commit fails

        return redirect(url_for('admin_dashboard'))

    return render_template('add_section.html')




# Route to delete a book
@app.route('/delete_book/<int:book_id>', methods=['POST'])
@login_required(user_type='admin')
def delete_book(book_id):
    # Find the book by its ID
    book = Book.query.get(book_id)

    if book:
        try:
            # Delete all associated book requests for this book
            BookRequest.query.filter_by(book_id=book_id).delete()
            db.session.commit()

            # Delete the book record from the database
            db.session.delete(book)
            db.session.commit()

            # Flash a success message
            flash('Book deleted successfully!', 'success')
        except Exception as e:
            # If any exception occurs during deletion, rollback the session
            db.session.rollback()
            flash('Failed to delete the book. Error: {}'.format(str(e)), 'error')
    else:
        # Flash an error message if the book doesn't exist
        flash('Book not found!', 'error')

    # Redirect back to the admin dashboard
    return redirect(url_for('admin_dashboard')) 


# Route to delete a section
@app.route('/delete_section/<section_id>', methods=['POST'])
def delete_section(section_id):
    # Retrieve the section from the database
    section = Section.query.get(section_id)

    if section:
        # Find all books in the section
        books = Book.query.filter_by(sec_name=section.sec_name).all()

        # Delete all related book requests
        for book in books:
            book_requests = BookRequest.query.filter_by(book_id=book.book_id).all()
            for request in book_requests:
                db.session.delete(request)

        # Delete all books inside the section
        for book in books:
            db.session.delete(book)

        # Delete the section from the database
        db.session.delete(section)
        db.session.commit()
        flash('Section, its books, and related requests deleted successfully!', 'success')
    else:
        flash('Section not found!', 'error')

    # Redirect the user back to the page where they can manage sections
    return redirect(url_for('admin_dashboard'))

# Edit section route
@app.route('/admin/edit_section/<int:section_id>', methods=['GET', 'POST'])
@login_required(user_type='admin')
def edit_section(section_id):
    section = Section.query.get(section_id)
    if section:
        if request.method == 'POST':
            # Handle form submission to edit the section
            sec_name = request.form.get('sec_name', section.sec_name)
            description = request.form.get('description', section.description)
            
            sec_image = request.files.get('sec_image')
            upload_folder = app.config['UPLOAD_FOLDER']

            # Ensure the upload directory exists
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # Check if a new image was uploaded
            if sec_image and sec_image.filename != '':
                # Remove old image if it exists
                if section.sec_image:
                    old_file_path = os.path.join(upload_folder, section.sec_image)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                
                # Save the uploaded image
                filename = secure_filename(sec_image.filename)
                file_path = os.path.join(upload_folder, filename)
                sec_image.save(file_path)
                section.sec_image = filename
                print("New image saved:", file_path)
            
            # Update section data
            section.sec_name = sec_name
            section.description = description
            
            # Save changes to the database
            db.session.commit()
            
            # Redirect to the section display page
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('edit_section.html', section=section)
    else:
        return render_template('error.html', error='Section not found'), 404


# display book in section 
@app.route('/admin/section_book_display/<int:section_id>')
@login_required(user_type='admin')
def section_book_display(section_id):
    section = Section.query.get(section_id)
    if section:
        books = Book.query.filter_by(sec_name=section.sec_name).all()
        return render_template('section_book_display.html', section=section, books=books)
    else:
        return render_template('error.html', error='Section not found'), 404
    
# Add book
@app.route('/add_book/<int:section_id>', methods=['GET', 'POST'])
def add_book(section_id):
    # Fetch the section from the database using the section_id
    section = Section.query.get_or_404(section_id)

    if request.method == 'POST':
        # Handle the form submission to add the book to the specified section
        # Extract book details from the form
        name = request.form['name']
        author = request.form['author']
        
        # Save the uploaded book image to the uploads folder
        book_image = request.files['book_image']
        if book_image:
            filename = secure_filename(book_image.filename)
            upload_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            book_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            book_image.save(book_image_path)
        
        # Save the uploaded book PDF to the uploads folder
        book_pdf = request.files['book_pdf']
        if book_pdf:
            filename = secure_filename(book_pdf.filename)
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            book_pdf_path = os.path.join(upload_folder, filename)
            book_pdf.save(book_pdf_path)
        
        # Create a new Book instance and set its attributes
        new_book = Book(name=name, author=author, book_image=book_image_path, book_pdf=book_pdf_path)
        # Set the section attribute of the new_book instance
        new_book.section = section
        
        # Save the book to the database
        db.session.add(new_book)
        db.session.commit()
        
        
        return redirect(url_for('admin_dashboard'))
    
    # Render the add_book.html template with the section
    # Pass the section to the template
    return render_template('add_book.html', section=section)


# Edit book route
@app.route('/admin/edit_book/<int:book_id>', methods=['GET', 'POST'])
@login_required(user_type='admin')
def edit_book(book_id):
    book = Book.query.get(book_id)
    if book:
        if request.method == 'POST':
            # Handle form submission to edit the book
            book.name = request.form.get('name', book.name)
            book.author = request.form.get('author', book.author)
            book.sec_name = request.form.get('sec_name', book.sec_name)
            
            # Check if a new image was uploaded
            if 'book_image' in request.files:
                file = request.files['book_image']
                if file.filename != '':
                    # Delete the old image file if it exists
                    if book.book_image:
                        old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], book.book_image)
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)
                    
                    # Save the uploaded image file
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    book.book_image = filename  # Update image_url with new filename
                    print("New image saved:", file_path)
            
            # Save the updated book details
            db.session.commit()
            
            # Redirect to the section book display page
            return redirect(url_for('section_book_display', section_id=book.section.id))
        else:
            return render_template('edit_book.html', book=book)
    else:
        return render_template('error.html', error='Book not found'), 404


# Request book API for users
@app.route('/api/request-book', methods=['POST'])
def request_book():
    # Get the user_id from the session
    user_id = session.get('user_id')
    
    # Get the book_id from the form data
    book_id = request.form.get('book_id')
    
    if has_reached_max_requests(user_id):
        return jsonify({'error': 'Maximum request limit reached'}), 400
    

    # Record the request in the database
    request_time = datetime.now()
    expiration_time = calculate_expiration_time(request_time, access_period=14)  # 14 days access
    # Save request details including request_time and expiration_time in the database
    
    # Check if the user_id and book_id are provided
    if not user_id or not book_id:
        return jsonify({'error': 'User ID and Book ID are required'}), 400
    
    # Check if the book is already requested by the user
    existing_request = BookRequest.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing_request:
        return jsonify({'message': 'Book already requested by the user'})
    
    
    
    # Create a new book request
    new_request = BookRequest(user_id=user_id, book_id=book_id)
    db.session.add(new_request)
    db.session.commit()
    
    return redirect(url_for('user', username=session.get('username')))


# Function to check if a user has reached the maximum request limit
def has_reached_max_requests(user_id):
    # Query the database to count the number of requests made by the user
    request_count = BookRequest.query.filter_by(user_id=user_id).count()
    return request_count >= 4  # 5 is the maximum allowed requests

# Function to calculate the expiration time for a book request
def calculate_expiration_time(request_time, access_period):
    return request_time + timedelta(days=access_period)

# book_already_requested
def book_already_requested(user_id, book_id):
    # Query the BookRequest table to check if the user has already requested the book
    existing_request = BookRequest.query.filter_by(user_id=user_id, book_id=book_id).first()
    return existing_request is not None

# Request management route
@app.route('/request-management')
@login_required(user_type='admin')
def request_management():
    # Retrieve requests from the database
    requests = BookRequest.query.all()
    return render_template('request_management.html', requests=requests)




# Reject request
@app.route('/api/reject-request', methods=['POST'])
@login_required(user_type='admin')
def reject_request():
    if request.method == 'POST':
        # Get the request ID from the form data
        request_id = request.form.get('request_id')
        
        # Query the database to find the request by ID
        request_record = BookRequest.query.get(request_id)
        
        if request_record:
            # Set the status of the request to 'Rejected'
            request_record.status = 'Rejected'
            
            # If the request was previously approved, update the book's status to reflect rejection
            if request_record.status == 'Approved':
                # Find the corresponding book and update its status
                book = Book.query.get(request_record.book_id)
                if book:
                    book.status = 'Rejected'
            
            # Delete the request record from the database
            db.session.delete(request_record)
            
            # Commit the changes
            db.session.commit()
            
            # Redirect to the request management page
            return redirect(url_for('request_management'))

        else:
            # If the request record does not exist, return an error message
            return jsonify({'error': 'Request not found'}), 404


# update request for admin 
@app.route('/api/update-request-status', methods=['POST'])
@login_required(user_type='admin')
def update_request_status():
    if request.method == 'POST':
        request_id = request.form.get('request_id')
        new_status = request.form.get('status')

        request_record = BookRequest.query.get(request_id)

        if request_record:
            # Update the status of the request
            request_record.status = new_status
            db.session.commit()

            # If the new status is "Rejected", delete the request
            if new_status == 'Rejected':
                db.session.delete(request_record)
                db.session.commit()

            return redirect(url_for('request_management'))
        else:
            return jsonify({'error': 'Request not found'}), 404



# Approve request
@app.route('/api/approve-request/<int:request_id>', methods=['POST'])
@login_required(user_type='admin')
def approve_request_api(request_id):
    # Retrieve the request from the database
    request_record = BookRequest.query.get(request_id)
    
    if request_record:
        # Update the status of the request to 'Approved'
        request_record.status = 'Approved'
        db.session.commit()
        
        # Redirect the user to the return route with the book ID
        return redirect(url_for('return_book', book_id=request_record.book_id))
    else:
        # If the request record does not exist, return an error message
        return jsonify({'error': 'Request not found'}), 404


 
@app.route('/view_book_pdf/<int:book_id>', methods=['GET'])
def view_book_pdf(book_id):
    # Retrieve the book details from the database using the book_id
    book = Book.query.get(book_id)
    
    if not session.get('user_id'):
        # If the user is not logged in, redirect to the login page
        return redirect(url_for('login'))
    

    # Fetch the user ID from the session
    user_id = session.get('user_id')

    # Retrieve the user based on the user ID
    user = User.query.get(user_id)

    # Call the book_request_status() function with the book_id argument
    request_status = book_request_status(user_id=user_id, book_id=book_id)

    # Query the BookRequest table to check if the book_id exists
    book_request = BookRequest.query.filter_by(book_id=book_id).first()


    
    if book_request and book_request.status == 'Approved':
        # If the request is approved, render the page to display the book
        return render_template('pdf_display.html', book=book, user=user, book_already_requested=book_already_requested, book_request_status=book_request_status, book_id=book_id)
    else:
        # If the request is not approved or if the user has not requested the book, set the error message
        error = 'You do not have access to view this book.'
        return render_template('pdf_display.html', book=book, user=user, book_already_requested=book_already_requested, book_request_status=book_request_status, book_id=book_id, error=error)




# User books route
@app.route('/<username>/my_books')
@login_required(user_type='user')
def my_books(username):
    # Retrieve user ID based on the username
    user = User.query.filter_by(username=username).first()

    if user:
        # Fetch requested books for the user
        requested_books = Book.query.join(BookRequest).filter(BookRequest.user_id == user.user_id).limit(4).all()
        
        # Fetch approved books for the user
        approved_books = Book.query.join(BookRequest).filter(BookRequest.user_id == user.user_id, BookRequest.status == 'Approved').limit(4).all()

        return render_template('my_books.html', requested_books=requested_books, approved_books=approved_books, user=user, book_already_requested=book_already_requested, book_request_status=book_request_status)
    else:
        return render_template('error.html', error='User not found'), 404

# route to handle book returns as an API endpoint
@app.route('/api/return-book', methods=['POST'])
@login_required(user_type='user')
def return_book_api():
    # Get the book ID from the request data
    book_id = request.form.get('book_id')

    # Find the corresponding book request and update its status
    request_record = BookRequest.query.filter_by(book_id=book_id, status='Approved').first()
    
    if request_record:
        # Set the status of the request to 'Returned'
        request_record.status = 'Returned'
        db.session.commit() 
        
        # Update the book status in the Book table if needed
        book = Book.query.get(book_id)
        if book:
            book.status = 'Returned'
            db.session.commit()

        # Redirect the user back to the user dashboard
        return redirect(url_for('user', username=session.get('username')))
    else:
        return jsonify({'error': 'Book return failed. Request not found or book not approved for return'}), 404




# Get book requests API for admins
@app.route('/api/book-requests', methods=['GET'])
def get_book_requests():
    # Get all book requests
    requests = BookRequest.query.all()
    requests_data = [{'id': req.id, 'user_id': req.user_id, 'book_id': req.book_id, 'status': req.status} for req in requests]
    return jsonify({'requests': requests_data})

# book status
def book_request_status(user_id, book_id):
    # Query the database to retrieve the book request status
    book_request = BookRequest.query.filter_by(user_id=user_id, book_id=book_id).first()
    if book_request:
        return book_request.status
    else:
        return 'Pending'

    

@app.route('/loading')
def loading():
    # Render the loading template
    return render_template('loading.html')        
    

# Route to redirect after loading 
@app.route('/after-loading')
def after_loading():
    if 'logged_in' in session:
        # Redirect to the user dashboard
        if 'admin_logged_in' not in session:
            return redirect(url_for('user', username=session.get('username')))
    return redirect(url_for('login'))
  
    

# book issued calculate
def calculate_book_issued():
    """
    Calculate the total number of books issued.
    """
    total_books_issued = BookRequest.query.filter(or_(BookRequest.status == 'Approved', BookRequest.status == 'Returned')).count()
    return total_books_issued    
    
# section issued calculate
def calculate_section_distribution():
    section_distribution = db.session.query(Section.sec_name, func.count(BookRequest.book_id)) \
        .select_from(Section) \
        .join(Book, Book.sec_name == Section.sec_name) \
        .join(BookRequest, BookRequest.book_id == Book.book_id) \
        .filter(or_(BookRequest.status == 'Approved', BookRequest.status == 'Returned')) \
        .group_by(Section.sec_name) \
        .all()

    return section_distribution

# admin stats
@app.route('/admin/stats')
@login_required(user_type='admin')
def admin_stats():
    # Fetch and process admin statistics data
    admin_statistics = fetch_admin_statistics()
    total_books_issued = admin_statistics.get('total_books_issued')
    section_distribution = admin_statistics.get('section_distribution')

    # Prepare data for JavaScript
    section_names = [sec_name for sec_name, _ in section_distribution]
    section_counts = [count for _, count in section_distribution]

    return render_template('admin_stats.html', 
                           total_books_issued=total_books_issued, 
                           section_names=section_names, 
                           section_counts=section_counts)




# data fetch for graph admin
def fetch_admin_statistics():
    # Calculate the total number of books issued
    total_books_issued = calculate_book_issued()
    
    # Calculate section distribution
    section_distribution = calculate_section_distribution()
    
    # Combine all statistics into a dictionary
    admin_statistics = {
        'total_books_issued': total_books_issued,
        'section_distribution': section_distribution,
        # Add more statistics as needed
    }
    
    return admin_statistics


# admin graph genearte function
def generate_admin_stats_graph(total_books_issued, section_distribution):
    # Ensure that the 'graph' folder exists
    graph_folder()

    if not section_distribution:
        return None, None  # Handle the case when section_distribution is empty

    # Unpack section names and counts from section_distribution
    section_names, section_counts = zip(*section_distribution)

    # Generate bar graph
    plt.figure(figsize=(10, 6))
    plt.bar(section_names, section_counts)
    plt.xlabel('Section Name')
    plt.ylabel('Number of Books Issued')
    plt.title('Section-wise Distribution of Books Issued')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the generated bar graph to the 'graph' folder
    bar_graph_filename = os.path.join(app.config['GRAPH_FOLDER'], 'bar_graph.png')  
    plt.savefig(bar_graph_filename)

    # Generate pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(section_counts, labels=section_names, autopct='%1.1f%%', startangle=140)
    plt.title('Distribution of Books Issued by Section')
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.tight_layout()

    # Save the generated pie chart to the 'graph' folder
    pie_chart_filename = os.path.join(app.config['GRAPH_FOLDER'], 'pie_chart.png') 
    plt.savefig(pie_chart_filename)


    plt.close('all')

    return bar_graph_filename, pie_chart_filename


# user graoh generate function 
def generate_section_stats(username):
    # Fetch user based on the provided username
    user = User.query.filter_by(username=username).first()

    if not user:
        return None, None 

    user_id = user.user_id

    # Query book requests data from the database for the specified user
    book_requests = db.session.query(Book.sec_name, db.func.count(BookRequest.id)).join(BookRequest).filter(BookRequest.user_id == user_id).group_by(Book.sec_name).all()

    if not book_requests:
        return None, None  

    # Extract section names and request counts
    section_names, request_counts = zip(*book_requests)

    # Generate the bar graph for section distribution
    plt.figure(figsize=(10, 6))
    plt.bar(section_names, request_counts)
    plt.xlabel('Section')
    plt.ylabel('Number of Requests')
    plt.title('Section-wise Book Requests')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the bar graph to the 'graph' folder
    graph_folder = 'graph'  
    if not os.path.exists(graph_folder):
        os.makedirs(graph_folder)
    bar_graph_filename = os.path.join(graph_folder, f'{username}_section_request_bar_graph.png')
    plt.savefig(bar_graph_filename)
    plt.close()

    # Generate the pie chart for section distribution
    plt.figure(figsize=(8, 8))
    plt.pie(request_counts, labels=section_names, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title('Section-wise Book Requests Distribution')
    plt.tight_layout()

    # Save the pie chart to the 'graph' folder
    pie_graph_filename = os.path.join(graph_folder, f'{username}_section_request_pie_chart.png')
    plt.savefig(pie_graph_filename)
    plt.close()

    return bar_graph_filename, pie_graph_filename


# user stats route
@app.route('/user_stats/<username>')
def user_stats(username):
    # Fetch user based on the provided username
    user = User.query.filter_by(username=username).first()
    if not user:
        return render_template('error.html', message='User not found')

    user_id = user.user_id

    # Fetch approved and requested book requests for the user, grouped by section
    approved_books = BookRequest.query.filter_by(user_id=user_id, status='Approved').all()
    requested_books = BookRequest.query.filter_by(user_id=user_id, status='Pending').all()  # Assuming 'Pending' means requested but not yet approved

    # Initialize default dictionaries to count the number of requests per section
    approved_books_data = defaultdict(int)
    requested_books_data = defaultdict(int)
    section_labels = set()

    for request in approved_books:
        section_name = request.book.section.sec_name
        approved_books_data[section_name] += 1
        section_labels.add(section_name)

    for request in requested_books:
        section_name = request.book.section.sec_name
        requested_books_data[section_name] += 1
        section_labels.add(section_name)

    section_labels = list(section_labels)

    # Prepare data for the frontend
    approved_books_data = [approved_books_data[section] for section in section_labels]
    requested_books_data = [requested_books_data[section] for section in section_labels]

    return render_template('user_stats.html',
                           username=username,user=user,
                           section_labels=section_labels,
                           approved_books_data=approved_books_data,
                           requested_books_data=requested_books_data)


if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'sec_images'
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['GRAPH_FOLDER'] = 'graph'
    app.run(debug=True)
