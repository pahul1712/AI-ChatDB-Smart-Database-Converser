import streamlit as st
from pathlib import Path
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq


st.set_page_config(page_title="AI-ChatDB-Smart-Database-Converser ", page_icon="🦜")



# Added Custom Styling for Better Visualization:
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            color: white;
        }
        h1, h2, h3 {
            text-align: center;
            color: #00e6ac;
        }
        .sidebar .sidebar-content {
            background-color: #1b2735;
        }
    </style>
""", unsafe_allow_html=True)




# Header Section
st.title("🧠 AI-ChatDB: Smart Database Converser")
st.markdown("""
### 💬 Your AI-powered assistant to query, analyze, and explore databases using natural language.
""")
st.divider()

# Sidebar Section
st.sidebar.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=160)
st.sidebar.markdown("### ⚙️ Configuration Panel")
st.sidebar.info("💡 Choose your database type and provide credentials to begin.")




LOCALDB = "USE_LOCALDB"
MYSQL = "USE_MYSQL"


radio_opt = ["Use SQLLite 3 Database - Student.db","Connect to your SQL Database"]

selected_opt = st.sidebar.radio(label="Choose the DB which you want to chat", options=radio_opt)

if radio_opt.index(selected_opt)==1:
    db_uri = MYSQL
    mysql_host = st.sidebar.text_input("Provide My SQL Host")
    mysql_user = st.sidebar.text_input("MYSQL User")
    mysql_password = st.sidebar.text_input("MYSQL password",type="password")
    mysql_db = st.sidebar.text_input("My SQL database")
else:
    db_uri = LOCALDB


api_key = st.sidebar.text_input(label="🔑 Groq API Key",type="password")

if not db_uri:
    st.info("Please enter the database information and uri")

if not api_key:
    st.warning("Please add your Groq API key to continue.")
    st.stop()

## LLM Model
llm=ChatGroq(groq_api_key=api_key,model="llama-3.3-70b-versatile",streaming=True)

@st.cache_resource(ttl="2h")
def configure_db(db_uri, mysql_host=None, mysql_user=None, mysql_password=None, mysql_db=None):
    if db_uri == LOCALDB:
        dbfilepath = (Path(__file__).parent / "student.db").absolute()
        st.sidebar.success(f"📁 Connected to local DB: {dbfilepath.name}")
        creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro", uri=True)
        return SQLDatabase(create_engine("sqlite:///", creator=creator))
    elif db_uri == MYSQL:
        if not (mysql_host and mysql_user and mysql_password and mysql_db):
            st.error("Please provide all MySQL connection details.")
            st.stop()
        st.sidebar.success(f"🌐 Connected to MySQL DB: {mysql_db}")
        return SQLDatabase(create_engine(f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"))



if db_uri==MYSQL:
    db=configure_db(db_uri,mysql_host,mysql_user,mysql_password,mysql_db)
else:
    db=configure_db(db_uri)


## toolkit
toolkit = SQLDatabaseToolkit(db=db,llm=llm)

agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type= AgentType.ZERO_SHOT_REACT_DESCRIPTION
)


if "messages" not in st.session_state or st.sidebar.button("🧹 Clear Chat History"):
    st.session_state["messages"] = [{"role":"assistant","content":"👋 Hello! I’m your Smart Database Converser. Ask me anything!"}]

for msg in st.session_state.messages:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
    st.chat_message(msg["role"]).write(f"{avatar} {msg['content']}")    


user_query=st.chat_input(placeholder="Type your question here (e.g., 'Show all students with marks above 80')...")

if user_query:
    st.session_state.messages.append({"role":"user", "content": user_query})
    st.chat_message("user").write(f"🧑‍💻 {user_query}")

    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            streamlit_callback = StreamlitCallbackHandler(st.container())
            response = agent.run(user_query, callbacks=[streamlit_callback])
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.success("✅ Query executed successfully!")
            st.write(response)


# Export Chat
if st.sidebar.button("📥 Export Chat History"):
    import json
    chat_json = json.dumps(st.session_state.messages, indent=2)
    st.sidebar.download_button("Download Chat History", chat_json, "chat_history.json")


st.markdown("---")
st.caption("🚀 Built with ❤️ by Pahuldeep Singh Dhingra | Powered by LangChain + Groq + Streamlit")




 