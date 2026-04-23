"""Claude Managed Agent — autonomous sessions for heavy tasks.

Used for deep research, morning briefings, and building.
Runs on Anthropic's cloud infrastructure in a sandboxed container.

Built-in tools (agent_toolset_20260401):
  - web_search: search the web (replaces Brave Search)
  - web_fetch: fetch any URL content (replaces httpx + BS4 for research)
  - bash: execute shell commands
  - read/write/edit: file operations
  - glob/grep: search files

MCP connector support:
  - Agents can connect to remote MCP servers via URL
  - Auth is handled through vaults at session creation
  - Up to 20 MCP servers per agent

Custom tools:
  - Define tools with JSON schema on the agent
  - Agent emits tool_use events; your code executes and returns results
  - Useful for Slack posting, database queries, etc.
"""

import logging
import anthropic
from alfred.config import Config
from alfred.brain.prompts import AGENT_SYSTEM_PROMPT

log = logging.getLogger("alfred.brain.agent")


def create_agent(client: anthropic.Anthropic) -> tuple[str, str]:
    """Create the ALFRED managed agent and environment. Run once.

    Returns (agent_id, environment_id).
    """
    log.info("Creating ALFRED managed agent...")

    agent = client.beta.agents.create(
        name="ALFRED — AI Chief of Staff",
        model=Config.AGENT_MODEL,
        system=AGENT_SYSTEM_PROMPT,
        tools=[
            {
                "type": "agent_toolset_20260401",
                "configs": [
                    {"name": "web_search", "enabled": True},
                    {"name": "web_fetch", "enabled": True},
                    {"name": "bash", "enabled": True},
                    {"name": "read", "enabled": True},
                    {"name": "write", "enabled": True},
                    {"name": "glob", "enabled": True},
                    {"name": "grep", "enabled": True},
                ],
            },
        ],
    )
    log.info(f"Agent created: {agent.id} (v{agent.version})")

    environment = client.beta.environments.create(
        name="alfred-env",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )
    log.info(f"Environment created: {environment.id}")

    return agent.id, environment.id


def update_agent(client: anthropic.Anthropic, agent_id: str, version: int, **kwargs):
    """Update an existing agent config (increments version).

    Pass only the fields you want to change. Omitted fields are preserved.
    Array fields (tools, mcp_servers, skills) are fully replaced if provided.
    """
    return client.beta.agents.update(agent_id, version=version, **kwargs)


def run_session(task: str, timeout_events: int = 200) -> str:
    """Fire a managed agent session, stream events, return the full text response.

    The agent runs autonomously in a container on Anthropic's cloud.
    It decides which tools to use (web_search, web_fetch, bash, etc.)
    based on the task description.

    Args:
        task: The task/prompt to send to the agent.
        timeout_events: Safety limit to prevent runaway sessions.

    Returns:
        The agent's complete text response.
    """
    if not Config.has_agent():
        return (
            "Managed Agent not configured. "
            "Run `python -m alfred.setup_agent` first."
        )

    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    try:
        session = client.beta.sessions.create(
            agent=Config.AGENT_ID,
            environment_id=Config.ENVIRONMENT_ID,
        )
        log.info(f"Session started: {session.id}")

        result_parts = []
        tools_used = []
        event_count = 0

        with client.beta.sessions.events.stream(session.id) as stream:
            client.beta.sessions.events.send(
                session.id,
                events=[{
                    "type": "user.message",
                    "content": [{"type": "text", "text": task}],
                }],
            )

            for event in stream:
                event_count += 1

                if event.type == "agent.message":
                    for block in event.content:
                        if hasattr(block, "text"):
                            result_parts.append(block.text)

                elif event.type == "agent.tool_use":
                    tool_name = getattr(event, "name", "unknown")
                    tools_used.append(tool_name)
                    log.info(f"Agent using tool: {tool_name}")

                elif event.type == "session.status_idle":
                    log.info(
                        f"Session complete. Events: {event_count}, "
                        f"Tools: {tools_used}"
                    )
                    break

                elif event.type == "session.error":
                    error_msg = getattr(event, "message", str(event))
                    log.error(f"Session error: {error_msg}")

                if event_count >= timeout_events:
                    log.warning(f"Session hit event limit ({timeout_events})")
                    break

        return "".join(result_parts) if result_parts else "Agent completed but produced no text output."

    except anthropic.APIError as e:
        log.error(f"Managed Agent API error: {e}")
        return f"Agent session failed: {e}"
    except Exception as e:
        log.error(f"Unexpected error in agent session: {e}", exc_info=True)
        return f"Agent session error: {e}"
