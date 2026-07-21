"""
Task Breakdown Agent for SpecPilot.
Converts requirements and ambiguities into categorized engineering tasks (Frontend, Backend, Database suggestions, Testing, Docs).
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from schemas.state import SpecPilotState, TaskBreakdown
from prompts.prompts import SYSTEM_BASE_INSTRUCTION, TASK_PROMPT
from utils.helper import get_groq_llm


def run_task_agent(state: SpecPilotState, api_key: str = None) -> Dict[str, Any]:
    """
    Task Breakdown Agent node function for LangGraph.
    """
    requirement_text = state.get("requirement_text", "")
    req_output = state.get("requirement_output", {})
    ambiguity_output = state.get("ambiguity_output", {})
    
    llm = get_groq_llm(api_key=api_key)
    structured_llm = llm.with_structured_output(TaskBreakdown)
    
    prompt = ChatPromptTemplate.from_template(TASK_PROMPT)
    chain = prompt | structured_llm
    
    result: TaskBreakdown = chain.invoke({
        "system_base": SYSTEM_BASE_INSTRUCTION,
        "requirement_text": requirement_text,
        "requirement_context": str(req_output),
        "ambiguity_context": str(ambiguity_output)
    })
    
    task_dict = result.model_dump()
    total_tasks = (
        len(result.frontend_tasks) +
        len(result.backend_tasks) +
        len(result.database_suggestions) +
        len(result.testing_tasks) +
        len(result.documentation_tasks)
    )
    
    logs = state.get("execution_logs", [])
    logs.append({
        "agent": "Task Breakdown Agent",
        "status": "Completed",
        "summary": f"Generated {total_tasks} technical engineering tasks across Frontend, Backend, DB, Testing & Docs."
    })
    
    return {
        "task_output": task_dict,
        "execution_logs": logs,
        "current_step": "Dependency Analysis"
    }
