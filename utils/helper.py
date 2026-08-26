"""
Helper Utilities for SpecPilot.
Includes Groq LLM initialization, PDF report generator, and preset sample requirements.
"""

import os
import time
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from fpdf import FPDF

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# 0. Groq Model Fallback Registry
#    Models are tried in order when a daily/minute quota is exhausted.
# ---------------------------------------------------------------------------
DEPRECATED_MODELS = {
    "llama-3.3-70b-versatile",
    "llama-3.3-70b-specdec",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    "llama3-groq-8b-8192-tool-use-preview",
}

# Ordered list of VERIFIED available models on this Groq account (queried via API).
# qwen3.6-27b is primary; qwen3.8-27b is fallback with its own separate daily quota.
GROQ_FALLBACK_MODELS: List[str] = [
    "qwen/qwen3.6-27b",
    "qwen/qwen3.8-27b",
]

# Module-level active model index — advanced when a model's daily TPD quota is exhausted.
# get_groq_llm() reads this so all agents automatically use the current fallback model.
_ACTIVE_MODEL_INDEX: int = 0


class FallbackModelAdvanced(Exception):
    """
    Sentinel raised by safe_chain_invoke when the daily quota for the current model
    is exhausted and the global model index has been advanced to the next fallback.
    The caller (workflow node) should re-invoke the agent function; it will then call
    get_groq_llm() fresh and automatically pick up the new model.
    """
    def __init__(self, new_model: str):
        self.new_model = new_model
        super().__init__(f"Switched to fallback model: {new_model}")


def advance_fallback_model() -> str:
    """
    Advance the global active model index to the next fallback model.
    Returns the name of the newly selected model.
    Raises RuntimeError if all models are exhausted.
    """
    global _ACTIVE_MODEL_INDEX
    _ACTIVE_MODEL_INDEX += 1
    if _ACTIVE_MODEL_INDEX >= len(GROQ_FALLBACK_MODELS):
        _ACTIVE_MODEL_INDEX = len(GROQ_FALLBACK_MODELS) - 1  # clamp
        raise RuntimeError(
            "All Groq model daily quotas are exhausted. "
            "Please wait for the quota to reset (~24h) or upgrade at "
            "https://console.groq.com/settings/billing"
        )
    return GROQ_FALLBACK_MODELS[_ACTIVE_MODEL_INDEX]


def safe_chain_invoke(
    chain,
    input_data: dict,
    max_retries: int = 4,
    base_delay: float = 3.0,
) -> Any:
    """
    Safely invokes a LangChain runnable chain with automatic retries on Groq rate limits:
      - TPM (tokens per minute) / 413: exponential backoff retry.
      - TPD (tokens per day) / 429:   advances the global model index and raises
        FallbackModelAdvanced so the workflow node re-invokes the agent with the new model.
      - Transient JSON / generation errors: retry with backoff.
    """
    for attempt in range(max_retries):
        try:
            return chain.invoke(input_data)
        except FallbackModelAdvanced:
            # Propagate immediately — don't swallow the sentinel
            raise
        except Exception as e:
            err_str = str(e).lower()

            # Daily quota (TPD) exhausted → advance global model, signal caller to re-invoke
            is_daily_limit = "tokens per day" in err_str or ("per day" in err_str and "429" in err_str)
            if is_daily_limit:
                new_model = advance_fallback_model()  # may raise RuntimeError if all exhausted
                print(f"[SpecPilot] Daily quota exhausted. Switching to fallback model: {new_model}")
                raise FallbackModelAdvanced(new_model) from e

            # Minute-level rate limit or transient error → exponential backoff
            is_retryable = any(keyword in err_str for keyword in [
                "rate limit", "rate_limit", "tpm", "429", "413", "tokens per minute",
                "request too large", "json_validate_failed", "failed to validate json", "failed_generation"
            ])
            if is_retryable and attempt < max_retries - 1:
                sleep_time = base_delay * (attempt + 1)
                print(f"[SpecPilot] Rate limit hit (attempt {attempt+1}/{max_retries}). Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                raise e


# ---------------------------------------------------------------------------
# 1. Groq LLM Provider
# ---------------------------------------------------------------------------
def get_groq_llm(
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    max_retries: int = 5,
) -> ChatGroq:
    """
    Initialize and return a ChatGroq LLM instance with rate-limit retries.
    Checks provided api_key, environment variable, or raises informative ValueError.
    Automatically sanitises deprecated model names to the first active fallback model.
    """
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError(
            "GROQ_API_KEY not found! Please set it in your .env file or enter it in the Streamlit sidebar."
        )

    # Use specified model, environment variable, or the currently active fallback model.
    # _ACTIVE_MODEL_INDEX is advanced by advance_fallback_model() when daily TPD is exhausted.
    selected_model = model_name or os.getenv("GROQ_MODEL_NAME")
    if not selected_model or selected_model in DEPRECATED_MODELS or "mixtral" in str(selected_model).lower():
        selected_model = GROQ_FALLBACK_MODELS[_ACTIVE_MODEL_INDEX]

    return ChatGroq(
        groq_api_key=key,
        model_name=selected_model,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,
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

