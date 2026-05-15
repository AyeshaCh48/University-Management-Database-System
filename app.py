import oracledb
import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'university_super_secret_key'

# --- ORACLE THICK MODE SETUP ---
lib_path = r"C:\instantclient_23"
try:
    if os.path.exists(lib_path):
        oracledb.init_oracle_client(lib_dir=lib_path)
except Exception as e:
    print(f"Oracle Client Error: {e}")

def get_db_connection():
    return oracledb.connect(
        user="PROJECT", 
        password="123", 
        host="localhost", 
        port=1521, 
        sid="xe"
    )

# --- PUBLIC ROUTES ---

@app.route('/')
def splash():
    return render_template('splash')

@app.route('/login/<role>')
def login_page(role):
    return render_template('login', role=role)

@app.route('/auth', methods=['POST'])
def auth():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""SELECT role, ref_id FROM user_logins 
                   WHERE username = :1 AND password = :2 AND role = :3""", 
                [username, password, role])
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        session['username'] = username
        session['role'] = user[0]
        session['ref_id'] = user[1]
        return redirect(url_for('dashboard'))
    else:
        error = "Invalid credentials or unauthorized portal access."
        return render_template('login', role=role, error=error)

# --- DASHBOARD REDIRECTOR ---

@app.route('/dashboard')
def dashboard():
    if 'role' not in session:
        return redirect(url_for('splash'))
    
    role = session['role']
    if session['role'] == 'ADMIN':
        return redirect(url_for('admin_action', action='welcome'))
    
    elif session['role'] == 'INSTRUCTOR':
        return redirect(url_for('instructor_action', action='welcome'))
    
    elif session['role'] == 'STUDENT':
        return redirect(url_for('student_action', action='welcome'))

# --- ADMIN PORTAL ACTIONS ---

@app.route('/admin_action/<action>', methods=['GET', 'POST'])
def admin_action(action):
    if session.get('role') != 'ADMIN':
        return redirect(url_for('splash'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    message = None
    data = []
    lists = {}

    # 1. HANDLE FORM SUBMISSIONS (POST)
    if request.method == 'POST':
        try:
            if action == 'add_exam':
                cur.callproc("add_new_exam", [request.form.get('id'), request.form.get('type'), request.form.get('date'), request.form.get('c_id')])
                message = "SUCCESS: Exam scheduled."
            
            elif action == 'remove_exam':
                cur.callproc("delete_exam", [request.form.get('id')])
                message = "SUCCESS: Exam removed."

            elif action == 'add_student':
                cur.callproc("add_full_student", [
                    request.form.get('id'), request.form.get('name'), request.form.get('email'),
                    request.form.get('phone'), request.form.get('year'), request.form.get('program'),
                    request.form.get('type'), request.form.get('spec')
                ])
                message = "SUCCESS: Student and Person record created."

            elif action == 'remove_student':
                cur.callproc("delete_full_student", [request.form.get('id')])
                message = "SUCCESS: Student records deleted."

            elif action == 'add_instructor':
                cur.callproc("add_full_instructor", [
                    request.form.get('id'), request.form.get('name'), request.form.get('email'),
                    request.form.get('phone'), request.form.get('salary'), request.form.get('rank'),
                    request.form.get('block'), request.form.get('floor'), request.form.get('room')
                ])
                message = "SUCCESS: Instructor added."

            elif action == 'remove_instructor':
                cur.callproc("delete_full_instructor", [request.form.get('id')])
                message = "SUCCESS: Instructor removed."

            elif action == 'add_course':
                cur.callproc("add_full_course", [
                    request.form.get('id'), request.form.get('name'), 
                    request.form.get('credits'), request.form.get('dept_no'), request.form.get('inst_id')
                ])
                message = "SUCCESS: Course created."

            elif action == 'remove_course':
                cur.callproc("delete_full_course", [request.form.get('id')])
                message = "SUCCESS: Course deleted."

            conn.commit()
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            message = f"DATABASE ERROR: {error_obj.message}"
        except Exception as e:
            message = f"SYSTEM ERROR: {str(e)}"

    # 2. FETCH DATA FOR DROPDOWNS (Required for GET and POST)
    try:
        # Departments
        cur.execute("SELECT dept_no, dept_name FROM department ORDER BY dept_name")
        lists['depts'] = cur.fetchall()

        # Courses
        cur.execute("SELECT course_id, course_name FROM course ORDER BY course_id")
        lists['courses'] = cur.fetchall()

        cur.execute("SELECT DISTINCT program FROM student WHERE program IS NOT NULL ORDER BY program")
        lists['programs'] = [row[0] for row in cur.fetchall()]
        # FIXED: Instructor Join (Solves ORA-00904)
        cur.execute("""
            SELECT i.person_id, p.name 
            FROM instructor i 
            JOIN person p ON i.person_id = p.person_id 
            ORDER BY p.name
        """)
        lists['instructors'] = cur.fetchall()

        # Exams for deletion
        cur.execute("SELECT exam_id, exam_type, course_id FROM exam")
        lists['exams'] = cur.fetchall()

        if action == 'view_passwords':
            cur.execute("SELECT * FROM user_logins")
            data = cur.fetchall()

    except oracledb.DatabaseError as e:
        print(f"Error loading dropdown lists: {e}")

    cur.close()
    conn.close()
    return render_template('admin_dashboard', action=action, message=message, data=data, lists=lists, user=session['username'])

@app.route('/instructor_action/<action>', methods=['GET', 'POST'])
def instructor_action(action):
    if session.get('role') != 'INSTRUCTOR': 
        return redirect(url_for('login_page', role='instructor'))
    
    # Initialize all variables at the top so they exist for the template
    inst_id = session.get('ref_id')
    message = request.args.get('message')
    students, exams, my_courses = [], [], []
    selected_cid = request.args.get('cid') or request.form.get('cid')
    view_data = {'attendance': [], 'grades': []}
    
    conn = None
    cur = None

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Fetch Instructor's courses
        cur.execute("SELECT course_id, course_name FROM course WHERE instructor_id = :1", [inst_id])
        my_courses = cur.fetchall()

        # 2. Handle POST submissions
        if request.method == 'POST' and 'sid' in request.form:
            if action == 'mark_attendance':
                cur.callproc("record_attendance", [
                    request.form.get('date'), request.form.get('status'),
                    request.form.get('sid'), request.form.get('cid')
                ])
                message = "SUCCESS: Attendance marked."
            elif action == 'upload_grades':
                cur.callproc("record_grade", [
                    request.form.get('marks'), request.form.get('grade'),
                    request.form.get('sid'), request.form.get('eid')
                ])
                message = "SUCCESS: Grade/Marks uploaded."
            conn.commit()

        # 3. Handle data fetching (Dropdowns or View Records)
        if selected_cid:
            # Students
            cur.execute("SELECT p.person_id, p.name FROM enrollment e JOIN person p ON e.student_id = p.person_id WHERE e.course_id = :1", [selected_cid])
            students = cur.fetchall()
            # Exams
            cur.execute("SELECT exam_id, exam_type FROM exam WHERE course_id = :1", [selected_cid])
            exams = cur.fetchall()

            if action == 'view_records':
                cur.execute("SELECT p.name, a.date_val, a.status FROM attendance a JOIN person p ON a.student_id = p.person_id WHERE a.course_id = :1 ORDER BY a.date_val DESC", [selected_cid])
                view_data['attendance'] = cur.fetchall()
                cur.execute("SELECT p.name, e.exam_type, g.marks, g.grade_letter FROM grade g JOIN person p ON g.student_id = p.person_id JOIN exam e ON g.exam_id = e.exam_id WHERE e.course_id = :1 ORDER BY p.name", [selected_cid])
                view_data['grades'] = cur.fetchall()

    except Exception as e:
        message = f"System Error: {str(e)}"
        print(f"DEBUG ERROR: {e}") # This shows in your terminal
    
    finally:
        # THE SAFE CLEANUP: Only close if they actually exist and are open
        if cur:
            cur.close()
        if conn:
            conn.close()
    
    # This return is OUTSIDE the try/finally so it always runs
    return render_template('instructor_dashboard', 
                           action=action, message=message, courses=my_courses, 
                           students=students, exams=exams, selected_cid=selected_cid,
                           view_data=view_data)

@app.route('/student_action/<action>')
def student_action(action):
    if session.get('role') != 'STUDENT':
        return redirect(url_for('login_page', role='student'))
    
    student_id = session.get('ref_id')
    selected_cid = request.args.get('cid')
    
    # Initialize data containers
    enrolled_courses = []
    attendance_records = []
    marks_data = []
    upcoming_exams = []
    
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Get courses the student is enrolled in
        cur.execute("""
            SELECT c.course_id, c.course_name 
            FROM enrollment e 
            JOIN course c ON e.course_id = c.course_id 
            WHERE e.student_id = :1
        """, [student_id])
        enrolled_courses = cur.fetchall()

        # 2. Get Upcoming Exams (for all enrolled courses)
        cur.execute("""
            SELECT e.exam_type, e.exam_date, e.course_id 
            FROM exam e 
            JOIN enrollment en ON e.course_id = en.course_id 
            WHERE en.student_id = :1 AND e.exam_date >= SYSDATE
            ORDER BY e.exam_date ASC
        """, [student_id])
        upcoming_exams = cur.fetchall()

        # 3. If a specific course is selected, fetch detailed Marks and Attendance
        if selected_cid:
            # Fetch Attendance for this course
            cur.execute("""
                SELECT date_val, status 
                FROM attendance 
                WHERE student_id = :1 AND course_id = :2 
                ORDER BY date_val DESC
            """, [student_id, selected_cid])
            attendance_records = cur.fetchall()

            # Fetch Marks categorized by exam type
            cur.execute("""
                SELECT e.exam_type, g.marks, g.grade_letter 
                FROM grade g 
                JOIN exam e ON g.exam_id = e.exam_id 
                WHERE g.student_id = :1 AND e.course_id = :2
            """, [student_id, selected_cid])
            marks_data = cur.fetchall()

    except Exception as e:
        print(f"Student Portal Error: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()
        
    return render_template('student_dashboard', 
                           action=action, 
                           courses=enrolled_courses, 
                           exams=upcoming_exams, 
                           attendance=attendance_records, 
                           marks=marks_data, 
                           selected_cid=selected_cid)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('splash'))

if __name__ == '__main__':
    app.run(debug=True)