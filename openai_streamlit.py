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

# Read test process description files and save descriptions in a session_state parameter
if 'desc_files_read' not in st.session_state:
    st.session_state.desc_files_read = False
    st.session_state.process_desc_nebentaetigkeiten = ""
    st.session_state.process_desc_debriefing = ""
    st.session_state.process_desc_bedarfsermittlung = ""
    
    # example input files for modell creating prompt
    st.session_state.example_input_file_1 = ""
    st.session_state.example_input_file_2 = ""

if st.session_state.desc_files_read == False:
    file_process_desc_nebentaetigkeiten = open("assets/process_desc_nebentaetigkeiten.txt", encoding="utf8")
    file_process_desc_debriefing = open("assets/process_desc_debriefing.txt", encoding="utf8")
    file_process_desc_bedarfsermittlung = open("assets/process_desc_bedarfsermittlung.txt", encoding="utf8")
    file_input_example_1 = open("assets/example_for_ai_1.drawio", encoding="utf8")
    file_input_example_2 = open("assets/example_for_ai_2.drawio", encoding="utf8")

    # save process descriptions
    process_desc_nebentaetigkeiten = file_process_desc_nebentaetigkeiten.read()
    process_desc_debriefing = file_process_desc_debriefing.read()
    process_desc_bedarfsermittlung = file_process_desc_bedarfsermittlung.read()
    st.session_state.example_input_file_1 = file_input_example_1
    st.session_state.example_input_file_2 = file_input_example_2

    # close files
    file_process_desc_nebentaetigkeiten.close()
    file_process_desc_debriefing.close()
    file_process_desc_bedarfsermittlung.close()
    file_input_example_1.close()
    file_input_example_2.close()

# Initialize Prompts
from langchain_core.prompts import ChatPromptTemplate
prompt_extracting_roles = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            'Du bist ein Prozessmanager extrahierst Rollen aus einer Prozessbeschreibung heraus.',
        ),
        ("human", 'Extrahiere aus folgender Prozessbeschreibung alle Beteiligten Rollen und gib diese als Liste zurück. Prozessbeschreibung: "{prozessbeschreibung}"'),
    ]
)

prompt_extracting_activities = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            'Du bist ein Prozessmanager extrahierst Aktivitäten aus einer Prozessbeschreibung heraus.',
        ),
        ("human", 'Extrahiere aus folgender Prozessbeschreibung alle Aktivitäten und gib diese als Liste zurück. Die Aktivitäten sollten so beschrieben sein, wie sie auch in einem BPMN Diagramm genutzt werden. Prozessbeschreibung: "{prozessbeschreibung}"'),
    ]
)

prompt_creating_bpmn_diagramm = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            'Du bist ein Prozessmanager. Dir werden zwei draw.io Dateien als Beispiel gegeben welche ein Prozessmodell darstellen und mit 3 Anführungszeichen abgegrenzt sind. Außerdem werden dir Rollen, Aktivitäten und eine Prozessbeschreibung gegeben. Daraus erstellst du ein Draw.io konformes XML Dokument.'
        ),
        ("human", 
         '''
         Erstelle aus den gegebenen Rollen, Aktivitäten und der Prozessbeschreibung ein Prozessmodell.
         Das XML muss Draw.io konform sein.
         Stelle sicher, dass alle Rollen als Swimlane dargestellt werden.
         Stelle sicher, dass Verzweigungen, signalisiert durch das Wort "oder", als Rauten dargestellt werden und dass diese beschriftet sind.
         Gib mir nur das Ergebnis in XML zurück. 
         Achte vor allem drauf, dass sich keine Elemente überlappen.
         Swimlanes sind immer nebeneinander.
         Achte auf eine angemessen Breite der Swimlanes und verdopple diese dann.
         Die Höhe der Swimlanes muss immer bis an das Ende der Seite gehen.
         Es sollen alle Aktivitäten und Rollen verwendet werden. 
         Rollen die keine Aufgabe übernehmen werden weggelassen.
         
         """{example_input_file_1}"""
         """{example_input_file_2}"""
         
         Rollen: {roles}. 
         Aktivitäten: {activities}. 
         Prozessbeschreibung: {process}
         '''
         )
    ]
)


prompt_roles_refreshed = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            'Du bist ein Prozessmanager. Dir werden Rollen und eine bestehende Liste an Rollen gegeben und du erweiterst die Liste mit den gegebenen Rollen'
        ),
        ("human", "Erweitere die Liste um die gegebenen Rollen. Rollen: {roles}. Liste: {list}.")
    ]
)

prompt_activities_refreshed = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            'Du bist ein Prozessmanager. Dir werden Aktivitäten und eine bestehende Liste an Aktivitäten gegeben und du erweiterst die Liste mit den gegebenen Aktivitäten'
        ),
        ("human", "Erweitere die Liste um die gegebenen Aktivitäten. Aktivitäten: {activities}. Liste: {list}.")
    ]
)


# Test String Prozessinput
# Start. Mitarbeiter 1 füllt Wasser in die Kaffeemaschine. Danach füllt Mitarbeiter 2 Kaffeebohnen in die Maschine. Ende
test_process_desc = "Start. Mitarbeiter 1 füllt Wasser in die Kaffeemaschine. Danach füllt Mitarbeiter 2 Kaffeebohnen in die Maschine. Ende"
test_process_desc_ppt = '''Recherche: Der Student sucht nach passenden Praktikumsstellen.
Wenn eine Praktikumsstelle gefunden wurde folgt die Erstellung der Unterlagen, falls nicht wird die Suche wiederholt.
Erstellung der Unterlagen: Geforderte Dokumente werden erstellt.
Einreichen der Bewerbung: Die Bewerbung wird über ein Online-Portal abgeschickt.'''
init_process = test_process_desc_ppt 

# init flags for form submit checking
if 'roles_form_submitted' not in st.session_state:
    st.session_state.desc_form_submitted = False
    
    st.session_state.roles_form_submitted = False
    st.session_state.roles_form_updated = False
    
    st.session_state.activity_form_submitted = False
    st.session_state.activity_form_updated = False

    
# First process description from user
if 'original_process_input' not in st.session_state:
    st.session_state.original_process_input = init_process
    
# edited process description from user for further processing
if 'edited_process_input' not in st.session_state:
    st.session_state.edited_process_input = ""

# response after role extraction prompt
if 'response_role_extraction' not in st.session_state:
    st.session_state.response_role_extraction = ""
        
# user input if roles were missing
if 'extra_roles_input' not in st.session_state:
    st.session_state.extra_roles_input = ""

# response after activity extraction prompt
if 'response_activity_extraction' not in st.session_state:
    st.session_state.response_activity_extraction = ""
    
# user input if activities were missing
if 'extra_activity_input' not in st.session_state:
    st.session_state.extra_activity_input = ""

# function for submit call after adding not extracted roles
def set_roles_form_submitted():
    st.session_state.roles_form_submitted = True
    
# funtion for update call after missing roles
def set_roles_form_updated():
    st.session_state.roles_form_updated = True
    
def set_process_description_form_submitted(process_description):
    st.session_state.desc_form_submitted = True 
    st.session_state.original_process_input = process_description   
    if st.session_state.roles_form_submitted == False:
        st.session_state.edited_process_input = process_description
        
def set_activity_form_submitted():
    st.session_state.activity_form_submitted = True
    
def set_activity_form_updated():
    st.session_state.activity_form_updated = True

# Initializing Streamlit App with title
st.title("Prozessmodell Generator")

# App start. Form for input process description
with st.form("process_description_input"):
    # value sets initial process description for testing
    desc_input = st.text_area(label="Bitte geben sie ihre Prozessbeschreibung an", value=init_process, height=500)
    st.form_submit_button("Rollen extrahieren", on_click=set_process_description_form_submitted, args=(desc_input,))

# Second form for extracting and correcting roles, only visible after description input
if(st.session_state.desc_form_submitted == True):
    with st.form("roles_form", enter_to_submit=False):
        
        # Trigger roles extraction prompt only the first time
        if st.session_state.response_role_extraction == "":
            chain = prompt_extracting_roles | llm
            response_role_extraction = chain.invoke({
                "prozessbeschreibung" : st.session_state.edited_process_input
            })
            # save answer in session state
            st.session_state.response_role_extraction = response_role_extraction.content
    
    
        # Ask user if all roles were extracted correctly, if not the user can add missing ones
        if(st.session_state.response_role_extraction != ""):
            st.write("Sind dies alle im Prozess enthaltenen Rollen? Falls nicht bitte weitere Rollen angeben.")
            extra_role_input = st.text_input(label="Rollen")
            st.session_state.extra_roles_input = extra_role_input
            
        # If the roles were updated by the user trigger this prompt
        if(st.session_state.roles_form_updated == True and st.session_state.get("extra_roles_input") != "" and st.session_state.roles_form_submitted == False):
            chain = prompt_roles_refreshed | llm
            response_updated_roles = chain.invoke({
                "list" : st.session_state.response_role_extraction,
                "roles" : st.session_state.extra_roles_input
            })
            # save answer in session state
            st.session_state.response_role_extraction = response_updated_roles.content
                
        st.write(st.session_state.response_role_extraction)
        
        # draw buttons for updating or confirming roles
        col1, col2 = st.columns([1,1])
        with col1:
            st.form_submit_button("Rollen bestätigen", on_click=set_roles_form_submitted)
        with col2:
            st.form_submit_button("Rollen aktualisieren", on_click=set_roles_form_updated)
    

if(st.session_state.roles_form_submitted == True):
    with st.form("activity_form"):
        
        # Trigger activity extraction prompt exactly one time
        if st.session_state.response_activity_extraction == "":
            chain = prompt_extracting_activities | llm
            response_activity_extraction = chain.invoke({
                "prozessbeschreibung" : st.session_state.edited_process_input
            })
            # save answer in session state
            st.session_state.response_activity_extraction = response_activity_extraction.content
                
        # Ask user if all activities were extracted correctly, if not the user can add missing ones
        if(st.session_state.response_activity_extraction != ""):
            st.write("Sind dies alle im Prozess enthaltenen Aktivitäten? Falls nicht bitte weitere Aktivitäten angeben.")
            extra_activity_input = st.text_input(label="Aktivitäten")
            st.session_state.extra_activity_input = extra_activity_input
        
        
        # If the roles were updated by the user trigger this prompt
        if(st.session_state.activity_form_updated == True and st.session_state.get("extra_activity_input") != "" and st.session_state.activity_form_submitted == False):
            chain = prompt_activities_refreshed | llm
            response_updated_activities = chain.invoke({
                "list" : st.session_state.response_activity_extraction,
                "activities" : st.session_state.extra_activity_input
            })
            # save answer in session state
            st.session_state.response_activity_extraction = response_updated_activities.content
        
        st.write(st.session_state.response_activity_extraction)
        
        # draw buttons for updating or confirming activities
        col1, col2 = st.columns([1,1])
        with col1:
            st.form_submit_button("Aktivitäten bestätigen", on_click=set_activity_form_submitted)
        with col2:
            st.form_submit_button("Aktivitäten aktualisieren", on_click=set_activity_form_updated)        


if(st.session_state.activity_form_submitted == True):
    with st.form("process_form"):
        
        chain = prompt_creating_bpmn_diagramm | llm
        response_diagramm_creation = chain.invoke({
            "roles": st.session_state.response_role_extraction,
            "activities": st.session_state.response_activity_extraction,
            "process" : st.session_state.edited_process_input,
            "example_input_file_1" : st.session_state.example_input_file_1,
            "example_input_file_2" : st.session_state.example_input_file_2
        })
        
        st.write(response_diagramm_creation.content)
        st.form_submit_button("BPMN Diagramm generieren")