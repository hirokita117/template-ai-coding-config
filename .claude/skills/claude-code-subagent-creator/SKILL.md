---
name: claude-code-subagent-creator
description: Create Claude Code subagents from natural language requirements. Use when users want to create specialized AI subagents for Claude Code without manually writing the configuration. Handles agent creation for testing, code review, debugging, documentation, refactoring, and custom workflows. Generates .claude/agents/*.md files with appropriate YAML frontmatter and system prompts.
---

# Claude Code Subagent Creator

This skill helps create specialized Claude Code subagents from natural language requirements, automatically generating properly formatted agent files with YAML frontmatter and system prompts.

## Overview

Claude Code subagents are specialized AI assistants that can be invoked for specific tasks. This skill automates the creation of these agents by:
- Converting natural language requirements into structured agent definitions
- Generating appropriate descriptions for automatic triggering
- Creating detailed system prompts based on the agent's purpose
- Configuring tools and model settings
- Saving agents to the correct location (.claude/agents/)

## When to Use This Skill

Use this skill when:
- Users want to create a new Claude Code subagent
- Setting up project-specific agents for team workflows
- Creating personal agents for repeated tasks
- Users describe agent requirements in natural language
- Automating agent creation without manual file editing
- Building specialized agents for testing, reviewing, debugging, etc.

## Instructions

### Quick Creation (Script)

For simple agent creation from requirements:

```bash
python scripts/create_subagent.py <name> "<requirements>" [options]
```

Options:
- `--tools`: Specify tools (e.g., --tools Read Write Bash)
- `--model`: Choose model (sonnet, opus, haiku, inherit)
- `--proactive`: Make agent trigger automatically
- `--project-path`: Set project directory
- `--output`: Custom output path

Example:
```bash
python scripts/create_subagent.py test-runner \
  "Run tests automatically after code changes and fix failures" \
  --tools Bash Read Write Execute \
  --proactive
```

### Interactive Creation

For guided agent creation with prompts:

```bash
python scripts/interactive_creator.py
```

This will:
1. Prompt for agent name and requirements
2. Help select appropriate tools
3. Configure proactive behavior
4. Choose the model
5. Determine save location (project/user/custom)
6. Preview and confirm before saving

### Programmatic Usage

Import and use the SubagentCreator class:

```python
from create_subagent import SubagentCreator

creator = SubagentCreator(project_path="/path/to/project")

agent_config = creator.create_agent_from_requirements(
    name="code-reviewer",
    requirements="Review code for quality, security, and best practices",
    tools=["Read", "Grep", "Glob"],
    model="sonnet",
    proactive=True
)

file_path = creator.save_agent(agent_config)
```

## Agent Configuration Options

### Name
- Use lowercase with hyphens (e.g., "test-runner", "code-reviewer")
- Should be descriptive and indicate the agent's purpose

### Description
- Critical for automatic triggering
- Include "use PROACTIVELY" for auto-invocation
- Be specific about when the agent should be used
- Keep concise but comprehensive

### Tools
Common tool combinations:
- **Code analysis**: Read, Grep, Glob
- **Code modification**: Read, Write, Grep
- **Testing**: Bash, Execute, Read, Write
- **System operations**: Bash, Shell, Run
- **Inherit all**: Omit tools field

### Models
- **sonnet**: Default, balanced performance
- **opus**: Most capable, complex tasks
- **haiku**: Fastest, simple tasks
- **inherit**: Same as main conversation

### Proactive Behavior
Proactive agents trigger automatically for:
- Test runners after code changes
- Code reviewers after modifications
- Security auditors for vulnerability checks
- Documentation updaters with code changes

## Common Agent Types

The skill recognizes and optimizes for common agent patterns:

1. **Testing Agents**: Includes test execution, failure analysis, and fix instructions
2. **Review Agents**: Adds code quality, security, and best practice checks
3. **Debugging Agents**: Provides systematic debugging methodology
4. **Documentation Agents**: Handles various documentation types and standards
5. **Refactoring Agents**: Includes refactoring principles and patterns

## File Locations

### Project Agents
- Path: `.claude/agents/` in project directory
- Shared with team via git
- Higher priority than user agents

### User Agents
- Path: `~/.claude/agents/`
- Available across all projects
- Personal agents for individual workflows

## Templates and Examples

See `references/subagent_templates.md` for:
- Complete agent templates for common use cases
- Tool selection guidelines
- Model selection best practices
- Proactive vs on-demand patterns
- Common mistakes to avoid

## Best Practices

1. **Focused Purpose**: Each agent should have one primary responsibility
2. **Clear Triggers**: Write descriptions that enable automatic invocation
3. **Minimal Tools**: Only request tools the agent actually needs
4. **Structured Prompts**: Use numbered steps and clear sections
5. **Test Agents**: Verify agents work as expected after creation
6. **Version Control**: Commit project agents to share with team

## Limitations

- Agents cannot spawn other subagents (no nesting)
- Each agent operates in its own context window
- Tool availability depends on Claude Code configuration
- Model selection limited to available models

## Resources

- `scripts/create_subagent.py`: Main agent creation script with CLI interface
- `scripts/interactive_creator.py`: Interactive wizard for guided creation
- `references/subagent_templates.md`: Complete templates and patterns library
