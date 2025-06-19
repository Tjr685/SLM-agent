import re
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
import calendar

class DateParser:
    """
    Natural language date parser for customer support workflows.
    Handles flexible date formats like "20th June 2025", "next month", etc.
    """
    
    # Month mappings
    MONTH_NAMES = {
        # Full month names
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
        
        # Abbreviated month names
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12    }
    
    def __init__(self):
        # Pre-compile regex patterns for better performance
        self.iso_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        self.ordinal_pattern = re.compile(r'(\d{1,2})(st|nd|rd|th)\s+(\w+)\s+(\d{4})')
        self.standard_pattern = re.compile(r'(\w+)\s+(\d{1,2}),?\s+(\d{4})')
        self.reverse_pattern = re.compile(r'(\d{1,2})/(\d{1,2})/(\d{4})')
        self.short_pattern = re.compile(r'(\d{1,2})-(\d{1,2})-(\d{4})')
        self.space_pattern = re.compile(r'(\d{1,2})\s+(\w+)\s+(\d{4})')  # "20 June 2025"
        self.dot_pattern = re.compile(r'(\d{1,2})\.(\d{1,2})\.(\d{4})')   # "20.06.2025"
    
    def parse_date(self, date_input: str) -> Tuple[bool, str, Optional[str]]:
        """
        Parse a date string into YYYY-MM-DD format.
        
        Args:
            date_input: Natural language date string
            
        Returns:
            Tuple of (success: bool, result: str, error_message: Optional[str])
            - If success: (True, "YYYY-MM-DD", None)
            - If failure: (False, original_input, error_message)
        """
        if not date_input or not isinstance(date_input, str):
            return False, date_input or "", "Date input is required"
        
        date_input = date_input.strip()
        
        try:
            # 1. Check if already in YYYY-MM-DD format
            if self.iso_pattern.match(date_input):
                # Validate the date is actually valid
                parsed_date = datetime.strptime(date_input, '%Y-%m-%d').date()
                return True, date_input, None
            
            # 2. Handle relative dates
            relative_result = self._parse_relative_date(date_input)
            if relative_result:
                return True, relative_result.strftime('%Y-%m-%d'), None
            
            # 3. Handle ordinal dates (20th June 2025, 1st January 2024)
            ordinal_match = self.ordinal_pattern.search(date_input.lower())
            if ordinal_match:
                day = int(ordinal_match.group(1))
                month_name = ordinal_match.group(3)
                year = int(ordinal_match.group(4))
                
                month = self.MONTH_NAMES.get(month_name.lower())
                if month:
                    parsed_date = date(year, month, day)
                    return True, parsed_date.strftime('%Y-%m-%d'), None
            
            # 4. Handle standard formats (June 20, 2025 or June 20 2025)
            standard_match = self.standard_pattern.search(date_input.lower())
            if standard_match:
                month_name = standard_match.group(1)
                day = int(standard_match.group(2))
                year = int(standard_match.group(3))
                
                month = self.MONTH_NAMES.get(month_name.lower())
                if month:
                    parsed_date = date(year, month, day)
                    return True, parsed_date.strftime('%Y-%m-%d'), None
              # 5. Handle MM/DD/YYYY format (fix the logic)
            reverse_match = self.reverse_pattern.match(date_input)
            if reverse_match:
                month = int(reverse_match.group(1))
                day = int(reverse_match.group(2))
                year = int(reverse_match.group(3))
                
                # Validate month and day ranges
                if 1 <= month <= 12 and 1 <= day <= 31:
                    parsed_date = date(year, month, day)
                    return True, parsed_date.strftime('%Y-%m-%d'), None
            
            # 6. Handle DD-MM-YYYY format  
            short_match = self.short_pattern.match(date_input)
            if short_match:
                day = int(short_match.group(1))
                month = int(short_match.group(2))
                year = int(short_match.group(3))
                
                # Validate ranges
                if 1 <= month <= 12 and 1 <= day <= 31:
                    parsed_date = date(year, month, day)
                    return True, parsed_date.strftime('%Y-%m-%d'), None
            
            # 7. Handle "20 June 2025" format (space separated)
            space_match = self.space_pattern.search(date_input.lower())
            if space_match:
                day = int(space_match.group(1))
                month_name = space_match.group(2)
                year = int(space_match.group(3))
                
                month = self.MONTH_NAMES.get(month_name.lower())
                if month:
                    parsed_date = date(year, month, day)
                    return True, parsed_date.strftime('%Y-%m-%d'), None
            
            # 8. Handle DD.MM.YYYY format
            dot_match = self.dot_pattern.match(date_input)
            if dot_match:
                day = int(dot_match.group(1))
                month = int(dot_match.group(2))
                year = int(dot_match.group(3))
                
                # Validate ranges
                if 1 <= month <= 12 and 1 <= day <= 31:
                    parsed_date = date(year, month, day)
                    return True, parsed_date.strftime('%Y-%m-%d'), None
            
            # If none of the patterns match
            return False, date_input, f"Could not parse date format: '{date_input}'. Supported formats: YYYY-MM-DD, '20th June 2025', 'June 20, 2025', 'next month', 'tomorrow', etc."
            
        except ValueError as e:
            return False, date_input, f"Invalid date: {str(e)}"
        except Exception as e:
            return False, date_input, f"Error parsing date: {str(e)}"
    
    def _parse_relative_date(self, date_input: str) -> Optional[date]:
        """Parse relative date expressions like 'tomorrow', 'next month', etc."""
        date_input = date_input.lower().strip()
        today = date.today()
        
        if date_input in ['today']:
            return today
        elif date_input in ['tomorrow']:
            return today + timedelta(days=1)
        elif date_input in ['yesterday']:
            return today - timedelta(days=1)
        elif date_input in ['next week']:
            return today + timedelta(weeks=1)
        elif date_input in ['next month']:
            # Go to first day of next month
            if today.month == 12:
                return date(today.year + 1, 1, 1)
            else:
                return date(today.year, today.month + 1, 1)
        elif date_input in ['next year']:
            return date(today.year + 1, today.month, today.day)
        elif 'days' in date_input:
            # Handle "in 30 days", "30 days from now"
            days_match = re.search(r'(\d+)\s*days?', date_input)
            if days_match:
                days = int(days_match.group(1))
                return today + timedelta(days=days)
        elif 'weeks' in date_input:
            # Handle "in 2 weeks", "2 weeks from now"
            weeks_match = re.search(r'(\d+)\s*weeks?', date_input)
            if weeks_match:
                weeks = int(weeks_match.group(1))
                return today + timedelta(weeks=weeks)
        elif 'months' in date_input:
            # Handle "in 3 months", "3 months from now"
            months_match = re.search(r'(\d+)\s*months?', date_input)
            if months_match:
                months = int(months_match.group(1))
                target_month = today.month + months
                target_year = today.year
                
                while target_month > 12:
                    target_month -= 12
                    target_year += 1
                
                # Handle day overflow (e.g., Jan 31 + 1 month = Feb 28/29)
                try:
                    return date(target_year, target_month, today.day)
                except ValueError:
                    # Day doesn't exist in target month, use last day of month
                    last_day = calendar.monthrange(target_year, target_month)[1]
                    return date(target_year, target_month, last_day)
        
        return None
    
    def validate_future_date(self, date_str: str, allow_past: bool = False) -> Tuple[bool, str]:
        """
        Validate that a date is in the future (for trial extensions, etc.)
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            allow_past: Whether to allow past dates
            
        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        try:
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            today = date.today()
            
            if not allow_past and parsed_date <= today:
                return False, f"Date {date_str} must be in the future"
            
            # Check if date is too far in the future (e.g., more than 2 years)
            max_future = today + timedelta(days=730)  # 2 years
            if parsed_date > max_future:
                return False, f"Date {date_str} is too far in the future (max 2 years from today)"
            
            return True, "Valid date"
            
        except ValueError:
            return False, f"Invalid date format: {date_str}"


# Convenience function for easy import
def parse_natural_date(date_input: str) -> Tuple[bool, str, Optional[str]]:
    """
    Convenience function to parse natural language dates.
    
    Args:
        date_input: Natural language date string
        
    Returns:
        Tuple of (success: bool, result: str, error_message: Optional[str])
    """
    parser = DateParser()
    return parser.parse_date(date_input)

def validate_future_date(date_str: str, allow_past: bool = False) -> Tuple[bool, str]:
    """
    Convenience function to validate future dates.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        allow_past: Whether to allow past dates
        
    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    parser = DateParser()
    return parser.validate_future_date(date_str, allow_past)

# Example usage and testing
if __name__ == "__main__":
    parser = DateParser()
    
    test_dates = [
        "2025-06-20",           # ISO format
        "20th June 2025",       # Ordinal
        "June 20, 2025",        # Standard
        "June 20 2025",         # Standard without comma
        "6/20/2025",            # MM/DD/YYYY
        "20-06-2025",           # DD-MM-YYYY
        "20 June 2025",         # Space separated
        "20.06.2025",           # Dot separated
        "tomorrow",             # Relative
        "next month",           # Relative
        "in 30 days",           # Relative
        "invalid date",         # Invalid
    ]
    
    print("Testing date parser:")
    for test_date in test_dates:
        success, result, error = parser.parse_date(test_date)
        print(f"Input: '{test_date}' -> Success: {success}, Result: '{result}', Error: {error}")
