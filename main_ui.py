"""Streamlit UI for the Placement & Recruitment Management System."""

try:
    import streamlit as st
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Streamlit is required. Install dependencies with: pip install streamlit pandas mysql-connector-python"
    ) from exc

from datetime import date
import importlib
import pandas as pd
import queries

# Ensure helper modules are always fresh on Streamlit hot-reloads
importlib.reload(queries)

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Placement & Recruitment Management System",
    layout="wide",
    page_icon="🎓",
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #64748B;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #3B82F6;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# SIDEBAR NAVIGATION & PORTAL ACCESS
# ==========================================
st.sidebar.title("🎓 Campus Placement Portal")
st.sidebar.markdown("---")
st.sidebar.subheader("Select Access Level")
user_role = st.sidebar.radio(
    "Login Role:",
    ["🎓 Student", "🏢 Company / Recruiter", "📊 Placement Cell Admin"],
    index=0,
)

st.sidebar.markdown("---")
# Live DB Status check
analytics_quick = queries.get_placement_analytics()
if analytics_quick:
    st.sidebar.success("🟢 Database: Online (TiDB Cloud)")
else:
    st.sidebar.error("🔴 Database: Connection Failed")

st.sidebar.info("Developed by: Reeshav, Uttam, and Mohit")
st.sidebar.caption("Normalized 3NF Relational Database Architecture")


# ==========================================
# 1. STUDENT PORTAL
# ==========================================
if user_role == "🎓 Student":
    st.markdown('<div class="main-header">🎓 Student Career Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Register, explore eligible job openings, track interview rounds, and manage job offers.</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["👤 Profile & Registration", "💼 Browse & Apply", "📑 Track Applications & Offers"])

    # --- TAB 1: Profile & Registration ---
    with tab1:
        col_reg, col_upd = st.columns(2)
        with col_reg:
            st.subheader("📝 New Student Registration")
            st.caption("Create your placement profile to start applying for campus drives.")
            with st.form("register_student_form", clear_on_submit=True):
                reg_roll = st.text_input("Roll Number", placeholder="e.g., 2025UCS1669")
                reg_name = st.text_input("Full Name", placeholder="e.g., John Doe")
                reg_branch = st.selectbox("Branch / Department", ["CSE", "IT", "ECE", "MAC", "EE", "ME"])
                reg_cgpa = st.number_input("Current CGPA (0.00 - 10.00)", min_value=0.0, max_value=10.0, step=0.05, value=8.0)
                reg_email = st.text_input("College / Official Email", placeholder="e.g., student@college.edu")
                submit_reg = st.form_submit_button("Register Profile", use_container_width=True)

            if submit_reg:
                if reg_roll.strip() and reg_name.strip() and reg_email.strip():
                    ok, msg = queries.register_student(
                        reg_roll.strip(), reg_name.strip(), reg_branch, reg_cgpa, reg_email.strip()
                    )
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill in all required fields (Roll Number, Name, Email).")

        with col_upd:
            st.subheader("🔄 Update Existing Profile")
            st.caption("Lookup and update your academic records and contact details.")
            search_roll = st.text_input("Enter Roll Number to Fetch Details", placeholder="e.g., 2025UCS1669")
            curr_student = None
            if search_roll.strip():
                curr_student = queries.get_student_by_roll(search_roll.strip())
                if curr_student:
                    st.info(f"Loaded: **{curr_student['Name']}** | Branch: **{curr_student['Branch']}** | CGPA: **{curr_student['CGPA']}**")
                else:
                    st.warning(f"No student found with Roll Number '{search_roll.strip()}'.")

            with st.form("update_profile_form"):
                upd_roll = st.text_input("Roll Number", value=curr_student['Roll_Number'] if curr_student else search_roll)
                upd_name = st.text_input("Full Name", value=curr_student['Name'] if curr_student else "")
                branches = ["CSE", "IT", "ECE", "MAC", "EE", "ME"]
                branch_idx = branches.index(curr_student['Branch']) if curr_student and curr_student['Branch'] in branches else 0
                upd_branch = st.selectbox("Branch", branches, index=branch_idx, key="upd_branch")
                curr_cgpa_val = float(curr_student['CGPA']) if curr_student else 8.0
                upd_cgpa = st.number_input("CGPA", min_value=0.0, max_value=10.0, step=0.05, value=curr_cgpa_val, key="upd_cgpa")
                upd_email = st.text_input("Email Address", value=curr_student['Email'] if curr_student else "", key="upd_email")
                submit_upd = st.form_submit_button("Save Profile Changes", use_container_width=True)

            if submit_upd:
                if all(v.strip() for v in [upd_roll, upd_name, upd_email]):
                    ok, msg = queries.update_student_profile(
                        upd_roll.strip(), upd_name.strip(), upd_branch, upd_cgpa, upd_email.strip()
                    )
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Please complete all fields before saving.")

    # --- TAB 2: Browse & Apply ---
    with tab2:
        st.subheader("🎯 Campus Drives & Opportunities")
        c1, c2 = st.columns([1, 2])
        with c1:
            check_eligibility_roll = st.text_input(
                "Filter by Roll Number (Smart Eligibility)",
                placeholder="e.g., 2025UCS1669",
                help="Enter your Roll Number to show only jobs matching your CGPA that you haven't applied to yet.",
            )

        if check_eligibility_roll.strip():
            jobs = queries.get_eligible_jobs(check_eligibility_roll.strip())
            st.caption(f"Showing **{len(jobs)} eligible jobs** meeting CGPA requirements for Roll Number **{check_eligibility_roll.strip()}**.")
        else:
            jobs = queries.get_all_jobs()
            st.caption("Showing all active campus drives.")

        if jobs:
            st.dataframe(pd.DataFrame(jobs), use_container_width=True, hide_index=True)
        else:
            st.info("No job openings found matching your criteria.")

        st.markdown("---")
        st.subheader("🚀 Submit Job Application")
        with st.form("apply_job_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                apply_roll = st.text_input("Your Roll Number", value=check_eligibility_roll.strip() if check_eligibility_roll else "")
            with col_b:
                all_active_jobs = queries.get_all_jobs()
                if all_active_jobs:
                    job_options = {
                        f"Job #{j['Job_ID']}: {j['Company_Name']} - {j['Role']} (₹{j['CTC']} LPA | Min CGPA: {j['Min_CGPA']})": j['Job_ID']
                        for j in all_active_jobs
                    }
                    selected_job_label = st.selectbox("Select Target Job", list(job_options.keys()))
                    apply_job_id = job_options[selected_job_label]
                else:
                    st.warning("No active jobs available.")
                    apply_job_id = None

            submit_apply = st.form_submit_button("Submit Application", use_container_width=True)

        if submit_apply:
            if apply_roll.strip() and apply_job_id:
                ok, msg = queries.apply_for_job(apply_roll.strip(), int(apply_job_id))
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.warning("Please provide your Roll Number and select a Job.")

    # --- TAB 3: Applications & Offers ---
    with tab3:
        if "student_track_roll" not in st.session_state:
            st.session_state.student_track_roll = ""

        c_track, c_offer = st.columns([1.4, 1.0])

        with c_track:
            st.subheader("📑 Application & Interview Status Tracker")
            col_in, col_btn = st.columns([3, 1])
            with col_in:
                input_roll = st.text_input(
                    "Roll Number",
                    value=st.session_state.student_track_roll,
                    placeholder="e.g., 2025UCS1669",
                    label_visibility="collapsed",
                )
            with col_btn:
                btn_track = st.button("Track Status", use_container_width=True)

            if btn_track and input_roll.strip():
                st.session_state.student_track_roll = input_roll.strip()

            active_roll = st.session_state.student_track_roll
            if active_roll:
                apps = queries.get_student_applications(active_roll)
                if apps:
                    st.markdown(f"**Found {len(apps)} Application(s) for `{active_roll}`:**")
                    st.dataframe(pd.DataFrame(apps), use_container_width=True, hide_index=True)

                    # Also show interview evaluation rounds for these applications
                    app_ids = [a['App_ID'] for a in apps]
                    interview_history = []
                    for aid in app_ids:
                        evals = queries.get_interview_evaluations(aid)
                        if evals:
                            interview_history.extend(evals)

                    if interview_history:
                        st.markdown("**Interview Rounds Conducted:**")
                        st.dataframe(pd.DataFrame(interview_history), use_container_width=True, hide_index=True)
                else:
                    st.info(f"No applications found for Roll Number '{active_roll}'.")
            else:
                st.caption("Enter your Roll Number above and click 'Track Status' to see your applications.")

        with c_offer:
            st.subheader("📩 Respond to Job Offer")
            st.caption("Received an official placement offer? Accept or decline it below.")
            with st.form("offer_response_form"):
                resp_app_id = st.number_input("Application ID", min_value=1, step=1, help="Locate your Application ID from the tracker on the left.")
                decision = st.radio("Decision", ["Accept Offer", "Decline Offer"], horizontal=True)
                submit_offer_decision = st.form_submit_button("Submit Response", use_container_width=True)

            if submit_offer_decision:
                if decision == "Accept Offer":
                    ok, msg = queries.accept_job_offer(int(resp_app_id))
                    if ok:
                        st.balloons()
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    ok, msg = queries.reject_job_offer(int(resp_app_id))
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


# ==========================================
# 2. RECRUITER PORTAL
# ==========================================
elif user_role == "🏢 Company / Recruiter":
    st.markdown('<div class="main-header">🏢 Recruiter & Corporate Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Post job drives, evaluate applicants, record interview rounds, and rollout offer letters.</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["💼 Job Postings & Applicants", "📋 Interview Rounds & Offer Letters"])

    # --- TAB 1: Jobs & Applicants ---
    with tab1:
        col_post, col_apps = st.columns([1, 1.3])
        with col_post:
            st.subheader("📢 Publish Placement Drive")
            companies = queries.get_all_companies()
            if companies:
                comp_map = {f"{c['Name']} (ID: {c['Company_ID']})": c['Company_ID'] for c in companies}
                with st.form("post_job_form", clear_on_submit=True):
                    chosen_comp = st.selectbox("Recruiting Company", list(comp_map.keys()))
                    role_title = st.text_input("Role / Job Title", placeholder="e.g., Software Development Engineer")
                    ctc = st.number_input("Package CTC (LPA)", min_value=0.5, max_value=200.0, step=0.5, value=12.0)
                    min_cgpa = st.number_input("Eligibility Cutoff (Min CGPA)", min_value=0.0, max_value=10.0, step=0.1, value=7.0)
                    openings = st.number_input("Total Openings", min_value=1, step=1, value=5)
                    submit_job = st.form_submit_button("Publish Drive", use_container_width=True)

                if submit_job:
                    if role_title.strip():
                        c_id = comp_map[chosen_comp]
                        ok, msg = queries.post_job(c_id, role_title.strip(), ctc, min_cgpa, int(openings))
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please provide a Job Role Title.")
            else:
                st.warning("No companies are registered yet. Please contact the Placement Cell Admin to register your company.")

        with col_apps:
            st.subheader("📑 Candidate Applications")
            overview = queries.get_recruitment_overview()
            if overview:
                st.dataframe(pd.DataFrame(overview), use_container_width=True, hide_index=True)
            else:
                st.info("No applications received yet.")

            st.markdown("---")
            st.subheader("⚡ Quick Pipeline Status Update")
            with st.form("shortlist_form"):
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    shortlist_id = st.number_input("Application ID", min_value=1, step=1)
                with col_s2:
                    new_status = st.selectbox("Set Status", ["In Process", "Rejected", "Offered", "Applied"])
                submit_status = st.form_submit_button("Update Status", use_container_width=True)

            if submit_status:
                ok, msg = queries.update_application_status(int(shortlist_id), new_status)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    # --- TAB 2: Interview Rounds & Offer Letters ---
    with tab2:
        col_eval, col_offer = st.columns(2)
        with col_eval:
            st.subheader("📝 Record Interview Round")
            with st.form("schedule_round_form", clear_on_submit=True):
                r_app_id = st.number_input("Application ID", min_value=1, step=1, key="round_app_id")
                r_type = st.selectbox(
                    "Interview Stage / Round",
                    ["Online Assessment", "Technical Round 1", "Technical Round 2", "HR Round"],
                )
                r_status = st.selectbox("Stage Verdict", ["Scheduled", "Cleared", "Failed"])
                r_score = st.slider("Assessment Score (0 - 100, 0 if not scored)", min_value=0, max_value=100, value=75)
                r_feedback = st.text_area("Candidate Feedback / Remarks", placeholder="e.g., Solid DSA skills, good communication")
                submit_round = st.form_submit_button("Save Interview Record", use_container_width=True)

            if submit_round:
                ok, msg = queries.schedule_interview_round(
                    int(r_app_id), r_type, r_score, r_feedback.strip() or None, r_status
                )
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

        with col_offer:
            st.subheader("📜 Rollout Official Job Offer")
            with st.form("release_offer_form", clear_on_submit=True):
                o_app_id = st.number_input("Application ID (Must be cleared)", min_value=1, step=1, key="offer_app_id")
                base_sal = st.number_input("Offered Base Salary (LPA)", min_value=1.0, max_value=200.0, step=0.5, value=15.0)
                join_date = st.date_input("Anticipated Joining Date", value=date.today())
                submit_offer = st.form_submit_button("Release Offer Letter", use_container_width=True)

            if submit_offer:
                ok, msg = queries.rollout_job_offer(int(o_app_id), base_sal, join_date)
                if ok:
                    st.balloons()
                    st.success(msg)
                else:
                    st.error(msg)

        st.markdown("---")
        st.subheader("📊 Recent Evaluations & Offers Log")
        log1, log2 = st.columns(2)
        with log1:
            st.write("##### Conducted Interview Rounds")
            rounds_data = queries.get_interview_evaluations()
            if rounds_data:
                st.dataframe(pd.DataFrame(rounds_data), use_container_width=True, hide_index=True)
            else:
                st.caption("No interview evaluations logged yet.")
        with log2:
            st.write("##### Released Job Offers")
            offers_data = queries.get_all_offers()
            if offers_data:
                st.dataframe(pd.DataFrame(offers_data), use_container_width=True, hide_index=True)
            else:
                st.caption("No job offers released yet.")


# ==========================================
# 3. PLACEMENT CELL ADMIN DASHBOARD
# ==========================================
else:
    st.markdown('<div class="main-header">📊 Placement Cell Admin & TPO Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Overall campus recruitment analytics, enterprise reports, and complete database administration.</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📈 Analytics & Executive Reports", "⚙️ Manage Master Records"])

    # --- TAB 1: Analytics & Reports ---
    with tab1:
        analytics = queries.get_placement_analytics()
        total_students = analytics.get("Total_Students", 0)
        total_placed = analytics.get("Total_Placed", 0)
        pct_placed = (total_placed / total_students * 100) if total_students else 0.0
        highest_pkg = float(analytics.get("Highest_Package") or 0.0)
        avg_pkg = float(analytics.get("Average_Package") or 0.0)
        total_comps = analytics.get("Total_Companies", 0)

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Registered Students", total_students)
        m2.metric("Students Placed", total_placed)
        m3.metric("Placement Rate", f"{pct_placed:.1f}%")
        m4.metric("Highest Package", f"₹{highest_pkg:.2f} L")
        m5.metric("Average Package", f"₹{avg_pkg:.2f} L")
        m6.metric("Partner Companies", total_comps)

        st.markdown("---")
        st.subheader("📋 Comprehensive Recruitment Pipeline")
        overview = queries.get_recruitment_overview()
        if overview:
            df_overview = pd.DataFrame(overview)
            st.dataframe(df_overview, use_container_width=True, hide_index=True)
            csv_data = df_overview.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Pipeline to CSV",
                data=csv_data,
                file_name="campus_recruitment_pipeline.csv",
                mime="text/csv",
            )
        else:
            st.info("No applications recorded in the database.")

        c_eval, c_off = st.columns(2)
        with c_eval:
            st.subheader("📝 Candidate Interview Rounds")
            evals = queries.get_interview_evaluations()
            if evals:
                st.dataframe(pd.DataFrame(evals), use_container_width=True, hide_index=True)
            else:
                st.info("No interview evaluations recorded.")

        with c_off:
            st.subheader("📜 Released Job Offers")
            all_offers = queries.get_all_offers()
            if all_offers:
                st.dataframe(pd.DataFrame(all_offers), use_container_width=True, hide_index=True)
            else:
                st.info("No job offers released.")

    # --- TAB 2: Manage Records ---
    with tab2:
        col_comp_reg, col_del = st.columns(2)
        with col_comp_reg:
            st.subheader("🏢 Register New Recruiting Company")
            with st.form("company_form", clear_on_submit=True):
                c_name = st.text_input("Company Name", placeholder="e.g., Amazon")
                c_industry = st.text_input("Industry", placeholder="e.g., E-Commerce & Cloud")
                c_loc = st.text_input("Headquarters / Location", placeholder="e.g., Bangalore, India")
                submit_comp = st.form_submit_button("Register Company", use_container_width=True)

            if submit_comp:
                if c_name.strip():
                    ok, msg = queries.add_company(c_name.strip(), c_industry.strip() or None, c_loc.strip() or None)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Please enter a valid company name.")

        with col_del:
            st.subheader("🗑️ Deregister Student")
            st.warning("⚠️ Deleting a student cascades and removes all their applications, interview evaluations, and job offers.")
            with st.form("delete_student_form", clear_on_submit=True):
                del_roll = st.text_input("Roll Number to Delete", placeholder="e.g., 2025UCS1669")
                submit_del = st.form_submit_button("Permanently Delete Student", use_container_width=True)

            if submit_del:
                if del_roll.strip():
                    ok, msg = queries.delete_student(del_roll.strip())
                    if ok:
                        st.warning(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Please enter a Roll Number.")

        st.markdown("---")
        st.subheader("📑 Master Directories")
        t_stud, t_comp, t_override = st.tabs(["👨‍🎓 Registered Students", "🏢 Registered Companies", "⚙️ Manual Status Override"])

        with t_stud:
            students = queries.get_all_students()
            if students:
                st.dataframe(pd.DataFrame(students), use_container_width=True, hide_index=True)
            else:
                st.info("No registered students.")

        with t_comp:
            comps = queries.get_all_companies()
            if comps:
                st.dataframe(pd.DataFrame(comps), use_container_width=True, hide_index=True)
            else:
                st.info("No registered companies.")

        with t_override:
            st.caption("Admin override tool to update candidate recruitment stage in the Application table.")
            with st.form("admin_override_form"):
                o_col1, o_col2 = st.columns(2)
                with o_col1:
                    override_app_id = st.number_input("Application ID", min_value=1, step=1)
                with o_col2:
                    override_stage = st.selectbox("New Stage", ["Applied", "In Process", "Offered", "Placed", "Rejected"])
                submit_override = st.form_submit_button("Update Candidate Stage", use_container_width=True)

            if submit_override:
                ok, msg = queries.update_application_status(int(override_app_id), override_stage)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
