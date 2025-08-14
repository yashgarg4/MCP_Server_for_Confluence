import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from crewai import Agent, Crew, Process, Task, LLM
from fastapi.responses import JSONResponse
import threading

# Import our custom tools and the client
from confluence_tools import (
    create_page,
    search_pages,
    get_page_details,
    delete_page,
    update_page,
    add_comment_to_page,
    create_space,
    confluence_client
)

# Load environment variables
load_dotenv()

# Pydantic Model for Request Body
class ConfluenceTaskRequest(BaseModel):
    prompt: str  # The main input is a natural language prompt

# FastAPI App Initialization
app = FastAPI(
    title="Confluence MCP Server",
    description="A Multi-agent Collaboration Platform for interacting with Confluence.",
)

# Global variables for Agent and LLM, to be initialized lazily
confluence_crew = None
crew_initialization_lock = threading.Lock()

def _initialize_crew():
    """
    Initializes the CrewAI components. This function is called lazily on the first request.
    It is guarded by a lock to ensure it only runs once, even with concurrent requests.
    """
    global confluence_crew
    with crew_initialization_lock:
        if confluence_crew is not None:
            return  # Already initialized by another thread

        print("\n⏳ First request received. Initializing CrewAI components (this may take a moment)...")

        # Initialize the LLM
        try:
            llm = LLM(
                model="gemini/gemini-1.5-flash-latest",
                temperature=0.1,
                api_key=os.getenv("GEMINI_API_KEY")
            )
            print("✅ LLM initialized successfully.")
        except Exception as e:
            print(f"Error initializing LLM: {e}")
            return

        # Define a capable agent that can use multiple tools
        confluence_expert = Agent(
            role="Confluence Expert",
            goal="Understand user requests, use the available tools to find information in Confluence or create new pages, and provide clear, helpful answers.",
            backstory=(
                "You are a dedicated Confluence expert. Your goal is to manage and interact with "
                "Confluence spaces and pages using natural language commands. You must be precise in "
                "identifying the correct tool and all its required arguments from the user's prompt. "
                "You have the ability to retrieve, search for, create, update, delete pages, and add comments."
            ),
            tools=[
                get_page_details, 
                search_pages, 
                create_page,
                delete_page,
                update_page,
                add_comment_to_page,
                create_space
            ],
            allow_delegation=False,
            verbose=True,
            llm=llm,
        )
        
        # Define the task for the agent
        analysis_task = Task(
            description="Run a prompt given by the user.",
            expected_output="A helpful and accurate answer to the user's request, based on the information retrieved from Confluence or the action performed. "
                            "The answer should be a concise summary if multiple items are found, or a confirmation of the created page.",
            agent=confluence_expert,
        )
        
        # Create the Crew
        confluence_crew = Crew(
            agents=[confluence_expert], 
            tasks=[analysis_task], 
            process=Process.sequential, 
            verbose=True
        )
        print("✅ CrewAI crew initialized successfully.")


# Crew Execution Logic
def run_crew(prompt: str) -> str:
    """Initializes and runs the Confluence crew for a given prompt."""
    global confluence_crew
    
    if confluence_crew is None:
        _initialize_crew()

    if not confluence_client:
        return "Error: The Confluence client is not initialized. Please check your .env file."
    
    if not confluence_crew:
        return "Error: The CrewAI crew is not initialized."
    
    # Update the task description with the new prompt
    confluence_crew.tasks[0].description = prompt
    
    return confluence_crew.kickoff()


# API Endpoints
@app.post("/invoke")
async def invoke_agent(request: ConfluenceTaskRequest):
    """Endpoint to invoke the Confluence agent with a natural language prompt."""
    try:
        if not request.prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
        result = run_crew(request.prompt)
        return {"response": result}
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Welcome to the Confluence MCP Server! Server is ready."}

@app.get("/context/spaces", tags=["MCP Context API"])
def get_all_spaces():
    """
    MCP-compatible context documents for all accessible Confluence spaces.
    Returns a list of structured JSON objects, one per space.
    """
    if not confluence_client:
        raise HTTPException(status_code=500, detail="Confluence client is not initialized.")
    try:
        spaces_response = confluence_client.get_all_spaces(start=0, limit=50, expand='name')
        
        result = []
        if 'results' in spaces_response:
            for space in spaces_response['results']:
                result.append({
                    "type": "space",
                    "key": space['key'],
                    "name": space['name'],
                    "id": space['id'] if 'id' in space else space['key'], # Fallback to key if id not present
                    "url": f"{os.getenv('CONFLUENCE_SERVER')}/wiki/spaces/{space['key']}"
                })
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving spaces: {str(e)}")

@app.get("/context/pages/{space_key}", tags=["MCP Context API"])
def get_all_pages_in_space(space_key: str):
    """
    MCP-compatible context documents for all pages in a given space.
    Returns a list of structured JSON objects, one per page.
    """
    if not confluence_client:
        raise HTTPException(status_code=500, detail="Confluence client is not initialized.")
    try:
        pages_response = confluence_client.get_all_pages_from_space(space_key, start=0, limit=50, expand='history')
        
        result = []
        for page in pages_response:
            result.append({
                "type": "page",
                "id": page['id'],
                "title": page['title'],
                "space_key": space_key,
                "url": f"{os.getenv('CONFLUENCE_SERVER')}/wiki/spaces/{space_key}/pages/{page['id']}"
            })
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving pages: {str(e)}")
