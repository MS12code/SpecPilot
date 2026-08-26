"""
Risk Analysis Agent for SpecPilot.
Evaluates security vulnerabilities, performance bottlenecks, edge cases, and mitigations.
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from schemas.state import SpecPilotState, RiskAssessment
from prompts.prompts import SYSTEM_BASE_INSTRUCTION, RISK_PROMPT
from utils.helper import get_groq_llm, safe_chain_invoke


def run_risk_agent(state: SpecPilotState, api_key: str = None) -> Dict[str, Any]:
    """
    Risk Analysis Agent node function for LangGraph.
    """
    requirement_text = state.get("requirement_text", "")
    task_output = state.get("task_output", {})
    
    llm = get_groq_llm(api_key=api_key)
    structured_llm = llm.with_structured_output(RiskAssessment, method="json_mode")
    
    prompt = ChatPromptTemplate.from_template(RISK_PROMPT)
    chain = prompt | structured_llm
    
    result: RiskAssessment = safe_chain_invoke(chain, {
        "system_base": SYSTEM_BASE_INSTRUCTION,
        "requirement_text": requirement_text,
        "task_context": str(task_output)
    })
    
    risk_dict = result.model_dump()
    
    logs = state.get("execution_logs", [])
    logs.append({
        "agent": "Risk Analysis Agent",
        "status": "Completed",
        "summary": f"Identified {len(result.risks)} risks ({result.overall_risk_level} Risk Level) & {len(result.edge_cases)} critical edge cases."
    })
    
    return {
        "risk_output": risk_dict,
        "execution_logs": logs,
        "current_step": "Acceptance Criteria"
    }
