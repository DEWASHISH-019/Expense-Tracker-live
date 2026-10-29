AI EXPENSE TRACKER - FULL STACK PYTHON PROJECT

1. REQUIREMENTS
- Python 3.10 or 3.11
- VS Code recommended
- Any modern web browser

2. INSTALLATION
Open the terminal inside this project folder and run:

pip install -r requirements.txt

3. RUN
Run:

python app.py

Then open:

http://127.0.0.1:5000

4. FEATURES
- User registration and login
- Password hashing
- SQLite database
- Add, edit and delete expenses
- Search and category filtering
- Dashboard
- Category and monthly charts
- AI spending analysis
- Basic future expense prediction
- Spending advice
- Reports page

5. DATABASE
The file expense_tracker.db is created automatically when the application starts.
SQLite is used, so MySQL/XAMPP is not required.

6. IMPORTANT
Change the Flask secret_key in app.py before using the project outside a classroom/demo environment.

7. PROJECT FLOW
Browser -> HTML/CSS/JavaScript -> Flask -> SQLite
                         |
                         -> AI analysis using Python/scikit-learn
