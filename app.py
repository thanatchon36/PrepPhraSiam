from sqlite3 import Timestamp
import streamlit as st
from bardapi import Bard
import pandas as pd
import ast
import json
import re
import os
import csv
import datetime
import time
import random
import numpy as np

def get_now():
    now = datetime.datetime.now()
    now = str(now)[:16]
    return now

def reset(df):
    cols = df.columns
    return df.reset_index()[cols]

st.set_page_config(page_title = 'PrepPhraSiam')

st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
""", unsafe_allow_html=True)

# Initialize chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []
else:
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"] + ' ' + message["timestamp"])

context_col = 'text'
csv_file = 'data/data.csv'
full_df = pd.read_csv(csv_file, dtype = str)
full_df['text_len'] = full_df['text_len'].astype(int)
full_df = reset(full_df[full_df['text_len'] >= 800])


total_no = len(full_df)

csv_file = "data/bard.csv"
file_exists = os.path.isfile(csv_file)
if not file_exists:
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp','file_name','page_no','text','generative_text','Doc_Page_ID'])
        print(f'Create {csv_file}')

if "progress_percent" not in st.session_state:
    st.session_state.progress_percent = 0
    st.session_state.completed_no = 0
    st.session_state.total_no = total_no
    st.session_state.error_no = 0
    
progress_text = f"Operation in progress. Please wait. {st.session_state.progress_percent}% ({st.session_state.completed_no}/{st.session_state.total_no})"
my_bar = st.progress(st.session_state.progress_percent, text=progress_text)

# # Check if there's a user input prompt
if prompt := st.chat_input(placeholder="Kindly input your cookie..."):
    token = prompt
    bard = Bard(token=token)

    timestamp = get_now()
    # Display user input in the chat
    st.chat_message("user").write(token + ' ' + timestamp)
    # Add user message to the chat history
    st.session_state.messages.append({"role": "user", "content": token, "timestamp": timestamp})
    
    # try:
    st.session_state.error_no = 0
    with st.spinner('Requesting...'):
        while True:
            try:        
                fil_df = pd.read_csv('data/bard.csv', dtype = str, usecols = ['Doc_Page_ID'])
                fil_id_list = list(fil_df['Doc_Page_ID'].values)

                completed_no = len(list(set(fil_id_list)))

                st.session_state.completed_no = completed_no
                st.session_state.progress_percent = round(completed_no / total_no, 4)

                progress_text = f"Operation in progress. Please wait. {round(st.session_state.progress_percent*100, 4)}% ({st.session_state.completed_no}/{st.session_state.total_no})"
                my_bar.progress(st.session_state.progress_percent, text=progress_text)
                
            except:
                fil_df = pd.DataFrame()
                fil_id_list = []
                pass
            
            sample_df = full_df.copy()
            sample_df = reset(sample_df[~sample_df['Doc_Page_ID'].isin(fil_id_list)])

            csv_file = "data/bard.csv"
            with open(csv_file, mode='a', newline='') as file:
                try:
                    sample_instance = sample_df.sample(1)
                    prompt = sample_instance[context_col].values[0]
                    Doc_Page_ID = sample_instance['Doc_Page_ID'].values[0]

                    prompt = f"""คุณเป็นอาจารย์มหาวิทยาลัย คุณต้องการสร้างคำถามและคำตอบเพื่อออกข้อสอบ จำนวน5ถึง20คำถาม คุณจะถามคำถามจากข้อเท็จจริงใน #เนื้อหา เท่านั้น ห้ามนำข้อมูลที่ไม่อยู่ใน #เนื้อหา มาเป็นคำถาม คำถามที่คุณสร้างจะแสดงผลในตาราง
                    โดยเนื้อหาที่คุณต้องการจะออกข้อสอบคือ
                    
                    #เนื้อหา
                    {prompt}
                        """
                    output = bard.get_answer(prompt)
                    output_0 = output['content']
                    output_1 = output['choices'][0]['content'][0]
                    output_2 = output['choices'][1]['content'][0]
                    output_3 = output['choices'][2]['content'][0]
                    
                    if 'Error' in output_0:
                        temp_msg = "Error ! " + str(Doc_Page_ID)
                        timestamp = get_now()
                        st.session_state.error_no = st.session_state.error_no + 1
                        st.chat_message("assistant").write(temp_msg + ' ' + timestamp)
                        st.session_state.messages.append({"role": "assistant", "content": temp_msg, "timestamp": timestamp})
                    else:
                        writer = csv.writer(file)
                        timestamp = get_now()
                        writer.writerow([timestamp, sample_instance['file_name'].values[0], sample_instance['page_no'].values[0], sample_instance['text'].values[0], output_1, sample_instance['Doc_Page_ID'].values[0]])
                        writer.writerow([timestamp, sample_instance['file_name'].values[0], sample_instance['page_no'].values[0], sample_instance['text'].values[0], output_2, sample_instance['Doc_Page_ID'].values[0]])
                        writer.writerow([timestamp, sample_instance['file_name'].values[0], sample_instance['page_no'].values[0], sample_instance['text'].values[0], output_3, sample_instance['Doc_Page_ID'].values[0]])
                        temp_msg = "Record Saved ! " + str(Doc_Page_ID)
                        st.session_state.error_no = 0
                        st.chat_message("assistant").write(temp_msg + ' ' + timestamp)
                        st.session_state.messages.append({"role": "assistant", "content": temp_msg, "timestamp": timestamp})

                    mu, sigma = 1, 0.1 # mean and standard deviation
                    s = np.random.normal(mu, sigma, 1000)
                    time.sleep(random.choice(s))
                except:
                    temp_msg = "Error ! " + str(Doc_Page_ID)
                    timestamp = get_now()
                    st.session_state.error_no = st.session_state.error_no + 1
                    st.chat_message("assistant").write(temp_msg + ' ' + timestamp)
                    st.session_state.messages.append({"role": "assistant", "content": temp_msg, "timestamp": timestamp})
                    pass

                if st.session_state.error_no >= 20:
                    temp_msg = 'Due to Errors, Stopped !'
                    timestamp = get_now()
                    st.chat_message("assistant").write(temp_msg + ' ' + timestamp)
                    st.session_state.messages.append({"role": "assistant", "content": temp_msg, "timestamp": timestamp})
                    break
    # except:
    #     pass