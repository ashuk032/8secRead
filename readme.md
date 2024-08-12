# 8secRead - E-library Application


## Local setup

### Creating virtual environment  
- `python -m venv .env`

### Activate the virtual environment 
- `.env\Scripts\activate`

### Install all the required packages
- `pip install -r requirements.txt`

### Start the application
- `python main.py`

Or, just open the root foder in any IDE, 
it will automatically create a virtual environment 
and install all the requirements from the requirements.txt file.


## Folder Structure


8secRead/
│
├── Application/
│   ├── _pycache_/         # Cached Python files
│   └── database.py        # all database model
│
├── graph/
│   ├── user_stats_image   # Image folder for user statistics
│   └── admin_stats_image  # Image folder for admin statistics
│
├── instance/
│   └── 8secRead.db           # SQLite database file
│
├── sec_images/
│   └── all_section_images # Folder containing images for all book sections
│
├── static/
│   ├── images/
│   │   ├── loading_logo.gif     # Loading animation image
│   │   ├── logo.png             # Logo image
│   │   ├── person-circle.svg    # Placeholder image
│   │   └── Untitled_design.png  # Image file
│   ├── admin_search.js    # JavaScript file for admin search functionality
│   ├── base_dashboard.css # CSS file for dashboard layout
│   ├── base_login.css     # CSS file for login page layout
│   ├── favicon.ico        # favicon of 8secRead
│   ├── function.js        # JavaScript functions
│   ├── loading.css        # CSS file for loading screen
│   ├── register.css       # CSS file for registration page layout
│   ├── user_search.js     # JavaScript file for user search functionality
│   └── user.css           # CSS file for user-related styles
│
├── templates/
│   ├── add_book.html            # HTML template for adding a book
│   ├── add_section.html         # HTML template for adding a section
│   ├── admin_dashboard.html     # HTML template for admin dashboard
│   ├── admin_login.html         # HTML template for admin login page
│   ├── admin_profile.html       # HTML template for admin profile page
│   ├── admin_search.html        # HTML template for admin search
│   ├── admin_stats.html         # HTML template for admin statistics
│   ├── all_book.html            # HTML template for displaying all books
│   ├── base_dashboard.html      # Base HTML template for dashboard
│   ├── base.html                # Base HTML template
│   ├── display_section.html     # HTML template for displaying a section
│   ├── edit_book.html           # HTML template for editing a book
│   ├── edit_section.html        # HTML template for editing a section
│   ├── loading.html             # HTML template for loading screen
│   ├── login.html               # HTML template for login page
│   ├── my_books.html            # HTML template for displaying user's books
│   ├── pdf_display.html         # HTML template for displaying PDF content
│   ├── register.html            # HTML template for registration page
│   ├── request_management.html  # HTML template for request management
│   ├── section_book_display.html# HTML template for displaying books in a section
│   ├── user_dashboard.html      # HTML template for user dashboard
│   ├── user_profile.html        # HTML template for user profile page
│   ├── user_search.html         # HTML template for user search
│   └── user_stats.html          # HTML template for user statistics
│
├── uploads/
│   └── all_book_image_and_pdf  # Folder containing all book images and PDFs
│
├── requirements.txt     # File containing Python dependencies
├── debug.log            # Log file for debugging // get the file after running the app.py
└── app.py               # Main Python script containing application code

