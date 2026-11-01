from __future__ import annotations

import re

from app.core.errors import InvalidRequestError, PreconditionRequiredError

_ETAG = re.compile(r'^(?:W/)?"?(\d{1,18})"?$')


def parse_if_match(header: str | None) -> int:
    """Accepts `"4"`, `W/"4"` or `4`. A revision is mandatory for event updates."""
    if header is None or not header.strip():
        raise PreconditionRequiredError(
            "An If-Match header with the event revision is required.",
        )
    match = _ETAG.match(header.strip())
    if not match:
        raise InvalidRequestError('The If-Match header must contain an event revision, e.g. "4".')
    return int(match.group(1))


def etag(revision: int) -> str:
    return f'"{revision}"'
