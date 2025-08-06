from fastmcp import FastMCP
import requests
import json
from dataclasses import dataclass

mcp = FastMCP("MCP_Agents")
agents = []

@dataclass
class Agent:
    method: str
    id: str
    description: str
    summary: str
    url: str

@mcp.tool()
def list_agents() -> list[Agent]:
    """
    Returns a list of available agents with their details.
    """
    if agents:
        return agents
    
    agent_api_url = "http://localhost:8005/openapi.json"
    response = requests.get(agent_api_url)
    if response.status_code == 200:
        api_spec = response.json()
        paths = api_spec.get("paths", {})
        for path in paths:
            for method, details in paths[path].items():
                print(f"Method: {method.upper()}, Path: {path}")
                agent = Agent(
                    method=method.upper(),
                    id=details.get("operationId", "unknown"),
                    description=details.get("description", "No description available"),
                    summary=details.get("summary", "No summary available"),
                    url=f"http://localhost:8005{path}"
                )
                agents.append(agent)
        return agents
    else:
        print(f"Error fetching API spec: {response.status_code}")

    return {}

@mcp.tool()
def execute_agent(agent_id: str, content: str = None) -> str:
    """
    Executes the specified agent.

    Args:
        id (str): The ID of the agent to execute.
        content (str): The content to send to the agent.

    """
    for agent in agents:
        if agent.id == agent_id:
            if agent.method == "POST":
                # Prepare the request payload
                payload = {"content": content}
                
                # Make the REST call
                try:
                    response = requests.post(
                        agent.url,
                        headers={"Content-Type": "application/json"},
                        data=json.dumps(payload),
                        stream=True
                    )
                    response.raise_for_status()
                    
                    # Stream the response
                    result = ""
                    for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                        if chunk:
                            result += chunk
                            print(chunk, end="")
                    
                    return result
                
                except requests.exceptions.RequestException as e:
                    return f"Error executing agent: {str(e)}"
            elif agent.method == "GET":
                # Make the REST call
                try:
                    response = requests.get(agent.url)
                    response.raise_for_status()
                    
                    return response.text
                except requests.exceptions.RequestException as e:
                    return f"Error executing agent: {str(e)}"

    return "Agent not found"

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)


