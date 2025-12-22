from pydantic import BaseModel


class DateRange(BaseModel):
    """Single date range extraction."""
    date_start: str
    date_end: str


class ComparisonDateRange(BaseModel):
    """Two date ranges for comparison queries."""
    date_start: str
    date_end: str
    compare_date_start: str
    compare_date_end: str


class AsinDateRange(BaseModel):
    """ASIN and date range extraction."""
    asin: str
    date_start: str
    date_end: str

