"""
Planner Agent for SpecPilot.
Analyzes initial software requirements and sets up workflow state.
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from schemas.state import SpecPilotState, PlannerAnalysis
from prompts.prompts import SYSTEM_BASE_INSTRUCTION, PLANNER_PROMPT
from utils.helper import get_groq_llm


def run_planner_agent(state: SpecPilotState, api_key: str = None) -> Dict[str, Any]:
    """
    Planner Agent node function for LangGraph.
    """
    requirement_text = state.get("requirement_text", "")
    
    llm = get_groq_llm(api_key=api_key)
    structured_llm = llm.with_structured_output(PlannerAnalysis)
    
    prompt = ChatPromptTemplate.from_template(PLANNER_PROMPT)
    chain = prompt | structured_llm
    
    result: PlannerAnalysis = chain.invoke({
        "system_base": SYSTEM_BASE_INSTRUCTION,
        "requirement_text": requirement_text
    })
    
    planner_dict = result.model_dump()
    
    logs = state.get("execution_logs", [])
    logs.append({
        "agent": "Planner Agent",
        "status": "Completed",
        "summary": f"Scope: {result.scope_complexity} | Focus areas: {', '.join(result.key_focus_areas[:2])}"
    })
    
    return {
        "planner_output": planner_dict,
        "execution_logs": logs,
        "current_step": "Requirement Understanding"
    }
