import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import streamlit as st
# using 3.2 as it is a lightweight 2gb model. Hier LANGCHAIN nötig um auf vorherige Chatergebnisse zugreifen zu können?
import ollama


# Test String Prozessinput
# Start. Mitarbeiter 1 füllt Wasser in die Kaffeemaschine. Danach füllt Mitarbeiter 2 Kaffeebohnen in die Maschine. Ende

if 'roles_form_submit' not in st.session_state:
    st.session_state.roles_form_submit = False
    
# First process description from user
if 'original_process_input' not in st.session_state:
    st.session_state.original_process_input = ""
    
# edited process description from user for further processing
if 'edited_process_input' not in st.session_state:
    st.session_state.edited_process_input = ""
    
if 'response_role_extraction' not in st.session_state:
    st.session_state.response_role_extraction = ""


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
    process_description_submit = st.form_submit_button("Rollen extrahieren", on_click=set_process_description_form_submit(st.text_input(label="Prozessbeschreibung")))

st.write(st.session_state.roles_form_submit)
st.write(st.session_state.original_process_input)
st.write(st.session_state.edited_process_input)

if(process_description_submit or st.session_state.roles_form_submit):
    with st.form("roles_form"):
        response_role_extraction = ollama.chat(model='llama3.2', messages=[
        {
            'role': 'User',
            'content': f'Du bist ein Prozessmanager. Extrahiere aus folgender Prozessbeschreibung alle Beteiligten Rollen und gib diese als Liste zurück. Prozessbeschreibung: "{st.session_state.edited_process_input}"',
        },
        ])
        
        # print(response['message']['content'])
        st.write(response_role_extraction['message']['content'])
        st.write("Sind dies alle im Prozess enthaltenen Rollen? Falls nicht bitte weitere Rollen angeben.")
        extra_roles_input = st.text_input(label="Rollen")
        st.form_submit_button("Rollen aktualisieren", on_click=set_roles_form_submit(extra_roles_input))


    # Test Image visusalization
    #img = mpimg.imread("./assets/bpmn_test.png")
    #plt.axis("off")
    #imgplot = plt.imshow(img)



