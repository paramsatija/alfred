"""One-time setup: create the ALFRED Managed Agent and Environment.

Run this once:
    python -m alfred.setup_agent

It will:
  1. Create the ALFRED agent on Anthropic's cloud
  2. Create the execution environment (container config)
  3. Print the IDs to add to your .env file
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import anthropic
from alfred.config import Config
from alfred.brain.agent import create_agent


def main():
    if not Config.ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)

    if Config.has_agent():
        print(f"Agent already configured:")
        print(f"  ALFRED_AGENT_ID={Config.AGENT_ID}")
        print(f"  ALFRED_ENVIRONMENT_ID={Config.ENVIRONMENT_ID}")
        print()
        response = input("Create a new agent anyway? (y/N): ").strip().lower()
        if response != "y":
            print("Keeping existing agent.")
            return

    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    try:
        agent_id, env_id = create_agent(client)
    except anthropic.APIError as e:
        print(f"ERROR: Failed to create agent: {e}")
        print()
        print("Make sure your Anthropic API key has access to the Managed Agents beta.")
        print("Check: https://platform.claude.com/docs/en/managed-agents/quickstart")
        sys.exit(1)

    print()
    print("=" * 60)
    print("  ALFRED Managed Agent created successfully!")
    print("=" * 60)
    print()
    print("Add these to your .env file:")
    print()
    print(f"  ALFRED_AGENT_ID={agent_id}")
    print(f"  ALFRED_ENVIRONMENT_ID={env_id}")
    print()

    # Try to auto-append to .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                content = f.read()

            updates = []
            if "ALFRED_AGENT_ID=" in content:
                content = "\n".join(
                    f"ALFRED_AGENT_ID={agent_id}" if line.startswith("ALFRED_AGENT_ID=") else line
                    for line in content.split("\n")
                )
            else:
                updates.append(f"ALFRED_AGENT_ID={agent_id}")

            if "ALFRED_ENVIRONMENT_ID=" in content:
                content = "\n".join(
                    f"ALFRED_ENVIRONMENT_ID={env_id}" if line.startswith("ALFRED_ENVIRONMENT_ID=") else line
                    for line in content.split("\n")
                )
            else:
                updates.append(f"ALFRED_ENVIRONMENT_ID={env_id}")

            if updates:
                content = content.rstrip("\n") + "\n" + "\n".join(updates) + "\n"

            with open(env_path, "w") as f:
                f.write(content)

            print("  .env updated automatically.")
        except IOError:
            print("  Could not auto-update .env — please add the values manually.")
    else:
        print("  No .env file found — copy .env.example to .env and add these values.")

    print()
    print("Now start ALFRED:")
    print("  python -m alfred.main")


if __name__ == "__main__":
    main()
