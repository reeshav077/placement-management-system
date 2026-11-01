import mysql.connector
import certifi
from streamlit import cursor

from db_connection import get_connection

# ==========================================
# CREATE OPERATIONS
# ==========================================

def add_student(roll_number, name, branch, cgpa, email):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = "INSERT INTO Student (Roll_Number, Name, Branch, CGPA, Email) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (roll_number, name, branch, cgpa, email))
            conn.commit()
            return True, "Student registered successfully."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    return False, "Database connection failed."

def add_company(name, industry, location):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = "INSERT INTO Company (Name, Industry, Location) VALUES (%s, %s, %s)"
            cursor.execute(sql, (name, industry, location))
            conn.commit()
            return True, f"Company '{name}' registered successfully!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    return False, "Database connection failed."

def add_job_posting(company_id, role_title, ctc_lpa, min_cgpa, openings):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = """
                INSERT INTO Job_Posting (Company_ID, Role_Title, CTC_LPA, Min_CGPA, Openings) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (company_id, role_title, ctc_lpa, min_cgpa, openings))
            conn.commit()
            return True, f"Job '{role_title}' posted successfully!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    return False, "Database connection failed."

def apply_for_job(roll_number, job_id):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = "INSERT INTO Application (Roll_Number, Job_ID, Application_Status) VALUES (%s, %s, 'Applied')"
            cursor.execute(sql, (roll_number, job_id))
            conn.commit()
            return True, "Application submitted."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    return False, "Database connection failed."

def schedule_interview_round(app_id, round_name, score, feedback, round_status):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = """
                INSERT INTO Interview_Round (App_ID, Round_Name, Score, Feedback, Round_Status) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (app_id, round_name, score, feedback, round_status))
            conn.commit()
            return True, f"{round_name} logged for Application #{app_id}."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    return False, "Database connection failed."

def rollout_job_offer(app_id, base_salary, joining_date):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            verify_sql = "SELECT Application_Status FROM Application WHERE App_ID = %s"
            cursor.execute(verify_sql, (app_id,))
            result = cursor.fetchone()
            
            if result and result[0] != 'Offered':
                offer_sql = """
                    INSERT INTO Job_Offer (App_ID, Offer_Date, Base_Salary_LPA, Joining_Date, Acceptance_Status) 
                    VALUES (%s, CURRENT_DATE(), %s, %s, 'Pending')
                """
                cursor.execute(offer_sql, (app_id, base_salary, joining_date))
                
                update_sql = "UPDATE Application SET Application_Status = 'Offered' WHERE App_ID = %s"
                cursor.execute(update_sql, (app_id,))
                
                conn.commit()
                return True, "Job offer rolled out successfully!"
            return False, "Candidate is already offered or invalid application."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    return False, "Database connection failed."

# ==========================================
# READ OPERATIONS
# ==========================================

def get_all_students():
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Student")
            return cursor.fetchall()
        finally:
            conn.close()
    return []

def get_all_companies():
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Company")
            return cursor.fetchall()
        finally:
            conn.close()
    return []

def get_all_jobs():
    """Fetches all active jobs for the student portal with JOIN."""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # Fixed schema: Aliases 'Name' and 'Openings' so Streamlit UI reads them cleanly
            sql = """
                SELECT 
                    jp.Job_ID, 
                    c.Name AS Company_Name, 
                    jp.Role_Title AS Role, 
                    jp.CTC_LPA AS CTC, 
                    jp.Min_CGPA, 
                    jp.Openings 
                FROM Job_Posting jp
                JOIN Company c ON jp.Company_ID = c.Company_ID
            """
            cursor.execute(sql)
            return cursor.fetchall()
        except Exception:
            return []
        finally:
            conn.close()
    return []
def get_recruitment_overview():
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT 
                    a.App_ID,
                    s.Name AS Student_Name,
                    s.Roll_Number,
                    c.Name AS Company,
                    j.Role_Title,
                    j.CTC_LPA,
                    a.Application_Status
                FROM Application a
                JOIN Student s ON a.Roll_Number = s.Roll_Number
                JOIN Job_Posting j ON a.Job_ID = j.Job_ID
                JOIN Company c ON j.Company_ID = c.Company_ID
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            conn.close()
    return []

def get_interview_evaluations():
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT 
                    ir.Round_ID,
                    ir.App_ID,
                    s.Name AS Candidate_Name,
                    c.Name AS Hiring_Company,
                    ir.Round_Name,
                    ir.Score,
                    ir.Feedback,
                    ir.Round_Status
                FROM Interview_Round ir
                JOIN Application a ON ir.App_ID = a.App_ID
                JOIN Student s ON a.Roll_Number = s.Roll_Number
                JOIN Job_Posting j ON a.Job_ID = j.Job_ID
                JOIN Company c ON j.Company_ID = c.Company_ID
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            conn.close()
    return []

def get_eligible_jobs(roll_number):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT j.Job_ID, c.Name AS Company, j.Role_Title, j.CTC_LPA, j.Min_CGPA
                FROM Job_Posting j
                JOIN Company c ON j.Company_ID = c.Company_ID
                WHERE j.Min_CGPA <= (
                    SELECT CGPA FROM Student WHERE Roll_Number = %s
                )
                AND j.Job_ID NOT IN (
                    SELECT Job_ID FROM Application WHERE Roll_Number = %s
                )
            """
            cursor.execute(sql, (roll_number, roll_number))
            return cursor.fetchall()
        finally:
            conn.close()
    return []

def get_placement_analytics():
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT 
                    (SELECT COUNT(*) FROM Student) as Total_Students,
                    (SELECT COUNT(*) FROM Job_Offer WHERE Acceptance_Status = 'Accepted') as Total_Placed,
                    (SELECT MAX(Base_Salary_LPA) FROM Job_Offer WHERE Acceptance_Status = 'Accepted') as Highest_Package,
                    (SELECT AVG(Base_Salary_LPA) FROM Job_Offer WHERE Acceptance_Status = 'Accepted') as Average_Package
            """
            cursor.execute(sql)
            return cursor.fetchone()
        finally:
            conn.close()
    return {}

# ==========================================
# UPDATE OPERATIONS
# ==========================================

def update_application_status(app_id, new_status):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = "UPDATE Application SET Application_Status = %s WHERE App_ID = %s"
            cursor.execute(sql, (new_status, app_id))
            conn.commit()
            if cursor.rowcount > 0:
                return True, f"Application #{app_id} status updated to '{new_status}'."
            return False, f"Application ID #{app_id} not found."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    return False, "Database connection failed."

def accept_job_offer(app_id):
    """Student accepts offer (atomic update)."""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Fixed bug: Ensure it only accepts 'Pending' offers
            sql_offer = "UPDATE Job_Offer SET Acceptance_Status = 'Accepted' WHERE App_ID = %s AND Acceptance_Status = 'Pending'"
            cursor.execute(sql_offer, (app_id,))
            if cursor.rowcount > 0:
                # Fixed bug: Also update the main application table
                sql_app = "UPDATE Application SET Status = 'Placed' WHERE App_ID = %s"
                cursor.execute(sql_app, (app_id,))
                conn.commit()
                return True, "Offer accepted! Status updated to Placed."
            return False, "No 'Pending' offer found for this Application ID."
        except Exception:
            return False, "An error occurred while accepting the offer."
        finally:
            conn.close()
    return False, "Database connection failed."

def update_student_profile(roll_number, new_name, new_branch, new_cgpa, new_email):
    """Updates a student's profile details based on their Roll Number."""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = """
                UPDATE Student 
                SET Name = %s, Branch = %s, CGPA = %s, Email = %s 
                WHERE Roll_Number = %s
            """
            cursor.execute(sql, (new_name, new_branch, new_cgpa, new_email, roll_number))
            conn.commit()
            
            if cursor.rowcount > 0:
                return True, "Profile updated successfully!"
            return False, "Roll Number not found. Please check and try again."
        except Exception as e:
            return False, f"Error updating profile: {str(e)}"
        finally:
            conn.close()
    return False, "Database connection failed."
# ==========================================
# DELETE OPERATIONS
# ==========================================

def delete_student(roll_number):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = "DELETE FROM Student WHERE Roll_Number = %s"
            cursor.execute(sql, (roll_number,))
            conn.commit()
            if cursor.rowcount > 0:
                return True, f"Student {roll_number} deleted successfully."
            return False, f"Student with Roll Number {roll_number} not found."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    return False, "Database connection failed."

def get_total_placed_students():
    """Counts unique placed students."""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Fixed bug: Uses DISTINCT Roll_Number via JOIN so multiple offers don't overcount
            sql = """
                SELECT COUNT(DISTINCT a.Roll_Number) 
                FROM Job_Offer jo
                JOIN Application a ON jo.App_ID = a.App_ID
                WHERE jo.Acceptance_Status = 'Accepted'
            """
            cursor.execute(sql)
            result = cursor.fetchone()
            return result[0] if result and result[0] else 0
        except Exception:
            return 0
        finally:
            conn.close()
    return 0

def get_highest_package():
    """Finds the maximum CTC among accepted offers."""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(Base_Salary_LPA) FROM Job_Offer WHERE Acceptance_Status = 'Accepted'")
            result = cursor.fetchone()
            return float(result[0]) if result and result[0] else 0.0
        except Exception as e:
            return 0.0
        finally:
            conn.close()
    return 0.0

def get_total_companies():
    """Counts the total number of registered recruiting companies."""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Company")
            result = cursor.fetchone()
            return result[0] if result and result[0] else 0
        except Exception as e:
            return 0
        finally:
            conn.close()
    return 0

def register_student(roll_num, name, branch, cgpa, email):
    """Registers a new student in the database."""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = "INSERT INTO Student (Roll_Number, Name, Branch, CGPA, Email) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (roll_num, name, branch, cgpa, email))
            conn.commit()
            return True, "Student registered successfully!"
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
        finally:
            conn.close()
    return False, "Database connection failed."

def post_job(comp_id, role_title, ctc, min_cgpa, openings):
    """Inserts a new job posting."""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Fixed schema: Uses 'Openings' instead of 'Openings_Available'
            sql = """
                INSERT INTO Job_Posting (Company_ID, Role_Title, CTC_LPA, Min_CGPA, Openings)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (comp_id, role_title, ctc, min_cgpa, openings))
            conn.commit()
            return True, "Job drive posted successfully!"
        except Exception:
            return False, "Failed to post job. Please verify the Company ID exists."
        finally:
            conn.close()
    return False, "Database connection failed."

def add_company(comp_id, comp_name):
    """Registers a new company into the database."""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Note: Ensure column names match your TiDB schema (e.g., Company_ID, Name)
            cursor.execute("INSERT INTO Company (Company_ID, Name) VALUES (%s, %s)", (comp_id, comp_name))
            conn.commit()
            return True, f"{comp_name} has been officially approved and added to the database!"
        except Exception as e:
            return False, f"Error adding company: {str(e)}"
        finally:
            conn.close()
    return False, "Database connection failed."

def get_student_applications(roll_num):
    """Fetches a student's real application statuses using JOINs."""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT 
                    a.Job_ID, 
                    c.Name AS Company, 
                    a.Status 
                FROM Application a
                JOIN Job_Posting jp ON a.Job_ID = jp.Job_ID
                JOIN Company c ON jp.Company_ID = c.Company_ID
                WHERE a.Roll_Number = %s
            """
            cursor.execute(sql, (roll_num,))
            return cursor.fetchall()
        except Exception as e:
            return []
        finally:
            conn.close()
    return []