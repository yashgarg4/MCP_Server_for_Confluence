import streamlit as st
import requests
import json
import os

# --- Configuration ---
# If FastAPI app is deployed elsewhere, update this URL.
FASTAPI_ENDPOINT = os.getenv("FASTAPI_BACKEND_URL", "http://127.0.0.1:8000/invoke")

# --- Streamlit UI ---
st.set_page_config(page_title="Confluence Agent Interface", layout="centered")

st.title("🚀 Confluence Agent Interface")

st.subheader("💡 How to use the Agent:")
with st.expander("Click to see available commands and examples"):
    st.markdown("""
    This agent can interact with **Confluence** using the following capabilities:

    ### Confluence Tools

    * **Confluence Space Creator Tool**: Create a new Confluence space.
        * _Example:_ `Create a new Confluence space with the key 'NB' and name 'Notebooks'.`

    * **Confluence Page Creator Tool**: Create a new page in a specified space.
        * _Example:_ `Create a new page in space 'NB' with title 'My First Page' and body 'This is the content of my first page.'`

    * **Confluence Page Retriever Tool**: Get the content and details of a Confluence page.
        * _Example:_ `Get the details of Confluence page with ID '12345'.`

    * **Confluence Page Searcher Tool**: Find Confluence pages based on a query or space key.
        * _Example:_ `Search for pages in space 'NB' that contain the word 'planning'.`

    * **Confluence Page Updater Tool**: Update the title or body of an existing page.
        * _Example:_ `Update the title of page '12345' to 'New Project Plan'.`

    * **Confluence Comment Adder Tool**: Add a comment to a Confluence page.
        * _Example:_ `Add a comment to Confluence page '12345' with the body 'This is a test comment.'`

    * **Confluence Page Deleter Tool**: Delete a specific Confluence page.
        * _Example:_ `Delete Confluence page with ID '12345'.`
    """)

# Text input for the user's prompt
request_prompt = st.text_area(
    "Enter your request for the agent:",
    height=150,
    placeholder="e.g., Create a new Confluence space with key 'PROJ' and name 'Project Documentation' and then create a page within it titled 'Project Overview' with a brief introduction."
)

if st.button("Send Request"):
    if request_prompt:
        try:
            with st.spinner("Agent is working..."):
                # Prepare the payload for the FastAPI endpoint
                payload = {"prompt": request_prompt}
                
                # Make the POST request to the FastAPI server
                response = requests.post(FASTAPI_ENDPOINT, json=payload)
                
                if response.status_code == 200:
                    response_json = response.json()
                    agent_output = "No response content found."

                    # Check for the top-level 'response' key from the FastAPI wrapper
                    if 'response' in response_json:
                        crewai_output = response_json['response']
                        
                        # Now, check the CrewAI output for the final message
                        if 'raw' in crewai_output:
                            agent_output = crewai_output['raw']
                        elif 'tasks_output' in crewai_output and isinstance(crewai_output['tasks_output'], list) and len(crewai_output['tasks_output']) > 0:
                            agent_output = crewai_output['tasks_output'][0].get('raw', 'No response content found in tasks_output.')
                        else:
                            agent_output = "The agent returned a response, but the content key ('raw' or 'tasks_output') was not found."

                    # logic to remove the URL and ID from the agent's output ---
                    # First, split the string by the page content marker
                    page_content_marker = "The page contains the text:"
                    before_content = agent_output
                    page_content = ""

                    if page_content_marker in agent_output:
                        parts = agent_output.split(page_content_marker)
                        before_content = parts[0]
                        page_content = page_content_marker + parts[1]

                    # Now, clean up the `before_content` part by removing ID and URL
                    url_keywords = [" with ID ", " and URL is ", ". atlassian.net"]
                    for keyword in url_keywords:
                        if keyword in before_content:
                            before_content = before_content.split(keyword)[0]
                            # Handle the trailing period
                            if before_content.endswith('.'):
                                before_content = before_content[:-1]
                            break
                    
                    # Reconstruct the final output
                    agent_output = (before_content + page_content).strip()
                    # Display the agent's response
                    st.success("Request Successful!")
                    st.markdown(agent_output)
                else:
                    st.error(f"Error from agent: Status Code {response.status_code}")
                    # Try to get a more user-friendly error message from the JSON response
                    error_details = response.json().get('detail', 'Unknown error occurred.')
                    st.write(f"Details: {error_details}")
                    st.json(response.json())
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the FastAPI server. Please ensure it is running at "
                     f"`{FASTAPI_ENDPOINT}`.")
        except json.JSONDecodeError:
            st.error("Received an invalid JSON response from the server.")
            st.write(response.text) # Show raw text if JSON decoding fails
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
    else:
        st.warning("Please enter a request before sending.")

st.markdown("---")