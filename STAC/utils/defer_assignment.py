import operator
from typing import Any, Protocol


class SupportsSetItem(Protocol):
    """
    Accepts `operator.setitem(obj, key, value)`,
    or equivalently `obj[key] = value`.
    """

    def __setitem__(self, key: str, value: Any, /) -> None: ...


class DeferAssignment:
    """
    Queue of assignments to apply at some later time.

    Call the instance to record a write.
    Nothing is stored until apply().
    """

    def __init__(self) -> None:
        self._pending: list[tuple[SupportsSetItem, str, Any]] = []

    def __call__(self, obj: SupportsSetItem, key: str, value: Any) -> None:
        """
        Record an assignment `obj[key] = value` for a later apply().
        """
        self._pending.append((obj, key, value))

    def apply(self) -> None:
        """Write every recorded assignment, then clear the queue."""
        for obj, key, value in self._pending:
            operator.setitem(obj, key, value)
        self._pending.clear()
