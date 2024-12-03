import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import streamlit as st
# Only needed if api Key doesnt work
# using 3.2 as it is a lightweight 2gb model. Hier LANGCHAIN nötig um auf vorherige Chatergebnisse zugreifen zu können?
#import ollama

# Set openAI Key in System Variables
import getpass
import os

if not os.environ.get("OPENAI_API_KEY"):
    st.write("OPEN AI API KEY IS MISSING")

# Initializing ChatGPT/Openai
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2
    # base_url="...",
    # organization="...",
    # other params...
)

# Initializing Prompts
from langchain_core.prompts import ChatPromptTemplate
prompt_extracting_roles = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            'Du bist ein Prozessmanager und versuchst Rollen aus einer Prozessbeschreibung zu heraus zu lesen.',
        ),
        ("human", 'Extrahiere aus folgender Prozessbeschreibung alle Beteiligten Rollen und gib diese als Liste zurück. Prozessbeschreibung: "{prozessbeschreibung}"'),
    ]
)

prompt_extracting_activities = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            'Du bist ein Prozessmanager und versuchst Aktivitäten aus einer Prozessbeschreibung zu heraus zu lesen.',
        ),
        ("human", 'Extrahiere aus folgender Prozessbeschreibung alle Aktivitäten und gib diese als Liste zurück. Die Aktivitäten sollten so beschrieben sein, wie sie auch in einem BPMN Diagramm genutzt werden. Prozessbeschreibung: "{prozessbeschreibung}"'),
    ]
)

prompt_creating_bpmn_diagramm = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            'Du bist ein Prozessmanager. Dir werden Rollen, Aktivitäten und eine Prozessbeschreibung gegeben. Daraus versuchst du ein BPMN 2.0 Dokument zu erstellen.'
        ),
        ("human", "Erstelle aus den gegebenen Rollen, Aktivitäten und der Prozessbeschreibung ein Prozessmodell.Das XML muss Draw.io konform sein. Gib mir nur das Ergebnis in XML zurück. Es sollen alle Aktivitäten und Rollen verwendet werden. Rollen: {roles}. Aktivitäten: {activities}. Prozessbeschreibung: {process}")
    ]
)


# Test String Prozessinput
# Start. Mitarbeiter 1 füllt Wasser in die Kaffeemaschine. Danach füllt Mitarbeiter 2 Kaffeebohnen in die Maschine. Ende
standard_process =  "Start. Mitarbeiter 1 füllt Wasser in die Kaffeemaschine. Danach füllt Mitarbeiter 2 Kaffeebohnen in die Maschine. Ende"

if 'roles_form_submit' not in st.session_state:
    st.session_state.roles_form_submit = False
    
# First process description from user
if 'original_process_input' not in st.session_state:
    st.session_state.original_process_input = "Start. Mitarbeiter 1 füllt Wasser in die Kaffeemaschine. Danach füllt Mitarbeiter 2 Kaffeebohnen in die Maschine. Ende"
    
# edited process description from user for further processing
if 'edited_process_input' not in st.session_state:
    st.session_state.edited_process_input = ""


# function for submit call after adding not extracted roles
def set_roles_form_submit(extra_roles_input):
    st.session_state.roles_form_submit = True
    st.session_state.edited_process_input = st.session_state.original_process_input + "Außerdem wurden folgende Rollen als Teil des Prozesses angegeben. Füge diese deiner Antwort Liste hinzu. Rollen: " + extra_roles_input
    
def set_process_description_form_submit(process_description):
    st.session_state.original_process_input = process_description   
    if st.session_state.roles_form_submit == False:
        st.session_state.edited_process_input = process_description


# Initializing Streamlit App
st.title("Streamlit BA Prototype")

# App Start. Input Prozess description
with st.form("process_description_input"):
    x = st.text_input(label="Prozessbeschreibung", value=standard_process)
    process_description_submit = st.form_submit_button("Rollen extrahieren", on_click=set_process_description_form_submit(x))

if(process_description_submit or st.session_state.roles_form_submit):
    with st.form("roles_form"):
        
        if 'response_role_extraction' not in st.session_state:
            st.session_state.response_role_extraction = ""
            
        st.write("Sind dies alle im Prozess enthaltenen Rollen? Falls nicht bitte weitere Rollen angeben.")
        extra_roles_input = st.text_input(label="Rollen")
        st.write(extra_roles_input)
        st.form_submit_button("Rollen aktualisieren", on_click=set_roles_form_submit(extra_roles_input))

        chain = prompt_extracting_roles | llm
        response_role_extraction = chain.invoke({
            "prozessbeschreibung" : st.session_state.edited_process_input
        })
        
        st.session_state.response_role_extraction = response_role_extraction.content
        st.write(response_role_extraction.content)
        
if(process_description_submit or st.session_state.roles_form_submit):
    with st.form("activity_form"):
        
        if 'response_activity_extraction' not in st.session_state:
            st.session_state.response_activity_extraction = ""
            
        st.write("Sind dies alle im Prozess enthaltenen Aktivitäten? Falls nicht bitte weitere Aktivitäten angeben.")
        extra_activity_input = st.text_input(label="activities")
        st.write(extra_activity_input)
        st.form_submit_button("Aktivitäten aktualisieren", on_click=set_roles_form_submit(extra_activity_input))

        chain = prompt_extracting_activities | llm
        response_activity_extraction = chain.invoke({
            "prozessbeschreibung" : st.session_state.edited_process_input
        })
        
        st.session_state.response_activity_extraction = response_activity_extraction.content
        st.write(response_activity_extraction.content)

if(process_description_submit or st.session_state.roles_form_submit):
    with st.form("process_form"):
        
        
        
        chain = prompt_creating_bpmn_diagramm | llm
        response_diagramm_creation = chain.invoke({
            "roles": st.session_state.response_role_extraction,
            "activities": st.session_state.response_activity_extraction,
            "process" : st.session_state.edited_process_input
        })
        
        st.write(response_diagramm_creation.content)
        st.form_submit_button("BPMN Diagramm generieren")


