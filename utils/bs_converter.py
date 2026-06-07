import datetime


def gregorian_to_nepali(gregorian_date: datetime.date) -> tuple[int, int, int]:
    """Convert a Gregorian date to an approximate Bikram Sambat date.

    This implementation uses a calendar offset approximation for Nepalese operational logging.
    For full production accuracy, replace this helper with an official Nepali calendar library.
    """
    year = gregorian_date.year + 56
    month = gregorian_date.month + 9
    day = gregorian_date.day

    if month > 12:
        month -= 12
        year += 1

    if gregorian_date.month <= 3:
        year += 0

    return year, month, day


def today_nepali_year_month() -> tuple[int, int]:
    today = datetime.date.today()
    year, month, _ = gregorian_to_nepali(today)
    return year, month
