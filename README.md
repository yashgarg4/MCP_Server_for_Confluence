# Confluence MCP Server

This project provides a powerful, natural language interface for interacting with Confluence. It uses a CrewAI agent powered by Google's Gemini model to understand user prompts and perform actions like creating, searching, and managing Confluence spaces and pages.

The backend is built with FastAPI, and a user-friendly web interface is provided with Streamlit.

## 🚀 Features

The agent can understand natural language requests to perform the following Confluence actions:

- **Create Space**: Create a new Confluence space with a given key and name.
- **Create Page**: Create a new page within a specified space with a title and body.
- **Update Page**: Update the title or body of an existing page.
- **Search Pages**: Find pages based on a query or space key.
- **Get Page Details**: Retrieve the content and details of a specific Confluence page by its ID.
- **Add Comments**: Add comments to an existing page.
- **Delete Pages**: Delete a specific page by its ID.
- **Expose Context API**: Provides structured JSON data about Confluence spaces and pages through dedicated endpoints, making it easy for other tools and agents to consume Confluence information.

## 🏛️ Architecture

The application consists of two main components that work together:

1.  **FastAPI Backend (`main.py`)**:

    - Exposes an agent endpoint (/invoke) for natural language processing.
    - Exposes a set of context endpoints (/context/...) for serving raw, structured Confluence data.
    - Receives a natural language prompt.
    - Initializes a CrewAI agent ("Confluence Expert").
    - The agent uses the Gemini LLM to decide which Confluence tool to use based on the prompt.
    - Executes the tool and returns the result.

2.  **Streamlit Frontend (`streamlit_app.py`)**:
    - Provides a simple web UI to enter a prompt.
    - Sends the prompt to the FastAPI backend.
    - Displays the agent's final response.

## 🔌 API Endpoints

The FastAPI server exposes the following endpoints. You can also explore them interactively via the auto-generated documentation at http://127.0.0.1:8000/docs when the server is running.

- +### Agent Invocation
- +- `POST /invoke`
- - **Description**: The primary endpoint to interact with the CrewAI agent. It accepts a natural language prompt and returns the agent's final response.
- - **Request Body**: `{"prompt": "your request here"}`
- - **Response Body**: `{"response": "agent's text response"}`
- +### MCP Context API
  These endpoints provide raw, structured data directly from Confluence, formatted for easy consumption by other applications or agents.
- +-  `GET /context/spaces`
- - **Description**: Retrieves a list of all accessible Confluence spaces.
- - **Example**: curl http://127.0.0.1:8000/context/spaces

- +-  `GET /context/pages/{space_key}`
- - **Description**: Retrieves a list of all pages for a specific Confluence space.
- - **Example**: curl http://127.0.0.1:8000/context/pages/NB

## 🛠️ Setup and Installation

Follow these steps to get the project running locally.

### 1. Prerequisites

- Python 3.9+
- Git

### 2. Clone the Repository

```bash
git clone <your-repository-url>
cd confluence-mcp-server
```

### 3. Set Up a Virtual Environment

It's highly recommended to use a virtual environment.

```bash
# For Windows
python -m venv venv
.\venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

Install all the required Python packages from `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the root of the project by copying the example file:

```bash
cp .env.example .env
```

Now, open the `.env` file and fill in your specific credentials:

```dotenv
# .env

# Confluence Configuration
CONFLUENCE_SERVER=https://your-domain.atlassian.net
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_API_TOKEN=your_confluence_api_token

# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key

# Backend URL for Streamlit (optional, defaults to localhost)
FASTAPI_BACKEND_URL=http://127.0.0.1:8000/invoke
```

- **CONFLUENCE_API_TOKEN**: You can generate this from your Atlassian account settings.
- **GEMINI_API_KEY**: You can get this from Google AI Studio.

## ▶️ Running the Application

You need to run the backend and frontend in two separate terminals.

### 1. Start the FastAPI Backend

In your first terminal, run:

```bash
uvicorn main:app --reload
```

The server will be available at `http://127.0.0.1:8000`.

### 2. Start the Streamlit Frontend

In your second terminal, run:

```bash
streamlit run streamlit_app.py
```

Your browser should automatically open to the Streamlit interface.

## 💡 How to Use

Once the application is running, navigate to the Streamlit URL and type your request into the text area.

**Examples:**

- `Create a new Confluence space with the key 'TEAM' and name 'Team Wiki'.`
- `Create a new page in space 'NB' with title 'Meeting Notes' and body 'Today we discussed project timelines.'`
- `Get the details of Confluence page with ID '12345'.`
- `Search for pages in the 'NB' space that mention 'project timelines'.`
- `Add a comment to Confluence page '12345': 'This document is ready for review.'`
