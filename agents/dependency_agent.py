"""
Dependency Analysis Agent for SpecPilot.
Identifies component dependencies, build sequences, and critical path items.
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from schemas.state import SpecPilotState, DependencyGraph
from prompts.prompts import SYSTEM_BASE_INSTRUCTION, DEPENDENCY_PROMPT
from utils.helper import get_groq_llm


def run_dependency_agent(state: SpecPilotState, api_key: str = None) -> Dict[str, Any]:
    """
    Dependency Analysis Agent node function for LangGraph.
    """
    requirement_text = state.get("requirement_text", "")
    task_output = state.get("task_output", {})
    
    llm = get_groq_llm(api_key=api_key)
    structured_llm = llm.with_structured_output(DependencyGraph, method="json_mode")
    
    prompt = ChatPromptTemplate.from_template(DEPENDENCY_PROMPT)
    chain = prompt | structured_llm
    
    result: DependencyGraph = chain.invoke({
        "system_base": SYSTEM_BASE_INSTRUCTION,
        "requirement_text": requirement_text,
        "task_context": str(task_output)
    })
    
    dep_dict = result.model_dump()
    
    logs = state.get("execution_logs", [])
    logs.append({
        "agent": "Dependency Analysis Agent",
        "status": "Completed",
        "summary": f"Mapped {len(result.dependencies)} component dependencies and defined critical path execution order."
    })
    
    return {
        "dependency_output": dep_dict,
        "execution_logs": logs,
        "current_step": "Risk Analysis"
    }
