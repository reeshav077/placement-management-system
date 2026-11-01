try:
    import streamlit as st  # type: ignore[import-not-found]
except ModuleNotFoundError as exc:
    raise RuntimeError("Streamlit is required to run this app. Install it with: pip install streamlit") from exc

import queries
import pandas as pd

# Set page configuration
st.set_page_config(page_title="Placement & Recruitment System", layout="wide")

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🔐 System Login")
st.sidebar.markdown("Select your portal access level:")

user_role = st.sidebar.radio(
    "Go to:",
    ["🎓 Student Portal", "🏢 Recruiter Portal", "📊 Admin Dashboard"]
)

st.sidebar.divider()
st.sidebar.info("Developed by: Reeshav, Uttam, and Mohit")

# --- 1. STUDENT PORTAL ---
if user_role == "🎓 Student Portal":
    st.title("🎓 Student Portal")
    st.markdown("Welcome! Register, update your profile, and apply for jobs.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### 📝 Student Registration")
        with st.form("register_student_form"):
            roll_num = st.text_input("Roll Number (e.g., 2025UCS1669)")
            name = st.text_input("Full Name")
            branch = st.selectbox("Branch", ["CSE", "IT", "ECE", "MAC", "EE", "ME"])
            cgpa = st.number_input("Current CGPA", min_value=0.0, max_value=10.0, step=0.1)
            email = st.text_input("Email Address")
            
            if st.form_submit_button("Register"):
                if roll_num and name and email:
                    # Assuming you have a register_student function in queries.py
                    success, msg = queries.register_student(roll_num, name, branch, cgpa, email)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill all required fields.")
                    
        st.divider()
        st.write("#### ✏️ Update Profile Details")
        with st.expander("Click here to update your Name, Branch, CGPA, or Email"):
            with st.form("update_profile_form"):
                st.info("Enter your existing Roll Number to verify your identity.")
                upd_roll = st.text_input("Your Roll Number")
                upd_name = st.text_input("Updated Name")
                upd_branch = st.selectbox("Updated Branch", ["CSE", "IT", "ECE", "MAC", "EE", "ME"])
                upd_cgpa = st.number_input("Updated CGPA", min_value=0.0, max_value=10.0, step=0.1)
                upd_email = st.text_input("Updated Email")
                
                if st.form_submit_button("Save Changes"):
                    if upd_roll and upd_name and upd_email:
                        success, msg = queries.update_student_profile(
                            upd_roll, upd_name, upd_branch, upd_cgpa, upd_email
                        )
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please fill in the Roll Number, Name, and Email fields.")

    with col2:
        st.write("#### 📋 Available Job Postings")
        jobs = queries.get_all_jobs() # Assuming this function exists
        if jobs:
            st.dataframe(pd.DataFrame(jobs), use_container_width=True)
        else:
            st.info("No active job postings right now.")
            
        st.divider()
        st.write("#### 📩 Accept Job Offer")
        with st.form("accept_offer_form"):
            app_id = st.text_input("Enter your Application ID to accept offer")
            if st.form_submit_button("Accept Offer"):
                if app_id:
                    success, msg = queries.accept_job_offer(app_id)
                    if success:
                        st.balloons()
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Please enter an Application ID.")


# --- 2. RECRUITER PORTAL ---
elif user_role == "🏢 Recruiter Portal":
    st.title("🏢 Recruiter Portal")
    st.markdown("Post new opportunities and manage candidate pipelines.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### 📢 Post a New Job")
        with st.form("post_job_form"):
            comp_id = st.text_input("Company ID")
            role = st.text_input("Role Title")
            ctc = st.number_input("CTC (in LPA)", min_value=0.0, step=0.5)
            min_cgpa = st.number_input("Minimum CGPA Required", min_value=0.0, max_value=10.0, step=0.1)
            openings = st.number_input("Number of Openings", min_value=1, step=1)
            
            if st.form_submit_button("Post Job"):
                if comp_id and role:
                    success, msg = queries.post_job(comp_id, role, ctc, min_cgpa, openings)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill in all required fields.")

    with col2:
        st.write("#### 🔄 Update Candidate Pipeline")
        with st.form("update_pipeline_form"):
            app_id_update = st.text_input("Application ID")
            new_status = st.selectbox("New Status", ["Applied", "Interviewing", "Offered", "Rejected"])
            
            if st.form_submit_button("Update Status"):
                if app_id_update:
                    success, msg = queries.update_application_status(app_id_update, new_status)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Please enter an Application ID.")


# --- 3. ADMIN DASHBOARD ---
elif user_role == "📊 Admin Dashboard":
    st.title("📊 Placement Admin Dashboard")
    st.markdown("Global overview of university placement statistics and database controls.")
    
    # Analytics row
    st.write("#### 📈 Real-Time Analytics")
    metric1, metric2, metric3 = st.columns(3)
    
    # Fetching aggregate data (ensure these functions exist or adapt as needed)
    total_placed = queries.get_total_placed_students()
    highest_package = queries.get_highest_package()
    total_companies = queries.get_total_companies()
    
    metric1.metric("Total Students Placed", total_placed)
    metric2.metric("Highest Package (LPA)", f"₹ {highest_package} L")
    metric3.metric("Recruiting Companies", total_companies)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### 🏆 Registered Students Database")
        students = queries.get_all_students()
        if students:
            st.dataframe(pd.DataFrame(students), use_container_width=True)
        else:
            st.info("No student records found.")
            
    with col2:
        st.write("#### ⚠️ Danger Zone: Delete Records")
        with st.expander("Delete a Student Record"):
            st.warning("Deleting a student will cascade and delete all their applications and offers.")
            with st.form("delete_student_form"):
                del_roll = st.text_input("Enter Roll Number to Delete")
                
                if st.form_submit_button("Delete Student"):
                    if del_roll:
                        success, msg = queries.delete_student(del_roll)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please enter a Roll Number.")