import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts.prompt import PromptTemplate
from langchain.callbacks import get_openai_callback
from langchain.tools.gmail.utils import build_resource_service, get_gmail_credentials
from langchain.agents.agent_toolkits import GmailToolkit
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferWindowMemory
from langchain.chat_models import ChatOpenAI
from google.auth.transport.requests import Request
from langchain import OpenAI
import langchain
from langchain.agents.agent_toolkits import ZapierToolkit
from langchain.utilities.zapier import ZapierNLAWrapper
import os
import sys
from io import StringIO
import threading
import time
from typing import Optional, List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client import tools
import json
import argparse
from googleapiclient.discovery import build
if 'initialized' not in st.session_state:
    st.session_state.initialized = True

_GO_TO_LINK_MESSAGE = """
Go to the following link in your browser:

    {address}
"""
DEFAULT_CLIENT_SECRETS_FILE = "credentials.json"
DEFAULT_SCOPES = ['https://mail.google.com/']

def get_authorization_url(
    token_file: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    client_secrets_file: Optional[str] = None
) -> Credentials:
    # Load client secrets from credentials.json
    with open(client_secrets_file, 'r') as f:
        client_secrets = json.load(f)

    client_id = client_secrets['installed']['client_id']
    client_secret = client_secrets['installed']['client_secret']
    print("client id: ", client_id)
    print("client secret: ", client_secret)

    flow = OAuth2WebServerFlow(
        client_id=client_id,
        client_secret=client_secret,
        scope=scopes,
        redirect_uri='http://localhost',

    )
    
    print("flow: ", flow)
    storage = Storage(token_file)
    creds = storage.get()

    print("creds: ", creds)
    

 
    if not creds or creds.invalid:
        creds = tools.run_flow(flow, storage, tools.argparser.parse_args(args=['--noauth_local_webserver','--auth_host_name=localhost', '--auth_host_port=8000']))

    # ...

    return creds


def get_authorization_url2(
    token_file: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    client_secrets_file: Optional[str] = None
) -> Credentials:
    # Load client secrets from credentials.json
    with open(client_secrets_file, 'r') as f:
        client_secrets = json.load(f)

    client_id = client_secrets['installed']['client_id']
    client_secret = client_secrets['installed']['client_secret']
    print("client id: ", client_id)
    print("client secret: ", client_secret)

    flow = OAuth2WebServerFlow(
        client_id=client_id,
        client_secret=client_secret,
        scope=scopes,
        redirect_uri='http://localhost'
    )

    print("flow: ", flow)
    storage = Storage(token_file)
    creds = storage.get()

    print("creds: ", creds)

    if not creds or creds.invalid:
        st.title("OAuth2 Authorization")
        st.write("Click the button below to authorize the application.")
        
        # Generate the authorization URL
        oauth_callback = tools.client.OOB_CALLBACK_URN
        flow.redirect_uri = oauth_callback
        authorize_url = flow.step1_get_authorize_url()
        # print(_GO_TO_LINK_MESSAGE.format(address=authorize_url))
        if st.button("Authorize"):
            st.markdown(f"[Authorize Here]({authorize_url})", unsafe_allow_html=True)
        code = None
        # code = input('Enter verification code: ').strip()
        code = st.text_input("Enter the verification code:")
        code = code.strip()
        try:
            credential = flow.step2_exchange(code, http=None)
        except tools.client.FlowExchangeError as e:
            sys.exit('Authentication has failed: {0}'.format(e))

        storage.put(credential)
        credential.set_store(storage)
        creds = credential

    return creds


class Chatbot:

    def __init__(self, model_name, temperature, vectors):
        self.model_name = model_name
        self.temperature = temperature
        self.vectors = vectors
        self.memory = ConversationBufferWindowMemory(memory_key="chat_history", k=10, return_messages=True)

    qa_template = """
        You are a helpful AI assistant named Alt bot. The user gives you a file its content is represented by the following pieces of context, use them to answer the question at the end.
        If you don't know the answer, just say you don't know. Do NOT try to make up an answer.
        If the question is not related to the context, politely respond that you are tuned to only answer questions that are related to the context.
        Use as much detail as possible when responding.

        context: {context}
        =========
        question: {question}
        ======
        """

    QA_PROMPT = PromptTemplate(template=qa_template, input_variables=["context","question" ])

    def conversational_chat(self, query):
        """
        Start a conversational chat with a model via Langchain
        """
        llm = ChatOpenAI(model_name=self.model_name, temperature=self.temperature)

        retriever = self.vectors.as_retriever()


        chain = ConversationalRetrievalChain.from_llm(llm=llm,
            retriever=retriever, verbose=True, return_source_documents=True, max_tokens_limit=4097, combine_docs_chain_kwargs={'prompt': self.QA_PROMPT})

        chain_input = {"question": query, "chat_history": st.session_state["history"]}
        result = chain(chain_input)

        st.session_state["history"].append((query, result["answer"]))
        #count_tokens_chain(chain, chain_input)
        return result["answer"]
    
    def gmailChatbot(self):

        llm = OpenAI(
            temperature=0
        )

        # output = StringIO()
        # sys.stdout = output

        # def run_gmail_toolkit():
        #     global toolkit
        # credentials = get_gmail_credentials(
        #     token_file='token.json',
        #     scopes=["https://mail.google.com/"],
        #     client_secrets_file="credentials.json",
            
        # )

        # credentials = login(client_id= "385200199539-ubvihejddlqp8fse65fs9h3rvia32dbo.apps.googleusercontent.com", client_secret="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", scopes= ["https://mail.google.com/"], redirect_uri='http://localhost:8000/')
        credentials = get_authorization_url2(token_file="token.json", scopes=["https://mail.google.com/"], client_secrets_file='credentials.json')
        print(credentials)
        api_resource = build_resource_service(credentials=credentials)
        print('api_resource:  ', api_resource)
        toolkit = GmailToolkit(api_resource=api_resource)

        # thread = threading.Thread(target=run_gmail_toolkit)
        # thread.start()
        # time.sleep(0.1)
        # sys.stdout = sys.__stdout__
        # printed_output = output.getvalue()

        # st.markdown(f"{printed_output}")
        # thread.join()

        agent = initialize_agent(
                tools=toolkit.get_tools(),
                llm=llm,
                memory=self.memory,
                agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            )

        # chain_input = {"question": query, "chat_history": st.session_state["history"]}

        # result = agent.run(chain_input)

        # st.session_state["history"].append((query, result["answer"]))
        # return result["answer"]
        return agent

    
    def meetingChatbot(self):
        llm = OpenAI(
            temperature=0
        )
        zapier = ZapierNLAWrapper()
        toolkit = ZapierToolkit.from_zapier_nla_wrapper(zapier)
        agent = initialize_agent(toolkit.get_tools(), llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True, max_iteration=3)
        
        return agent
        



def count_tokens_chain(chain, query):
    with get_openai_callback() as cb:
        result = chain.run(query)
        st.write(f'###### Tokens used in this conversation : {cb.total_tokens} tokens')
    return result 

    
    
