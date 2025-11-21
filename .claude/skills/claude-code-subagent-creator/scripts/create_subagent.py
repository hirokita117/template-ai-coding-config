#!/usr/bin/env python3
"""
Create Claude Code subagent from requirements.
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Union
import json


class SubagentCreator:
    """Create Claude Code subagents from requirements."""
    
    # Default tools available in Claude Code
    AVAILABLE_TOOLS = [
        "Read", "Write", "Grep", "Glob", "Bash", "Execute", 
        "Search", "RequestUserInput", "AttemptCompletion", 
        "KeepAlive", "Shell", "Run", "DeleteFile", "ListDirectory",
        "CreateDirectory", "MoveFile"
    ]
    
    # Available model options
    AVAILABLE_MODELS = ["sonnet", "opus", "haiku", "inherit"]
    
    # Available permission modes
    AVAILABLE_PERMISSION_MODES = ["default", "acceptEdits", "bypassPermissions", "plan", "ignore"]

    def __init__(self, project_path: Optional[str] = None):
        """Initialize the SubagentCreator.
        
        Args:
            project_path: Path to the project directory. If None, uses current directory.
        """
        self.project_path = Path(project_path or os.getcwd())
        self.agents_dir = self.project_path / ".claude" / "agents"
    
    def create_agent_from_requirements(
        self,
        name: str,
        requirements: str,
        tools: Optional[List[str]] = None,
        model: str = "sonnet",
        proactive: bool = False,
        permission_mode: str = "default",
        skills: Optional[List[str]] = None,
        color: Optional[str] = None
    ) -> Dict[str, any]:
        """Create a subagent from natural language requirements.
        
        Args:
            name: Name of the subagent
            requirements: Natural language description of what the agent should do
            tools: List of tools the agent should have access to
            model: The model to use (sonnet, opus, haiku, inherit)
            proactive: Whether the agent should be used proactively
            permission_mode: Permission mode for the subagent
            skills: List of skills to auto-load
            color: Optional color identifier for UI display (color name or hex code)
            
        Returns:
            Dictionary containing the generated agent details
        """
        # Generate description from requirements
        description = self._generate_description(requirements, proactive)
        
        # Generate system prompt from requirements
        system_prompt = self._generate_system_prompt(requirements)
        
        # Validate and filter tools
        if tools:
            tools = self._validate_tools(tools)
        
        # Validate model
        if model not in self.AVAILABLE_MODELS:
            print(f"Warning: Unknown model '{model}'. Using 'sonnet' as default.")
            model = "sonnet"

        # Validate permission mode
        if permission_mode not in self.AVAILABLE_PERMISSION_MODES:
            print(f"Warning: Unknown permission mode '{permission_mode}'. Using 'default' as default.")
            permission_mode = "default"
        
        return {
            "name": name,
            "description": description,
            "tools": tools,
            "model": model,
            "permission_mode": permission_mode,
            "skills": skills,
            "color": color,
            "system_prompt": system_prompt
        }
    
    def _generate_description(self, requirements: str, proactive: bool = False) -> str:
        """Generate a description field from requirements.
        
        Args:
            requirements: Natural language requirements
            proactive: Whether to add proactive triggers
            
        Returns:
            Generated description
        """
        # Create a concise description that triggers the agent appropriately
        description = f"Specialized agent for: {requirements[:100]}"
        
        if proactive:
            description += " Use PROACTIVELY when relevant."
        
        # Add common trigger patterns
        if "test" in requirements.lower():
            description += " Use after code changes for testing."
        elif "review" in requirements.lower():
            description += " Use for code review and quality checks."
        elif "debug" in requirements.lower():
            description += " Use when errors or issues occur."
        elif "document" in requirements.lower():
            description += " Use for documentation generation and updates."
        elif "refactor" in requirements.lower():
            description += " Use for code refactoring and improvements."
        
        return description
    
    def _generate_system_prompt(self, requirements: str) -> str:
        """Generate a detailed system prompt from requirements.
        
        Args:
            requirements: Natural language requirements
            
        Returns:
            Generated system prompt
        """
        prompt_parts = []
        
        # Add role definition
        prompt_parts.append(f"You are a specialized Claude Code subagent with the following responsibilities:\n")
        prompt_parts.append(f"{requirements}\n")
        
        # Add standard operating procedures based on keywords
        if "test" in requirements.lower():
            prompt_parts.append(self._get_testing_instructions())
        if "review" in requirements.lower():
            prompt_parts.append(self._get_review_instructions())
        if "debug" in requirements.lower():
            prompt_parts.append(self._get_debugging_instructions())
        if "document" in requirements.lower():
            prompt_parts.append(self._get_documentation_instructions())
        if "refactor" in requirements.lower():
            prompt_parts.append(self._get_refactoring_instructions())
        
        # Add general best practices
        prompt_parts.append("""
## General Guidelines

1. Work systematically and methodically
2. Provide clear explanations for your actions
3. Consider edge cases and potential issues
4. Follow project conventions and best practices
5. Communicate findings and recommendations clearly
""")
        
        return "\n".join(prompt_parts)
    
    def _get_testing_instructions(self) -> str:
        """Get standard testing instructions."""
        return """
## Testing Approach

When invoked for testing:
1. Identify relevant test files and test suites
2. Run appropriate tests using available test runners
3. Analyze test failures and provide detailed reports
4. Fix failing tests while preserving test intent
5. Add new tests for uncovered code paths
6. Ensure all tests pass before completion

Best practices:
- Run tests incrementally to identify issues early
- Use appropriate test frameworks for the project
- Maintain test coverage metrics
- Document any test environment requirements
"""
    
    def _get_review_instructions(self) -> str:
        """Get standard code review instructions."""
        return """
## Code Review Process

When reviewing code:
1. Check for code quality and readability
2. Identify potential bugs and edge cases
3. Verify adherence to project standards
4. Review security implications
5. Suggest performance improvements
6. Check documentation completeness

Focus areas:
- Logic errors and potential bugs
- Security vulnerabilities
- Performance bottlenecks
- Code style and formatting
- Test coverage
- Documentation quality
"""
    
    def _get_debugging_instructions(self) -> str:
        """Get standard debugging instructions."""
        return """
## Debugging Methodology

When debugging issues:
1. Gather error information and stack traces
2. Identify steps to reproduce the issue
3. Isolate the problem to specific code sections
4. Form hypotheses about root causes
5. Test fixes systematically
6. Verify the solution resolves the issue

Debugging techniques:
- Add strategic logging statements
- Use debugger tools when available
- Check recent code changes
- Review related issues and documentation
- Test edge cases and boundary conditions
"""
    
    def _get_documentation_instructions(self) -> str:
        """Get standard documentation instructions."""
        return """
## Documentation Standards

When creating or updating documentation:
1. Write clear and concise explanations
2. Include code examples where helpful
3. Document parameters, return values, and exceptions
4. Maintain consistency with existing documentation
5. Include usage examples and best practices
6. Update related documentation when making changes

Documentation types:
- API documentation
- Code comments and docstrings
- README files
- Architecture documentation
- User guides and tutorials
"""
    
    def _get_refactoring_instructions(self) -> str:
        """Get standard refactoring instructions."""
        return """
## Refactoring Principles

When refactoring code:
1. Understand the current implementation thoroughly
2. Identify code smells and improvement opportunities
3. Plan refactoring in small, testable steps
4. Maintain functionality while improving structure
5. Update tests to reflect changes
6. Document significant architectural changes

Refactoring goals:
- Improve code readability and maintainability
- Reduce duplication and complexity
- Enhance performance where needed
- Apply design patterns appropriately
- Ensure backward compatibility when required
"""
    
    def _validate_tools(self, tools: List[str]) -> List[str]:
        """Validate and filter tools list.
        
        Args:
            tools: List of requested tools
            
        Returns:
            Filtered list of valid tools
        """
        valid_tools = []
        for tool in tools:
            if tool in self.AVAILABLE_TOOLS:
                valid_tools.append(tool)
            else:
                print(f"Warning: Unknown tool '{tool}' will be ignored.")
        
        return valid_tools if valid_tools else None
    
    def save_agent(self, agent_config: Dict[str, any], output_path: Optional[str] = None) -> str:
        """Save the agent configuration to a Markdown file.
        
        Args:
            agent_config: Agent configuration dictionary
            output_path: Optional custom output path
            
        Returns:
            Path to the saved agent file
        """
        # Ensure agents directory exists
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine output file path
        if output_path:
            file_path = Path(output_path)
        else:
            file_path = self.agents_dir / f"{agent_config['name']}.md"
        
        # Create the Markdown content
        content = self._generate_markdown(agent_config)
        
        # Write the file
        file_path.write_text(content)
        
        return str(file_path)
    
    def _generate_markdown(self, agent_config: Dict[str, any]) -> str:
        """Generate the Markdown file content for the agent.
        
        Args:
            agent_config: Agent configuration dictionary
            
        Returns:
            Markdown content
        """
        # Create YAML frontmatter
        frontmatter = {
            "name": agent_config["name"],
            "description": agent_config["description"]
        }
        
        if agent_config.get("tools"):
            frontmatter["tools"] = agent_config["tools"]
        
        if agent_config.get("model") and agent_config["model"] != "sonnet":
            frontmatter["model"] = agent_config["model"]

        if agent_config.get("permission_mode") and agent_config["permission_mode"] != "default":
            frontmatter["permissionMode"] = agent_config["permission_mode"]

        if agent_config.get("skills"):
            frontmatter["skills"] = ", ".join(agent_config["skills"])

        if agent_config.get("color"):
            frontmatter["color"] = agent_config["color"]
        
        # Generate the complete Markdown
        yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        
        markdown = f"---\n{yaml_content}---\n\n{agent_config['system_prompt']}"
        
        return markdown


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Create Claude Code subagents from requirements"
    )
    
    parser.add_argument(
        "name",
        help="Name of the subagent"
    )
    
    parser.add_argument(
        "requirements",
        help="Natural language description of what the agent should do"
    )
    
    parser.add_argument(
        "--tools",
        nargs="*",
        help="List of tools the agent should have access to"
    )
    
    parser.add_argument(
        "--model",
        default="sonnet",
        choices=["sonnet", "opus", "haiku", "inherit"],
        help="Model to use for the agent"
    )
    
    parser.add_argument(
        "--proactive",
        action="store_true",
        help="Make the agent proactive (automatically triggered)"
    )

    parser.add_argument(
        "--permission-mode",
        default="default",
        choices=["default", "acceptEdits", "bypassPermissions", "plan", "ignore"],
        help="Permission mode for the subagent"
    )

    parser.add_argument(
        "--skills",
        nargs="*",
        help="List of skills to auto-load"
    )

    parser.add_argument(
        "--color",
        help="Color identifier for UI display (e.g., 'blue' or '#3B82F6')"
    )
    
    parser.add_argument(
        "--project-path",
        help="Path to the project directory (default: current directory)"
    )
    
    parser.add_argument(
        "--output",
        help="Custom output path for the agent file"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output agent configuration as JSON instead of saving"
    )
    
    args = parser.parse_args()
    
    # Create the subagent creator
    creator = SubagentCreator(args.project_path)
    
    # Generate agent configuration
    agent_config = creator.create_agent_from_requirements(
        name=args.name,
        requirements=args.requirements,
        tools=args.tools,
        model=args.model,
        proactive=args.proactive,
        permission_mode=args.permission_mode,
        skills=args.skills,
        color=args.color
    )
    
    if args.json:
        # Output as JSON
        print(json.dumps(agent_config, indent=2))
    else:
        # Save to file
        file_path = creator.save_agent(agent_config, args.output)
        print(f"✅ Subagent '{args.name}' created successfully at: {file_path}")
        print(f"\nTo use this agent in Claude Code:")
        print(f"1. Ensure the file is in .claude/agents/ directory")
        print(f"2. Use '/agents' command to manage agents")
        print(f"3. Invoke with: 'Use the {args.name} agent to...'")


if __name__ == "__main__":
    main()
