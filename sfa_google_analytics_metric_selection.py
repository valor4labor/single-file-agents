#!/usr/bin/env -S uv run --script

# /// script
# dependencies = [
#   "pydantic>=2.0.0",
#   "anthropic>=0.45.2",
#   "rich>=13.7.0",
# ]
# ///

"""
/// GoogleAnalyticsMetricSelectionAgent
This agent selects appropriate Google Analytics metrics based on a business goal.
It's a key entry point in the Google Analytics data fetching workflow.

Usage as standalone:
uv run sfa_google_analytics_metric_selection.py --goal "Increase website conversions"

Usage in PydanticGraph:
from sfa_google_analytics_metric_selection import GoogleAnalyticsMetricSelectionNode
///
"""

import os
import sys
import json
import argparse
import asyncio
from typing import Dict, List, Optional, Any, Union, TypeVar, Generic
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

# --------  Agent Metadata --------

META = {
    "name": "GoogleAnalyticsMetricSelection",
    "description": "Selects appropriate Google Analytics metrics based on business goals",
    "version": "1.0.0",
    "category": "Data Operations",
    "status": "Implemented",
    "priority": "P0"
}

# -------- Schema Definitions --------

class GoogleAnalyticsMetricSelectionSchema(BaseModel):
    """Schema for the output of the GA metric selection agent"""
    selected_metrics: List[str] = Field(
        description="List of selected Google Analytics metrics",
        min_items=1
    )
    reasoning: str = Field(
        description="Explanation of why these metrics were selected"
    )
    confidence: float = Field(
        description="Confidence score from 0.0 to 1.0",
        ge=0.0,
        le=1.0,
        default=0.0
    )

# -------- Default Available Metrics --------

DEFAULT_GA_METRICS = [
    "activeUsers", "newUsers", "totalUsers", 
    "sessions", "sessionsPerUser", "averageSessionDuration",
    "screenPageViews", "screenPageViewsPerSession", "bounceRate",
    "conversions", "conversionRate", "engagementRate",
    "ecommercePurchases", "purchaseRevenue", "transactions",
    "entrances", "engagedSessions", "userEngagementDuration"
]

# -------- Agent Prompt Template --------

AGENT_PROMPT = """<purpose>
    You are an expert at selecting the most appropriate Google Analytics metrics for business purposes.
    Your goal is to identify the key metrics that will help track progress towards a specific business objective.
</purpose>

<instructions>
    <instruction>Review the available metrics and select only those relevant to the business goal</instruction>
    <instruction>Consider both leading and lagging indicators</instruction>
    <instruction>Select between 3-5 metrics at most</instruction>
    <instruction>Include at least one conversion-related metric if the goal involves conversions</instruction>
    <instruction>Provide reasoning that explains why each metric is relevant to the stated goal</instruction>
    <instruction>Format your response as a JSON object with the following fields:</instruction>
    <instruction>- selected_metrics: array of metric names</instruction>
    <instruction>- reasoning: string explaining the rationale</instruction>
    <instruction>- confidence: number from 0.0 to 1.0 indicating your confidence in these selections</instruction>
</instructions>

<context>
    Business Goal: {business_goal}
    
    Available Metrics:
    {metrics_list}
</context>

Respond with a JSON object that matches the requested schema.
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
    
    async def run_standalone(self, **kwargs) -> R:
        """Run the agent as a standalone tool"""
        # Create synthetic state with passed kwargs
        state_dict = {"context": {}, **kwargs}
        state = type("State", (), state_dict)
        ctx = GraphRunContext(state)
        
        # Run the agent
        result = await self.run(ctx)
        return result.data if isinstance(result, End) else None

# -------- Workflow State Definition --------

@dataclass
class GoogleAnalyticsWorkflowState:
    """State for Google Analytics workflow"""
    business_goal: str
    available_metrics: List[str] = field(default_factory=lambda: DEFAULT_GA_METRICS.copy())
    selected_metrics: Optional[List[str]] = None
    metric_selection_reasoning: str = ""
    dataframe_dict: Optional[Dict[str, Any]] = None
    dataset_id: Optional[int] = None
    last_error: str = ""
    retry_count: int = 0
    
    @property
    def context(self) -> Dict[str, Any]:
        """Context dict for easier access in standalone mode"""
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

# -------- Agent Implementation --------

class GoogleAnalyticsMetricSelectionNode(BaseNode[GoogleAnalyticsWorkflowState, GoogleAnalyticsMetricSelectionSchema]):
    """Google Analytics Metric Selection Node
    
    Selects appropriate Google Analytics metrics based on a business goal.
    This is typically the first node in the Google Analytics data fetching workflow.
    """
    
    async def run(self, ctx: GraphRunContext[GoogleAnalyticsWorkflowState]) -> End[GoogleAnalyticsMetricSelectionSchema]:
        """Run the Google Analytics metric selection agent"""
        try:
            # Input validation
            if not ctx.state.business_goal:
                ctx.state.last_error = "Missing business goal"
                return End(GoogleAnalyticsMetricSelectionSchema(
                    selected_metrics=["sessions"], 
                    reasoning="Error: No business goal provided. Using sessions as a default metric.",
                    confidence=0.1
                ))
            
            # Build prompt from state
            metrics_list = "\n".join([f"- {metric}" for metric in ctx.state.available_metrics])
            prompt = AGENT_PROMPT.format(
                business_goal=ctx.state.business_goal,
                metrics_list=metrics_list
            )
            
            # Run the LLM
            try:
                from anthropic import Anthropic
                client = Anthropic()
                response = await self._run_anthropic_agent(client, prompt)
            except ImportError:
                # Fallback if Anthropic isn't available
                response = self._run_simple_agent(prompt)
            
            # Parse and validate result
            result = GoogleAnalyticsMetricSelectionSchema(
                selected_metrics=response.get("selected_metrics", ["sessions"]),
                reasoning=response.get("reasoning", "No reasoning provided"),
                confidence=response.get("confidence", 0.5)
            )
            
            # Update workflow state
            ctx.state.selected_metrics = result.selected_metrics
            ctx.state.metric_selection_reasoning = result.reasoning
            
            # Log results
            console.print(f"[green]Selected metrics:[/green] {', '.join(result.selected_metrics)}")
            console.print(f"[blue]Reasoning:[/blue] {result.reasoning}")
            
            # Return result
            return End(result)
            
        except Exception as e:
            # Error handling
            error_msg = f"Error in GoogleAnalyticsMetricSelectionNode: {str(e)}"
            console.print(f"[red]{error_msg}[/red]")
            ctx.state.last_error = error_msg
            
            # Simple retry logic
            if ctx.state.retry_count < 2:
                ctx.state.retry_count += 1
                console.print(f"[yellow]Retrying (attempt {ctx.state.retry_count})[/yellow]")
                return await self.run(ctx)
            
            # Return error result
            return End(GoogleAnalyticsMetricSelectionSchema(
                selected_metrics=["sessions", "pageviews"],  # Default fallback metrics
                reasoning=f"Error occurred: {error_msg}. Using default metrics.",
                confidence=0.0
            ))
    
    async def _run_anthropic_agent(self, client, prompt: str) -> Dict[str, Any]:
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
                
                # If no JSON block, try to find JSON-like content
                json_match = re.search(r'\{.*\}', message_content, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group(0))
                    except:
                        pass
                
                # If no parseable JSON found, create a simple result with the response text
                return {
                    "selected_metrics": self._extract_metrics(message_content, DEFAULT_GA_METRICS),
                    "reasoning": message_content,
                    "confidence": 0.5
                }
            except (json.JSONDecodeError, AttributeError):
                return {
                    "selected_metrics": ["sessions", "conversions", "bounceRate"],
                    "reasoning": response.content[0].text if hasattr(response, 'content') else str(response),
                    "confidence": 0.5
                }
        except Exception as e:
            console.print(f"[red]Error calling Anthropic API: {str(e)}[/red]")
            return {
                "selected_metrics": ["sessions", "pageviews"],
                "reasoning": f"API Error: {str(e)}",
                "confidence": 0.0
            }
    
    def _run_simple_agent(self, prompt: str) -> Dict[str, Any]:
        """Simple fallback agent that doesn't require API calls"""
        console.print("[yellow]Using simple fallback agent (no API call)[/yellow]")
        
        # Extract the business goal from the prompt
        import re
        goal_match = re.search(r'Business Goal: (.*?)$', prompt, re.MULTILINE)
        goal = goal_match.group(1) if goal_match else "unknown goal"
        
        # Simple logic to select metrics based on keywords in the goal
        metrics = ["sessions", "newUsers"]
        reasoning = f"Based on the business goal: '{goal}', selected basic traffic metrics."
        
        if "conversion" in goal.lower():
            metrics.append("conversions")
            metrics.append("conversionRate")
            reasoning += " Added conversion metrics since the goal mentions conversions."
        
        if "revenue" in goal.lower() or "sales" in goal.lower():
            metrics.append("purchaseRevenue")
            reasoning += " Added revenue metrics since the goal relates to sales."
        
        if "engagement" in goal.lower():
            metrics.append("engagementRate")
            reasoning += " Added engagement metrics since the goal mentions engagement."
        
        return {
            "selected_metrics": metrics[:5],  # Limit to 5 metrics
            "reasoning": reasoning,
            "confidence": 0.3
        }
    
    def _extract_metrics(self, text: str, available_metrics: List[str]) -> List[str]:
        """Extract metric names from text"""
        metrics = []
        for metric in available_metrics:
            if metric in text:
                metrics.append(metric)
        
        # If no metrics found, return default set
        if not metrics:
            return ["sessions", "newUsers", "bounceRate"]
        
        return metrics[:5]  # Limit to 5 metrics

# -------- Command-line Interface --------

async def main():
    parser = argparse.ArgumentParser(description="Google Analytics Metric Selection Agent")
    parser.add_argument("--goal", required=True, help="The business goal")
    args = parser.parse_args()
    
    # Create workflow state
    state = GoogleAnalyticsWorkflowState(business_goal=args.goal)
    
    # Create context
    ctx = GraphRunContext(state)
    
    # Run the agent
    console.print(f"[blue]Running GA Metric Selection Agent for goal: {args.goal}[/blue]")
    agent = GoogleAnalyticsMetricSelectionNode()
    result = await agent.run(ctx)
    
    # Print result
    if result.data:
        console.print("\n[green]Selected Metrics:[/green]")
        for metric in result.data.selected_metrics:
            console.print(f"- {metric}")
        console.print("\n[blue]Reasoning:[/blue]")
        console.print(result.data.reasoning)
        console.print(f"\nConfidence: {result.data.confidence}")
    else:
        console.print("[red]No result returned[/red]")

if __name__ == "__main__":
    asyncio.run(main())