"""
Ambiguity Detection Agent for SpecPilot.
Identifies missing details, ambiguous phrasing, developer questions, and design assumptions.
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from schemas.state import SpecPilotState, AmbiguityReport
from prompts.prompts import SYSTEM_BASE_INSTRUCTION, AMBIGUITY_PROMPT
from utils.helper import get_groq_llm


def run_ambiguity_agent(state: SpecPilotState, api_key: str = None) -> Dict[str, Any]:
    """
    Ambiguity Detection Agent node function for LangGraph.
    """
    requirement_text = state.get("requirement_text", "")
    req_output = state.get("requirement_output", {})
    
    llm = get_groq_llm(api_key=api_key)
    structured_llm = llm.with_structured_output(AmbiguityReport)
    
    prompt = ChatPromptTemplate.from_template(AMBIGUITY_PROMPT)
    chain = prompt | structured_llm
    
    result: AmbiguityReport = chain.invoke({
        "system_base": SYSTEM_BASE_INSTRUCTION,
        "requirement_text": requirement_text,
        "requirement_context": str(req_output)
    })
    
    ambiguity_dict = result.model_dump()
    
    logs = state.get("execution_logs", [])
    logs.append({
        "agent": "Ambiguity Detection Agent",
        "status": "Completed",
        "summary": f"Identified {len(result.missing_details)} missing details & {len(result.developer_questions)} clarifying developer questions."
    })
    
    return {
        "ambiguity_output": ambiguity_dict,
        "execution_logs": logs,
        "current_step": "Task Breakdown"
    }
