try:
    import streamlit as st  # type: ignore[import-not-found]
except ModuleNotFoundError as exc:
    raise RuntimeError("Streamlit is required to run this app. Install it with: pip install streamlit") from exc

import queries
import pandas as pd

st.set_page_config(page_title="Placement & Recruitment Portal", layout="wide", page_icon="🎓")
st.title("🎓 Placement & Recruitment Management System")
st.caption("Live Cloud Database on TiDB Serverless (3NF Normalized Schema)")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard & Analytics",
    "🎯 Placement Portal (Students)",
    "💼 Recruitment Portal (Corporate)",
    "✏️ Pipeline Status Update",
    "🗑️ Admin Controls"
])

# ----------------- TAB 1: DASHBOARD & ANALYTICS -----------------
with tab1:
    st.subheader("📈 Campus Placement Analytics")
    stats = queries.get_placement_analytics()
    if stats and stats.get('Total_Students') is not None:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Registered", stats['Total_Students'])
        m2.metric("Students Placed", stats['Total_Placed'])
        
        highest = f"₹{stats['Highest_Package']} LPA" if stats['Highest_Package'] else "N/A"
        m3.metric("Highest Package", highest)
        
        avg = f"₹{round(stats['Average_Package'], 2)} LPA" if stats['Average_Package'] else "N/A"
        m4.metric("Average Package", avg)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("#### 👨‍🎓 Registered Students")
        students = queries.get_all_students()
        if students:
            st.dataframe(pd.DataFrame(students), use_container_width=True)
        else:
            st.info("No student records.")
            
    with col2:
        st.write("#### 💼 Company Job Postings")
        jobs = queries.get_all_jobs()
        if jobs:
            st.dataframe(pd.DataFrame(jobs), use_container_width=True)
        else:
            st.info("No job postings available.")

    st.write("#### 📑 Active Recruitment Pipeline (Applications)")
    recruitment_data = queries.get_recruitment_overview()
    if recruitment_data:
        st.dataframe(pd.DataFrame(recruitment_data), use_container_width=True)
    else:
        st.info("No active applications.")

    st.write("#### 📝 Candidate Interview Evaluations")
    interviews = queries.get_interview_evaluations()
    if interviews:
        st.dataframe(pd.DataFrame(interviews), use_container_width=True)
    else:
        st.info("No interview rounds conducted yet.")

# ----------------- TAB 2: PLACEMENT PORTAL -----------------
with tab2:
    st.divider()
    st.write("#### 📩 Pending Job Offers (Student Inbox)")
    with st.form("accept_offer_form"):
        st.info("Did you receive an offer? Enter your Application ID below to officially accept it and finalize your placement.")
        offer_app_id = st.number_input("Application ID to Accept", min_value=1, step=1)
        if st.form_submit_button("Accept Job Offer"):
            success, msg = queries.accept_job_offer(offer_app_id)
            if success:
                st.success(msg)
                st.balloons()
                st.rerun()
            else:
                st.error(msg)
    st.subheader("Placement Cell: Student Registration & Applications")
    p1, p2 = st.columns(2)
    
    with p1:
        st.write("#### Register New Student")
        with st.form("student_form", clear_on_submit=True):
            roll = st.text_input("Roll Number", placeholder="e.g., 2025UCS1669")
            name = st.text_input("Candidate Name")
            branch = st.selectbox("Department/Branch", ["CSE", "IT", "ECE", "EE", "ME"])
            cgpa = st.number_input("CGPA", min_value=0.0, max_value=10.0, value=8.0, step=0.01)
            email = st.text_input("Official Email")
            if st.form_submit_button("Register Student"):
                if roll and name and email:
                    success, msg = queries.add_student(roll, name, branch, cgpa, email)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("Please fill in all fields.")

    with p2:
        st.write("#### 🎯 Smart Apply (CGPA Eligibility Checker)")
        with st.form("smart_apply_form"):
            student_roll = st.text_input("Enter your Roll Number (e.g., 2025UCS1669)")
            check_jobs = st.form_submit_button("Find Eligible Jobs")

        if 'eligible_jobs' not in st.session_state:
            st.session_state.eligible_jobs = []

        if check_jobs and student_roll:
            jobs = queries.get_eligible_jobs(student_roll)
            if jobs:
                st.session_state.eligible_jobs = jobs
                st.success(f"Found {len(jobs)} jobs meeting your CGPA criteria!")
            else:
                st.error("No eligible jobs found or invalid Roll Number.")

        if st.session_state.eligible_jobs:
            st.dataframe(pd.DataFrame(st.session_state.eligible_jobs), use_container_width=True)
            with st.form("final_apply"):
                target_job = st.selectbox("Select Job ID to Apply", [j['Job_ID'] for j in st.session_state.eligible_jobs])
                if st.form_submit_button("Submit Application"):
                    success, msg = queries.apply_for_job(student_roll, target_job)
                    if success:
                        st.success(msg)
                        st.session_state.eligible_jobs = []
                        st.rerun()
                    else:
                        st.error(msg)

# ----------------- TAB 3: RECRUITMENT PORTAL -----------------
with tab3:
    st.subheader("Corporate Recruitment: Postings, Scoring & Offers")
    
    r1, r2, r3 = st.columns(3)
    
    with r1:
        st.write("#### 🏢 Post a Job Opening")
        companies = queries.get_all_companies()
        if companies:
            company_options = {c['Name']: c['Company_ID'] for c in companies}
            with st.form("job_posting_form", clear_on_submit=True):
                selected_company = st.selectbox("Select Company", list(company_options.keys()))
                role = st.text_input("Role Title")
                ctc = st.number_input("CTC (LPA)", min_value=1.0, value=12.0, step=0.5)
                min_cgpa = st.number_input("Min CGPA", min_value=0.0, max_value=10.0, value=7.0, step=0.1)
                openings = st.number_input("Openings", min_value=1, step=1, value=2)
                
                if st.form_submit_button("Publish Job"):
                    if role:
                        comp_id = company_options[selected_company]
                        success, msg = queries.add_job_posting(comp_id, role, ctc, min_cgpa, openings)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("Provide a Job Role Title.")
        else:
            st.warning("No companies registered yet.")

    with r2:
        st.write("#### 📝 Log Interview Evaluation")
        with st.form("interview_form", clear_on_submit=True):
            app_id = st.number_input("Candidate Application ID", min_value=1, step=1)
            round_name = st.selectbox("Interview Round", [
                "Online Assessment", "Technical Round 1", "Technical Round 2", "HR Round"
            ])
            score = st.slider("Assessment Score", min_value=0, max_value=100, value=75)
            feedback = st.text_area("Feedback")
            round_status = st.selectbox("Verdict", ["Scheduled", "Cleared", "Failed"])
            
            if st.form_submit_button("Submit Evaluation"):
                success, msg = queries.schedule_interview_round(app_id, round_name, score, feedback, round_status)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with r3:
        st.write("#### 📜 Roll Out Job Offer")
        with st.form("offer_form", clear_on_submit=True):
            target_app_id = st.number_input("Application ID (Must be cleared)", min_value=1, step=1)
            base_salary = st.number_input("Final CTC (LPA)", min_value=1.0, value=15.0, step=0.5)
            joining_date = st.date_input("Joining Date")
            
            if st.form_submit_button("Generate Offer Letter"):
                success, msg = queries.rollout_job_offer(target_app_id, base_salary, joining_date)
                if success:
                    st.success(msg)
                    st.balloons()
                    st.rerun()
                else:
                    st.error(msg)

# ----------------- TAB 4: UPDATE STATUS -----------------
with tab4:
    st.subheader("Manual Pipeline Status Override")
    with st.form("update_form"):
        target_app = st.number_input("Application ID", min_value=1, step=1)
        status = st.selectbox("Update Candidate Stage", ["Applied", "In Process", "Offered", "Rejected"])
        if st.form_submit_button("Update Pipeline Status"):
            success, msg = queries.update_application_status(target_app, status)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

# ----------------- TAB 5: DELETE -----------------
with tab5:
    st.subheader("Placement Cell Records Management")
    with st.form("del_form"):
        del_roll = st.text_input("Roll Number of Student to Deregister")
        st.caption("⚠️ Removing a student cascades and deletes all related applications, interviews, and offers.")
        if st.form_submit_button("Remove Student"):
            if del_roll:
                success, msg = queries.delete_student(del_roll)
                if success:
                    st.warning(msg)
                    st.rerun()
                else:
                    st.error(msg)