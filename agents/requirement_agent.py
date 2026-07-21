"""
Requirement Understanding Agent for SpecPilot.
Extracts functional & non-functional requirements, target actors, and main features.
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from schemas.state import SpecPilotState, RequirementSummary
from prompts.prompts import SYSTEM_BASE_INSTRUCTION, REQUIREMENT_PROMPT
from utils.helper import get_groq_llm


def run_requirement_agent(state: SpecPilotState, api_key: str = None) -> Dict[str, Any]:
    """
    Requirement Understanding Agent node function for LangGraph.
    """
    requirement_text = state.get("requirement_text", "")
    planner_output = state.get("planner_output", {})
    
    llm = get_groq_llm(api_key=api_key)
    structured_llm = llm.with_structured_output(RequirementSummary)
    
    prompt = ChatPromptTemplate.from_template(REQUIREMENT_PROMPT)
    chain = prompt | structured_llm
    
    result: RequirementSummary = chain.invoke({
        "system_base": SYSTEM_BASE_INSTRUCTION,
        "requirement_text": requirement_text,
        "planner_context": str(planner_output)
    })
    
    req_dict = result.model_dump()
    
    logs = state.get("execution_logs", [])
    logs.append({
        "agent": "Requirement Understanding Agent",
        "status": "Completed",
        "summary": f"Extracted {len(result.functional_requirements)} Functional & {len(result.non_functional_requirements)} Non-functional requirements."
    })
    
    return {
        "requirement_output": req_dict,
        "execution_logs": logs,
        "current_step": "Ambiguity Detection"
    }
