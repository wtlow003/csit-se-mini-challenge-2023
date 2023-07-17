from datetime import date
from typing import Tuple


def validate_date_format(date_str: str) -> Tuple[bool, str]:
    """_summary_

    Args:
        date (str): _description_

    Returns:
        _type_: _description_
    """
    correct = False
    try:
        date.fromisoformat(date_str)
        correct = True
    except ValueError:
        correct = False

    return correct, date_str
