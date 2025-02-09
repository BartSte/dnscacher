from collections.abc import Iterable


def product(objects: list[object], format_specs: Iterable[str]) -> str:
    """Return a list of formatted strings, concatenated by a newline character.

    Args:
        objects (list[object]): List of objects.
        format_specs (list[str]): List of format specifications.

    Returns:
        formatted string

    """
    result: str = ""
    for spec in format_specs:
        for obj in objects:
            result += format(obj, spec)
            result += "\n" if not result.endswith("\n") else ""

    return result.strip()
