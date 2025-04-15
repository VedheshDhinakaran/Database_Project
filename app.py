from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from functools import wraps
import mysql.connector
from flask_cors import CORS
app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app)

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="mysql123*",
        database="temp"
    )
def nocache(view_function):
    def wrapper(*args, **kwargs):
        response = make_response(view_function(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    wrapper.__name__ = view_function.__name__
    return wrapper
# Route for login page
@app.route('/')
def index():
    return render_template('login.html')
    

# Route for handling login with role-based authentication
@app.route('/login', methods=['POST'])
def login():
    username = request.form['login-user']
    password = request.form['login-password']
    role = request.form['role']

    conn = get_db_connection()
    cursor = conn.cursor()

    if role == 'student':
        cursor.execute("SELECT * FROM credentials WHERE RegNo = %s AND Password = %s", (username, password))
        result = cursor.fetchone()
        if result:
            session['username'] = username
            session['role'] = 'student'
            # Clear flash messages before redirecting
            session.pop('_flashes', None)
            return redirect(url_for('student'))
        else:
            flash("Invalid student credentials. Please try again.", "error")

    elif role == 'admin':
        cursor.execute("SELECT * FROM admin WHERE adminID = %s AND pwd = %s", (username, password))
        result = cursor.fetchone()
        if result:
            session['username'] = username
            session['role'] = 'admin'
            # Clear flash messages before redirecting
            session.pop('_flashes', None)
            return redirect(url_for('admin_home'))
        else:
            flash("Invalid admin credentials. Please try again.", "error")
    else:
        flash("Invalid role selected.", "error")

    cursor.close()
    conn.close()
    return redirect(url_for('index'))

global username
# Route for student home page
@app.route('/student')
@nocache
def student():
    username = session.get('username')
    session['username']=username
    if session.get('role') != 'student':
        flash("Access denied. Please log in as a student.", "error")
        return redirect(url_for('index'))

    # Fetch student data based on the username
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Name, RollNo, CGPA, Sem, Branch FROM stdetails WHERE RollNo = %s", (username,))
    student_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if student_data:
        return render_template('Student_Home_index.html', student_data=student_data)
    else:
        flash("No student data found.", "error")
        return redirect(url_for('student'))

# Route for admin home page
@app.route('/admin_home')
@nocache
def admin_home():
    if session.get('role') != 'admin':
        flash("Access denied. Please log in as an admin.", "error")
        return redirect(url_for('index'))

    # Retrieve admin details using the stored adminID
    admin_id = session.get('username')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Name, empID FROM adetails WHERE empID = %s", (admin_id,))
    admin_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if admin_data:
        return render_template('Admin_Home_index.html', admin_data=admin_data)
    else:
        flash("No admin data found.", "error")
        return redirect(url_for('index'))

# All other routes remain the same...
# Route to retrieve courses for Re-Registration (RR)
@app.route('/get-courses_RR', methods=['GET'])
@nocache
def get_courses_RR():
    semester = request.args.get('semester')
    if not semester:
        return jsonify({'error': 'Semester parameter is missing'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT Cname FROM sub_RR WHERE sem = %s;", (semester,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)


# Route to add selected courses for Re-Registration (RR)
@app.route('/add-selected-courses_RR', methods=['POST'])
@nocache
def add_selected_courses_RR():
    data = request.json
    semester = int(data.get('semester'))
    courses = data.get('courses')

    if not semester or not courses:
        return jsonify({'error': 'Semester or courses data is missing'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing records for the semester in selected_courses_RR
    try:
        cursor.execute("DELETE FROM selected_courses_RR WHERE semester = %s", (semester,))
        conn.commit()

        # Insert new selected courses
        query = "INSERT INTO selected_courses_RR (semester, course_name) VALUES (%s, %s)"
        for course in courses:
            cursor.execute(query, (semester, course))
        conn.commit()

    except mysql.connector.Error as err:
        print("Error inserting courses:", err)
        return jsonify({'status': 'Failed to add courses'}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({'status': 'Courses added successfully'})

# Route to retrieve courses for Additional Slot (AS)
@app.route('/get-courses_AS', methods=['GET'])
@nocache
def get_courses_AS():
    semester = request.args.get('semester')
    if not semester:
        return jsonify({'error': 'Semester parameter is missing'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT Cname FROM sub_AS WHERE sem = %s;", (semester,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)

# Route to add selected courses for Additional Slot (AS)
@app.route('/add-selected-courses_AS', methods=['POST'])
@nocache
def add_selected_courses_AS():
    data = request.json
    semester = int(data.get('semester'))
    courses = data.get('courses')

    if not semester or not courses:
        return jsonify({'error': 'Semester or courses data is missing'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing records for the semester in selected_courses_AS
    try:
        cursor.execute("DELETE FROM selected_courses_AS WHERE semester = %s", (semester,))
        conn.commit()

        # Insert new selected courses
        query = "INSERT INTO selected_courses_AS (semester, course_name) VALUES (%s, %s)"
        for course in courses:
            cursor.execute(query, (semester, course))
        conn.commit()

    except mysql.connector.Error as err:
        print("Error inserting courses:", err)
        return jsonify({'status': 'Failed to add courses'}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({'status': 'Courses added successfully'})

# Route to retrieve courses for Contact Course (CC)
@app.route('/get-courses_CC', methods=['GET'])
@nocache
def get_courses_CC():
    semester = request.args.get('semester')
    if not semester:
        return jsonify({'error': 'Semester parameter is missing'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT Cname FROM sub_CC WHERE sem = %s;", (semester,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)

# Route to add selected courses for Contact Course (CC)
@app.route('/add-selected-courses_CC', methods=['POST'])
@nocache
def add_selected_courses_CC():
    data = request.json
    semester = int(data.get('semester'))
    courses = data.get('courses')

    if not semester or not courses:
        return jsonify({'error': 'Semester or courses data is missing'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing records for the semester in selected_courses_CC
    try:
        cursor.execute("DELETE FROM selected_courses_cc WHERE semester = %s", (semester,))
        conn.commit()

        # Insert new selected courses
        query = "INSERT INTO selected_courses_cc (semester, course_name) VALUES (%s, %s)"
        for course in courses:
            cursor.execute(query, (semester, course))
        conn.commit()

    except mysql.connector.Error as err:
        print("Error inserting courses:", err)
        return jsonify({'status': 'Failed to add courses'}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({'status': 'Courses added successfully'})

# Route to retrieve courses for Supply (S)
@app.route('/get-courses_S', methods=['GET'])
@nocache
def get_courses_S():
    semester = request.args.get('semester')
    if not semester:
        return jsonify({'error': 'Semester parameter is missing'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT Cname FROM sub_S WHERE sem = %s;", (semester,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)

# Route to add selected courses for Supply (S)
@app.route('/add-selected-courses_S', methods=['POST'])
@nocache
def add_selected_courses_S():
    data = request.json
    semester = int(data.get('semester'))
    courses = data.get('courses')

    if not semester or not courses:
        return jsonify({'error': 'Semester or courses data is missing'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing records for the semester in selected_courses_S
    try:
        cursor.execute("DELETE FROM selected_courses_S WHERE semester = %s", (semester,))
        conn.commit()

        # Insert new selected courses
        query = "INSERT INTO selected_courses_S (semester, course_name) VALUES (%s, %s)"
        for course in courses:
            cursor.execute(query, (semester, course))
        conn.commit()

    except mysql.connector.Error as err:
        print("Error inserting courses:", err)
        return jsonify({'status': 'Failed to add courses'}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({'status': 'Courses added successfully'})

@app.route('/get-courses_st_CC', methods=['GET'])
@nocache
def get_courses_st_CC():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    username=session.get('username')
    try:
        # Fetch distinct course names from selected_courses_CC
        cursor.execute("SELECT c.course_name FROM selected_courses_cc c,student s where s.Cname=c.course_name and s.RollNo=%s",(username,))
        data = cursor.fetchall()
    except Exception as e:
        print("Error fetching courses:", e)
        return jsonify({'error': 'Failed to fetch courses'}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify(data)

@app.route('/submit_CC', methods=['POST'])
@nocache
def submit_CC():
    data = request.json
    username=session.get('username')
    courses = data.get('courses')

    if not username or not courses:
        return jsonify({'error': 'Roll No or courses data is missing'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing records for the semester in selected_courses_S
    try:
        cursor.execute("SELECT Name FROM stdetails WHERE RollNo = %s", (username,))
        student_name = cursor.fetchone()
        student_name = student_name[0]
        # Clear existing records for the user
        cursor.execute("DELETE FROM student_app_cc WHERE RollNo = %s", (username,))
        conn.commit()

        # Insert new selected courses with the course name explicitly
        query = "INSERT INTO student_app_cc (RollNo, StudentName, CourseName) VALUES (%s, %s, %s)"
        for course in courses:
            cursor.execute(query, (username, student_name, course))
        conn.commit()

    except Exception as e:
        print("Error inserting courses:", e)
        return jsonify({'status': 'Failed to add courses'}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({'status': 'Courses added successfully'})

@app.route('/get-courses_st_RR', methods=['GET'])
@nocache
def get_courses_st_RR():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    username=session.get('username')
    try:
        # Fetch distinct course names from selected_courses_CC
        cursor.execute("SELECT c.course_name FROM selected_courses_rr c,student s where s.Cname=c.course_name and s.RollNo=%s",(username,))
        data = cursor.fetchall()
    except Exception as e:
        print("Error fetching courses:", e)
        return jsonify({'error': 'Failed to fetch courses'}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify(data)

@app.route('/submit_RR', methods=['POST'])
@nocache
def submit_RR():
    data = request.json
    username=session.get('username')
    courses = data.get('courses')

    if not username or not courses:
        return jsonify({'error': 'Roll No or courses data is missing'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing records for the semester in selected_courses_S
    try:
        cursor.execute("SELECT Name FROM stdetails WHERE RollNo = %s", (username,))
        student_name = cursor.fetchone()
        student_name = student_name[0]
        # Clear existing records for the user
        cursor.execute("DELETE FROM student_app_rr WHERE RollNo = %s", (username,))
        conn.commit()

        # Insert new selected courses with the course name explicitly
        query = "INSERT INTO student_app_rr (RollNo, StudentName, CourseName) VALUES (%s, %s, %s)"
        for course in courses:
            cursor.execute(query, (username, student_name, course))
        conn.commit()

    except Exception as e:
        print("Error inserting courses:", e)
        return jsonify({'status': 'Failed to add courses'}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({'status': 'Courses added successfully'})

@app.route('/get-courses_st_AS', methods=['GET'])
@nocache
def get_courses_st_AS():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    username=session.get('username')
    try:
        # Fetch distinct course names from selected_courses_CC
        cursor.execute("SELECT c.course_name FROM selected_courses_as c,student s where s.Cname=c.course_name and s.RollNo=%s",(username,))
        data = cursor.fetchall()
    except Exception as e:
        print("Error fetching courses:", e)
        return jsonify({'error': 'Failed to fetch courses'}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify(data)
@app.route('/get-st_s')
@nocache
def get_st_s():
    # Get query parameters
    roll_no = request.args.get('RollNo', '').strip()
    course_name = request.args.get('CourseName', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Build query with filters
        query = "SELECT RollNo, StudentName, CourseName FROM student_app_s WHERE 1=1"
        params = []
        if roll_no:
            query += " AND RollNo LIKE %s"
            params.append(f"%{roll_no}%")
        if course_name:
            query += " AND CourseName LIKE %s"
            params.append(f"%{course_name}%")
        
        cursor.execute(query, params)
        courses = cursor.fetchall()
        return jsonify([{"RollNo": row[0], "StudentName": row[1], "CourseName": row[2]} for row in courses])
    finally:
        cursor.close()
        conn.close()

@app.route('/submit_AS', methods=['POST'])
@nocache
def submit_AS():
    data = request.json
    username=session.get('username')
    courses = data.get('courses')

    if not username or not courses:
        return jsonify({'error': 'Roll No or courses data is missing'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing records for the semester in selected_courses_S
    try:
        cursor.execute("SELECT Name FROM stdetails WHERE RollNo = %s", (username,))
        student_name = cursor.fetchone()
        student_name = student_name[0]
        # Clear existing records for the user
        cursor.execute("DELETE FROM student_app_as WHERE RollNo = %s", (username,))
        conn.commit()

        # Insert new selected courses with the course name explicitly
        query = "INSERT INTO student_app_as (RollNo, StudentName, CourseName) VALUES (%s, %s, %s)"
        for course in courses:
            cursor.execute(query, (username, student_name, course))
        conn.commit()

    except Exception as e:
        print("Error inserting courses:", e)
        return jsonify({'status': 'Failed to add courses'}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({'status': 'Courses added successfully'})

@app.route('/get-courses_st_S', methods=['GET'])
@nocache
def get_courses_st_S():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    username=session.get('username')
    try:
        # Fetch distinct course names from selected_courses_CC
        cursor.execute("SELECT c.course_name FROM selected_courses_s c,student s where s.Cname=c.course_name and s.RollNo=%s",(username,))
        data = cursor.fetchall()
    except Exception as e:
        print("Error fetching courses:", e)
        return jsonify({'error': 'Failed to fetch courses'}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify(data)

@app.route('/submit_S', methods=['POST'])
@nocache
def submit_S():
    data = request.json
    username=session.get('username')
    courses = data.get('courses')

    if not username or not courses:
        return jsonify({'error': 'Roll No or courses data is missing'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing records for the semester in selected_courses_S
    try:
        cursor.execute("SELECT Name FROM stdetails WHERE RollNo = %s", (username,))
        student_name = cursor.fetchone()
        student_name = student_name[0]
        # Clear existing records for the user
        cursor.execute("DELETE FROM student_app_s WHERE RollNo = %s", (username,))
        conn.commit()

        # Insert new selected courses with the course name explicitly
        query = "INSERT INTO student_app_s (RollNo, StudentName, CourseName) VALUES (%s, %s, %s)"
        for course in courses:
            cursor.execute(query, (username, student_name, course))
        conn.commit()

    except Exception as e:
        print("Error inserting courses:", e)
        return jsonify({'status': 'Failed to add courses'}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({'status': 'Courses added successfully'})



@app.route('/get-st_cc', methods=['GET'])
@nocache
def get_st_cc():
    search_rollno = request.args.get('searchRollNo', '').strip()
    search_course_name = request.args.get('searchCourseName', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Base query
        query = "SELECT * FROM student_app_cc WHERE 1=1"
        params = []

        # Add search filters if provided
        if search_rollno:
            query += " AND RollNo LIKE %s"
            params.append(f"%{search_rollno}%")
        if search_course_name:
            query += " AND CourseName LIKE %s"
            params.append(f"%{search_course_name}%")

        cursor.execute(query, params)
        data = cursor.fetchall()
    except Exception as e:
        print("Error fetching courses:", e)
        return jsonify({'error': 'Failed to fetch courses'}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify(data)

# View Arrears
# Route to view arrears
@app.route('/view_arrears', methods=['GET'])
@nocache
def view_arrears():
    username = session.get('username')
    semester = request.args.get('semester')
    
    if not semester:
        # Render the initial view page without data
        return render_template('viewarrears.html')

    if session.get('role') != 'student':
        flash("Access denied. Please log in as a student.", "error")
        return redirect(url_for('index'))

    # Fetch arrears data for the specific semester
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT code, Cname, sem FROM starrears WHERE RollNo = %s AND sem = %s;", (username, semester,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    # Convert data to a list of dictionaries
    arrears_data = [{'code': row[0], 'Cname': row[1]} for row in data]
    return jsonify(arrears_data)



@app.route('/admin_re_registration')
@nocache
def admin_re_registration():
    print("Accessing Re-Registration")
    return render_template('Admin_ReRegistration.html')

@app.route('/admin_additional_slot')
@nocache
def admin_additional_slot():
    return render_template('Admin_AdditionalSlot.html')

@app.route('/admin_supply')
@nocache
def admin_supply():
    return render_template('Admin_Supply.html')

@app.route('/admin_contact_course')
@nocache
def admin_contact_course():
    return render_template('Admin_ContactCourse.html')

@app.route('/admin_add_slot')
@nocache
def admin_add_slot():
    return render_template('Admin_AdditionalSlot.html')


@app.route('/course_re_registration')
@nocache
def course_re_registration():
    return render_template('ReRegistration.html')

@app.route('/apply_additional_slot')
@nocache
def apply_additional_slot():
    return render_template('AdditionalSlot.html')

@app.route('/apply_supply')
@nocache
def apply_supply():
    return render_template('Supply.html')

@app.route('/apply_contact_course')
@nocache
def apply_contact_course():
    return render_template('ContactCourse.html')

@app.route('/admin_view_rr')
@nocache
def admin_view_rr():
    return render_template('Admin_View_RR.html')

@app.route('/admin_view_as')
@nocache
def admin_view_as():
    return render_template('Admin_View_AS.html')

@app.route('/admin_view_cc')
@nocache
def admin_view_cc():
    return render_template('Admin_View_CC.html')

@app.route('/admin_view_s')
@nocache
def admin_view_s():
    return render_template('Admin_View_S.html')

@app.route('/mark_paid', methods=['POST'])
@nocache
def mark_paid():
    # Get the JSON data from the frontend
    data = request.get_json()
    selected_students = data.get('students', [])

    # Validate input
    if not selected_students or not isinstance(selected_students, list):
        return jsonify({'success': False, 'status': 'No students selected or invalid input.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Build query dynamically based on the number of students
        query = "UPDATE student_app_cc SET Paid = 1 WHERE RollNo IN (%s)" % ','.join(['%s'] * len(selected_students))
        cursor.execute(query, selected_students)
        conn.commit()

        return jsonify({'success': True, 'status': 'Marked as paid successfully.'})
    except Exception as e:
        print("Error updating records:", e)
        return jsonify({'success': False, 'status': 'Failed to update records.'}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/view_paid_courses')
@nocache
def view_paid_courses():
    search_rollno = request.args.get('searchRollNo', '').strip()
    search_course_name = request.args.get('searchCourseName', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Base query
    query = "SELECT RollNo, StudentName, CourseName FROM student_app_cc WHERE 1=1"
    params = []

    # Add filters dynamically based on input
    if search_rollno:
        query += " AND RollNo LIKE %s"
        params.append(f"%{search_rollno}%")
    if search_course_name:
        query += " AND CourseName LIKE %s"
        params.append(f"%{search_course_name}%")

    cursor.execute(query, params)
    paid_courses = cursor.fetchall()

    cursor.close()
    conn.close()

    # Pass the search parameters back to the template for form persistence
    return render_template(
        'view_paid_courses.html',
        paid_courses=paid_courses,
        search_rollno=search_rollno,
        search_course_name=search_course_name
    )
@app.route('/view_admin_course')
@nocache
def view_admin_course():
    search_rollno = request.args.get('searchRollNo', '').strip()
    search_course_name = request.args.get('searchCourseName', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Base query
    query = "SELECT RollNo, StudentName, CourseName FROM student_app_cc WHERE 1=1"
    params = []

    # Add filters dynamically based on input
    if search_rollno:
        query += " AND RollNo LIKE %s"
        params.append(f"%{search_rollno}%")
    if search_course_name:
        query += " AND CourseName LIKE %s"
        params.append(f"%{search_course_name}%")

    cursor.execute(query, params)
    paid_courses = cursor.fetchall()

    cursor.close()
    conn.close()

    # Pass the search parameters back to the template for form persistence
    return render_template(
        'Admin_View_CC.html',
        paid_courses=paid_courses,
        search_rollno=search_rollno,
        search_course_name=search_course_name
    )

@app.route('/view_paid_courses_as')
@nocache
def view_paid_courses_as():
    search_rollno = request.args.get('searchRollNo', '').strip()
    search_course_name = request.args.get('searchCourseName', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Base query
    query = "SELECT RollNo, StudentName, CourseName FROM student_app_as WHERE 1=1"
    params = []

    # Add filters dynamically based on input
    if search_rollno:
        query += " AND RollNo LIKE %s"
        params.append(f"%{search_rollno}%")
    if search_course_name:
        query += " AND CourseName LIKE %s"
        params.append(f"%{search_course_name}%")

    cursor.execute(query, params)
    paid_courses = cursor.fetchall()

    cursor.close()
    conn.close()

    # Pass the search parameters back to the template for form persistence
    return render_template(
        'view_paid_courses_as.html',
        paid_courses=paid_courses,
        search_rollno=search_rollno,
        search_course_name=search_course_name
    )

@app.route('/get-st_rr')
@nocache
def get_st_rr():
    # Get query parameters
    roll_no = request.args.get('RollNo', '').strip()
    course_name = request.args.get('CourseName', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Build query with filters
        query = "SELECT RollNo, StudentName, CourseName FROM student_app_rr WHERE 1=1"
        params = []
        if roll_no:
            query += " AND RollNo LIKE %s"
            params.append(f"%{roll_no}%")
        if course_name:
            query += " AND CourseName LIKE %s"
            params.append(f"%{course_name}%")
        
        cursor.execute(query, params)
        courses = cursor.fetchall()
        return jsonify([{"RollNo": row[0], "StudentName": row[1], "CourseName": row[2]} for row in courses])
    finally:
        cursor.close()
        conn.close()

@app.route('/get-st_course_AS')
@nocache
def get_st_course_as():
    # Get query parameters
    roll_no = request.args.get('RollNo', '').strip()
    course_name = request.args.get('CourseName', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Build query with filters
        query = "SELECT RollNo, StudentName, CourseName FROM student_app_as WHERE 1=1"
        params = []
        if roll_no:
            query += " AND RollNo LIKE %s"
            params.append(f"%{roll_no}%")
        if course_name:
            query += " AND CourseName LIKE %s"
            params.append(f"%{course_name}%")
        
        cursor.execute(query, params)
        courses = cursor.fetchall()
        return jsonify([{"RollNo": row[0], "StudentName": row[1], "CourseName": row[2]} for row in courses])
    finally:
        cursor.close()
        conn.close()

@app.route('/mark_paid_as', methods=['POST'])
@nocache
def mark_paid_as():
    # Get the JSON data from the frontend
    data = request.get_json()
    selected_students = data.get('students', [])

    # Validate input
    if not selected_students or not isinstance(selected_students, list):
        return jsonify({'success': False, 'status': 'No students selected or invalid input.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Build query dynamically based on the number of students
        query = "UPDATE student_app_as SET Paid = 1 WHERE RollNo IN (%s)" % ','.join(['%s'] * len(selected_students))
        cursor.execute(query, selected_students)
        conn.commit()

        return jsonify({'success': True, 'status': 'Marked as paid successfully.'})
    except Exception as e:
        print("Error updating records:", e)
        return jsonify({'success': False, 'status': 'Failed to update records.'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/view_admin_course_as')
@nocache
def view_admin_course_as():
    search_rollno = request.args.get('searchRollNo', '').strip()
    search_course_name = request.args.get('searchCourseName', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Base query
    query = "SELECT RollNo, StudentName, CourseName FROM student_app_as WHERE 1=1"
    params = []

    # Add filters dynamically based on input
    if search_rollno:
        query += " AND RollNo LIKE %s"
        params.append(f"%{search_rollno}%")
    if search_course_name:
        query += " AND CourseName LIKE %s"
        params.append(f"%{search_course_name}%")

    cursor.execute(query, params)
    paid_courses = cursor.fetchall()

    cursor.close()
    conn.close()

    # Pass the search parameters back to the template for form persistence
    return render_template(
        'Admin_View_AS.html',
        paid_courses=paid_courses,
        search_rollno=search_rollno,
        search_course_name=search_course_name
    )

@app.route('/logout', methods=['POST'])
def logout():
    # Clear session data (this logs out the user)
    session.clear()

    # Optional: Clear cookies if necessary
    resp = redirect('/')
    resp.set_cookie('logged_out', 'true', max_age=0)  # Clear any 'logged_out' cookies

    return resp

# Re-registration confirmation
@app.route('/confirmation_page_rr1')
def confirmation_page_rr1():
    if 'username' not in session or session.get('role') != 'student':
        flash("Access denied. Please log in as a student.", "error")
        return redirect(url_for('index'))

    username = session.get('username')

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch student details and re-registration data
    cursor.execute("SELECT Name, RollNo, Branch FROM stdetails WHERE RollNo = %s", (username,))
    student_info = cursor.fetchone()

    cursor.execute(
        "SELECT CourseName FROM student_app_rr WHERE RollNo = %s", 
        (username,)
    )
    courses = cursor.fetchall()

    cursor.close()
    conn.close()

    if student_info:
        return render_template(
            'ConfirmationPage_RR1.html',
            student_name=student_info[0],
            roll_no=student_info[1],
            branch=student_info[2],
            courses=courses
        )
    else:
        flash("No student data found.", "error")
        return redirect(url_for('student'))


# Additional slot confirmation
@app.route('/confirmation_page_as1')
def confirmation_page_as1():
    if 'username' not in session or session.get('role') != 'student':
        flash("Access denied. Please log in as a student.", "error")
        return redirect(url_for('index'))

    username = session.get('username')

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch student details and additional slot data
    cursor.execute("SELECT Name, RollNo, Branch FROM stdetails WHERE RollNo = %s", (username,))
    student_info = cursor.fetchone()

    if student_info:
        cursor.execute("SELECT CourseName FROM student_app_as WHERE RollNo = %s", (username,))
        courses = cursor.fetchall()

        # If no courses are found, handle it appropriately
        if not courses:
            courses = []

        cursor.close()
        conn.close()

        return render_template(
            'ConfirmationPage_AS1.html',
            student_name=student_info[0],
            roll_no=student_info[1],
            branch=student_info[2],
            courses=courses
        )
    else:
        flash("No student data found.", "error")
        cursor.close()
        conn.close()
        return redirect(url_for('student'))


# Supply confirmation
@app.route('/confirmation_page_s1')
def confirmation_page_s1():
    if 'username' not in session or session.get('role') != 'student':
        flash("Access denied. Please log in as a student.", "error")
        return redirect(url_for('index'))

    username = session.get('username')

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch student details and supply data
    cursor.execute("SELECT Name, RollNo, Branch FROM stdetails WHERE RollNo = %s", (username,))
    student_info = cursor.fetchone()

    if student_info:
        cursor.execute("SELECT CourseName FROM student_app_s WHERE RollNo = %s", (username,))
        courses = cursor.fetchall()

        # If no courses are found, handle it appropriately
        if not courses:
            courses = []

        cursor.close()
        conn.close()

        return render_template(
            'ConfirmationPage_S1.html',
            student_name=student_info[0],
            roll_no=student_info[1],
            branch=student_info[2],
            courses=courses
        )
    else:
        flash("No student data found.", "error")
        cursor.close()
        conn.close()
        return redirect(url_for('student'))


# Core course confirmation
@app.route('/confirmation_page_cc1')
def confirmation_page_cc1():
    if 'username' not in session or session.get('role') != 'student':
        flash("Access denied. Please log in as a student.", "error")
        return redirect(url_for('index'))

    username = session.get('username')

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch student details and core course data
    cursor.execute("SELECT Name, RollNo, Branch FROM stdetails WHERE RollNo = %s", (username,))
    student_info = cursor.fetchone()

    if student_info:
        cursor.execute("SELECT CourseName FROM student_app_cc WHERE RollNo = %s", (username,))
        courses = cursor.fetchall()
        cursor.close()
        conn.close()

        # If no courses are found, handle it appropriately
        if not courses:
            courses = []

        cursor.close()
        conn.close()

        return render_template(
            'ConfirmationPage_CC1.html',
            student_name=student_info[0],
            roll_no=student_info[1],
            branch=student_info[2],
            courses=courses
        )
    else:
        flash("No student data found.", "error")
        return redirect(url_for('student'))

if __name__ == '__main__':
    app.run(debug=True)
