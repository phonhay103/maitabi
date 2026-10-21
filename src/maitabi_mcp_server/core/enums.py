"""Enumeration IDs shared by MCP tools, CLI flags, and raw-HTTP extraction."""

from enum import IntEnum


class TravelType(IntEnum):
    """Category ID for Maitabi general tours (www.maitabi.jp)."""

    DOMESTIC_MOUNTAIN = 1  # Domestic Mountain Climbing / Trekking
    DOMESTIC_TRAVEL = 2  # Domestic Travel / Hiking
    MOUNTAIN_BUS = 3  # Mountain Bus
    OVERSEAS_MOUNTAIN = 4  # Overseas Mountain Climbing / Trekking
    OVERSEAS_TRAVEL = 5  # Overseas Travel


class DeparturePoint(IntEnum):
    """Point of departure for Maitabi bus tours (bus.maitabi.jp)."""

    TOKYO = 1  # Departure from Tokyo (Takebashi / Shinjuku)
    OSAKA_KYOTO = 2  # Departure from Osaka / Kyoto
    NAGOYA = 3  # Departure from Nagoya


class TourStyle(IntEnum):
    """Tour style ID for mountain bus tours."""

    ROUND_TRIP_BUS = 1  # Round-trip bus only (daytime departure, no mountain lodge)
    OUTBOUND_BUS = 2  # Outbound bus only (daytime departure)
    INBOUND_BUS = 3  # Inbound bus only (daytime departure)
    ROUND_TRIP_LODGE = 4  # Round-trip bus with mountain lodge (daytime departure, stay overnight at lodge)
    OUTBOUND_LODGE = 5  # Outbound bus with mountain lodge (daytime departure, stay overnight at lodge)
    OVERNIGHT_DAY_TRIP = 6  # Night bus departure from Tokyo → arrive at mountain early morning → day hike → return same day (no lodge stay); 夜行日帰り/往復夜行
    TAXI_PLAN = 7  # Taxi plan


class ReturnDayOption(IntEnum):
    """Return date option ID for mountain bus tours relative to departure."""

    DAY_1 = 1  # Return 1 day after departure — used for style=6 (night bus: depart day 0 night, return day 1 evening)
    DAY_2 = 2  # Return 2 days after departure (1 night stay at mountain lodge)
    DAY_3 = 3  # Return 3 days after departure (2 nights stay)
    DAY_4 = 4  # Return 4 days after departure (3 nights stay)
    DAY_5 = 5  # Return 5 days after departure (4 nights stay)


class BusSeatType(IntEnum):
    """Bus seat configuration ID for mountain bus tours."""

    STANDARD = 1  # Standard seat
    PREMIUM = 2  # Premium seat
    OUTBOUND_PREMIUM_INBOUND_STANDARD = 3  # Outbound Premium, Inbound Standard
    OUTBOUND_STANDARD_INBOUND_PREMIUM = 4  # Outbound Standard, Inbound Premium
    DOUBLE_SEAT = 5  # Double seat option
    TAXI = 6  # Taxi option
