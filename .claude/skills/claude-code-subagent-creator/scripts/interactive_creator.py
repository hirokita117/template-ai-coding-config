#!/usr/bin/env python3
"""
Interactive Claude Code subagent creator.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional
from create_subagent import SubagentCreator


def get_input(prompt: str, default: Optional[str] = None) -> str:
    """Get user input with optional default value.
    
    Args:
        prompt: The prompt to display
        default: Optional default value
        
    Returns:
        User input or default value
    """
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    response = input(full_prompt).strip()
    
    if not response and default:
        return default
    
    return response


def get_multiline_input(prompt: str) -> str:
    """Get multiline input from user.
    
    Args:
        prompt: The prompt to display
        
    Returns:
        Multiline user input
    """
    print(f"{prompt} (Enter 'END' on a new line to finish):")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)
    
    return "\n".join(lines)


def get_tools_input(available_tools: List[str]) -> Optional[List[str]]:
    """Get tools selection from user.
    
    Args:
        available_tools: List of available tools
        
    Returns:
        Selected tools or None for all tools
    """
    print("\nAvailable tools:")
    for i, tool in enumerate(available_tools, 1):
        print(f"  {i}. {tool}")
    
    print("\nSelect tools (comma-separated numbers, or 'all' for all tools, or 'none' to inherit):")
    response = input("> ").strip().lower()
    
    if response == "none" or not response:
        return None
    elif response == "all":
        return available_tools
    else:
        selected = []
        try:
            indices = [int(x.strip()) - 1 for x in response.split(",")]
            for idx in indices:
                if 0 <= idx < len(available_tools):
                    selected.append(available_tools[idx])
        except (ValueError, IndexError):
            print("Invalid selection. Using all tools.")
            return available_tools
        
        return selected if selected else None


def main():
    """Main interactive flow."""
    print("🤖 Claude Code Subagent Creator")
    print("=" * 50)
    print("This tool will help you create a specialized subagent for Claude Code.")
    print()
    
    # Get basic information
    name = get_input("Enter subagent name (e.g., 'test-runner', 'code-reviewer')")
    if not name:
        print("Error: Name is required")
        sys.exit(1)
    
    # Ensure valid name format
    name = name.lower().replace(" ", "-").replace("_", "-")
    
    print("\nDescribe what this subagent should do:")
    requirements = get_multiline_input("Requirements")
    if not requirements:
        print("Error: Requirements are required")
        sys.exit(1)
    
    # Ask about proactive behavior
    print("\nShould this agent be invoked proactively?")
    print("(Proactive agents are automatically triggered when relevant)")
    proactive_response = get_input("Make proactive? (yes/no)", "no")
    proactive = proactive_response.lower() in ["yes", "y", "true"]
    
    # Select tools
    creator = SubagentCreator()
    tools = get_tools_input(creator.AVAILABLE_TOOLS)
    
    # Select model
    print("\nSelect model for the subagent:")
    print("  1. sonnet (default, balanced)")
    print("  2. opus (more capable)")
    print("  3. haiku (faster, lighter)")
    print("  4. inherit (use same as main conversation)")
    
    model_choice = get_input("Choice (1-4)", "1")
    model_map = {"1": "sonnet", "2": "opus", "3": "haiku", "4": "inherit"}
    model = model_map.get(model_choice, "sonnet")
    
    # Ask about output location
    print("\nWhere should the subagent be saved?")
    print("  1. Project (.claude/agents/) - Shared with team")
    print("  2. User (~/.claude/agents/) - Personal use")
    print("  3. Custom path")
    
    location_choice = get_input("Choice (1-3)", "1")
    
    if location_choice == "1":
        project_path = get_input("Project path", os.getcwd())
        output_path = None
    elif location_choice == "2":
        project_path = None
        user_agents_dir = Path.home() / ".claude" / "agents"
        user_agents_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(user_agents_dir / f"{name}.md")
    else:
        project_path = None
        output_path = get_input("Enter full path for the agent file")
    
    # Create the subagent
    print("\n" + "=" * 50)
    print("Creating subagent...")
    
    creator = SubagentCreator(project_path)
    
    # Generate agent configuration
    agent_config = creator.create_agent_from_requirements(
        name=name,
        requirements=requirements,
        tools=tools,
        model=model,
        proactive=proactive
    )
    
    # Show preview
    print("\nGenerated configuration:")
    print("-" * 30)
    print(f"Name: {agent_config['name']}")
    print(f"Description: {agent_config['description']}")
    print(f"Model: {agent_config.get('model', 'sonnet')}")
    print(f"Tools: {agent_config.get('tools', 'All tools (inherited)')}")
    print("\nSystem Prompt Preview (first 500 chars):")
    print(agent_config['system_prompt'][:500] + "...")
    print("-" * 30)
    
    # Confirm save
    confirm = get_input("\nSave this subagent? (yes/no)", "yes")
    if confirm.lower() not in ["yes", "y"]:
        print("Cancelled.")
        sys.exit(0)
    
    # Save the agent
    file_path = creator.save_agent(agent_config, output_path)
    
    print("\n✅ Success!")
    print(f"Subagent '{name}' has been created at: {file_path}")
    print("\n📝 Next steps:")
    print("1. Review and customize the generated agent file if needed")
    print("2. In Claude Code, use '/agents' to manage your agents")
    print(f"3. Invoke with: 'Use the {name} agent to...'")
    
    if proactive:
        print(f"\n⚡ This agent is proactive and will be automatically triggered when relevant!")


if __name__ == "__main__":
    main()
