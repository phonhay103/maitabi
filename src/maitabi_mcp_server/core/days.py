"""Day-input parsing shared by bus and general search services."""


def parse_days(day_input: int | list[int] | str | None) -> list[int] | None:
    """Parse day input (int, list of ints, or string like '14-16, 20') into a sorted list of ints."""
    if day_input is None:
        return None
    if isinstance(day_input, int):
        return [day_input]
    if isinstance(day_input, list):
        # Flatten strings in list if necessary, but assume list of ints for now
        days = set()
        for d in day_input:
            if isinstance(d, int):
                days.add(d)
            elif isinstance(d, str):
                parsed = parse_days(d)
                if parsed:
                    days.update(parsed)
        return sorted(list(days)) if days else None

    if isinstance(day_input, str):
        days = set()
        for part in day_input.split(','):
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                try:
                    start_str, end_str = part.split('-', 1)
                    start, end = int(start_str), int(end_str)
                    if start <= end:
                        days.update(range(start, end + 1))
                except ValueError:
                    pass
            elif part.isdigit():
                days.add(int(part))
        return sorted(list(days)) if days else None
    return None
