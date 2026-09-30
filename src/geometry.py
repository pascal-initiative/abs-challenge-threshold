"""Fixed a priori circle/rectangle intersection at ABS middle-of-plate plane."""
import math

BALL_RADIUS_FEET = 2.9 / 2 / 12  # Official Savant zone visualization constant, not fitted.
HALF_WIDTH_FEET = 17 / 2 / 12
METHOD = 'abs_2026_circle_rectangle_r1.45in_v1'


def derive(x, z, top, bottom, season=2026):
    if season != 2026 or any(v is None or not math.isfinite(v) for v in (x, z, top, bottom)) or top <= bottom:
        return None, None
    dx = abs(x) - HALF_WIDTH_FEET
    dz = max(bottom - z, z - top)
    # Signed distance from the ball center to the rectangle; rounded corners.
    signed = math.hypot(max(dx, 0), max(dz, 0)) + min(max(dx, dz), 0)
    distance = signed - BALL_RADIUS_FEET
    return ('STRIKE' if distance <= 0 else 'BALL'), distance
