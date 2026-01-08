import streamlit as st
import pandas as pd
import sqlite3
import os
from utils.processor import clean_text, extract_text_from_pdf, get_similarity_score

# --- DATABASE SETUP ---
conn = sqlite3.connect('database.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, title TEXT, description TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS applications (id INTEGER PRIMARY KEY, job_id INTEGER, name TEXT, email TEXT, file_name TEXT)')
    conn.commit()

init_db()

if not os.path.exists("uploads"):
    os.makedirs("uploads")

# --- UI NAVIGATION ---
st.set_page_config(page_title="AI Resume Screener", layout="wide")
st.title("🚀 Intelligent Job Matcher")
menu = ["User: Apply for Job", "Admin: Post Job", "Admin: Matching Dashboard"]
choice = st.sidebar.selectbox("Navigation", menu)

# --- USER SIDE: APPLY ---
if choice == "User: Apply for Job":
    st.header("Apply for an Opening")
    jobs_df = pd.read_sql_query("SELECT * FROM jobs", conn)
    
    if jobs_df.empty:
        st.warning("No jobs posted yet. Please check back later.")
    else:
        job_titles = jobs_df['title'].tolist()
        selected_job = st.selectbox("Select a Job", job_titles)
        
        with st.form("apply_form", clear_on_submit=True):
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            cv_file = st.file_uploader("Upload CV (PDF)", type=["pdf"])
            submit = st.form_submit_button("Submit Application")
            
            if submit:
                if name and email and cv_file:
                    file_path = os.path.join("uploads", cv_file.name)
                    with open(file_path, "wb") as f:
                        f.write(cv_file.getbuffer())
                    
                    job_id = jobs_df[jobs_df['title'] == selected_job]['id'].values[0]
                    c.execute('INSERT INTO applications (job_id, name, email, file_name) VALUES (?,?,?,?)', 
                              (int(job_id), name, email, cv_file.name))
                    conn.commit()
                    st.success(f"Successfully applied for {selected_job}!")
                else:
                    st.error("Please fill all fields and upload a CV.")

# --- ADMIN SIDE: POST JOB ---
elif choice == "Admin: Post Job":
    st.header("Post a New Job Description")
    with st.form("job_form", clear_on_submit=True):
        title = st.text_input("Job Title")
        description = st.text_area("Full Job Description", height=200)
        post_btn = st.form_submit_button("Post Job")
        
        if post_btn and title and description:
            c.execute('INSERT INTO jobs (title, description) VALUES (?,?)', (title, description))
            conn.commit()
            st.success("Job posted successfully!")

# --- ADMIN SIDE: MATCHING ---
elif choice == "Admin: Matching Dashboard":
    st.header("Candidate Matching Engine")
    jobs_df = pd.read_sql_query("SELECT * FROM jobs", conn)
    
    if jobs_df.empty:
        st.info("No jobs available to screen.")
    else:
        selected_job_title = st.selectbox("Select Job to Screen", jobs_df['title'].tolist())
        jd_text = jobs_df[jobs_df['title'] == selected_job_title]['description'].values[0]
        
        if st.button("Run Intelligence Test"):
            job_id = jobs_df[jobs_df['title'] == selected_job_title]['id'].values[0]
            apps_df = pd.read_sql_query(f"SELECT * FROM applications WHERE job_id={job_id}", conn)
            
            if apps_df.empty:
                st.warning("No applicants for this role yet.")
            else:
                results = []
                with st.spinner('Analyzing resumes...'):
                    clean_jd = clean_text(jd_text)
                    for _, row in apps_df.iterrows():
                        file_path = os.path.join("uploads", row['file_name'])
                        resume_raw = extract_text_from_pdf(file_path)
                        clean_resume = clean_text(resume_raw)
                        
                        score = get_similarity_score(clean_jd, clean_resume)
                        results.append({
                            "Candidate": row['name'], 
                            "Email": row['email'], 
                            "Match Score": f"{score}%"
                        })
                
                res_df = pd.DataFrame(results).sort_values(by="Match Score", ascending=False)
                st.subheader(f"Ranked Candidates for {selected_job_title}")
                st.table(res_df)
                st.balloons()