"""
State and Pydantic Schemas for SpecPilot Multi-Agent System.
Defines structured outputs for each agent and the LangGraph workflow state.
"""

from typing import List, Dict, Any, Optional, TypedDict
from pydantic import BaseModel, Field, AliasChoices, field_validator


def _ensure_string_list(v: Any) -> List[str]:
    if isinstance(v, str):
        return [s.strip() for s in v.split(",") if s.strip()]
    if isinstance(v, list):
        return [str(item) for item in v]
    return []


# ---------------------------------------------------------------------------
# 1. Planner Agent Schema
# ---------------------------------------------------------------------------
class PlannerAnalysis(BaseModel):
    initial_assessment: str = Field(default="", description="High-level understanding of the product requirement", validation_alias=AliasChoices("initial_assessment", "high_level_assessment", "assessment"))
    scope_complexity: str = Field(default="Medium", description="Estimated complexity: Low, Medium, High, or Enterprise", validation_alias=AliasChoices("scope_complexity", "complexity"))
    key_focus_areas: List[str] = Field(default_factory=list, description="Key technical areas to focus on during analysis", validation_alias=AliasChoices("key_focus_areas", "key_technical_focus_areas", "focus_areas"))
    planned_steps: List[str] = Field(default_factory=list, description="Sequential workflow steps planned for downstream agents", validation_alias=AliasChoices("planned_steps", "analysis_plan_steps", "steps"))

    @field_validator("key_focus_areas", "planned_steps", mode="before")
    @classmethod
    def _parse_list(cls, v):
        return _ensure_string_list(v)


# ---------------------------------------------------------------------------
# 2. Requirement Understanding Agent Schema
# ---------------------------------------------------------------------------
class RequirementSummary(BaseModel):
    summary: str = Field(default="", description="Concise summary of the software requirement", validation_alias=AliasChoices("summary", "requirement_summary"))
    functional_requirements: List[str] = Field(default_factory=list, description="Explicit functional requirements capabilities", validation_alias=AliasChoices("functional_requirements", "functional_reqs"))
    non_functional_requirements: List[str] = Field(default_factory=list, description="Performance, security, scalability, UI/UX criteria", validation_alias=AliasChoices("non_functional_requirements", "non_functional_reqs"))
    actors: List[str] = Field(default_factory=list, description="User roles, systems, or entities interacting with the feature", validation_alias=AliasChoices("actors", "user_roles", "roles"))
    main_features: List[str] = Field(default_factory=list, description="Primary features extracted from the text", validation_alias=AliasChoices("main_features", "features", "key_features"))

    @field_validator("functional_requirements", "non_functional_requirements", "actors", "main_features", mode="before")
    @classmethod
    def _parse_list(cls, v):
        return _ensure_string_list(v)


# ---------------------------------------------------------------------------
# 3. Ambiguity Detection Agent Schema
# ---------------------------------------------------------------------------
class AmbiguityReport(BaseModel):
    missing_details: List[str] = Field(default_factory=list, description="Crucial details missing from the input requirement", validation_alias=AliasChoices("missing_details", "missing_information", "gaps"))
    ambiguous_statements: List[str] = Field(default_factory=list, description="Vague or loosely defined phrases", validation_alias=AliasChoices("ambiguous_statements", "ambiguities", "vague_phrases"))
    developer_questions: List[str] = Field(default_factory=list, description="Clarifying questions developers must ask stakeholders", validation_alias=AliasChoices("developer_questions", "questions", "clarifying_questions"))
    assumptions_made: List[str] = Field(default_factory=list, description="Reasonable default assumptions made to enable design", validation_alias=AliasChoices("assumptions_made", "assumptions", "working_assumptions"))

    @field_validator("missing_details", "ambiguous_statements", "developer_questions", "assumptions_made", mode="before")
    @classmethod
    def _parse_list(cls, v):
        return _ensure_string_list(v)


# ---------------------------------------------------------------------------
# 4. Task Breakdown Agent Schema
# ---------------------------------------------------------------------------
class TaskItem(BaseModel):
    title: str = Field(default="", description="Short title of the task", validation_alias=AliasChoices("title", "task_title", "name"))
    description: str = Field(default="", description="Detailed explanation of what needs to be implemented", validation_alias=AliasChoices("description", "task_description", "details"))
    priority: str = Field(default="Medium", description="Priority: High, Medium, or Low", validation_alias=AliasChoices("priority", "task_priority"))


class TaskBreakdown(BaseModel):
    frontend_tasks: List[TaskItem] = Field(default_factory=list, description="UI/UX and web client engineering tasks", validation_alias=AliasChoices("frontend_tasks", "frontend"))
    backend_tasks: List[TaskItem] = Field(default_factory=list, description="API, business logic, background job tasks", validation_alias=AliasChoices("backend_tasks", "backend"))
    database_suggestions: List[TaskItem] = Field(default_factory=list, description="Data modeling and storage suggestions (conceptual)", validation_alias=AliasChoices("database_suggestions", "database_tasks", "database"))
    testing_tasks: List[TaskItem] = Field(default_factory=list, description="Unit, integration, and E2E testing tasks", validation_alias=AliasChoices("testing_tasks", "testing"))
    documentation_tasks: List[TaskItem] = Field(default_factory=list, description="API spec, user guide, and tech doc tasks", validation_alias=AliasChoices("documentation_tasks", "documentation"))


# ---------------------------------------------------------------------------
# 5. Dependency Analysis Agent Schema
# ---------------------------------------------------------------------------
class DependencyItem(BaseModel):
    component: str = Field(default="", description="Component or module name", validation_alias=AliasChoices("component", "name", "module"))
    depends_on: List[str] = Field(default_factory=list, description="Prerequisite services, tools, or components", validation_alias=AliasChoices("depends_on", "prerequisites", "dependencies"))
    explanation: str = Field(default="", description="Why this dependency relationship exists", validation_alias=AliasChoices("explanation", "reason", "description"))

    @field_validator("depends_on", mode="before")
    @classmethod
    def _parse_list(cls, v):
        return _ensure_string_list(v)


class DependencyGraph(BaseModel):
    dependencies: List[DependencyItem] = Field(default_factory=list, description="List of component dependencies", validation_alias=AliasChoices("dependencies", "component_dependencies"))
    execution_order: List[str] = Field(default_factory=list, description="Recommended build sequence for implementation", validation_alias=AliasChoices("execution_order", "build_order", "sequence"))
    critical_path: List[str] = Field(default_factory=list, description="High-risk bottleneck components on the critical path", validation_alias=AliasChoices("critical_path", "bottlenecks"))

    @field_validator("execution_order", "critical_path", mode="before")
    @classmethod
    def _parse_list(cls, v):
        return _ensure_string_list(v)


# ---------------------------------------------------------------------------
# 6. Risk Analysis Agent Schema
# ---------------------------------------------------------------------------
class RiskItem(BaseModel):
    category: str = Field(default="General", description="Category: Security, Performance, Edge Case, Integration, or Reliability", validation_alias=AliasChoices("category", "type", "risk_type"))
    description: str = Field(default="", description="Description of potential failure point or risk", validation_alias=AliasChoices("description", "risk", "details"))
    impact: str = Field(default="Medium", description="Impact level: High, Medium, or Low", validation_alias=AliasChoices("impact", "severity", "impact_level"))
    mitigation: str = Field(default="", description="Recommended engineering mitigation or prevention strategy", validation_alias=AliasChoices("mitigation", "prevention", "strategy"))


class RiskAssessment(BaseModel):
    risks: List[RiskItem] = Field(default_factory=list, description="Identified technical and operational risks", validation_alias=AliasChoices("risks", "risk_list"))
    edge_cases: List[str] = Field(default_factory=list, description="Corner/edge cases to handle during development", validation_alias=AliasChoices("edge_cases", "corner_cases"))
    overall_risk_level: str = Field(default="Moderate", description="Overall risk score: Low, Moderate, High, or Severe", validation_alias=AliasChoices("overall_risk_level", "risk_level", "overall_risk"))

    @field_validator("edge_cases", mode="before")
    @classmethod
    def _parse_list(cls, v):
        return _ensure_string_list(v)


# ---------------------------------------------------------------------------
# 7. Acceptance Criteria Agent Schema
# ---------------------------------------------------------------------------
class AcceptanceCriteriaItem(BaseModel):
    feature: str = Field(default="", description="Feature or scenario title", validation_alias=AliasChoices("feature", "title", "scenario"))
    given: str = Field(default="", description="Initial precondition state", validation_alias=AliasChoices("given", "precondition"))
    when: str = Field(default="", description="Action or event triggered", validation_alias=AliasChoices("when", "action", "event"))
    then: str = Field(default="", description="Expected outcome or assertion", validation_alias=AliasChoices("then", "outcome", "assertion"))


class AcceptanceCriteriaList(BaseModel):
    criteria: List[AcceptanceCriteriaItem] = Field(default_factory=list, description="Structured Given-When-Then criteria", validation_alias=AliasChoices("criteria", "acceptance_criteria"))
    general_rules: List[str] = Field(default_factory=list, description="General validation rules and pass/fail conditions", validation_alias=AliasChoices("general_rules", "qa_rules", "rules"))

    @field_validator("general_rules", mode="before")
    @classmethod
    def _parse_list(cls, v):
        return _ensure_string_list(v)


# ---------------------------------------------------------------------------
# 8. Technical Specification Generator Schema
# ---------------------------------------------------------------------------
class ApiEndpointSuggestion(BaseModel):
    method: str = Field(default="GET", description="HTTP Method: GET, POST, PUT, DELETE, PATCH", validation_alias=AliasChoices("method", "http_method"))
    endpoint: str = Field(default="", description="URL Path e.g. /api/v1/auth/reset-password", validation_alias=AliasChoices("endpoint", "path", "url"))
    purpose: str = Field(default="", description="Brief explanation of endpoint responsibility", validation_alias=AliasChoices("purpose", "description"))


class DatabaseTableSuggestion(BaseModel):
    table_name: str = Field(default="", description="Conceptual DB Table name", validation_alias=AliasChoices("table_name", "name", "table"))
    fields: List[str] = Field(default_factory=list, description="Key fields and data types", validation_alias=AliasChoices("fields", "columns"))
    purpose: str = Field(default="", description="Data stored and relationship", validation_alias=AliasChoices("purpose", "description"))

    @field_validator("fields", mode="before")
    @classmethod
    def _parse_list(cls, v):
        return _ensure_string_list(v)


class TechnicalSpec(BaseModel):
    executive_summary: str = Field(default="", description="High-level engineering overview of the project spec", validation_alias=AliasChoices("executive_summary", "summary"))
    system_architecture_overview: str = Field(default="", description="Architectural design summary", validation_alias=AliasChoices("system_architecture_overview", "architecture"))
    suggested_apis: List[ApiEndpointSuggestion] = Field(default_factory=list, description="Recommended REST API structure", validation_alias=AliasChoices("suggested_apis", "api_endpoints", "apis"))
    suggested_db_tables: List[DatabaseTableSuggestion] = Field(default_factory=list, description="Conceptual data model schema", validation_alias=AliasChoices("suggested_db_tables", "db_tables", "database_tables"))
    overall_complexity: str = Field(default="Medium", description="Estimated complexity rating: Low, Medium, High, Very High", validation_alias=AliasChoices("overall_complexity", "complexity"))
    development_recommendations: List[str] = Field(default_factory=list, description="Key recommendations for developers before coding", validation_alias=AliasChoices("development_recommendations", "recommendations"))
    full_report_markdown: str = Field(default="", description="Complete, beautifully formatted Markdown report", validation_alias=AliasChoices("full_report_markdown", "markdown_report", "report"))

    @field_validator("development_recommendations", mode="before")
    @classmethod
    def _parse_list(cls, v):
        return _ensure_string_list(v)


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
