import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
from google.oauth2 import id_token
from google.auth.transport import requests
import google.generativeai as genai
import sqlite3
import pandas as pd
import plotly.express as px

# Firebase initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("datasci-45410-66555c180fd9.json")
    firebase_admin.initialize_app(cred)

# Google API Key for GenAI
GOOGLE_API_KEY = 'AIzaSyAhPdM6jGrv-CTRuI6tqOrd4qXmyObJnpY'
genai.configure(api_key=GOOGLE_API_KEY)

# Streamlit page configuration
st.set_page_config(page_title="DataNest", page_icon="🔎")

# Prompt for GenAI
prompt = [
    """
    Imagine you're an SQL expert and data visualization advisor adept at translating English questions into precise SQL queries and recommending visualization types for a database named Job_Postings, which comprises two key tables: Companies and Salaries. Your expertise enables you to select the most appropriate chart type based on the expected query result set to effectively communicate the insights.

    Here are examples to guide your query generation and visualization recommendation:

    - Example Question 1: "How many unique company names are there?"
      SQL Query: SELECT COUNT(DISTINCT name) FROM Companies;
      Recommended Chart: None (The result is a single numeric value.)

    - Example Question 2: "What are the total number of companies in each city?"
      SQL Query: SELECT city, COUNT(*) AS total_companies FROM Companies GROUP BY city;
      Recommended Chart: Bar chart (Cities on the X-axis and total companies on the Y-axis.)

    - Example Question 3: "List all companies with more than 500 employees."
      SQL Query: SELECT name FROM Companies WHERE company_size > 500;
      Recommended Chart: None (The result is a list of company names.)

    - Example Question 4: "What percentage does each formatted_work_type represent of the total?"
      SQL Query: SELECT formatted_work_type, (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Jobs)) AS percentage FROM Jobs GROUP BY formatted_work_type;
      Recommended Chart: Pie chart (Show each formatted_work_type's percentage of the total.)

    - Example Question 5: "Which companies have the most job openings?"
      SQL Query: SELECT Companies.name, COUNT(Jobs.job_id) AS total_openings FROM Companies JOIN Jobs ON Companies.company_id = Jobs.company_id GROUP BY Companies.name ORDER BY total_openings DESC LIMIT 10;
      Recommended Chart: Bar chart (Company names on the X-axis and total job openings on the Y-axis.)


    Your task is to craft the correct SQL query in response to the given English questions and suggest an appropriate chart type for visualizing the query results, if applicable. Please ensure that the SQL code generated does not include triple backticks (\`\`\`) at the beginning or end and avoids including the word "sql" within the output. Also, provide clear and concise chart recommendations when the query results lend themselves to visualization.
    """
]

# Function to retrieve SQL query from GenAI response
def get_sql_query_from_response(response):
    try:
        query_start = response.index('SELECT')  
        query_end = response.index(';') + 1  
        sql_query = response[query_start:query_end]  
        return sql_query
    except ValueError:
        return None

# Function to retrieve SQL query from GenAI for a given question
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt[0], question])
    return response.text

#  main fun
def app():
    st.title('Welcome to DataNest')

    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'useremail' not in st.session_state:
        st.session_state.useremail = ''

    def f(email): 
        try:
            user = auth.get_user_by_email(email)
            st.session_state.username = user.uid
            st.session_state.useremail = user.email
            st.session_state.signedout = True
            st.session_state.signout = True
            st.success("Login Successful!")
            st.toast('You can now access all features.')
            st.snow()
        except: 
            st.warning('Login Failed')

    def google_login(id_token):
        try:
            decoded_token = id_token.verify_oauth2_token(id_token, requests.Request())
            email = decoded_token['email']
            user = auth.get_user_by_email(email)
            st.session_state.username = user.uid
            st.session_state.useremail = user.email
            st.session_state.signedout = True
            st.session_state.signout = True
            st.success("Login Successful! You can now access all features.")    
        except Exception as e: 
            st.warning(f'Google Login Failed: {str(e)}')

    def t():
        st.session_state.signout = False
        st.session_state.signedout = False   
        st.session_state.username = ''
        st.session_state.useremail = ''
    
    if "signedout"  not in st.session_state:
        st.session_state["signedout"] = False
    if 'signout' not in st.session_state:
        st.session_state['signout'] = False    
    
    if not st.session_state["signedout"]:
        choice = st.selectbox('Login/Signup',['Login','Sign up'])
        if choice == 'Sign up':
            email = st.text_input('Email Address')
            username = st.text_input("Enter your unique username")
            password = st.text_input('Password',type='password')
            if st.button('Create my account'):
                if username and '@' in email and '.' in email:
                    user = auth.create_user(email=email, password=password, uid=username)
                    st.success('Account created successfully!')
                    st.markdown('Please Login using your email and password')
                    st.balloons()
                else:
                    st.warning('Fill all the criteria')
        elif choice == 'Login':
            email = st.text_input('Email Address')
            password = st.text_input('Password',type='password')
            if st.button('Login'):
                f(email)
            
    
    # if st.session_state.signout:
    #     # st.write('Posts')

    if st.session_state.username:  # Check user loged in or not
        with st.container():
            st.subheader("What are you looking for?")

            question = st.text_input("Ask Your Question......", key="input", placeholder="Type here your question...", max_chars=200)

            submit = st.button("Submit", help="Click to submit your question.")

        if submit and question:
            response = get_gemini_response(question, prompt)
            sql_query = get_sql_query_from_response(response)
            
            if sql_query:
                st.balloons()
                st.code(sql_query, language='sql')
                
            else:
                st.write("No valid SQL query could be extracted from the response.")

app()
