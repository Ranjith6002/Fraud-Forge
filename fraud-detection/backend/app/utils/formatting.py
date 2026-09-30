"""Human-readable formatting used in rule reasons and notifications."""

_SYMBOLS = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}


def format_money(amount: float, currency: str = "INR") -> str:
    symbol = _SYMBOLS.get((currency or "").upper())
    body = f"{amount:,.0f}" if abs(amount - round(amount)) < 0.005 else f"{amount:,.2f}"
    return f"{symbol}{body}" if symbol else f"{currency} {body}"


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f} sec"
    if seconds < 3600:
        return f"{seconds / 60:.0f} min"
    if seconds < 86400:
        return f"{seconds / 3600:.1f} h"
    return f"{seconds / 86400:.1f} days"
