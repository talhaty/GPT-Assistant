import os
import sys
import streamlit as st
from io import StringIO
import re
from modules.history import ChatHistory
from modules.layout import Layout
from modules.utils import Utilities
from modules.sidebar import Sidebar
import json
#To be able to update the changes made to modules in localhost (press r)
def reload_module(module_name):
    import importlib
    import sys
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
    return sys.modules[module_name]

history_module = reload_module('modules.history')
layout_module = reload_module('modules.layout')
utils_module = reload_module('modules.utils')
sidebar_module = reload_module('modules.sidebar')

ChatHistory = history_module.ChatHistory
Layout = layout_module.Layout
Utilities = utils_module.Utilities
Sidebar = sidebar_module.Sidebar

st.set_page_config(layout="wide", page_icon="💬", page_title="Alt-Bot 🤖")

# Instantiate the main components
layout, sidebar, utils = Layout(), Sidebar(), Utilities()

layout.show_header("Meetings and Calendar")

user_api_key = utils.load_api_key()

if not user_api_key:
    layout.show_api_key_missing()
else:
    zapier_api_key=None
    if os.path.exists(".env") and os.environ.get("ZAPIER_NLA_API_KEY") is not None:
        zapier_api_key = os.environ["ZAPIER_NLA_API_KEY"]
    if not zapier_api_key:
        zapier_api_key = st.sidebar.text_input(
            label="#### Your Zapier API key 👇", placeholder="sk-...", type="password"
        )
        if zapier_api_key:
            st.session_state.zapier_api_key = zapier_api_key

    os.environ["OPENAI_API_KEY"] = user_api_key
    os.environ["ZAPIER_NLA_API_KEY"] = zapier_api_key

    # Configure the sidebar
    sidebar.show_options()
    # Initialize chat history
    history = ChatHistory()
    try:
        chatbot = utils.setup_gmail_chatbot(
            st.session_state["model"], st.session_state["temperature"]
        )
        st.session_state["meeting_chatbot"] = chatbot.meetingChatbot()

        if st.session_state["ready"]:
            # Create containers for chat responses and user prompts
            response_container, prompt_container = st.container(), st.container()
         
            with prompt_container:
                # Display the prompt form
                is_ready, user_input = layout.meeting_prompt_form()
             
                history.initialize('')
               
                if st.session_state["reset_chat"]:
                    history.reset('')
                 
                if is_ready:
                    
                    # Update the chat history and display the chat messages
                    history.append("user", user_input)
                    
                    old_stdout = sys.stdout
                    sys.stdout = captured_output = StringIO()             

                    chain_input = {"question": user_input, "chat_history": st.session_state["history"]}
                    
                    # result = agent.run(chain_input)
                    
                    # st.session_state["history"].append((query, result["answer"]))
                    # return result["answer"]

                    output = st.session_state["meeting_chatbot"].run(user_input)
                    
                    sys.stdout = old_stdout
                   

                    history.append("assistant", output)
                    

                    # Clean up the agent's thoughts to remove unwanted characters
                    thoughts = captured_output.getvalue()
                    cleaned_thoughts = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', thoughts)
                    cleaned_thoughts = re.sub(r'\[1m>', '', cleaned_thoughts)

                    # Display the agent's thoughts
                    with st.expander("Display the agent's thoughts"):
                        st.write(cleaned_thoughts)

                history.generate_messages(response_container)
    except Exception as e:
        st.error(f"Error: {str(e)}")


