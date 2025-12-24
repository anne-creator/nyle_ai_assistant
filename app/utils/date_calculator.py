# app/graph/nodes/shared/date_calculator.py

from datetime import datetime, timedelta, timezone
import calendar
from typing import Tuple
from app.models.date_labels import DateLabelLiteral


class DateCalculator:
    """Convert pre-defined date labels to ISO format dates."""
    
    def __init__(self, current_date=None):
        self.current_date = current_date or datetime.now(timezone.utc).date()
    
    def calculate(
        self,
        label: DateLabelLiteral,  # ⚡ TYPE SAFE: Only accepts valid labels
        explicit_date: str = None,
        custom_days: int = None
    ) -> Tuple[str, str]:
        """
        Convert label to (date_start, date_end) in ISO format.
        
        Args:
            label: One of the DateLabelLiteral values
            explicit_date: Required if label is "explicit_date"
            custom_days: Required if label is "past_days"
        
        Returns:
            (date_start, date_end) as ISO format strings (YYYY-MM-DD)
        
        Raises:
            ValueError: If required parameters are missing or label is invalid
        """
        
        # Validate: "explicit_date" requires explicit_date parameter
        if label == "explicit_date":
            if not explicit_date:
                raise ValueError("Label 'explicit_date' requires explicit_date parameter")
            return (explicit_date, explicit_date)
        
        # Validate: "past_days" requires custom_days parameter
        if label == "past_days":
            if not custom_days or custom_days <= 0:
                raise ValueError("Label 'past_days' requires custom_days_count parameter (must be > 0)")
            return self._past_x_days(custom_days)
        
        # Mapping for all other labels
        label_map = {
            # Relative dates
            "today": self._today,
            "yesterday": self._yesterday,
            "this_week": self._this_week,
            "last_week": self._last_week,
            "this_month": self._this_month,
            "mtd": self._mtd,
            "last_month": self._last_month,
            "this_year": self._this_year,
            "last_year": self._last_year,
            "ytd": self._ytd,
            
            # Past X days - SPECIFIC values
            "past_7_days": lambda: self._past_x_days(7),
            "past_14_days": lambda: self._past_x_days(14),
            "past_30_days": lambda: self._past_x_days(30),
            "past_60_days": lambda: self._past_x_days(60),
            "past_90_days": lambda: self._past_x_days(90),
            "past_180_days": lambda: self._past_x_days(180),

            # Months
            "january": lambda: self._month_range(1),
            "february": lambda: self._month_range(2),
            "march": lambda: self._month_range(3),
            "april": lambda: self._month_range(4),
            "may": lambda: self._month_range(5),
            "june": lambda: self._month_range(6),
            "july": lambda: self._month_range(7),
            "august": lambda: self._month_range(8),
            "september": lambda: self._month_range(9),
            "october": lambda: self._month_range(10),
            "november": lambda: self._month_range(11),
            "december": lambda: self._month_range(12),
            
            
            # Default
            "default": lambda: self._past_x_days(7),
        }
        
        if label not in label_map:
            # This should never happen due to Literal typing, but safeguard anyway
            raise ValueError(f"Unknown date label: {label}")
        
        return label_map[label]()
    
    # ========== Calculation Methods ==========
    # (Same as before - keeping them here for completeness)
    
    def _today(self) -> Tuple[str, str]:
        date_str = self.current_date.strftime("%Y-%m-%d")
        return (date_str, date_str)
    
    def _yesterday(self) -> Tuple[str, str]:
        yesterday = self.current_date - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")
        return (date_str, date_str)
    
    def _past_x_days(self, days: int) -> Tuple[str, str]:
        start_date = self.current_date - timedelta(days=days - 1)
        return (
            start_date.strftime("%Y-%m-%d"),
            self.current_date.strftime("%Y-%m-%d")
        )
    
    def _this_week(self) -> Tuple[str, str]:
        """This calendar week: Monday to Sunday (full week)"""
        weekday = self.current_date.weekday()
        monday = self.current_date - timedelta(days=weekday)
        sunday = monday + timedelta(days=6)
        return (
            monday.strftime("%Y-%m-%d"),
            sunday.strftime("%Y-%m-%d")
        )
    
    def _last_week(self) -> Tuple[str, str]:
        weekday = self.current_date.weekday()
        last_monday = self.current_date - timedelta(days=weekday + 7)
        last_sunday = last_monday + timedelta(days=6)
        return (
            last_monday.strftime("%Y-%m-%d"),
            last_sunday.strftime("%Y-%m-%d")
        )
    
    def _this_month(self) -> Tuple[str, str]:
        """This calendar month: First day to last day of month (full month)"""
        first_day = self.current_date.replace(day=1)
        last_day = calendar.monthrange(self.current_date.year, self.current_date.month)[1]
        last_day_date = self.current_date.replace(day=last_day)
        return (
            first_day.strftime("%Y-%m-%d"),
            last_day_date.strftime("%Y-%m-%d")
        )
    
    def _mtd(self) -> Tuple[str, str]:
        """Month-to-Date: First day of current month to today"""
        first_day = self.current_date.replace(day=1)
        return (
            first_day.strftime("%Y-%m-%d"),
            self.current_date.strftime("%Y-%m-%d")
        )
    
    def _last_month(self) -> Tuple[str, str]:
        first_this_month = self.current_date.replace(day=1)
        last_day_last_month = first_this_month - timedelta(days=1)
        first_last_month = last_day_last_month.replace(day=1)
        return (
            first_last_month.strftime("%Y-%m-%d"),
            last_day_last_month.strftime("%Y-%m-%d")
        )
    
    def _this_year(self) -> Tuple[str, str]:
        jan_1 = self.current_date.replace(month=1, day=1)
        return (
            jan_1.strftime("%Y-%m-%d"),
            self.current_date.strftime("%Y-%m-%d")
        )
    
    def _last_year(self) -> Tuple[str, str]:
        year = self.current_date.year - 1
        return (f"{year}-01-01", f"{year}-12-31")
    
    def _ytd(self) -> Tuple[str, str]:
        return self._this_year()
    
    def _month_range(self, month: int) -> Tuple[str, str]:
        year = self.current_date.year
        last_day = calendar.monthrange(year, month)[1]
        return (
            f"{year}-{month:02d}-01",
            f"{year}-{month:02d}-{last_day:02d}"
        )
    