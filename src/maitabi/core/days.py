"""Day-input parsing shared by bus and general search services."""


def parse_days(day_input: object) -> list[int] | None:
    """Parse day input (int, list of ints/strings, or string like '14-16, 20').

    Unrecognised shapes yield None (no day filter) instead of raising: callers
    map the result straight onto upstream query params.
    """
    if day_input is None:
        return None
    if isinstance(day_input, int):
        return [day_input]
    if isinstance(day_input, list):
        days: set[int] = set()
        for item in day_input:
            if isinstance(item, int):
                days.add(item)
            elif isinstance(item, str):
                nested = parse_days(item)
                if nested is not None:
                    days.update(nested)
        return sorted(days) if days else None

    if isinstance(day_input, str):
        days = set()
        for part in day_input.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                try:
                    start_str, end_str = part.split("-", 1)
                    start, end = int(start_str), int(end_str)
                    if start <= end:
                        days.update(range(start, end + 1))
                except ValueError:
                    continue
            elif part.isdigit():
                days.add(int(part))
        return sorted(days) if days else None
    return None
