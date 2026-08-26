"""
Helper Utilities for SpecPilot.
Includes Groq LLM initialization, PDF report generator, and preset sample requirements.
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from fpdf import FPDF

# Load environment variables
load_dotenv()


import time

def safe_chain_invoke(chain, input_data: dict, max_retries: int = 4, base_delay: float = 3.0) -> Any:
    """
    Safely invokes a LangChain runnable chain with automatic retries on Groq TPM / RateLimit (413, 429) 
    and transient JSON validation errors (400 json_validate_failed).
    """
    for attempt in range(max_retries):
        try:
            return chain.invoke(input_data)
        except Exception as e:
            err_str = str(e).lower()
            is_retryable = any(keyword in err_str for keyword in [
                "rate limit", "rate_limit", "tpm", "429", "413", "tokens per minute",
                "request too large", "json_validate_failed", "failed to validate json", "failed_generation"
            ])
            if is_retryable and attempt < max_retries - 1:
                sleep_time = base_delay * (attempt + 1)
                time.sleep(sleep_time)
            else:
                raise e


# ---------------------------------------------------------------------------
# 1. Groq LLM Provider
# ---------------------------------------------------------------------------
def get_groq_llm(api_key: Optional[str] = None, model_name: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 4096, max_retries: int = 5) -> ChatGroq:
    """
    Initialize and return a ChatGroq LLM instance with rate-limit retries.
    Checks provided api_key, environment variable, or raises informative ValueError.
    """
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError(
            "GROQ_API_KEY not found! Please set it in your .env file or enter it in the Streamlit sidebar."
        )

    # Use specified model, environment variable, or fall back to active high-performing model
    selected_model = model_name or os.getenv("GROQ_MODEL_NAME")
    DEPRECATED_MODELS = {
        "llama-3.3-70b-versatile",
        "llama-3.3-70b-specdec",
        "llama-3.1-70b-versatile",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768"
    }
    if not selected_model or selected_model in DEPRECATED_MODELS or any(dep in str(selected_model).lower() for dep in ["llama-3.3", "llama-3.1", "llama3-", "mixtral"]):
        selected_model = "qwen/qwen3.6-27b"

    return ChatGroq(
        groq_api_key=key,
        model_name=selected_model,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries
    )


# ---------------------------------------------------------------------------
# 2. Preset Requirement Examples
# ---------------------------------------------------------------------------
SAMPLE_REQUIREMENTS = {
    "🔑 Password Reset & Email Verification": """Users should be able to reset their password using email verification. 
When a user requests a password reset, an email with a secure, time-limited token link should be sent. 
Clicking the link opens a form to enter and confirm a new password. 
System must invalidate old tokens and update credentials securely.""",

    "🍔 Online Food Delivery Platform": """Build an online food delivery application where customers can order food from local restaurants, 
pay online via card or UPI, track real-time delivery status on a map, and rate/review restaurants and drivers. 
Restaurant managers need a portal to accept orders and update menu availability.""",

    "🛒 E-Commerce Checkout & Inventory": """Implement an e-commerce checkout workflow where users can review items in their cart, 
apply discount coupon codes, calculate taxes and shipping fees, select payment methods, 
and complete payment. Upon successful payment, deduct inventory count and send an order confirmation email.""",

    "🏦 Digital Banking Fund Transfer": """Design a peer-to-peer digital banking fund transfer module. 
Users can transfer money to registered payees using account numbers or mobile handles. 
The system must enforce daily transaction limits, multi-factor authentication (MFA) for amounts over $500, 
log all transactions for audit compliance, and send real-time SMS notifications."""
}


# ---------------------------------------------------------------------------
# 3. PDF Generator Helper
# ---------------------------------------------------------------------------
class SpecPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 41, 59)  # Slate dark
        self.cell(0, 10, "SpecPilot - Technical Requirement Analysis Spec", border=False, ln=True, align="C")
        self.set_draw_color(203, 213, 225)
        self.line(10, 22, 200, 22)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def _safe_text(text: str, max_len: int = 900) -> str:
    """
    Sanitise text for FPDF:
      1. Encode to latin-1, replacing any unmappable characters.
      2. Truncate lines longer than max_len chars so no word is wider than the page.
      3. Insert a zero-width space every 80 chars so FPDF can always find a break point.
    """
    # Latin-1 encode/decode to strip unsupported unicode
    text = text.encode("latin-1", "replace").decode("latin-1")
    # Insert soft break every 80 chars to avoid "no break point" error
    words = text.split(" ")
    broken = []
    for word in words:
        if len(word) > 80:
            # Chunk long words so FPDF can wrap them
            chunks = [word[i:i+80] for i in range(0, len(word), 80)]
            broken.append(" ".join(chunks))
        else:
            broken.append(word)
    text = " ".join(broken)
    return text[:max_len]


def generate_pdf_report(markdown_text: str, requirement_title: str = "Requirement Spec") -> bytes:
    """
    Converts markdown technical specification text to downloadable PDF bytes.
    Uses explicit cell width (W=190) to avoid FPDFException in fpdf2 >= 2.7.
    """
    # A4 page: 210mm wide, margins 10mm each side → usable width = 190mm
    PAGE_W = 190

    pdf = SpecPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Document title
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(15, 23, 42)
    safe_title = _safe_text(f"Technical Analysis: {requirement_title}")
    pdf.multi_cell(PAGE_W, 8, safe_title)
    pdf.ln(4)

    lines = markdown_text.split("\n")

    for line in lines:
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            pdf.ln(3)
            continue

        # Skip Markdown code fences and table separators (unrenderable in plain PDF)
        if stripped.startswith("```") or stripped.startswith("---") or stripped.startswith("| :"):
            continue

        if stripped.startswith("# "):
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(30, 58, 138)
            pdf.multi_cell(PAGE_W, 7, _safe_text(stripped.replace("# ", "", 1)))
            pdf.ln(2)

        elif stripped.startswith("## "):
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 41, 59)
            pdf.multi_cell(PAGE_W, 6, _safe_text(stripped.replace("## ", "", 1)))
            pdf.ln(2)

        elif stripped.startswith("### "):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(71, 85, 105)
            pdf.multi_cell(PAGE_W, 5, _safe_text(stripped.replace("### ", "", 1)))
            pdf.ln(1)

        elif stripped.startswith("#### "):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(100, 116, 139)
            pdf.multi_cell(PAGE_W, 5, _safe_text(stripped.replace("#### ", "", 1)))

        elif stripped.startswith("- ") or stripped.startswith("* "):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(PAGE_W, 5, _safe_text("  - " + stripped[2:]))

        elif stripped.startswith("|"):
            # Render Markdown table rows as plain text
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(51, 65, 85)
            row_text = stripped.replace("|", "  ").strip()
            pdf.multi_cell(PAGE_W, 5, _safe_text(row_text))

        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(PAGE_W, 5, _safe_text(stripped))

    return bytes(pdf.output())

