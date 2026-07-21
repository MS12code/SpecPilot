"""
Technical Specification Generator Agent for SpecPilot.
Synthesizes all previous outputs into a polished, executive-ready Markdown technical spec.
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from schemas.state import SpecPilotState, TechnicalSpec
from prompts.prompts import SYSTEM_BASE_INSTRUCTION, SPEC_GENERATOR_PROMPT
from utils.helper import get_groq_llm


def run_spec_generator_agent(state: SpecPilotState, api_key: str = None) -> Dict[str, Any]:
    """
    Technical Specification Generator Agent node function for LangGraph.
    """
    requirement_text = state.get("requirement_text", "")
    req_output = state.get("requirement_output", {})
    ambiguity_output = state.get("ambiguity_output", {})
    task_output = state.get("task_output", {})
    dep_output = state.get("dependency_output", {})
    risk_output = state.get("risk_output", {})
    acc_output = state.get("acceptance_output", {})
    
    llm = get_groq_llm(api_key=api_key)
    structured_llm = llm.with_structured_output(TechnicalSpec)
    
    prompt = ChatPromptTemplate.from_template(SPEC_GENERATOR_PROMPT)
    chain = prompt | structured_llm
    
    result: TechnicalSpec = chain.invoke({
        "system_base": SYSTEM_BASE_INSTRUCTION,
        "requirement_text": requirement_text,
        "requirement_context": str(req_output),
        "ambiguity_context": str(ambiguity_output),
        "task_context": str(task_output),
        "dependency_context": str(dep_output),
        "risk_context": str(risk_output),
        "acceptance_context": str(acc_output)
    })
    
    spec_dict = result.model_dump()
    
    logs = state.get("execution_logs", [])
    logs.append({
        "agent": "Technical Specification Generator",
        "status": "Completed",
        "summary": f"Generated final Technical Specification Report (Complexity: {result.overall_complexity})."
    })
    
    return {
        "spec_output": spec_dict,
        "execution_logs": logs,
        "current_step": "Completed"
    }
