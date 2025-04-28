# DeckFusion Simplified Agent Definitions

This document proposes a simplified approach to agent definition in DeckFusion, inspired by the Single-File Agents (SFA) pattern while maintaining compatibility with PydanticGraph workflows.

## Core Concepts

1. **Single-File Pattern**: Each agent is defined in a single file with clear dependencies, making it easier to understand, test, and deploy.

2. **Dual Usage**: Agents can be used both standalone (with CLI) and as part of larger workflows.

3. **Schema-First**: Every agent defines its inputs and outputs using Pydantic schemas for strong typing and validation.

4. **Prompt Template**: Each agent has a well-structured prompt template with clearly marked sections.

5. **PydanticGraph Integration**: Seamless integration with the existing workflow system.

## Agent Definition Template

```python
# Agent metadata and purpose definition
META = {
    "name": "GoogleAnalyticsMetricSelectionAgent",
    "description": "Selects appropriate Google Analytics metrics based on business goals",
    "version": "1.0.0",
    "category": "Data Operations",
    "status": "Implemented",
    "priority": "P0"
}

# Input/output schemas using Pydantic
class InputSchema(BaseModel):
    business_goal: str
    available_metrics: List[str] = Field(default_factory=list)
    
class OutputSchema(BaseModel):
    selected_metrics: List[str]
    reasoning: str
    confidence: float = 0.0

# Agent prompt template with clear sections
PROMPT = """<purpose>
    You are an expert at selecting the most appropriate Google Analytics metrics.
    Your goal is to identify the best metrics to track for a specific business objective.
</purpose>

<instructions>
    <instruction>Review the available metrics and select only those relevant to the business goal</instruction>
    <instruction>Consider both leading and lagging indicators</instruction>
    <instruction>Provide a brief explanation for your selections</instruction>
    <instruction>Format your response as a JSON object matching the requested schema</instruction>
</instructions>

<context>
    Business Goal: {business_goal}
    
    Available Metrics:
    {metrics_list}
</context>
"""

# Agent node definition that implements the BaseNode interface
class GoogleAnalyticsMetricSelectionNode(BaseNode[WorkflowState, OutputSchema]):
    """Implementation of the agent node that handles metric selection"""
    async def run(self, ctx: GraphRunContext[WorkflowState]) -> Union[NextNode, End[OutputSchema]]:
        # Implementation goes here, integrating with your workflow system
        ...
```

## Simplified Comparison

### Current Approach vs. Simplified SFA Approach

Current AGENTS.md:
```markdown
### GoogleAnalyticsMetricSelectionNode
- **Purpose**: Selects appropriate Google Analytics metrics based on a business goal
- **Implementation Status**: ✅ Implemented
- **Output Schema**: `GoogleAnalyticsMetricSelectionSchema(selected_metrics: list[str])`
- **Test Coverage**: ✅ `test_google_analytics_nodes.py`
- **Workflows**: Google Analytics data fetching workflow
- **Dependencies**: None (entry point)
- **Categories**: 
  - Function: Data Operations
  - Stage: Data
  - Priority: Core (P0)
  - Integration: Data-Integration
```

Simplified SFA-Style Approach:
```markdown
### GoogleAnalyticsMetricSelection

```python
# Agent imports and dependencies documented at the top
# from anthropic import Anthropic
# from pydantic import BaseModel, Field

# Agent metadata in structured format
META = {
    "name": "GoogleAnalyticsMetricSelection",
    "purpose": "Selects appropriate Google Analytics metrics based on business goals",
    "status": "Implemented",
    "category": "Data Operations",
    "priority": "P0"
}

# Input and output schemas clearly defined
class InputSchema(BaseModel):
    business_goal: str
    
class OutputSchema(BaseModel):
    selected_metrics: List[str]
    reasoning: str

# The core prompt template is included directly in the documentation
PROMPT = """<purpose>
    You are an expert at selecting the most appropriate Google Analytics metrics.
    Your goal is to identify the best metrics to track for a specific business objective.
</purpose>

<context>
    Business Goal: {business_goal}
    
    Available Metrics:
    {metrics_list}
</context>
"""
```

### Workflow Composition Example

```python
# PydanticGraph workflow definition remains largely the same
workflow = Graph(nodes=[
    GoogleAnalyticsMetricSelectionNode,
    GoogleAnalyticsDataFetchNode,
    AnalysisNode,
    # ...
])

# But agents can now also be run independently
if __name__ == "__main__":
    result = await GoogleAnalyticsMetricSelectionNode().run_standalone(
        business_goal="Increase website conversions",
        available_metrics=["pageviews", "sessions", "conversion_rate", "bounce_rate"]
    )
    print(f"Selected metrics: {result.selected_metrics}")
```

## Benefits of SFA-Style Approach

1. **Readability**: All aspects of an agent are documented in one place with clear structure
2. **Self-contained**: Each agent file can be run and tested independently
3. **Standardized**: Consistent pattern for all agents makes them easier to understand
4. **Development Velocity**: New agents can be created faster with less boilerplate
5. **Documentation as Code**: The agent definition itself serves as documentation
6. **Composability**: Still fully compatible with PydanticGraph workflow system

## Conclusion

The Single-File Agents pattern offers a way to simplify agent definition in DeckFusion while maintaining compatibility with the existing PydanticGraph workflow system. It reduces cognitive overhead, improves development velocity, and makes agents more testable while preserving all the benefits of the current architecture.