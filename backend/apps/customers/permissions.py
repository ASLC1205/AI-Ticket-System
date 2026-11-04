"""Customer-app permission imports.

Keep role checks centralized so every app applies the same authorization rules.
"""
from apps.accounts.permissions import IsCustomer, IsAdmin

__all__ = ["IsCustomer", "IsAdmin"]
