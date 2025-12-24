# app/models/date_labels.py

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ========== Date Label Literal Type ==========
# This is the single source of truth for all valid date labels

DateLabelLiteral = Literal[
    # Relative dates
    "today",
    "yesterday",
    "this_week",
    "last_week",
    "this_month",
    "mtd",
    "last_month",
    "this_year",
    "last_year",
    "ytd",
    
    # Past X days - SPECIFIC predefined values
    "past_7_days",
    "past_14_days",
    "past_30_days",
    "past_60_days",
    "past_90_days",
    "past_180_days",
    
    # Past X days - GENERIC (requires custom_days_count)
    "past_days",
    
    # Specific months
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
    
    # Quarters
    "q1",
    "q2",
    "q3",
    "q4",
    
    # Special cases
    "explicit_date",  # User gave specific date like "Oct 15"
    "default"         # No date mentioned (becomes past_7_days)
]


# ========== Helper: Get all valid labels as list ==========
# Useful for prompts, validation, etc.

def get_all_date_labels() -> list[str]:
    """Return all valid date label values as a list."""
    return [
        "today", "yesterday", "this_week", "last_week",
        "this_month", "mtd", "last_month", "this_year", "last_year", "ytd",
        "past_7_days", "past_14_days", "past_30_days", "past_60_days", "past_90_days", "past_180_days",
        "past_days",
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december",
        "q1", "q2", "q3", "q4",
        "explicit_date", "default"
    ]

class NormalizedDates(BaseModel):
    """
    Output from Label Extractor (Node 1).
    
    Uses DateLabelLiteral for type safety.
    The LLM must return one of the predefined label values.
    """
    
    # Primary period labels (REQUIRED)
    date_start_label: DateLabelLiteral = Field(
        description="Label for start date. Use 'past_days' for custom day counts (not 7/14/30/60/90)."
    )
    date_end_label: DateLabelLiteral = Field(
        description="Label for end date. Use 'past_days' for custom day counts."
    )
    
    # Comparison period labels (OPTIONAL)
    compare_date_start_label: Optional[DateLabelLiteral] = Field(
        default=None,
        description="Label for comparison start date (for comparison questions)"
    )
    compare_date_end_label: Optional[DateLabelLiteral] = Field(
        default=None,
        description="Label for comparison end date (for comparison questions)"
    )
    
    # Metadata: Explicit dates (when label is "explicit_date")
    explicit_date_start: Optional[str] = Field(
        default=None,
        description="Actual date if date_start_label is 'explicit_date' (YYYY-MM-DD)"
    )
    explicit_date_end: Optional[str] = Field(
        default=None,
        description="Actual date if date_end_label is 'explicit_date' (YYYY-MM-DD)"
    )
    explicit_compare_start: Optional[str] = Field(
        default=None,
        description="Actual date if compare_date_start_label is 'explicit_date'"
    )
    explicit_compare_end: Optional[str] = Field(
        default=None,
        description="Actual date if compare_date_end_label is 'explicit_date'"
    )
    
    # Metadata: Custom days count (when label is "past_days")
    custom_days_count: Optional[int] = Field(
        default=None,
        description="REQUIRED if label is 'past_days'. Number of days (e.g., 9, 23, 100)."
    )