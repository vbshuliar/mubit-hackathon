"""Process-local guard against external outreach, always active under pytest."""
from __future__ import annotations

import os

_TRUTHY = {"1", "true", "yes", "on"}

#: Channels that reach a human outside this process.
OUTREACH_CHANNELS = ("sms", "email", "provider_booking_request")


class NoContactViolation(RuntimeError):
    """Raised instead of performing real outreach while no-contact is on."""

    def __init__(self, channel: str, target: str | None = None) -> None:
        self.channel = channel
        self.target = target
        super().__init__(
            f"no-contact mode is active: refused to use the {channel} transport"
            + (f" for {target}" if target else "")
            + ". Unset FIXI_NO_CONTACT (and run outside pytest) to allow real outreach."
        )


def no_contact_enabled() -> bool:
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return True
    return os.environ.get("FIXI_NO_CONTACT", "").strip().lower() in _TRUTHY


def assert_contact_allowed(channel: str, target: str | None = None) -> None:
    """Call immediately before any network write that reaches a person.

    Raises `NoContactViolation` when the process is in no-contact mode.
    Callers should let it propagate: every outreach path in this codebase
    already records a durable failure event for an exception, so the
    refusal is audited rather than swallowed.
    """
    if no_contact_enabled():
        raise NoContactViolation(channel, target)
