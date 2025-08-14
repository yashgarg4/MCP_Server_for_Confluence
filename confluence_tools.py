import os
from dotenv import load_dotenv
from atlassian import Confluence
from atlassian.errors import ApiError
from crewai.tools import tool
from typing import Optional

# Load environment variables from the .env file
load_dotenv()

# Initialize the Confluence client once
confluence_client = None
try:
    confluence_client = Confluence(
        url=os.getenv("CONFLUENCE_SERVER"),
        username=os.getenv("CONFLUENCE_USERNAME"),
        password=os.getenv("CONFLUENCE_API_TOKEN")
    )
    print("\n✅ Confluence client initialized.")
except Exception as e:
    print(f"Warning: Failed to initialize Confluence client in confluence_tools.py: {e}")
    confluence_client = None

@tool("Confluence Page Retriever Tool")
def get_page_details(page_id: str) -> str:
    """
    Retrieves the details of a specific Confluence page by its ID.
    The input must be a valid Confluence page ID, not the page title.
    Returns a string with the page's title, content, and the space it belongs to.
    """
    if not confluence_client:
        return "Error: Confluence client is not initialized. Check your .env configuration."
    try:
        page = confluence_client.get_page_by_id(page_id, expand='body.storage,space')
        content = page['body']['storage']['value']
        title = page['title']
        space_key = page['space']['key']

        return f"Successfully retrieved Confluence page details.\nTitle: {title}\nSpace: {space_key}\nContent:\n{content}"
    except ApiError as e:
        if e.response.status_code == 404:
            return f"Error: Page with ID '{page_id}' was not found. Please provide a correct page ID."
        return f"Error: An API error occurred while retrieving page '{page_id}'. Details: {e.text}"
    except Exception as e:
        return f"An unexpected error occurred while retrieving page '{page_id}': {e}"

@tool("Confluence Page Searcher Tool")
def search_pages(query: Optional[str] = None, space_key: Optional[str] = None) -> str:
    """
    Searches for Confluence pages based on a text query.
    The input can be a text search query string ('query') and/or a 'space_key' to limit the search.
    If only a 'space_key' is provided, it will find all pages in that space.
    Returns a list of pages found with their titles and IDs.
    """
    if not confluence_client:
        return "Error: Confluence client is not initialized. Check your .env configuration."
    try:
        cql_parts = ['type = "page"']
        if query:
            cql_parts.append(f'text ~ "{query}"')
        if space_key:
            cql_parts.append(f'space = "{space_key}"')

        if len(cql_parts) == 1:
            return "Error: You must provide either a search query or a space key."

        cql = " and ".join(cql_parts)
        results = confluence_client.cql(cql, limit=50)

        if not results['results']:
            return f"No pages found for the search criteria."
        
        output = "Found the following pages:\n"
        for result in results['results']:
            page_title = result['content']['title']
            page_id = result['content']['id']
            output += f"  - Title: {page_title}, ID: {page_id}\n"
        
        return output
    except Exception as e:
        return f"An unexpected error occurred while searching for pages: {e}"

@tool("Confluence Page Creator Tool")
def create_page(space_key: str, title: str, body: str, parent_page_id: Optional[str] = None) -> str:
    """
    Creates a new Confluence page in a specified space with a given title and body content.
    The input should be a 'space_key', a 'title' for the new page, and the 'body' content.
    An optional 'parent_page_id' can be provided to create a child page.
    Returns the URL and ID of the newly created page.
    """
    if not confluence_client:
        return "Error: Confluence client is not initialized. Check your .env configuration."
    try:
        new_page = confluence_client.create_page(
            space=space_key,
            title=title,
            body=body,
            parent_id=parent_page_id
        )
        page_id = new_page['id']
        page_url = f"{os.getenv('CONFLUENCE_SERVER')}{new_page['_links']['webui']}"
        return f"Successfully created a new Confluence page! Title: '{title}', ID: '{page_id}', URL: {page_url}"
    except ApiError as e:
        if e.response.status_code == 404:
            return f"Error: Space with key '{space_key}' was not found. Please provide a correct space key."
        return f"Error: An API error occurred while creating page. Details: {e.text}"
    except Exception as e:
        return f"An unexpected error occurred while creating a page: {e}"

@tool("Confluence Page Deleter Tool")
def delete_page(page_id: str) -> str:
    """
    Deletes a specific Confluence page by its ID.
    The input must be a valid Confluence page ID.
    Returns a success message upon successful deletion or an error message.
    """
    if not confluence_client:
        return "Error: Confluence client is not initialized. Check your .env configuration."
    try:
        confluence_client.remove_page(page_id)
        return f"Successfully deleted page with ID '{page_id}'."
    except ApiError as e:
        if e.response.status_code == 404:
            return f"Error: Page with ID '{page_id}' was not found. Please provide a correct page ID."
        return f"Error: An API error occurred while deleting page '{page_id}'. Details: {e.text}"
    except Exception as e:
        return f"An unexpected error occurred while deleting page '{page_id}': {e}"

@tool("Confluence Page Updater Tool")
def update_page(page_id: str, title: Optional[str] = None, body: Optional[str] = None) -> str:
    """
    Updates the title or body of a Confluence page.
    The input must be a valid page ID and at least one of the following: a new 'title' or a new 'body'.
    Returns a success message with the URL to the updated page.
    """
    if not confluence_client:
        return "Error: Confluence client is not initialized. Check your .env configuration."
    if not (title or body):
        return "Error: You must provide either a new title or a new body to update the page."
    try:
        page = confluence_client.get_page_by_id(page_id)
        current_title = page['title']
        current_space = page['space']['key']
        current_body = confluence_client.get_page_by_id(page_id, expand='body.storage')['body']['storage']['value']
        
        updated_title = title if title else current_title
        updated_body = body if body else current_body
        
        confluence_client.update_page(
            parent_id=None,
            page_id=page_id,
            title=updated_title,
            body=updated_body,
            representation='storage',
        )
        
        page_url = f"{os.getenv('CONFLUENCE_SERVER')}{confluence_client.get_page_by_id(page_id)['_links']['webui']}"
        return f"Successfully updated page with ID '{page_id}'. New Title: '{updated_title}'. URL: {page_url}"
    except ApiError as e:
        if e.response.status_code == 404:
            return f"Error: Page with ID '{page_id}' was not found. Please provide a correct page ID."
        return f"Error: An API error occurred while updating page '{page_id}'. Details: {e.text}"
    except Exception as e:
        return f"An unexpected error occurred while updating page '{page_id}': {e}"

@tool("Confluence Comment Adder Tool")
def add_comment_to_page(page_id: str, comment_body: str) -> str:
    """
    Adds a comment to an existing Confluence page.
    The input must be a valid page ID and the 'comment_body' text.
    Returns a success message with the URL of the page.
    """
    if not confluence_client:
        return "Error: Confluence client is not initialized. Check your .env configuration."
    try:
        formatted_comment_body = f"<div>{comment_body}</div>"
        confluence_client.add_comment(
            page_id,
            formatted_comment_body
        )
        page_url = f"{os.getenv('CONFLUENCE_SERVER')}{confluence_client.get_page_by_id(page_id)['_links']['webui']}"
        return f"Successfully added a comment to page with ID '{page_id}'. URL: {page_url}"
    except ApiError as e:
        if e.response.status_code == 404:
            return f"Error: Page with ID '{page_id}' was not found. Please provide a correct page ID."
        return f"Error: An API error occurred while adding a comment to page '{page_id}'. Details: {e.text}"
    except Exception as e:
        return f"An unexpected error occurred while adding a comment to page '{page_id}': {e}"
    
@tool("Confluence Space Creator Tool")
def create_space(space_key: str, space_name: str) -> str:
    """
    Creates a new Confluence space with a given key and name.
    The input requires a 'space_key' (a unique identifier, e.g., 'DEV'), a 'space_name' (e.g., 'Development Team').
    Returns a success message with the key of the newly created space.
    """
    if not confluence_client:
        return "Error: Confluence client is not initialized. Check your .env configuration."
    try:
        confluence_client.create_space(space_key, space_name)
        return f"Successfully created a new Confluence space with key '{space_key}' and name '{space_name}'."
    except ApiError as e:
        if e.response.status_code == 409: # 409 Conflict typically means the space already exists
            return f"Error: A space with key '{space_key}' already exists. Please choose a different key."
        return f"Error: An API error occurred while creating the space '{space_key}'. Details: {e.text}"
    except Exception as e:
        return f"An unexpected error occurred while creating the space '{space_key}': {e}"

