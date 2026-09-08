"""
Transforms position data from UniFi Design (presumably normalized 0..1 or
pixels relative to the map image size - MUST be verified against real API
responses, see TODO below) into the coordinate system netbox_floorplan
expects for its `layout` JSON field (pixels relative to canvas size, see
the dashboard debugging analysis).

TODO before production use: log a real `get_maps()` response against your
UCK (e.g. via `python manage.py shell` + calling client.py manually) and check:
  1. Are x/y normalized (0..1) or already pixel values?
  2. Is the origin (0,0) top-left or bottom-left?
  3. Is there a per-map rotation angle that needs to be accounted for?
Only then finalize/adjust this function.
"""

_NORMALIZED_TOLERANCE = 0.01


def unifi_to_floorplan_coords(
    unifi_x: float,
    unifi_y: float,
    unifi_map_width: float,
    unifi_map_height: float,
    floorplan_canvas_width: float,
    floorplan_canvas_height: float,
    normalized: bool = True,
) -> tuple[float, float]:
    """
    Converts a single UniFi coordinate into floorplan canvas pixels.

    :param normalized: True if unifi_x/unifi_y are already 0..1 values (then
        they are range-checked against [0, 1] as a safety check - a value
        outside that range means the "normalized" assumption is wrong for
        this API response and needs to be re-verified, see the module TODO).
        False if unifi_x/unifi_y are pixel values relative to
        unifi_map_width/height.
    """
    if normalized:
        lo, hi = -_NORMALIZED_TOLERANCE, 1 + _NORMALIZED_TOLERANCE
        if not (lo <= unifi_x <= hi) or not (lo <= unifi_y <= hi):
            raise ValueError(
                f'unifi_x/unifi_y ({unifi_x}, {unifi_y}) outside the expected 0..1 range - '
                f'the normalized coordinate assumption may be wrong for this API response.'
            )
        fx_ratio, fy_ratio = unifi_x, unifi_y
    else:
        if not unifi_map_width or not unifi_map_height:
            raise ValueError('unifi_map_width/height required when normalized=False')
        fx_ratio = unifi_x / unifi_map_width
        fy_ratio = unifi_y / unifi_map_height

    return (
        fx_ratio * floorplan_canvas_width,
        fy_ratio * floorplan_canvas_height,
    )
