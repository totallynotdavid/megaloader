#!/usr/bin/env python3
"""
MEGALOADER: Logo generator

Generates the project logo featuring an isometric cube with liquid fill effect.
Uses pixel-based rendering with dithering for retro aesthetic.

OUTPUT: logo.svg (1024x1024 SVG with transparent background)
"""

import math
import pathlib
import random


# fmt: off
CONFIG = {
    # CANVAS SETTINGS
    "width": 1024,      # Output width in pixels
    "height": 1024,     # Output height in pixels

    # PIXEL ART CONFIGURATION
    "pixel_size": 12,   # Size of each "pixel" block (24px = ~43x43 grid)

    # CUBE GEOMETRY
    "radius": 420,      # Base radius of hexagon (42% of canvas width)

    # LIQUID FILL EFFECT
    "solid_threshold": 0.65,        # Y-position where liquid becomes solid (0.0-1.0)
    "curvature_strength": 0.3,      # Meniscus curve intensity at edges

    # DITHERING & GRADIENT
    "dissolve_power": 3.5,          # Gradient transition sharpness (higher = sharper)
    "fade_start": -0.2,             # Start position for particle fade (can be negative)
    "jitter_amount": 0.04,          # Random noise amplitude for organic look

    # BRAND COLORS
    "fill_color": "#1a1a1a",      # Primary brand color (dark charcoal)
}
# fmt: on


def point_in_polygon(x, y, polygon):
    """Check if point (x, y) is inside the polygon using ray casting algorithm."""
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if (
            y > min(p1y, p2y)
            and y <= max(p1y, p2y)
            and x <= max(p1x, p2x)
            and (
                p1y != p2y
                and (p1x == p2x or x <= (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x)
            )
        ):
            inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def calculate_vertices(cx, cy, r_radius):
    """Generate 6 vertices of hexagon with 30º isometric offset."""
    vertices = []
    for i in range(6):
        angle = math.radians(30 + 60 * i)  # 30º offset + 60º increments
        vertices.append(
            {"x": cx + math.cos(angle) * r_radius, "y": cy + math.sin(angle) * r_radius}
        )
    return vertices


def get_cube_faces(cx, cy, vertices):
    """Construct three visible faces of the isometric cube."""
    # Top face (vertices: center, 3, 4, 5)
    top_face = [
        (cx, cy),
        (vertices[3]["x"], vertices[3]["y"]),
        (vertices[4]["x"], vertices[4]["y"]),
        (vertices[5]["x"], vertices[5]["y"]),
    ]

    # Left face (vertices: center, 3, 2, 1)
    left_face = [
        (cx, cy),
        (vertices[3]["x"], vertices[3]["y"]),
        (vertices[2]["x"], vertices[2]["y"]),
        (vertices[1]["x"], vertices[1]["y"]),
    ]

    # Right face (vertices: center, 1, 0, 5)
    right_face = [
        (cx, cy),
        (vertices[1]["x"], vertices[1]["y"]),
        (vertices[0]["x"], vertices[0]["y"]),
        (vertices[5]["x"], vertices[5]["y"]),
    ]

    return top_face, left_face, right_face


def generate_logo():
    # RESOLUTION SCALING
    # Convert to low-res grid for pixel art effect
    rw = math.ceil(CONFIG["width"] / CONFIG["pixel_size"])  # Scaled width
    rh = math.ceil(CONFIG["height"] / CONFIG["pixel_size"])  # Scaled height
    r_radius = CONFIG["radius"] / CONFIG["pixel_size"]  # Scaled radius

    # Center point with visual weight adjustment
    # Note: Y offset compensates for isometric perspective imbalance
    cx = rw / 2
    cy = (rh / 2) + (r_radius * 0.1)

    vertices = calculate_vertices(cx, cy, r_radius)
    top_face, left_face, right_face = get_cube_faces(cx, cy, vertices)

    # Calculate vertical bounds for gradient mapping
    top_y = cy - r_radius
    shape_height = (cy + r_radius) - top_y

    # Collect rectangles for SVG
    rects = []

    # Process each pixel in the low-res grid
    for y in range(rh):
        for x in range(rw):
            # Check if in any face
            in_shape = (
                point_in_polygon(x, y, top_face)
                or point_in_polygon(x, y, left_face)
                or point_in_polygon(x, y, right_face)
            )
            if in_shape:
                # LIQUID HEIGHT CALCULATION
                # Normalize Y position within cube (0.0 = top, 1.0 = bottom)
                norm_y = (y - top_y) / shape_height

                # Apply perspective curve to create meniscus effect
                # Distance from center affects apparent liquid height
                x_dist = abs(x - cx) / (r_radius * 0.866)
                perspective_y = norm_y + (x_dist * CONFIG["curvature_strength"])

                # Add noise for organic dithering
                jitter = random.uniform(
                    -CONFIG["jitter_amount"], CONFIG["jitter_amount"]
                )
                final_y = perspective_y + jitter

                # DENSITY CALCULATION
                if final_y > CONFIG["solid_threshold"]:
                    # Solid region - always render pixel
                    density = 1.0
                else:
                    # Gradient region - calculate fade based on position
                    fade = (final_y - CONFIG["fade_start"]) / (
                        CONFIG["solid_threshold"] - CONFIG["fade_start"]
                    )
                    fade = max(0, min(1, fade))
                    density = fade ** CONFIG["dissolve_power"]

                # PIXEL RENDERING DECISION
                # Use density value for probabilistic dithering
                if random.random() < density:
                    # Add rect to SVG
                    rects.append(
                        f'<rect x="{x * CONFIG["pixel_size"]}" y="{y * CONFIG["pixel_size"]}" width="{CONFIG["pixel_size"]}" height="{CONFIG["pixel_size"]}" fill="{CONFIG["fill_color"]}"/>'
                    )

    # Generate SVG
    svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{CONFIG["width"]}" height="{CONFIG["height"]}" viewBox="0 0 {CONFIG["width"]} {CONFIG["height"]}" xmlns="http://www.w3.org/2000/svg">
{chr(10).join(rects)}
</svg>"""

    # Save the SVG
    with pathlib.Path("assets/logo.svg").open("w") as f:
        f.write(svg_content)
    print("Logo generated: assets/logo.svg")


if __name__ == "__main__":
    generate_logo()
