# Maitabi MCP Server

## Tagline
Search Japanese alpine bus tours, mountain lodges, and trekking packages from Maitabi.

## Description
Maitabi MCP Server provides AI agents with real-time access to Japan's premier alpine transportation and mountain tour network, Maitabi (まいたび - 毎日新聞旅行 / 毎日あるぺん号). It enables LLMs to search mountain bus departures across the Japanese Alps (Northern, Central, and Southern Alps including Kamikochi, Tateyama Murodo, Hakuba, Yatsugatake, and Mt. Fuji), filter alpine lodge packages, inspect guided trekking itineraries, check live seat availability, and explore departure calendars. Designed for hikers, outdoor enthusiasts, travel concierges, and trip planning agents.

## Setup Requirements
- `MCP_TRANSPORT` (optional): Transport protocol to use (`stdio`, `sse`, or `streamable-http`). Default is `stdio`.
- `PORT` (optional): Port number for HTTP/SSE transport modes. Default is `8000`.
- `HOST` (optional): Host address to bind for HTTP/SSE transport modes. Default is `0.0.0.0`.
- `MCP_PATH` (optional): Path for Streamable HTTP transport mode. Default is `/mcp`.

## Category
Search & Web

## Use Cases
Japan Alpine Trip Planning, Mountain Bus Departure Search, Mountain Lodge Package Discovery, Guided Trekking Itinerary Exploration, Multi-filter Tour Comparison, Departure Calendar Matrix Tracking, Outdoor & Hiking Concierge, Travel Assistant Integration

## Features
- Search mountain bus departures and alpine lodge packages across the Japanese Alps (bus.maitabi.jp)
- Search domestic and overseas guided climbing tours and hiking trips (www.maitabi.jp)
- Support for multiple departure hubs including Tokyo (Takebashi/Shinjuku), Osaka, Kyoto, and Nagoya
- Filter by seat classes including Standard, Premium, and Double seat configurations
- Filter by specific mountain huts and lodges (e.g., Enzanso, Nishiho Sanso, Murodo Sanso)
- Filter tours by date ranges, price range, and live seat availability (excluding full/closed tours)
- Retrieve complete tour itineraries, bus stop locations, meal plans, guide details, and direct booking links
- Extract monthly departure calendar matrix and tour counts for any given year and month
- Zero API key requirement with direct connection to public Maitabi endpoints
- Seamless compatibility with stdio, SSE, and Streamable HTTP transports

## Getting Started
- "Find mountain bus tours from Tokyo to Kamikochi departing next month with available seats."
- "Search for trekking packages staying at Enzanso lodge with premium bus seating."
- "Check the departure calendar for domestic mountain climbing tours in August 2026."
- "Show me tour details, prices, and itinerary for course number 14241."
- Tool: list_filters — Fetch available filter dropdown options, departure areas, tour styles, mountain lodges, and live tour counts.
- Tool: list_district_groups — Fetch mountain area/district groups and tour counts based on active filters.
- Tool: search_tours — Search mountain bus tours and lodge packages with full filter support (departure, date, seat type, lodge, price, availability).
- Tool: get_tour_detail — Fetch complete tour schedule, pricing matrix, and bus stop details for a specific bus tour by course_no.
- Tool: search_general_tours — Search general travel tours and alpine trekking packages across 5 categories on www.maitabi.jp.
- Tool: get_general_tour_detail — Fetch complete itinerary, meal condition, guide info, and booking links for a general tour by course_no.
- Tool: get_tour_calendar — Fetch monthly departure calendar matrix and tour availability for a given year and month.

## Tags
maitabi, japan-alps, mountain-bus, trekking, hiking, travel, alpine, kamikochi, tateyama, hakuba, fuji, japan-travel, tour-search, fastmcp, mcp-server

## Documentation URL
https://github.com/phonhay103/maitabi
