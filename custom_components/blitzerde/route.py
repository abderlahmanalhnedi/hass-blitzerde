"""Pure route geometry helpers for Blitzer.de."""

from __future__ import annotations

import math
from itertools import pairwise

_EARTH_RADIUS_M = 6_371_008.8


def route_sample_points(
    waypoints: list[dict[str, float]],
    corridor_width_m: float,
) -> list[tuple[float, float]]:
    """Interpolate overlapping query centers along each route segment."""
    if not waypoints:
        return []

    points: list[tuple[float, float]] = [
        (
            float(waypoints[0]["latitude"]),
            float(waypoints[0]["longitude"]),
        )
    ]

    for start, end in pairwise(waypoints):
        start_lat = float(start["latitude"])
        start_lng = float(start["longitude"])
        end_lat = float(end["latitude"])
        end_lng = float(end["longitude"])

        segment_m = haversine_m(
            start_lat,
            start_lng,
            end_lat,
            end_lng,
        )
        steps = max(
            1,
            math.ceil(
                segment_m / max(corridor_width_m, 1.0)
            ),
        )
        for step in range(1, steps + 1):
            fraction = step / steps
            points.append(
                (
                    start_lat
                    + (end_lat - start_lat) * fraction,
                    start_lng
                    + (end_lng - start_lng) * fraction,
                )
            )

    return points


def route_query_count(
    waypoints: list[dict[str, float]],
    corridor_width_m: float,
) -> int:
    """Return how many upstream circles a route needs."""
    if len(waypoints) < 2:
        return 0
    return len(
        route_sample_points(
            waypoints, corridor_width_m
        )
    )


def distance_to_route_km(
    latitude: float,
    longitude: float,
    waypoints: list[dict[str, float]],
) -> float:
    """Approximate shortest distance from a POI to the waypoint polyline."""
    distances = [
        distance_point_to_segment_m(
            latitude,
            longitude,
            float(start["latitude"]),
            float(start["longitude"]),
            float(end["latitude"]),
            float(end["longitude"]),
        )
        for start, end in pairwise(waypoints)
    ]
    return min(distances) / 1000 if distances else math.inf


def distance_point_to_segment_m(
    point_lat: float,
    point_lng: float,
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
) -> float:
    """Distance to a short WGS84 segment using a local equirectangular plane."""
    reference_lat = math.radians(
        (point_lat + start_lat + end_lat) / 3
    )

    def xy(lat: float, lng: float) -> tuple[float, float]:
        return (
            math.radians(lng - point_lng)
            * _EARTH_RADIUS_M
            * math.cos(reference_lat),
            math.radians(lat - point_lat)
            * _EARTH_RADIUS_M,
        )

    sx, sy = xy(start_lat, start_lng)
    ex, ey = xy(end_lat, end_lng)
    dx = ex - sx
    dy = ey - sy
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.hypot(sx, sy)

    projection = max(
        0.0,
        min(1.0, -(sx * dx + sy * dy) / length_sq),
    )
    closest_x = sx + projection * dx
    closest_y = sy + projection * dy
    return math.hypot(closest_x, closest_y)


def haversine_m(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
) -> float:
    """Return great-circle distance in meters."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * _EARTH_RADIUS_M * math.atan2(
        math.sqrt(a), math.sqrt(1 - a)
    )
