"""Helpers for converting Blitzer.de POIs into Home Assistant attributes."""

from __future__ import annotations

from typing import Any

from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE

from .const import ATTR_DISTANCE_KM


class BlitzerItem:
    """Helpers for a single upstream POI."""

    @staticmethod
    def get_backend_id(item: dict[str, Any]) -> str:
        """Return a stable-looking backend identifier."""
        backend = str(item.get("backend", "unknown"))
        return backend.rsplit("-", 1)[-1]

    @staticmethod
    def get_picture_path(item: dict[str, Any]) -> str:
        """Return the upstream marker picture name."""
        vmax = str(item.get("vmax", "?"))
        if vmax == "?":
            vmax = "v"
        elif vmax == "/":
            vmax = "redlight"

        info = item.get("info") or {}
        if info.get("fixed"):
            return f"fixed_{vmax}"
        if info.get("partly_fixed"):
            return f"ts_{vmax}"
        return f"mobile_{vmax}"

    @staticmethod
    def get_attributes(
        item: dict[str, Any], *, include_location: bool = True
    ) -> dict[str, Any]:
        """Build safe state attributes from an upstream POI."""
        address = item.get("address") or {}
        info = item.get("info") or {}
        attrs: dict[str, Any] = {
            "backend": BlitzerItem.get_backend_id(item),
            "vmax": item.get("vmax"),
            "entity_picture": (
                "https://map.blitzer.de/v5/images/"
                f"{BlitzerItem.get_picture_path(item)}.svg"
            ),
            "counter": item.get("counter", 0),
            "city": address.get("city"),
            "street": address.get("street"),
            "zip_code": address.get("zip_code"),
        }

        if ATTR_DISTANCE_KM in item:
            attrs[ATTR_DISTANCE_KM] = item[ATTR_DISTANCE_KM]

        if include_location:
            if "lat" in item:
                attrs[ATTR_LATITUDE] = item["lat"]
            if "lng" in item:
                attrs[ATTR_LONGITUDE] = item["lng"]

        if description := info.get("desc"):
            attrs["description"] = description

        return {
            key: value
            for key, value in attrs.items()
            if value is not None
        }
