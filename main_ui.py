"""Streamlit UI for the Placement & Recruitment Management System."""

try:
    import streamlit as st
except ModuleNotFoundError as exc:
    raise RuntimeError("Streamlit is required. Install dependencies with: pip install streamlit pandas mysql-connector-python") from exc

import pandas as pd
import queries

st.set_page_config(page_title="Placement & Recruitment System", layout="wide", page_icon="🎓")
st.sidebar.title("🔐 System Login")
st.sidebar.markdown("Select your portal access level:")
user_role = st.sidebar.radio("Role:", ["🎓 Student", "🏢 Company / Recruiter", "📊 Placement Cell Admin"])
st.sidebar.divider()
st.sidebar.info("Developed by: Reeshav, Uttam, and Mohit")
st.sidebar.text("Database: TiDB Serverless (3NF)")

if user_role == "🎓 Student":
    st.title("🎓 Student Portal")
    tab1, tab2, tab3 = st.tabs(["Profile", "Browse & Apply", "Applications & Offers"])
    with tab1:
        left, right = st.columns(2)
        with left:
            st.subheader("Register Account")
            with st.form("register_student_form"):
                roll = st.text_input("Roll Number")
                name = st.text_input("Full Name")
                branch = st.selectbox("Branch", ["CSE", "IT", "ECE", "MAC", "EE", "ME"])
                cgpa = st.number_input("Current CGPA", min_value=0.0, max_value=10.0, step=0.1)
                email = st.text_input("Email Address")
                if st.form_submit_button("Register"):
                    if roll.strip() and name.strip() and email.strip():
                        ok, msg = queries.register_student(roll.strip(), name.strip(), branch, cgpa, email.strip())
                        (st.success if ok else st.error)(msg)
                    else:
                        st.warning("Please fill in all fields.")
        with right:
            st.subheader("Update Profile")
            with st.form("update_profile_form"):
                upd_roll = st.text_input("Roll Number")
                upd_name = st.text_input("Full Name")
                upd_branch = st.selectbox("Branch", ["CSE", "IT", "ECE", "MAC", "EE", "ME"], key="upd_branch")
                upd_cgpa = st.number_input("CGPA", min_value=0.0, max_value=10.0, step=0.1, key="upd_cgpa")
                upd_email = st.text_input("Email Address", key="upd_email")
                if st.form_submit_button("Save Profile"):
                    if all(v.strip() for v in [upd_roll, upd_name, upd_email]):
                        ok, msg = queries.update_student_profile(upd_roll.strip(), upd_name.strip(), upd_branch, upd_cgpa, upd_email.strip())
                        (st.success if ok else st.error)(msg)
                    else:
                        st.warning("Please complete all fields.")
    with tab2:
        st.subheader("Available Jobs")
        jobs = queries.get_all_jobs()
        if jobs:
            st.dataframe(pd.DataFrame(jobs), use_container_width=True, hide_index=True)
        else:
            st.info("No job postings are available, or the database could not be reached.")
        with st.form("apply_job_form"):
            apply_roll = st.text_input("Your Roll Number")
            apply_job_id = st.number_input("Job ID", min_value=1, step=1)
            if st.form_submit_button("Apply"):
                if apply_roll.strip():
                    ok, msg = queries.apply_for_job(apply_roll.strip(), int(apply_job_id))
                    (st.success if ok else st.error)(msg)
                else:
                    st.warning("Enter your Roll Number.")
    with tab3:
        left, right = st.columns(2)
        with left:
            st.subheader("Track Applications")
            with st.form("track_form"):
                check_roll = st.text_input("Roll Number")
                track = st.form_submit_button("Load Applications")
            if track:
                rows = queries.get_student_applications(check_roll.strip()) if check_roll.strip() else []
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.info("No applications found.")
        with right:
            st.subheader("Respond to an Offer")
            with st.form("offer_response_form"):
                app_id = st.number_input("Application ID", min_value=1, step=1)
                decision = st.radio("Decision", ["Accept", "Reject"], horizontal=True)
                respond = st.form_submit_button("Submit Decision")
            if respond:
                fn = queries.accept_job_offer if decision == "Accept" else queries.reject_job_offer
                ok, msg = fn(int(app_id))
                if ok and decision == "Accept":
                    st.balloons()
                (st.success if ok else st.error)(msg)

elif user_role == "🏢 Company / Recruiter":
    st.title("🏢 Recruiter Portal")
    tab1, tab2 = st.tabs(["Jobs & Applicants", "Interview Rounds & Offers"])
    with tab1:
        left, right = st.columns(2)
        with left:
            st.subheader("Post a Job")
            with st.form("post_job_form"):
                comp_id = st.number_input("Company ID", min_value=1, step=1)
                role = st.text_input("Role Title")
                ctc = st.number_input("CTC (LPA)", min_value=0.0, step=0.5)
                min_cgpa = st.number_input("Minimum CGPA", min_value=0.0, max_value=10.0, step=0.1)
                openings = st.number_input("Number of Openings", min_value=1, step=1)
                if st.form_submit_button("Publish Drive"):
                    if role.strip():
                        ok, msg = queries.post_job(int(comp_id), role.strip(), ctc, min_cgpa, int(openings))
                        (st.success if ok else st.error)(msg)
                    else:
                        st.warning("Enter a role title.")
        with right:
            st.subheader("Applicants")
            applicants = queries.get_recruitment_overview()
            if applicants:
                st.dataframe(pd.DataFrame(applicants), use_container_width=True, hide_index=True)
            else:
                st.info("No applications found.")
            with st.form("shortlist_form"):
                shortlist_id = st.number_input("Application ID to shortlist", min_value=1, step=1)
                if st.form_submit_button("Shortlist"):
                    ok, msg = queries.update_application_status(int(shortlist_id), "Interviewing")
                    (st.success if ok else st.error)(msg)
    with tab2:
        left, right = st.columns(2)
        with left:
            st.subheader("Record Interview Round")
            with st.form("schedule_round_form"):
                round_app_id = st.number_input("Application ID", min_value=1, step=1, key="round_app_id")
                round_type = st.selectbox("Round", ["Online Assessment", "Technical Interview", "HR Interview"])
                round_status = st.selectbox("Status", ["Scheduled", "Passed", "Failed"])
                score = st.number_input("Score (optional; use 0 if not scored)", min_value=0.0, step=0.5)
                feedback = st.text_area("Feedback")
                if st.form_submit_button("Save Round"):
                    ok, msg = queries.schedule_interview_round(int(round_app_id), round_type, score, feedback.strip() or None, round_status)
                    (st.success if ok else st.error)(msg)
        with right:
            st.subheader("Release Offer")
            with st.form("release_offer_form"):
                offer_app_id = st.number_input("Application ID", min_value=1, step=1, key="offer_app_id")
                base_salary = st.number_input("Base Salary (LPA)", min_value=0.0, step=0.5)
                joining = st.date_input("Joining Date")
                if st.form_submit_button("Release Offer"):
                    ok, msg = queries.rollout_job_offer(int(offer_app_id), base_salary, joining)
                    (st.success if ok else st.error)(msg)

else:
    st.title("📊 Admin & TPO Dashboard")
    tab1, tab2 = st.tabs(["Analytics", "Manage Records"])
    with tab1:
        a, b, c = st.columns(3)
        a.metric("Students Placed", queries.get_total_placed_students())
        b.metric("Highest Package (LPA)", f"₹ {queries.get_highest_package():,.2f} L")
        c.metric("Registered Companies", queries.get_total_companies())
        st.subheader("Recruitment Overview")
        overview = queries.get_recruitment_overview()
        if overview:
            st.dataframe(pd.DataFrame(overview), use_container_width=True, hide_index=True)
            st.download_button("Download Applications CSV", pd.DataFrame(overview).to_csv(index=False), "applications.csv", "text/csv")
        else:
            st.info("No recruitment records found.")
        st.subheader("Interview Evaluations")
        evaluations = queries.get_interview_evaluations()
        if evaluations:
            st.dataframe(pd.DataFrame(evaluations), use_container_width=True, hide_index=True)
    with tab2:
        left, right = st.columns(2)
        with left:
            st.subheader("Register Company")
            with st.form("company_form"):
                company_name = st.text_input("Company Name")
                industry = st.text_input("Industry")
                location = st.text_input("Location")
                if st.form_submit_button("Add Company"):
                    if company_name.strip():
                        ok, msg = queries.add_company(company_name.strip(), industry.strip() or None, location.strip() or None)
                        (st.success if ok else st.error)(msg)
                    else:
                        st.warning("Enter a company name.")
        with right:
            st.subheader("Delete Student")
            st.warning("This may also delete linked records if your foreign keys use ON DELETE CASCADE.")
            with st.form("delete_student_form"):
                del_roll = st.text_input("Roll Number")
                if st.form_submit_button("Delete Student"):
                    if del_roll.strip():
                        ok, msg = queries.delete_student(del_roll.strip())
                        (st.success if ok else st.error)(msg)
                    else:
                        st.warning("Enter a Roll Number.")
