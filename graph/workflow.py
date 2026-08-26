"""
LangGraph Workflow Orchestration for SpecPilot Multi-Agent System.
Defines the StateGraph execution pipeline across all 8 specialized AI agents.
"""

import time
from typing import Dict, Any, Optional, Callable
from langgraph.graph import StateGraph, START, END
from schemas.state import SpecPilotState
from agents.planner_agent import run_planner_agent
from agents.requirement_agent import run_requirement_agent
from agents.ambiguity_agent import run_ambiguity_agent
from agents.task_agent import run_task_agent
from agents.dependency_agent import run_dependency_agent
from agents.risk_agent import run_risk_agent
from agents.acceptance_agent import run_acceptance_agent
from agents.spec_generator import run_spec_generator_agent
from utils.helper import FallbackModelAdvanced, GROQ_FALLBACK_MODELS


def _with_fallback(agent_fn, state, api_key):
    """
    Invoke an agent function, automatically retrying with the next Groq fallback model
    if the current model's daily token quota (TPD) is exhausted.
    """
    for _ in range(len(GROQ_FALLBACK_MODELS)):
        try:
            return agent_fn(state, api_key=api_key)
        except FallbackModelAdvanced as fb:
            # _ACTIVE_MODEL_INDEX already advanced in helper.py; just re-invoke.
            print(f"[SpecPilot] Retrying agent with model: {fb.new_model}")
            time.sleep(1.5)
    # If we exit the loop without returning, something unexpected happened.
    raise RuntimeError("Failed to complete agent after exhausting all fallback models.")


def build_specpilot_workflow(api_key: Optional[str] = None):
    """
    Build and compile the LangGraph workflow graph.
    """
    # Initialize StateGraph with typed state
    workflow = StateGraph(SpecPilotState)

    # Define wrapper functions to pass API key and handle model fallback
    def planner_node(state: SpecPilotState):
        return _with_fallback(run_planner_agent, state, api_key)

    def requirement_node(state: SpecPilotState):
        return _with_fallback(run_requirement_agent, state, api_key)

    def ambiguity_node(state: SpecPilotState):
        return _with_fallback(run_ambiguity_agent, state, api_key)

    def task_node(state: SpecPilotState):
        return _with_fallback(run_task_agent, state, api_key)

    def dependency_node(state: SpecPilotState):
        return _with_fallback(run_dependency_agent, state, api_key)

    def risk_node(state: SpecPilotState):
        return _with_fallback(run_risk_agent, state, api_key)

    def acceptance_node(state: SpecPilotState):
        return _with_fallback(run_acceptance_agent, state, api_key)

    def spec_generator_node(state: SpecPilotState):
        return _with_fallback(run_spec_generator_agent, state, api_key)

    # Add Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("requirement_understanding", requirement_node)
    workflow.add_node("ambiguity_detection", ambiguity_node)
    workflow.add_node("task_breakdown", task_node)
    workflow.add_node("dependency_analysis", dependency_node)
    workflow.add_node("risk_analysis", risk_node)
    workflow.add_node("acceptance_criteria", acceptance_node)
    workflow.add_node("spec_generator", spec_generator_node)

    # Define Linear Graph Pipeline Edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "requirement_understanding")
    workflow.add_edge("requirement_understanding", "ambiguity_detection")
    workflow.add_edge("ambiguity_detection", "task_breakdown")
    workflow.add_edge("task_breakdown", "dependency_analysis")
    workflow.add_edge("dependency_analysis", "risk_analysis")
    workflow.add_edge("risk_analysis", "acceptance_criteria")
    workflow.add_edge("acceptance_criteria", "spec_generator")
    workflow.add_edge("spec_generator", END)

    # Compile Graph
    app = workflow.compile()
    return app


def execute_analysis_workflow(
    requirement_text: str,
    api_key: Optional[str] = None,
    progress_callback: Optional[Callable[[str, int], None]] = None
) -> Dict[str, Any]:
    """
    Executes the LangGraph analysis workflow step-by-step and invokes progress callbacks.
    """
    graph = build_specpilot_workflow(api_key=api_key)
    
    initial_state: SpecPilotState = {
        "requirement_text": requirement_text,
        "execution_logs": [],
        "current_step": "Starting Workflow"
    }

    step_weights = {
        "planner": (12, "🧠 1/8 Planner Agent: Assessing scope & key focus areas..."),
        "requirement_understanding": (25, "📋 2/8 Requirement Agent: Extracting functional & non-functional rules..."),
        "ambiguity_detection": (37, "🔍 3/8 Ambiguity Agent: Identifying gaps & developer questions..."),
        "task_breakdown": (50, "🛠️ 4/8 Task Agent: Breaking down engineering tasks..."),
        "dependency_analysis": (62, "🔗 5/8 Dependency Agent: Mapping module dependencies..."),
        "risk_analysis": (75, "⚠️ 6/8 Risk Agent: Evaluating security, edge cases & mitigations..."),
        "acceptance_criteria": (87, "✅ 7/8 Acceptance Agent: Writing Given-When-Then scenarios..."),
        "spec_generator": (100, "📄 8/8 Spec Generator: Formatting Technical Specification Document...")
    }

    final_state = initial_state
    
    for event in graph.stream(initial_state):
        for node_name, state_update in event.items():
            final_state.update(state_update)
            if progress_callback and node_name in step_weights:
                pct, msg = step_weights[node_name]
                progress_callback(msg, pct)
            time.sleep(0.8)

    return final_state
