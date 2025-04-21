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
            time.sleep(10)
            status = get_progress(data_api_key, channel_snapshot_id['snapshot_id'])
            
            if status['status'] == "failed":
                status_container.info(f"Current status: {status['status']}")
               return
    
        if status['status'] == "ready":
            status_container.success("Scrapping completed successfully")
            # Show a list of Youtube videos here in a scrollable container
            channel_scrapped_output = get_output(data_api_key. status['snapshot_id'], format="json")

            st.markdown("### YouTube Videos")
            # Create a container for the carousel
            carousel_container = st.container()

            # Calculate number of videos per row (adjust as needed)
            videos_per_row = 3

            with carousel_container:
                # Calculate number of rows needed
                num_videos = len(channel_scrapped_output[0])
                num_rows = (num_videos + videos_per_row - 1) // videos_per_row

                for row in range(num_rows):
                    # Create a row container
                    cols = st.columns(videos_per_row)

                    # Fill each column with a video
                    for col_idx in range(videos_per_row):
                        video_idx = row * videos_per_row + col_idx
                        
                        # Check if we still have videos to display
                        if video_idx < num_videos:
                            with cols[col_idx]:
                                st.video(channel_scrapped_output[0][video_idx]['url'])

            status_container.info("Processing transcript...")
            st.session_state.all_files = []
            # Calculate transcripts
            for i in tqdm(range(len(channel_scrapped_output[0]))):
                # Save transcript to a file
                youtube_video_id = channel_scrapped_output[0][i]['shortcode']

                file = "transcript/" + youtube_video_id + ".txt"
                st.session_state.all_files.append(file)

                with open(file, "w") as f:
                    for j in range(len(channel_scrapped_output[0][i]['formatted_script'])):
                        text = channel_scrapped_output[0][i]['formatted_script'][j]['text']
                        start_time = channel_scrapped_output[0][i]['formatted_script'][j]['start_time']
                        end_time = channel_scrapped_output[0][i]['formatted_script'][j]['end_time']
                        f.write(f"{start_time:.2f} - {end_time:.2f}: {text}\n")

                    f.close()
                
            st.session_state.channel_scrapped_output = channel_scrapped_output
            status_container.success("Scrapping complete! We shall now analyze the videos and report trends...")

        else:
            status_container.error(f"Scrapping failed with status : {status}")

    if status['status'] == "ready":
        status_container = st.empty()
        with st.spinner('The agent is analyzing the videos... This may take a moment'):
            # Create crew
            st.session_state.crew = create_agents_and_tasks()
            st.session_state.response = st.session_state.crew.kickoff(inputs = {"file_paths": ", ".join(st.session_state.all_files)})

# =============================================================================
# Sidebar
# =============================================================================
with st.sidebar:
    st.header("Youtube Channels")

    # Initialize the channels list in session state if it doesn't exist
    if "youtube_channels" not in st.session_state:
        st.session_state.youtube_channels = [""] # Start with empty field
    
    # Function to add new channel field
    def add_channel_field():
        st.session_state.youtube_channels.append("")
    
    # Create input fields for each channel
    for i, channel in enumerate(st.session_state.youtube_channels):
        col1, col2 = st.columns([6, 1])
        with col1:
            st.session_state.youtube_channels[i] = st.text_input(
                f"Channel URL",
                 value=channel,
                 key = f"channel_{i}",
                 label_visibility="collapsed"
            )