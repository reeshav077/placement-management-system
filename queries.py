"""Database operations for the placement management app.

Requires db_connection.py to expose get_connection(), returning a
mysql-connector compatible connection (or None on failure).
"""

from contextlib import closing
from db_connection import get_connection


def _run(sql, params=(), *, fetch=None, dictionary=False, return_lastrowid=False):
    """Run one statement and always close its cursor/connection.

    fetch: 'all', 'one', or None. Writes are committed only on success.
    """
    conn = get_connection()
    if conn is None:
        return None
    try:
        with closing(conn.cursor(dictionary=dictionary)) as cur:
            cur.execute(sql, params)
            if fetch == "all":
                return cur.fetchall()
            if fetch == "one":
                return cur.fetchone()
            conn.commit()
            if return_lastrowid:
                return cur.lastrowid
            return cur.rowcount
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


def _safe_all(sql, params=()):
    try:
        return _run(sql, params, fetch="all", dictionary=True) or []
    except Exception:
        return []


def _safe_one(sql, params=()):
    try:
        return _run(sql, params, fetch="one", dictionary=True)
    except Exception:
        return None


def _format_error(exc):
    msg = str(exc)
    if "Duplicate entry" in msg:
        if "PRIMARY" in msg or "Student.PRIMARY" in msg:
            return "A student with this Roll Number is already registered."
        if "Email" in msg:
            return "This email address is already registered."
        if "Company_ID" in msg:
            return "This Company ID already exists."
        return "A record with this identifier already exists."
    if "Cannot add or update a child row" in msg or "foreign key constraint fails" in msg:
        if "Roll_Number" in msg:
            return "Student Roll Number does not exist."
        if "Job_ID" in msg:
            return "Job ID does not exist."
        if "Company_ID" in msg:
            return "Company ID does not exist."
        if "App_ID" in msg:
            return "Application ID does not exist."
        return "Referenced record does not exist."
    if "Data truncated" in msg:
        return "Invalid input format or status value provided."
    if "Out of range value" in msg:
        return "Value entered is out of acceptable numerical range."
    return msg


def _write(sql, params, success_message, *, missing_message=None):
    try:
        count = _run(sql, params)
        if count is None:
            return False, "Database connection failed. Please check your network or DB credentials."
        if count == 0 and missing_message:
            return False, missing_message
        return True, success_message
    except Exception as exc:
        return False, _format_error(exc)


# ==========================================
# STUDENT OPERATIONS
# ==========================================

def add_student(roll_number, name, branch, cgpa, email):
    return register_student(roll_number, name, branch, cgpa, email)


def register_student(roll_num, name, branch, cgpa, email):
    roll_num = str(roll_num).strip()
    name = str(name).strip()
    branch = str(branch).strip()
    email = str(email).strip()
    try:
        cgpa = float(cgpa)
    except (ValueError, TypeError):
        return False, "CGPA must be a valid number."
    if not (0.0 <= cgpa <= 10.0):
        return False, "CGPA must be between 0.0 and 10.0."
    if not roll_num or not name or not email:
        return False, "Roll number, name, and email are required."

    return _write(
        "INSERT INTO Student (Roll_Number, Name, Branch, CGPA, Email) VALUES (%s,%s,%s,%s,%s)",
        (roll_num, name, branch, round(cgpa, 2), email),
        f"Student '{name}' ({roll_num}) registered successfully!",
    )


def update_student_profile(roll_number, new_name, new_branch, new_cgpa, new_email):
    roll_number = str(roll_number).strip()
    new_name = str(new_name).strip()
    new_branch = str(new_branch).strip()
    new_email = str(new_email).strip()
    try:
        new_cgpa = float(new_cgpa)
    except (ValueError, TypeError):
        return False, "CGPA must be a valid number."

    if not (0.0 <= new_cgpa <= 10.0):
        return False, "CGPA must be between 0.0 and 10.0."
    if not roll_number or not new_name or not new_email:
        return False, "Roll number, name, and email are required."

    return _write(
        "UPDATE Student SET Name=%s, Branch=%s, CGPA=%s, Email=%s WHERE Roll_Number=%s",
        (new_name, new_branch, round(new_cgpa, 2), new_email, roll_number),
        "Profile updated successfully!",
        missing_message=f"Student with Roll Number '{roll_number}' not found.",
    )


def delete_student(roll_number):
    roll_number = str(roll_number).strip()
    if not roll_number:
        return False, "Roll number is required."
    return _write(
        "DELETE FROM Student WHERE Roll_Number=%s",
        (roll_number,),
        f"Student '{roll_number}' and all associated records deleted successfully.",
        missing_message=f"Student with Roll Number '{roll_number}' not found.",
    )


def get_student_by_roll(roll_number):
    roll_number = str(roll_number).strip()
    if not roll_number:
        return None
    return _safe_one(
        "SELECT Roll_Number, Name, Branch, CGPA, Email FROM Student WHERE Roll_Number=%s",
        (roll_number,),
    )


def get_all_students():
    return _safe_all("SELECT Roll_Number, Name, Branch, CGPA, Email FROM Student ORDER BY Roll_Number ASC")


# ==========================================
# COMPANY OPERATIONS
# ==========================================

def add_company(name, industry=None, location=None, comp_id=None):
    """Register a company; ID is generated by the DB unless explicitly supplied."""
    name = str(name).strip()
    if not name:
        return False, "Company name is required."
    industry = industry.strip() if industry and str(industry).strip() else None
    location = location.strip() if location and str(location).strip() else None

    conn = get_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        with closing(conn.cursor()) as cur:
            if comp_id is not None:
                cur.execute(
                    "INSERT INTO Company (Company_ID, Name, Industry, Location) VALUES (%s,%s,%s,%s)",
                    (int(comp_id), name, industry, location),
                )
                new_id = comp_id
            else:
                cur.execute(
                    "INSERT INTO Company (Name, Industry, Location) VALUES (%s,%s,%s)",
                    (name, industry, location),
                )
                new_id = cur.lastrowid
            conn.commit()
            return True, f"Company '{name}' registered successfully! (Company ID: {new_id})"
    except Exception as exc:
        return False, _format_error(exc)
    finally:
        conn.close()


def get_all_companies():
    return _safe_all("SELECT Company_ID, Name, Industry, Location FROM Company ORDER BY Company_ID ASC")


# ==========================================
# JOB POSTING & APPLICATION OPERATIONS
# ==========================================

def post_job(comp_id, role_title, ctc, min_cgpa, openings):
    return add_job_posting(comp_id, role_title, ctc, min_cgpa, openings)


def add_job_posting(company_id, role_title, ctc_lpa, min_cgpa, openings=1):
    role_title = str(role_title).strip()
    if not role_title:
        return False, "Job role title is required."
    try:
        company_id = int(company_id)
        ctc_lpa = float(ctc_lpa)
        min_cgpa = float(min_cgpa)
        openings = int(openings)
    except (ValueError, TypeError):
        return False, "Invalid numeric input for Company ID, CTC, CGPA, or Openings."

    if ctc_lpa <= 0:
        return False, "CTC (LPA) must be greater than 0."
    if not (0.0 <= min_cgpa <= 10.0):
        return False, "Minimum CGPA must be between 0.0 and 10.0."
    if openings < 1:
        return False, "Openings must be at least 1."

    conn = get_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        with closing(conn.cursor()) as cur:
            cur.execute("SELECT Name FROM Company WHERE Company_ID=%s", (company_id,))
            comp = cur.fetchone()
            if not comp:
                return False, f"Company ID #{company_id} does not exist. Please register the company first."
            cur.execute(
                "INSERT INTO Job_Posting (Company_ID, Role_Title, CTC_LPA, Min_CGPA, Openings) VALUES (%s,%s,%s,%s,%s)",
                (company_id, role_title, round(ctc_lpa, 2), round(min_cgpa, 2), openings),
            )
            job_id = cur.lastrowid
            conn.commit()
            return True, f"Job '{role_title}' for {comp[0]} posted successfully! (Job ID: {job_id})"
    except Exception as exc:
        return False, _format_error(exc)
    finally:
        conn.close()


def get_all_jobs():
    return _safe_all(
        "SELECT jp.Job_ID, c.Company_ID, c.Name AS Company_Name, c.Location, jp.Role_Title AS Role, "
        "jp.CTC_LPA AS CTC, jp.Min_CGPA, jp.Openings "
        "FROM Job_Posting jp JOIN Company c ON jp.Company_ID=c.Company_ID ORDER BY jp.Job_ID DESC"
    )


def get_eligible_jobs(roll_number):
    roll_number = str(roll_number).strip()
    if not roll_number:
        return []
    return _safe_all(
        "SELECT j.Job_ID, c.Name AS Company, j.Role_Title, j.CTC_LPA, j.Min_CGPA, j.Openings "
        "FROM Job_Posting j "
        "JOIN Company c ON j.Company_ID=c.Company_ID "
        "JOIN Student s ON s.Roll_Number=%s AND s.CGPA>=j.Min_CGPA "
        "WHERE NOT EXISTS (SELECT 1 FROM Application a WHERE a.Roll_Number=s.Roll_Number AND a.Job_ID=j.Job_ID) "
        "ORDER BY j.CTC_LPA DESC",
        (roll_number,),
    )


def apply_for_job(roll_number, job_id):
    """Insert an application with clear validation of student, job, CGPA cutoff, and duplicates."""
    roll_number = str(roll_number).strip()
    try:
        job_id = int(job_id)
    except (ValueError, TypeError):
        return False, "Invalid Job ID."

    if not roll_number:
        return False, "Roll Number is required."

    conn = get_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        with closing(conn.cursor()) as cur:
            # 1. Check student
            cur.execute("SELECT Name, CGPA FROM Student WHERE Roll_Number=%s", (roll_number,))
            student = cur.fetchone()
            if not student:
                return False, f"Student with Roll Number '{roll_number}' not found. Please register your account first."
            student_name, student_cgpa = student[0], float(student[1])

            # 2. Check job
            cur.execute(
                "SELECT jp.Role_Title, jp.Min_CGPA, c.Name "
                "FROM Job_Posting jp JOIN Company c ON jp.Company_ID=c.Company_ID WHERE jp.Job_ID=%s",
                (job_id,),
            )
            job = cur.fetchone()
            if not job:
                return False, f"Job ID #{job_id} does not exist."
            role_title, min_cgpa, company_name = job[0], float(job[1]), job[2]

            # 3. Check duplicate application
            cur.execute(
                "SELECT App_ID, Application_Status FROM Application WHERE Roll_Number=%s AND Job_ID=%s",
                (roll_number, job_id),
            )
            existing = cur.fetchone()
            if existing:
                return False, f"You have already applied for '{role_title}' at {company_name} (Application #{existing[0]}, Status: {existing[1]})."

            # 4. Check CGPA cutoff
            if student_cgpa < min_cgpa:
                return False, f"Eligibility not met: '{role_title}' requires minimum {min_cgpa:.2f} CGPA, but your current CGPA is {student_cgpa:.2f}."

            # 5. Insert application
            cur.execute(
                "INSERT INTO Application (Roll_Number, Job_ID, Application_Status) VALUES (%s, %s, 'Applied')",
                (roll_number, job_id),
            )
            app_id = cur.lastrowid
            conn.commit()
            return True, f"Application for '{role_title}' at {company_name} submitted successfully! (Application ID: #{app_id})"
    except Exception as exc:
        return False, _format_error(exc)
    finally:
        conn.close()


def get_student_applications(roll_num):
    roll_num = str(roll_num).strip()
    if not roll_num:
        return []
    return _safe_all(
        "SELECT a.App_ID, a.Job_ID, c.Name AS Company, jp.Role_Title AS Role, "
        "jp.CTC_LPA AS CTC, a.Application_Status, "
        "jo.Acceptance_Status AS Offer_Status, jo.Base_Salary_LPA AS Offered_Salary, "
        "jo.Joining_Date, a.Applied_Date "
        "FROM Application a "
        "JOIN Job_Posting jp ON a.Job_ID=jp.Job_ID "
        "JOIN Company c ON jp.Company_ID=c.Company_ID "
        "LEFT JOIN Job_Offer jo ON a.App_ID=jo.App_ID "
        "WHERE a.Roll_Number=%s ORDER BY a.App_ID DESC",
        (roll_num,),
    )


def update_application_status(app_id, new_status):
    try:
        app_id = int(app_id)
    except (ValueError, TypeError):
        return False, "Invalid Application ID."

    valid_statuses = ["Applied", "In Process", "Offered", "Placed", "Rejected"]
    if new_status not in valid_statuses:
        return False, f"Invalid status '{new_status}'. Must be one of: {', '.join(valid_statuses)}"

    return _write(
        "UPDATE Application SET Application_Status=%s WHERE App_ID=%s",
        (new_status, app_id),
        f"Application #{app_id} status updated to '{new_status}'.",
        missing_message=f"Application ID #{app_id} not found.",
    )


# ==========================================
# INTERVIEW ROUNDS & OFFERS
# ==========================================

def schedule_interview_round(app_id, round_name, score=None, feedback=None, round_status="Scheduled"):
    try:
        app_id = int(app_id)
    except (ValueError, TypeError):
        return False, "Invalid Application ID."

    round_aliases = {
        "online assessment": "Online Assessment",
        "aptitude": "Online Assessment",
        "technical interview": "Technical Round 1",
        "technical": "Technical Round 1",
        "technical round": "Technical Round 1",
        "technical round 1": "Technical Round 1",
        "technical round 2": "Technical Round 2",
        "hr interview": "HR Round",
        "hr": "HR Round",
        "hr round": "HR Round",
    }
    normalized_round = round_aliases.get(str(round_name).strip().lower(), str(round_name).strip())
    valid_rounds = ["Online Assessment", "Technical Round 1", "Technical Round 2", "HR Round"]
    if normalized_round not in valid_rounds:
        return False, f"Invalid round '{round_name}'. Must be one of: {', '.join(valid_rounds)}"

    valid_statuses = ["Scheduled", "Cleared", "Failed"]
    round_status = str(round_status).strip()
    if round_status not in valid_statuses:
        return False, f"Invalid round status '{round_status}'. Must be one of: {', '.join(valid_statuses)}"

    int_score = None
    if score is not None:
        try:
            s_val = float(score)
            if s_val > 0:
                int_score = int(round(s_val))
            elif s_val == 0:
                int_score = 0
        except (ValueError, TypeError):
            int_score = None

    feedback_text = feedback.strip() if feedback and str(feedback).strip() else None

    conn = get_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        with closing(conn.cursor()) as cur:
            cur.execute("SELECT App_ID, Application_Status FROM Application WHERE App_ID=%s", (app_id,))
            app = cur.fetchone()
            if not app:
                return False, f"Application ID #{app_id} not found."

            cur.execute(
                "INSERT INTO Interview_Round (App_ID, Round_Name, Score, Feedback, Round_Status) VALUES (%s,%s,%s,%s,%s)",
                (app_id, normalized_round, int_score, feedback_text, round_status),
            )

            curr_status = app[1]
            if round_status == "Failed":
                cur.execute("UPDATE Application SET Application_Status='Rejected' WHERE App_ID=%s", (app_id,))
            elif round_status in ("Scheduled", "Cleared") and curr_status == "Applied":
                cur.execute("UPDATE Application SET Application_Status='In Process' WHERE App_ID=%s", (app_id,))

            conn.commit()
            return True, f"{normalized_round} recorded for Application #{app_id} (Status: {round_status})."
    except Exception as exc:
        return False, _format_error(exc)
    finally:
        conn.close()


def rollout_job_offer(app_id, base_salary, joining_date):
    """Create a pending offer once for an existing application."""
    try:
        app_id = int(app_id)
        base_salary = float(base_salary)
    except (ValueError, TypeError):
        return False, "Invalid numeric input for Application ID or Base Salary."

    if base_salary <= 0:
        return False, "Base salary must be greater than 0 LPA."

    conn = get_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        with closing(conn.cursor()) as cur:
            cur.execute(
                "SELECT a.App_ID, a.Application_Status, s.Name, j.Role_Title "
                "FROM Application a "
                "JOIN Student s ON a.Roll_Number=s.Roll_Number "
                "JOIN Job_Posting j ON a.Job_ID=j.Job_ID "
                "WHERE a.App_ID=%s",
                (app_id,),
            )
            app = cur.fetchone()
            if not app:
                return False, f"Application ID #{app_id} not found."

            student_name, role_title = app[2], app[3]

            cur.execute("SELECT Offer_ID, Acceptance_Status FROM Job_Offer WHERE App_ID=%s", (app_id,))
            existing_offer = cur.fetchone()
            if existing_offer:
                return False, f"An offer already exists for Application #{app_id} (Status: {existing_offer[1]})."

            cur.execute(
                "INSERT INTO Job_Offer (App_ID, Offer_Date, Base_Salary_LPA, Joining_Date, Acceptance_Status) "
                "VALUES (%s, CURRENT_DATE(), %s, %s, 'Pending')",
                (app_id, round(base_salary, 2), joining_date),
            )
            cur.execute("UPDATE Application SET Application_Status='Offered' WHERE App_ID=%s", (app_id,))
            conn.commit()
            return True, f"Job offer of ₹{base_salary:.2f} LPA for {student_name} ({role_title}) rolled out successfully!"
    except Exception as exc:
        return False, _format_error(exc)
    finally:
        conn.close()


def accept_job_offer(app_id):
    try:
        app_id = int(app_id)
    except (ValueError, TypeError):
        return False, "Invalid Application ID."

    conn = get_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        with closing(conn.cursor()) as cur:
            cur.execute("SELECT Acceptance_Status FROM Job_Offer WHERE App_ID=%s", (app_id,))
            offer = cur.fetchone()
            if not offer:
                return False, f"No job offer found for Application #{app_id}."
            if offer[0] == "Accepted":
                return False, f"Offer for Application #{app_id} has already been accepted!"
            if offer[0] in ("Declined", "Rejected"):
                return False, f"Offer for Application #{app_id} was previously declined."

            cur.execute("UPDATE Job_Offer SET Acceptance_Status='Accepted' WHERE App_ID=%s", (app_id,))
            cur.execute("UPDATE Application SET Application_Status='Placed' WHERE App_ID=%s", (app_id,))
            conn.commit()
            return True, "Congratulations! Offer accepted successfully. Status updated to Placed."
    except Exception as exc:
        return False, _format_error(exc)
    finally:
        conn.close()


def reject_job_offer(app_id):
    try:
        app_id = int(app_id)
    except (ValueError, TypeError):
        return False, "Invalid Application ID."

    conn = get_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        with closing(conn.cursor()) as cur:
            cur.execute("SELECT Acceptance_Status FROM Job_Offer WHERE App_ID=%s", (app_id,))
            offer = cur.fetchone()
            if not offer:
                return False, f"No job offer found for Application #{app_id}."
            if offer[0] == "Accepted":
                return False, f"Cannot decline: Offer for Application #{app_id} was already accepted."
            if offer[0] in ("Declined", "Rejected"):
                return False, f"Offer for Application #{app_id} has already been declined."

            cur.execute("UPDATE Job_Offer SET Acceptance_Status='Declined' WHERE App_ID=%s", (app_id,))
            cur.execute("UPDATE Application SET Application_Status='Rejected' WHERE App_ID=%s", (app_id,))
            conn.commit()
            return True, "Job offer declined."
    except Exception as exc:
        return False, _format_error(exc)
    finally:
        conn.close()


# ==========================================
# REPORTING & ANALYTICS
# ==========================================

def get_recruitment_overview(company_id=None):
    if company_id:
        return _safe_all(
            "SELECT a.App_ID, s.Name AS Student_Name, s.Roll_Number, s.CGPA, s.Branch, "
            "c.Name AS Company, j.Role_Title, j.CTC_LPA, a.Application_Status, a.Applied_Date "
            "FROM Application a "
            "JOIN Student s ON a.Roll_Number=s.Roll_Number "
            "JOIN Job_Posting j ON a.Job_ID=j.Job_ID "
            "JOIN Company c ON j.Company_ID=c.Company_ID "
            "WHERE c.Company_ID=%s ORDER BY a.App_ID DESC",
            (company_id,),
        )
    return _safe_all(
        "SELECT a.App_ID, s.Name AS Student_Name, s.Roll_Number, s.CGPA, s.Branch, "
        "c.Name AS Company, j.Role_Title, j.CTC_LPA, a.Application_Status, a.Applied_Date "
        "FROM Application a "
        "JOIN Student s ON a.Roll_Number=s.Roll_Number "
        "JOIN Job_Posting j ON a.Job_ID=j.Job_ID "
        "JOIN Company c ON j.Company_ID=c.Company_ID "
        "ORDER BY a.App_ID DESC"
    )


def get_interview_evaluations(app_id=None):
    if app_id:
        return _safe_all(
            "SELECT ir.Round_ID, ir.App_ID, s.Name AS Candidate_Name, s.Roll_Number, "
            "c.Name AS Hiring_Company, j.Role_Title, ir.Round_Name, ir.Score, ir.Feedback, ir.Round_Status "
            "FROM Interview_Round ir "
            "JOIN Application a ON ir.App_ID=a.App_ID "
            "JOIN Student s ON a.Roll_Number=s.Roll_Number "
            "JOIN Job_Posting j ON a.Job_ID=j.Job_ID "
            "JOIN Company c ON j.Company_ID=c.Company_ID "
            "WHERE ir.App_ID=%s ORDER BY ir.Round_ID ASC",
            (app_id,),
        )
    return _safe_all(
        "SELECT ir.Round_ID, ir.App_ID, s.Name AS Candidate_Name, s.Roll_Number, "
        "c.Name AS Hiring_Company, j.Role_Title, ir.Round_Name, ir.Score, ir.Feedback, ir.Round_Status "
        "FROM Interview_Round ir "
        "JOIN Application a ON ir.App_ID=a.App_ID "
        "JOIN Student s ON a.Roll_Number=s.Roll_Number "
        "JOIN Job_Posting j ON a.Job_ID=j.Job_ID "
        "JOIN Company c ON j.Company_ID=c.Company_ID "
        "ORDER BY ir.Round_ID DESC"
    )


def get_all_offers():
    return _safe_all(
        "SELECT jo.Offer_ID, jo.App_ID, s.Name AS Student_Name, s.Roll_Number, "
        "c.Name AS Company, j.Role_Title, jo.Base_Salary_LPA, jo.Joining_Date, "
        "jo.Offer_Date, jo.Acceptance_Status "
        "FROM Job_Offer jo "
        "JOIN Application a ON jo.App_ID=a.App_ID "
        "JOIN Student s ON a.Roll_Number=s.Roll_Number "
        "JOIN Job_Posting j ON a.Job_ID=j.Job_ID "
        "JOIN Company c ON j.Company_ID=c.Company_ID "
        "ORDER BY jo.Offer_ID DESC"
    )


def get_placement_analytics():
    try:
        return _run(
            "SELECT "
            "(SELECT COUNT(*) FROM Student) AS Total_Students, "
            "(SELECT COUNT(DISTINCT a.Roll_Number) FROM Job_Offer jo JOIN Application a ON jo.App_ID=a.App_ID WHERE jo.Acceptance_Status='Accepted') AS Total_Placed, "
            "(SELECT MAX(Base_Salary_LPA) FROM Job_Offer WHERE Acceptance_Status='Accepted') AS Highest_Package, "
            "(SELECT AVG(Base_Salary_LPA) FROM Job_Offer WHERE Acceptance_Status='Accepted') AS Average_Package, "
            "(SELECT COUNT(*) FROM Company) AS Total_Companies, "
            "(SELECT COUNT(*) FROM Job_Posting) AS Total_Jobs, "
            "(SELECT COUNT(*) FROM Application) AS Total_Applications",
            fetch="one", dictionary=True
        ) or {}
    except Exception:
        return {}


def get_total_placed_students():
    try:
        row = _run(
            "SELECT COUNT(DISTINCT a.Roll_Number) FROM Job_Offer jo JOIN Application a ON jo.App_ID=a.App_ID WHERE jo.Acceptance_Status='Accepted'",
            fetch="one",
        )
        return int(row[0] or 0) if row else 0
    except Exception:
        return 0


def get_highest_package():
    try:
        row = _run("SELECT MAX(Base_Salary_LPA) FROM Job_Offer WHERE Acceptance_Status='Accepted'", fetch="one")
        return float(row[0] or 0) if row else 0.0
    except Exception:
        return 0.0


def get_total_companies():
    try:
        row = _run("SELECT COUNT(*) FROM Company", fetch="one")
        return int(row[0] or 0) if row else 0
    except Exception:
        return 0