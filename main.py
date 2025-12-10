# Import asyncio for running asynchronous code
import asyncio

# Import os for environment variable access
import os

# Import AssistantAgent for multi-agent task execution
from autogen_agentchat.agents import AssistantAgent

# Import OpenAIChatCompletionClient to connect to OpenAI LLMs
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Import ModelInfo to define model metadata
from autogen_core.models import ModelInfo

# Import Console to stream outputs in the terminal
from autogen_agentchat.ui import Console

# Import RoundRobinGroupChat to orchestrate multiple agents
from autogen_agentchat.teams import RoundRobinGroupChat

# Import termination condition based on text mentions
from autogen_agentchat.conditions import TextMentionTermination

# Import MCP workbench and server parameters for automation
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams


# ------------------ ENV VARIABLES ------------------

# Set OpenAI API key from environment variable
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

# Set Jira instance URL from environment variable
os.environ["JIRA_URL"] = os.getenv("JIRA_URL", "")

# Set Jira username/email from environment variable
os.environ["JIRA_USERNAME"] = os.getenv("JIRA_USERNAME", "")

# Set Jira API token from environment variable
os.environ["JIRA_API_TOKEN"] = os.getenv("JIRA_API_TOKEN", "")

# Set Jira project filter, defaulting to "AATC" if not provided
os.environ["JIRA_PROJECTS_FILTER"] = os.getenv("JIRA_PROJECTS_FILTER", "AATC")


# ------------------ MAIN ASYNC FUNCTION ------------------

# Define main asynchronous function
async def main():

    # ------------------ MODEL CLIENT ------------------

    # Initialize OpenAI LLM client with structured output and Gemini-2.5-flash model
    model_client = OpenAIChatCompletionClient(
        model="gemini-2.5-flash",
        model_info=ModelInfo(
            vision=True,               # Enable image/vision capabilities
            function_calling=True,     # Enable function calling
            json_output=True,          # Structured JSON output
            family="unknown",          # Model family metadata
            structured_output=True     # Enforce structured output parsing
        )
    )

    # ------------------ MCP WORKBENCHES ------------------

    # Configure Jira MCP workbench with Docker container
    JIRA_server_params = StdioServerParams(
        command="docker",  # Docker command to run MCP container
        args=[
            "run", "-i", "--rm",  # Interactive mode, remove container after run
            "--dns", "8.8.8.8", "--dns", "1.1.1.1",  # DNS servers
            "-e", f"JIRA_URL={os.environ['JIRA_URL']}",  # Inject Jira URL
            "-e", f"JIRA_USERNAME={os.environ['JIRA_USERNAME']}",  # Inject Jira username
            "-e", f"JIRA_API_TOKEN={os.environ['JIRA_API_TOKEN']}",  # Inject Jira API token
            "-e", f"JIRA_PROJECTS_FILTER={os.environ['JIRA_PROJECTS_FILTER']}",  # Inject project filter
            "ghcr.io/sooperset/mcp-atlassian:latest"  # MCP Docker image
        ],
        read_timeout_seconds=60  # Timeout for reading MCP responses
    )

    # Instantiate Jira workbench
    JIRA_workbench = McpWorkbench(JIRA_server_params)

    # Configure Playwright MCP workbench
    Playwright_server_params = StdioServerParams(
        command="npx",  # Node.js command to run MCP package
        args=["@playwright/mcp@latest"],  # Latest Playwright MCP package
        read_timeout_seconds=60  # Timeout for reading MCP responses
    )

    # Instantiate Playwright workbench
    Playwright_workbench = McpWorkbench(Playwright_server_params)

    # ------------------ PROMPTS ------------------

    # Prompt for Jira bug analysis agent
    JIRA_prompt = """
You are a Bug Analyst specializing in Jira defect analysis.

Goal: Analyze defects and create comprehensive test scenarios.
1. Retrieve the most recent bugs from the [JIRA PROJECT (Project Key: <PROJECT KEY>].
2. Carefully read through bug titles and descriptions.
3. Identify recurring issues or patterns in bug descriptions.
3. Design a detailed user flow for smoke testing based on these patterns.

Instructions:
- Provide step-by-step manual testing instructions
- Include URLs or page routes
- Describe user actions (clicks, inputs, submissions)
- Specify expected outcomes/validations for each step
- clearly output the final smoke testing steps in a structured format under heading: 'SMOKE TEST SCRIPTS'   
- Give a summary of the actions taken.
- Conclude with the phrase: 'HANDOFF TO AUTOMATION' to signal completion.

    End your analysis with 'HANDOFF TO AUTOMATION'.
"""

    # Prompt for Playwright automation agent
# Prompt for Playwright automation agent using concatenated string for clarity

    Playwright_prompt = """

You are a Playwright automation expert. 

Goal: Analayze the smoke test scripts provided by BugAnalyst and convert it into executable Playwright commands. 

1. After receiving the smoke test scripts from BugAnalyst, carefully read through each step.
2. Translate each manual test step into Playwright MCP commands.
3. Use Playwright MCP tools to execute the smoke test. 
4. Execute the automated test step by step and report results clearly, including any errors or successes. 
5. Take screenshots at key points to document the test execution. 
6. Make sure expected results in the bug are validated in your flow.

Important: Use browser_wait_for to wait for success/error messages
   - Wait for buttons to change state (e.g., 'Applying...' to complete)
   - Verify expected outcomes as specified by Bug_Analyst
   - Always follow the exact timing and waiting instructions provided.

   Complete ALL steps before saying 'TESTING COMPLETE, Execute each step fully, don't rush to completion'.
"""

    # ------------------ AGENTS ------------------

    # Use async context managers to start/stop MCP workbenches cleanly
    async with JIRA_workbench as JIRA_wb, Playwright_workbench as PW_wb:

        # Instantiate Jira bug analysis agent
        JIRA_Agent = AssistantAgent(
            name="Bug_Analyst",
            model_client=model_client,
            workbench=JIRA_wb,
            system_message=JIRA_prompt
        )

        # Instantiate Playwright automation agent
        PLAYWRIGHT_Agent = AssistantAgent(
            name="Automation_Expert",
            model_client=model_client,
            workbench=PW_wb,
            system_message=Playwright_prompt
        )

        # ------------------ ROUND ROBIN CHAT ------------------

        # Multi-agent conversation with round-robin turn-taking
        JIRA_Automation_Team = RoundRobinGroupChat(
            participants=[JIRA_Agent, PLAYWRIGHT_Agent],
            termination_condition=TextMentionTermination("TESTING COMPLETE")  # End chat on this phrase
        )

        # ------------------ TASK ------------------

        # Define task for agents to execute
        task = """
JIRA_Agent:
1. Search for recent bugs in AATC projects
2. Design a stable user flow for smoke testing
3. Use real URLs like: https://rahulshettyacademy.com/seleniumPractise/#/

PLAYWRIGHT_Agent:
Once ready, automate this flow using Playwright MCP and execute it
"""

        # Run the agents and stream output in console
        await Console(JIRA_Automation_Team.run_stream(task=task))

        # Close the model client to release resources
        await model_client.close()


# ------------------ RUN ------------------

# Run the main asynchronous function
asyncio.run(main())
