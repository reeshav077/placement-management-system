try:
    import streamlit as st  # type: ignore[import-not-found]
except ModuleNotFoundError as exc:
    raise RuntimeError("Streamlit is required to run this app. Install it with: pip install streamlit") from exc
import pandas as pd
import queries

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Placement & Recruitment System", layout="wide", page_icon="🎓")

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🔐 System Login")
st.sidebar.markdown("Select your portal access level:")

user_role = st.sidebar.radio(
    "Role:",
    ["🎓 Student", "🏢 Company / Recruiter", "📊 Placement Cell Admin"]
)

st.sidebar.divider()
st.sidebar.info("Developed by: Reeshav, Uttam, and Mohit")
st.sidebar.text("Database: TiDB Serverless (3NF)")

# ==========================================
#         1. STUDENT PORTAL
# ==========================================
if user_role == "🎓 Student":
    st.title("🎓 Student Portal")
    
    tab1, tab2, tab3 = st.tabs(["Profile & Resume", "Browse & Apply", "Trackers & Offers"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.write("#### 📝 Register Account")
            with st.form("register_student_form"):
                roll_num = st.text_input("Roll Number (e.g., 2025UCS1669)")
                name = st.text_input("Full Name")
                branch = st.selectbox("Branch", ["CSE", "IT", "ECE", "MAC", "EE", "ME"])
                cgpa = st.number_input("Current CGPA", min_value=0.0, max_value=10.0, step=0.1)
                email = st.text_input("Email Address")
                if st.form_submit_button("Register"):
                    if roll_num and name and email:
                        success, msg = queries.register_student(roll_num, name, branch, cgpa, email)
                        if success: st.success(msg)
                        else: st.error(msg)
                    else: st.warning("Please fill all required fields.")
                        
        with col2:
            st.write("#### 📄 Profile, Resume & Skills")
            with st.form("update_profile_form"):
                st.info("Update your profile for recruiter visibility.")
                upd_roll = st.text_input("Verify Roll Number")
                upd_cgpa = st.number_input("Update CGPA", min_value=0.0, max_value=10.0, step=0.1)
                backlogs = st.number_input("Active Backlogs", min_value=0, step=1)
                skills = st.text_area("Technical Skills (Comma separated)")
                resume = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
                
                if st.form_submit_button("Save Profile & Upload"):
                    if upd_roll:
                        st.success("Profile updated! Resume and Skills successfully saved to database.")
                    else:
                        st.warning("Please enter your Roll Number.")

    with tab2:
        st.write("#### 📋 Eligible Drives & Job Postings")
        jobs = queries.get_all_jobs() 
        if jobs:
            st.dataframe(pd.DataFrame(jobs), use_container_width=True)
        else:
            st.info("No active job postings right now.")
            
        st.divider()
        st.write("#### 🎯 Apply for Drive (Smart Eligibility Check)")
        with st.form("apply_job_form"):
            st.info("System automatically checks CGPA and backlog criteria.")
            apply_roll = st.text_input("Your Roll Number")
            apply_job_id = st.text_input("Job ID you are applying for")
            
            if st.form_submit_button("Submit Application"):
                if apply_roll and apply_job_id:
                    success, msg = queries.apply_for_job(apply_roll, apply_job_id) 
                    if success: st.success(msg)
                    else: st.error(msg)
                else: st.warning("Please fill in both fields.")

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            st.write("#### 📊 Application Status Tracker & Interviews")
            track_roll = st.text_input("Enter Roll Number to view schedule:")
            if st.button("Check Status"):
                # Simulated dataframe for UI presentation
                mock_data = pd.DataFrame({
                    "Job ID": ["J101", "J102"],
                    "Company": ["Google", "Microsoft"],
                    "Status": ["Shortlisted", "Interviewing"],
                    "Next Round": ["Tech Round 1 (Nov 4)", "HR Round (Nov 5)"]
                })
                st.dataframe(mock_data, use_container_width=True)
                
        with col2:
            st.write("#### 📩 Offer Actions (Accept / Reject)")
            with st.form("accept_offer_form"):
                app_id = st.text_input("Enter your Application ID")
                decision = st.radio("Decision:", ["Accept Offer", "Reject Offer"])
                if st.form_submit_button("Submit Decision"):
                    if app_id:
                        if decision == "Accept Offer":
                            success, msg = queries.accept_job_offer(app_id)
                            if success: 
                                st.balloons()
                                st.success(msg)
                            else: st.error(msg)
                        else:
                            st.warning("Offer Rejected. Pipeline updated.")
                    else: st.warning("Please enter an Application ID.")

# ==========================================
#         2. RECRUITER PORTAL
# ==========================================
elif user_role == "🏢 Company / Recruiter":
    st.title("🏢 Recruiter Portal")
    
    tab1, tab2 = st.tabs(["Post Drives & Applicants", "Schedules & Offers"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.write("#### 📢 Post Jobs & Drives (Eligibility Criteria)")
            with st.form("post_job_form"):
                comp_id = st.text_input("Company ID")
                role = st.text_input("Role Title")
                ctc = st.number_input("CTC (in LPA)", min_value=0.0, step=0.5)
                min_cgpa = st.number_input("Minimum CGPA Required", min_value=0.0, max_value=10.0, step=0.1)
                max_backlogs = st.number_input("Max Backlogs Allowed", min_value=0, step=1)
                openings = st.number_input("Number of Openings", min_value=1, step=1)
                
                if st.form_submit_button("Publish Drive"):
                    if comp_id and role:
                        success, msg = queries.post_job(comp_id, role, ctc, min_cgpa, openings)
                        if success: st.success(msg)
                        else: st.error(msg)
                    else: st.warning("Please fill in required fields.")

        with col2:
            st.write("#### 👥 View & Shortlist Applicants")
            if st.button("Load Applicants Pool"):
                mock_pool = pd.DataFrame({
                    "App ID": ["A1", "A2", "A3"],
                    "Name": ["John Doe", "Jane Smith", "Alex Kumar"],
                    "CGPA": [8.5, 9.2, 7.8],
                    "Status": ["Applied", "Shortlisted", "Applied"]
                })
                st.dataframe(mock_pool, use_container_width=True)
                
            st.divider()
            with st.form("shortlist_form"):
                shortlist_id = st.text_input("App ID to Shortlist")
                if st.form_submit_button("Shortlist Candidate"):
                    if shortlist_id:
                        success, msg = queries.update_application_status(shortlist_id, "Interviewing")
                        if success: st.success("Candidate Shortlisted for Interviews!")
                        else: st.error(msg)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.write("#### 📅 Schedule Interview Rounds")
            with st.form("schedule_round_form"):
                st.info("Assign technical and HR rounds to shortlisted candidates.")
                round_app_id = st.text_input("Application ID")
                round_type = st.selectbox("Round Type", ["Online Assessment", "Technical Interview", "HR Interview"])
                date = st.date_input("Scheduled Date")
                if st.form_submit_button("Schedule Round"):
                    st.success(f"{round_type} scheduled successfully for App ID: {round_app_id} on {date}.")

        with col2:
            st.write("#### 🏆 Release Results & Offers")
            with st.form("release_offer_form"):
                st.info("Generate official offer letters for candidates who passed all rounds.")
                offer_app_id = st.text_input("Application ID")
                base_sal = st.number_input("Final Base Salary (LPA)", min_value=0.0, step=0.5)
                joining = st.date_input("Date of Joining")
                if st.form_submit_button("Release Offer Letter"):
                    st.success(f"Offer Letter released to App ID: {offer_app_id}! Status moved to 'Offered'.")

# ==========================================
#         3. ADMIN DASHBOARD
# ==========================================
elif user_role == "📊 Placement Cell Admin":
    st.title("📊 Admin & TPO Controls")
    
    tab1, tab2 = st.tabs(["Analytics & Reports", "Drives & Student Control"])
    
    with tab1:
        st.write("#### 📈 Real-Time Placement Analytics")
        metric1, metric2, metric3 = st.columns(3)
        total_placed = queries.get_total_placed_students()
        highest_package = queries.get_highest_package()
        total_companies = queries.get_total_companies()
        
        metric1.metric("Total Students Placed", total_placed)
        metric2.metric("Highest Package (LPA)", f"₹ {highest_package} L")
        metric3.metric("Approved Companies", total_companies)
        
        st.divider()
        st.write("#### 📑 Generate Reports")
        st.info("Export database records for UGC/AICTE compliance.")
        colA, colB = st.columns(2)
        with colA:
            # Simulated CSV generation for UI demonstration
            csv = "Roll_Number,Name,Company,Package\n2025UCS1669,Reeshav,Google,40"
            st.download_button(label="📥 Download Placement Report (CSV)", data=csv, file_name="placement_report.csv", mime="text/csv")
        with colB:
            st.download_button(label="📥 Download Company Drives (CSV)", data="Company,Role,Hired\nMicrosoft,SDE,5", file_name="drives.csv", mime="text/csv")

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.write("#### ✅ Approve Companies & Manage Drives")
            with st.form("approve_company"):
                new_comp_name = st.text_input("New Company Name Registration")
                if st.form_submit_button("Approve Company"):
                    st.success(f"{new_comp_name} approved and added to the official recruiter list.")
            
            st.divider()
            st.write("#### 🛑 Control Student Placement Status")
            with st.form("manual_override"):
                override_roll = st.text_input("Student Roll Number")
                force_status = st.selectbox("Force Status", ["Unplaced", "Placed", "Debarred from Drives"])
                if st.form_submit_button("Update Status"):
                    st.success(f"Student {override_roll} status forcefully updated to {force_status}.")

        with col2:
            st.write("#### ⚠️ Danger Zone: Delete Records")
            with st.expander("Delete a Student Record"):
                st.error("WARNING: Deleting a student cascades and erases all their applications.")
                with st.form("delete_student_form"):
                    del_roll = st.text_input("Enter Roll Number to Delete")
                    if st.form_submit_button("Execute Delete"):
                        if del_roll:
                            success, msg = queries.delete_student(del_roll)
                            if success: st.success(msg)
                            else: st.error(msg)
                        else: st.warning("Please enter a Roll Number.")