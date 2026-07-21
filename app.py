"""
SpecPilot - Agentic Software Requirement Analysis Assistant.
Streamlit Web Application powered by LangGraph, LangChain, Groq, and Pydantic.
"""

import os
import streamlit as st
from dotenv import load_dotenv

from utils.helper import SAMPLE_REQUIREMENTS, generate_pdf_report
from graph.workflow import execute_analysis_workflow

# Load environment variables
load_dotenv()

# Streamlit Page Configuration
st.set_page_config(
    page_title="SpecPilot - Requirement Analysis Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Glassmorphism, Vibrant Dark/Light theme, Modern Typography)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .main-subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-bottom: 1rem;
    }
    
    .badge-container {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    
    .tech-badge {
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .card-box {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 1.25rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.5rem;
        transition: all 0.2s ease-in-out;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    
    .metric-badge-high {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 700;
    }
    
    .metric-badge-medium {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 700;
    }

    .metric-badge-low {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State Variables
if "requirement_input" not in st.session_state:
    st.session_state.requirement_input = ""
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "is_analyzing" not in st.session_state:
    st.session_state.is_analyzing = False


# Sidebar Configuration
with st.sidebar:
    st.title("⚙️ Settings & Configuration")
    
    env_api_key = os.getenv("GROQ_API_KEY", "")
    api_key_input = st.text_input(
        "Groq API Key",
        value=env_api_key,
        type="password",
        help="Required for LLM inference via Groq (llama-3.3-70b-versatile)."
    )
    
    st.markdown("---")
    st.markdown("### 🤖 Agent Architecture Flow")
    st.markdown("""
    1. 🧠 **Planner Agent**
    2. 📋 **Requirement Agent**
    3. 🔍 **Ambiguity Agent**
    4. 🛠️ **Task Breakdown Agent**
    5. 🔗 **Dependency Agent**
    6. ⚠️ **Risk Analysis Agent**
    7. ✅ **Acceptance Agent**
    8. 📄 **Technical Spec Generator**
    """)
    
    st.markdown("---")
    st.markdown("### ℹ️ About SpecPilot")
    st.caption("Built with LangGraph, LangChain, Groq, Pydantic & Streamlit. Designed for modern engineering team requirement refinement.")
    
    if st.button("🗑️ Clear Session State"):
        st.session_state.analysis_results = None
        st.session_state.requirement_input = ""
        st.rerun()


# Main Page Header
st.markdown("""
<div class="main-header">
    <div class="main-title">✈️ SpecPilot</div>
    <div class="main-subtitle">Agentic Software Requirement Analysis Assistant</div>
    <div class="badge-container">
        <span class="tech-badge">LangGraph Orchestrated</span>
        <span class="tech-badge">Groq Llama 3.3 70B</span>
        <span class="tech-badge">Pydantic Schema Enforced</span>
        <span class="tech-badge">Local Execution</span>
    </div>
</div>
""", unsafe_allow_html=True)


# Sample Requirement Selector Section
st.subheader("💡 Try Sample Requirements")
cols = st.columns(len(SAMPLE_REQUIREMENTS))
for idx, (label, sample_text) in enumerate(SAMPLE_REQUIREMENTS.items()):
    with cols[idx]:
        if st.button(label, use_container_width=True):
            st.session_state.requirement_input = sample_text
            st.rerun()


# Main Input Area
st.subheader("📝 Enter Software Requirement")
user_requirement = st.text_area(
    "Paste plain English product requirements, feature requests, or user stories below:",
    value=st.session_state.requirement_input,
    height=150,
    placeholder="e.g. Users should be able to reset their password using email verification..."
)

col_run, col_info = st.columns([1, 4])
with col_run:
    run_btn = st.button("🚀 Analyze Requirement", use_container_width=True)

if run_btn:
    if not user_requirement.strip():
        st.error("Please enter a software requirement before analyzing.")
    elif not api_key_input:
        st.error("Groq API Key is missing! Please provide it in the sidebar or in your `.env` file.")
    else:
        st.session_state.is_analyzing = True
        st.session_state.requirement_input = user_requirement
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(message: str, pct: int):
            status_text.markdown(f"**Current Status:** {message}")
            progress_bar.progress(pct)

        try:
            with st.spinner("Multi-Agent Graph executing..."):
                results = execute_analysis_workflow(
                    requirement_text=user_requirement,
                    api_key=api_key_input,
                    progress_callback=update_progress
                )
            
            st.session_state.analysis_results = results
            st.session_state.is_analyzing = False
            status_text.success("🎉 Multi-Agent Requirement Analysis Completed Successfully!")
            progress_bar.progress(100)
            st.rerun()
            
        except Exception as e:
            st.session_state.is_analyzing = False
            st.error(f"Execution Error: {str(e)}")


# Display Analysis Results
if st.session_state.analysis_results:
    res = st.session_state.analysis_results
    
    st.markdown("---")
    st.header("📊 Technical Analysis Results")
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📋 Requirements",
        "🔍 Ambiguity",
        "🛠️ Tasks",
        "🔗 Dependencies",
        "⚠️ Risks",
        "✅ Acceptance",
        "📄 Technical Spec",
        "🧠 Agent Logs"
    ])
    
    # -----------------------------------------------------------------------
    # Tab 1: Requirements Breakdown
    # -----------------------------------------------------------------------
    with tab1:
        req = res.get("requirement_output", {})
        if req:
            st.markdown(f"### Summary\n{req.get('summary', '')}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### ⚙️ Functional Requirements")
                for item in req.get("functional_requirements", []):
                    st.markdown(f"- {item}")
                    
                st.markdown("#### 👥 User Roles / Actors")
                for actor in req.get("actors", []):
                    st.markdown(f"- `{actor}`")
            
            with c2:
                st.markdown("#### 🛡️ Non-functional Requirements")
                for item in req.get("non_functional_requirements", []):
                    st.markdown(f"- {item}")
                    
                st.markdown("#### ✨ Main Features")
                for feat in req.get("main_features", []):
                    st.markdown(f"- **{feat}**")

    # -----------------------------------------------------------------------
    # Tab 2: Ambiguity & Questions
    # -----------------------------------------------------------------------
    with tab2:
        amb = res.get("ambiguity_output", {})
        if amb:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### ❓ Clarifying Developer Questions")
                st.caption("Ask product owners these questions before sprint planning:")
                for q in amb.get("developer_questions", []):
                    st.warning(f"• {q}")
                    
                st.markdown("#### 🔍 Ambiguous Phrasing")
                for a in amb.get("ambiguous_statements", []):
                    st.markdown(f"- *\"{a}\"*")
            
            with c2:
                st.markdown("#### 🚨 Missing Details")
                for m in amb.get("missing_details", []):
                    st.error(f"• {m}")
                    
                st.markdown("#### 📌 Working Assumptions Made")
                for asm in amb.get("assumptions_made", []):
                    st.info(f"• {asm}")

    # -----------------------------------------------------------------------
    # Tab 3: Engineering Tasks
    # -----------------------------------------------------------------------
    with tab3:
        tasks = res.get("task_output", {})
        if tasks:
            st.markdown("### 🛠️ Categorized Engineering Task List")
            
            sub_tabs = st.tabs(["Frontend", "Backend", "Database (Conceptual)", "Testing", "Documentation"])
            
            categories = [
                (sub_tabs[0], "frontend_tasks", "🎨"),
                (sub_tabs[1], "backend_tasks", "⚙️"),
                (sub_tabs[2], "database_suggestions", "🗄️"),
                (sub_tabs[3], "testing_tasks", "🧪"),
                (sub_tabs[4], "documentation_tasks", "📚")
            ]
            
            for tab_obj, key, icon in categories:
                with tab_obj:
                    task_list = tasks.get(key, [])
                    if not task_list:
                        st.info("No specific tasks in this category.")
                    for t in task_list:
                        priority = t.get("priority", "Medium")
                        p_color = "red" if priority == "High" else "orange" if priority == "Medium" else "green"
                        with st.expander(f"{icon} {t.get('title', 'Task')}  | Priority: :{p_color}[{priority}]"):
                            st.write(t.get("description", ""))

    # -----------------------------------------------------------------------
    # Tab 4: Dependencies
    # -----------------------------------------------------------------------
    with tab4:
        deps = res.get("dependency_output", {})
        if deps:
            st.markdown("### 🔗 System Dependencies & Execution Plan")
            
            st.markdown("#### 🏗️ Recommended Execution Order")
            order = deps.get("execution_order", [])
            for idx, step in enumerate(order, 1):
                st.markdown(f"**Step {idx}:** `{step}`")
                
            st.markdown("---")
            st.markdown("#### 🎯 Critical Path Components")
            for cp in deps.get("critical_path", []):
                st.error(f"Critical Component: **{cp}**")
                
            st.markdown("---")
            st.markdown("#### 🧩 Dependency Graph Breakdown")
            for dep in deps.get("dependencies", []):
                with st.expander(f"Component: {dep.get('component', '')}"):
                    st.write(f"**Prerequisites:** {', '.join(dep.get('depends_on', []))}")
                    st.write(f"**Explanation:** {dep.get('explanation', '')}")

    # -----------------------------------------------------------------------
    # Tab 5: Risks & Edge Cases
    # -----------------------------------------------------------------------
    with tab5:
        risk = res.get("risk_output", {})
        if risk:
            overall_level = risk.get("overall_risk_level", "Moderate")
            st.markdown(f"### Overall Risk Rating: **{overall_level}**")
            
            st.markdown("#### ⚠️ Technical Risks & Mitigations")
            for r in risk.get("risks", []):
                impact = r.get("impact", "Medium")
                badge_class = "metric-badge-high" if impact == "High" else "metric-badge-medium"
                
                with st.expander(f"[{r.get('category', 'Risk')}] {r.get('description', '')[:80]}..."):
                    st.markdown(f"**Category:** {r.get('category')}")
                    st.markdown(f"**Impact:** <span class='{badge_class}'>{impact}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Description:** {r.get('description')}")
                    st.markdown(f"**Mitigation:** {r.get('mitigation')}")
                    
            st.markdown("---")
            st.markdown("#### 🧪 Critical Edge Cases to Handle")
            for ec in risk.get("edge_cases", []):
                st.warning(f"• {ec}")

    # -----------------------------------------------------------------------
    # Tab 6: Acceptance Criteria
    # -----------------------------------------------------------------------
    with tab6:
        acc = res.get("acceptance_output", {})
        if acc:
            st.markdown("### ✅ Testable Acceptance Criteria")
            
            st.markdown("#### 🥒 Given-When-Then Scenarios")
            for idx, c in enumerate(acc.get("criteria", []), 1):
                with st.container():
                    st.markdown(f"**Scenario {idx}: {c.get('feature', '')}**")
                    st.markdown(f"- **Given** {c.get('given')}")
                    st.markdown(f"- **When** {c.get('when')}")
                    st.markdown(f"- **Then** {c.get('then')}")
                    st.markdown("---")
                    
            st.markdown("#### 📏 General QA Pass/Fail Rules")
            for rule in acc.get("general_rules", []):
                st.markdown(f"- {rule}")

    # -----------------------------------------------------------------------
    # Tab 7: Technical Specification & PDF
    # -----------------------------------------------------------------------
    with tab7:
        spec = res.get("spec_output", {})
        if spec:
            st.markdown("### 📄 Technical Specification Document")
            
            col_spec_header, col_pdf = st.columns([3, 1])
            with col_spec_header:
                st.markdown(f"**Overall System Complexity:** `{spec.get('overall_complexity', 'Medium')}`")
            with col_pdf:
                # Generate PDF Bytes
                markdown_content = spec.get("full_report_markdown", "")
                if not markdown_content:
                    markdown_content = f"# Executive Summary\n{spec.get('executive_summary', '')}\n\n# System Architecture\n{spec.get('system_architecture_overview', '')}"
                    
                pdf_bytes = generate_pdf_report(
                    markdown_text=markdown_content,
                    requirement_title=st.session_state.requirement_input[:30]
                )
                st.download_button(
                    label="📥 Download Spec PDF",
                    data=pdf_bytes,
                    file_name="SpecPilot_Technical_Specification.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
            st.markdown("#### 📌 Executive Summary")
            st.info(spec.get("executive_summary", ""))
            
            st.markdown("#### 🌐 Suggested REST API Endpoints")
            apis = spec.get("suggested_apis", [])
            if apis:
                st.table([{
                    "Method": a.get("method"),
                    "Endpoint": a.get("endpoint"),
                    "Purpose": a.get("purpose")
                } for a in apis])
                
            st.markdown("#### 🗄️ Conceptual Database Schema Suggestions")
            dbs = spec.get("suggested_db_tables", [])
            if dbs:
                for db in dbs:
                    with st.expander(f"Table: {db.get('table_name')} ({db.get('purpose')})"):
                        st.markdown(f"**Fields:** `{', '.join(db.get('fields', []))}`")
                        
            st.markdown("---")
            st.markdown("#### 📄 Full Generated Specification Report")
            st.markdown(spec.get("full_report_markdown", ""))

    # -----------------------------------------------------------------------
    # Tab 8: Agent Execution Logs
    # -----------------------------------------------------------------------
    with tab8:
        st.markdown("### 🧠 Multi-Agent Execution Reasoning Logs")
        logs = res.get("execution_logs", [])
        for log in logs:
            with st.expander(f"🤖 {log.get('agent')} - Status: {log.get('status')}"):
                st.write(log.get("summary"))
