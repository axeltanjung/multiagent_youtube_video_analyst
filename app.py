import streamlit as st
import os
import tempfile
import gc
import base64
import time
import yaml

from tqdm import tqdm
from data_scrapper import *
from dotenv import load_dotenv
load_dotenv()

from crewai import Agent, Crew, Process, Task, LLM
from crewai_tools import FileReadTool

docs_tool = FileReadTool()

data_api_key = os.getenv("BRIGHT_DATA_API_KEY")

@st.cache_resource
def load_llm():
    llm = LLM(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))

    return llm

# =============================================================================
# Define Agents & Task
# =============================================================================
def create_agents_and_tasks():
    """Creates a Crew for analysis of channel scrapped output"""

    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)

    analysis_agent = Agent(
        role=config["agents"][0]["role"],
        goal=config["agents"][0]["goal"],
        backstory=config["agents"][0]["backstory"],
        verbose=True,
        tools=[docs_tool],
        llm=load_llm()
    )

    response_synth_agent = Agent(
        role=config["agents"][1]["role"],
        goal=config["agents"][1]["goal"],
        backstory=config["agents"][1]["backstory"],
        verbose=True,
        llm=load_llm()
    )

    analysis_task = Task(
        description=config["task"][0]["description"],
        expected_output=config["task"][0]["expected_output"],
        agent=analysis_agent
    )

    response_task = Task(
        description=config["task"][1]["description"],
        expected_output=config["task"][1]["expected_output"],
        agent=response_synth_agent
    )

    crew = Crew(
        agents=[analysis_agent, response_synth_agent],
        tasks=[analysis_task, response_task],
        process=Process.sequential,
        verbose=True
    )
    return crew

# =============================================================================
# Streamlit App
# =============================================================================

st.markdown("""YouTube Trend Analysis""")

if "message" not in st.session_state:
    st.session_state.message = [] # Chat history

if "response" not in st.session_state:
    st.session_state.response = None # Response history

if "crew" not in st.session_state:
    st.session_state.crew = None

def reset_chat():
    st.session_state.message = []
    gc.collect()

def start_analysis():
    # Create a status container
    with st.spinner("Scrapping videos... This may take a momment"):
        status_container = st.empty()
        status_container.info("Extracting data from YouTube...")
        channel_snapshot_id = trigger_scraping_channels(data_api_key, st.session_state.youtube_channels, 10, st.session_state.start_date, st.session_state.end_date, "Latest", "")
        status = get_progress(data_api_key, channel_snapshot_id['snapshot_id'])

        while status['status'] != "ready":
            status_container.error(f"Scrapping failed: {status}")
            return
    
    if status['status'] == "ready":
        status_container.success("Scrapping completed successfully")
        # Show a list of Youtube videos here in a scrollable container
        channel_scrapped_output = get_output(data_api_key. status['snapshot_id'], format="json")