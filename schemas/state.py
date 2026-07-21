"""
State and Pydantic Schemas for SpecPilot Multi-Agent System.
Defines structured outputs for each agent and the LangGraph workflow state.
"""

from typing import List, Dict, Any, Optional, TypedDict
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. Planner Agent Schema
# ---------------------------------------------------------------------------
class PlannerAnalysis(BaseModel):
    initial_assessment: str = Field(description="High-level understanding of the product requirement")
    scope_complexity: str = Field(description="Estimated complexity: Low, Medium, High, or Enterprise")
    key_focus_areas: List[str] = Field(description="Key technical areas to focus on during analysis")
    planned_steps: List[str] = Field(description="Sequential workflow steps planned for downstream agents")


# ---------------------------------------------------------------------------
# 2. Requirement Understanding Agent Schema
# ---------------------------------------------------------------------------
class RequirementSummary(BaseModel):
    summary: str = Field(description="Concise summary of the software requirement")
    functional_requirements: List[str] = Field(description="Explicit functional requirements capabilities")
    non_functional_requirements: List[str] = Field(description="Performance, security, scalability, UI/UX criteria")
    actors: List[str] = Field(description="User roles, systems, or entities interacting with the feature")
    main_features: List[str] = Field(description="Primary features extracted from the text")


# ---------------------------------------------------------------------------
# 3. Ambiguity Detection Agent Schema
# ---------------------------------------------------------------------------
class AmbiguityReport(BaseModel):
    missing_details: List[str] = Field(description="Crucial details missing from the input requirement")
    ambiguous_statements: List[str] = Field(description="Vague or loosely defined phrases")
    developer_questions: List[str] = Field(description="Clarifying questions developers must ask stakeholders")
    assumptions_made: List[str] = Field(description="Reasonable default assumptions made to enable design")


# ---------------------------------------------------------------------------
# 4. Task Breakdown Agent Schema
# ---------------------------------------------------------------------------
class TaskItem(BaseModel):
    title: str = Field(description="Short title of the task")
    description: str = Field(description="Detailed explanation of what needs to be implemented")
    priority: str = Field(description="Priority: High, Medium, or Low")


class TaskBreakdown(BaseModel):
    frontend_tasks: List[TaskItem] = Field(description="UI/UX and web client engineering tasks")
    backend_tasks: List[TaskItem] = Field(description="API, business logic, background job tasks")
    database_suggestions: List[TaskItem] = Field(description="Data modeling and storage suggestions (conceptual)")
    testing_tasks: List[TaskItem] = Field(description="Unit, integration, and E2E testing tasks")
    documentation_tasks: List[TaskItem] = Field(description="API spec, user guide, and tech doc tasks")


# ---------------------------------------------------------------------------
# 5. Dependency Analysis Agent Schema
# ---------------------------------------------------------------------------
class DependencyItem(BaseModel):
    component: str = Field(description="Component or module name")
    depends_on: List[str] = Field(description="Prerequisite services, tools, or components")
    explanation: str = Field(description="Why this dependency relationship exists")


class DependencyGraph(BaseModel):
    dependencies: List[DependencyItem] = Field(description="List of component dependencies")
    execution_order: List[str] = Field(description="Recommended build sequence for implementation")
    critical_path: List[str] = Field(description="High-risk bottleneck components on the critical path")


# ---------------------------------------------------------------------------
# 6. Risk Analysis Agent Schema
# ---------------------------------------------------------------------------
class RiskItem(BaseModel):
    category: str = Field(description="Category: Security, Performance, Edge Case, Integration, or Reliability")
    description: str = Field(description="Description of potential failure point or risk")
    impact: str = Field(description="Impact level: High, Medium, or Low")
    mitigation: str = Field(description="Recommended engineering mitigation or prevention strategy")


class RiskAssessment(BaseModel):
    risks: List[RiskItem] = Field(description="Identified technical and operational risks")
    edge_cases: List[str] = Field(description="Corner/edge cases to handle during development")
    overall_risk_level: str = Field(description="Overall risk score: Low, Moderate, High, or Severe")


# ---------------------------------------------------------------------------
# 7. Acceptance Criteria Agent Schema
# ---------------------------------------------------------------------------
class AcceptanceCriteriaItem(BaseModel):
    feature: str = Field(description="Feature or scenario title")
    given: str = Field(description="Initial precondition state")
    when: str = Field(description="Action or event triggered")
    then: str = Field(description="Expected outcome or assertion")


class AcceptanceCriteriaList(BaseModel):
    criteria: List[AcceptanceCriteriaItem] = Field(description="Structured Given-When-Then criteria")
    general_rules: List[str] = Field(description="General validation rules and pass/fail conditions")


# ---------------------------------------------------------------------------
# 8. Technical Specification Generator Schema
# ---------------------------------------------------------------------------
class ApiEndpointSuggestion(BaseModel):
    method: str = Field(description="HTTP Method: GET, POST, PUT, DELETE, PATCH")
    endpoint: str = Field(description="URL Path e.g. /api/v1/auth/reset-password")
    purpose: str = Field(description="Brief explanation of endpoint responsibility")


class DatabaseTableSuggestion(BaseModel):
    table_name: str = Field(description="Conceptual DB Table name")
    fields: List[str] = Field(description="Key fields and data types")
    purpose: str = Field(description="Data stored and relationship")


class TechnicalSpec(BaseModel):
    executive_summary: str = Field(description="High-level engineering overview of the project spec")
    system_architecture_overview: str = Field(description="Architectural design summary")
    suggested_apis: List[ApiEndpointSuggestion] = Field(description="Recommended REST API structure")
    suggested_db_tables: List[DatabaseTableSuggestion] = Field(description="Conceptual data model schema")
    overall_complexity: str = Field(description="Estimated complexity rating: Low, Medium, High, Very High")
    development_recommendations: List[str] = Field(description="Key recommendations for developers before coding")
    full_report_markdown: str = Field(description="Complete, beautifully formatted Markdown report")


# ---------------------------------------------------------------------------
# LangGraph Workflow State
# ---------------------------------------------------------------------------
class SpecPilotState(TypedDict, total=False):
    requirement_text: str
    planner_output: Optional[Dict[str, Any]]
    requirement_output: Optional[Dict[str, Any]]
    ambiguity_output: Optional[Dict[str, Any]]
    task_output: Optional[Dict[str, Any]]
    dependency_output: Optional[Dict[str, Any]]
    risk_output: Optional[Dict[str, Any]]
    acceptance_output: Optional[Dict[str, Any]]
    spec_output: Optional[Dict[str, Any]]
    execution_logs: List[Dict[str, Any]]
    current_step: str
    error: Optional[str]
