"""
Acceptance Criteria Agent for SpecPilot.
Generates testable Given-When-Then criteria and QA pass/fail rules.
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from schemas.state import SpecPilotState, AcceptanceCriteriaList
from prompts.prompts import SYSTEM_BASE_INSTRUCTION, ACCEPTANCE_PROMPT
from utils.helper import get_groq_llm


def run_acceptance_agent(state: SpecPilotState, api_key: str = None) -> Dict[str, Any]:
    """
    Acceptance Criteria Agent node function for LangGraph.
    """
    requirement_text = state.get("requirement_text", "")
    risk_output = state.get("risk_output", {})
    
    llm = get_groq_llm(api_key=api_key)
    structured_llm = llm.with_structured_output(AcceptanceCriteriaList, method="json_mode")
    
    prompt = ChatPromptTemplate.from_template(ACCEPTANCE_PROMPT)
    chain = prompt | structured_llm
    
    result: AcceptanceCriteriaList = chain.invoke({
        "system_base": SYSTEM_BASE_INSTRUCTION,
        "requirement_text": requirement_text,
        "risk_context": str(risk_output)
    })
    
    acc_dict = result.model_dump()
    
    logs = state.get("execution_logs", [])
    logs.append({
        "agent": "Acceptance Criteria Agent",
        "status": "Completed",
        "summary": f"Formulated {len(result.criteria)} testable Given-When-Then scenarios."
    })
    
    return {
        "acceptance_output": acc_dict,
        "execution_logs": logs,
        "current_step": "Technical Specification Generator"
    }
