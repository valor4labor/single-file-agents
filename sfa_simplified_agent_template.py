#!/usr/bin/env -S uv run --script

# /// script
# dependencies = [
#   "pydantic>=2.0.0",
#   "anthropic>=0.45.2",
#   "rich>=13.7.0",
# ]
# ///

"""
/// Example SFA with PydanticGraph compatibility
This single-file agent template demonstrates a simplified way to define agents
that can work standalone but also be composed in PydanticGraph workflows.

Usage as standalone:
uv run sfa_simplified_agent_template.py --prompt "Your prompt here"

Usage in PydanticGraph:
import the AgentNode and use it in your workflow graph
///
"""

import os
import sys
import json
import argparse
import asyncio
from typing import Dict, List, Optional, Any, Callable, Union, TypeVar, Generic
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from rich.console import Console

# Initialize rich console
console = Console()

# Check for API key if running standalone
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY and __name__ == "__main__":
    console.print("[red]Error: ANTHROPIC_API_KEY environment variable is not set[/red]")
    console.print("Please set it with: export ANTHROPIC_API_KEY='your-api-key-here'")
    sys.exit(1)

# --------  Core Agent Definition --------

# Define the output schema
class TemplateAgentSchema(BaseModel):
    """Schema for the output of the template agent"""
    result: str
    confidence: float = 0.0

# Define the agent prompt template
AGENT_PROMPT = """<purpose>
    You are a specialized agent that performs a single focused task.
    Your goal is to {goal}.
</purpose>

<instructions>
    <instruction>Think step by step about how to accomplish this task</instruction>
    <instruction>Be precise and specific in your reasoning</instruction>
    <instruction>Format your answer according to the requested schema</instruction>
    <instruction>Provide your confidence level from 0.0 to 1.0</instruction>
</instructions>

<context>
{context}
</context>

<user_request>
{user_request}
</user_request>
"""

# -------- PydanticGraph Compatibility Layer --------

# Minimal implementation of PydanticGraph-like interfaces for standalone use
T = TypeVar('T')
R = TypeVar('R')

class GraphRunContext(Generic[T]):
    """Minimal GraphRunContext implementation for standalone use"""
    def __init__(self, state: T):
        self.state = state

class End(Generic[R]):
    """End marker with optional result data"""
    def __init__(self, data: Optional[R] = None):
        self.data = data

class BaseNode(Generic[T, R]):
    """Base class for agent nodes"""
    async def run(self, ctx: GraphRunContext[T]) -> Union['BaseNode', End[R]]:
        """Run the agent node"""
        raise NotImplementedError("Subclasses must implement run()")

# -------- Agent Implementation --------

@dataclass
class TemplateAgentState:
    """State for template agent workflow"""
    goal: str
    context: str = ""
    user_request: str = ""
    result: Optional[TemplateAgentSchema] = None
    last_error: str = ""
    retry_count: int = 0

class TemplateAgentNode(BaseNode[TemplateAgentState, TemplateAgentSchema]):
    """Template agent node that demonstrates best practices.
    
    This node shows how to implement an agent that can be used both
    standalone and as part of a PydanticGraph workflow.
    """
    
    async def run(self, ctx: GraphRunContext[TemplateAgentState]) -> End[TemplateAgentSchema]:
        """Run the template agent node."""
        try:
            # Input validation
            if not ctx.state.user_request:
                ctx.state.last_error = "Missing user request"
                return End(TemplateAgentSchema(result="Error: Missing user request", confidence=0.0))
            
            # Build prompt from state
            prompt = AGENT_PROMPT.format(
                goal=ctx.state.goal,
                context=ctx.state.context,
                user_request=ctx.state.user_request
            )
            
            # Call the LLM (implementation varies based on provider)
            try:
                from anthropic import Anthropic
                client = Anthropic()
                response = await run_anthropic_agent(client, prompt)
            except ImportError:
                # Fallback to synchronous execution if needed
                response = run_simple_agent(prompt)
            
            # Parse and validate result
            result = TemplateAgentSchema(
                result=response.get("result", "No result provided"),
                confidence=response.get("confidence", 0.5)
            )
            
            # Update state
            ctx.state.result = result
            
            # Return result
            return End(result)
            
        except Exception as e:
            # Error handling
            error_msg = f"Error in TemplateAgentNode: {str(e)}"
            console.print(f"[red]{error_msg}[/red]")
            ctx.state.last_error = error_msg
            
            # Simple retry logic
            if ctx.state.retry_count < 2:
                ctx.state.retry_count += 1
                console.print(f"[yellow]Retrying (attempt {ctx.state.retry_count})[/yellow]")
                return await self.run(ctx)
            
            # Return error result
            return End(TemplateAgentSchema(
                result=f"Error occurred: {error_msg}",
                confidence=0.0
            ))

# -------- LLM Integration --------

async def run_anthropic_agent(client, prompt: str) -> Dict[str, Any]:
    """Run the agent using Anthropic's Claude"""
    try:
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Try to parse the response as JSON
        try:
            # Look for JSON-like content in the response
            message_content = response.content[0].text
            import re
            json_match = re.search(r'```json\n(.*?)\n```', message_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # If no JSON found, create a simple result
            return {
                "result": message_content,
                "confidence": 0.7
            }
        except (json.JSONDecodeError, AttributeError):
            return {
                "result": response.content[0].text if hasattr(response, 'content') else str(response),
                "confidence": 0.5
            }
    except Exception as e:
        console.print(f"[red]Error calling Anthropic API: {str(e)}[/red]")
        return {"result": f"API Error: {str(e)}", "confidence": 0.0}

def run_simple_agent(prompt: str) -> Dict[str, Any]:
    """Simple fallback agent that doesn't require API calls"""
    console.print("[yellow]Using simple fallback agent (no API call)[/yellow]")
    return {
        "result": "This is a fallback response when no API is available",
        "confidence": 0.3
    }

# -------- Command-line Interface --------

async def main():
    parser = argparse.ArgumentParser(description="Template Agent CLI")
    parser.add_argument("--prompt", required=True, help="The user's prompt")
    parser.add_argument("--goal", default="process the user's request and provide a helpful response", 
                       help="The goal for the agent")
    parser.add_argument("--context", default="", help="Additional context for the request")
    args = parser.parse_args()
    
    # Create workflow state
    state = TemplateAgentState(
        goal=args.goal,
        context=args.context,
        user_request=args.prompt
    )
    
    # Create context
    ctx = GraphRunContext(state)
    
    # Run the agent
    console.print(f"[blue]Running agent with prompt: {args.prompt}[/blue]")
    agent = TemplateAgentNode()
    result = await agent.run(ctx)
    
    # Print result
    if result.data:
        console.print("\n[green]Result:[/green]")
        console.print(f"[bold]{result.data.result}[/bold]")
        console.print(f"Confidence: {result.data.confidence}")
    else:
        console.print("[red]No result returned[/red]")

if __name__ == "__main__":
    asyncio.run(main())