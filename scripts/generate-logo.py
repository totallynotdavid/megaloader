#!/usr/bin/env python3
"""Write the project logo to apps/docs/megaloader/public/logo.svg."""

import math
import pathlib
import random


# fmt: off
CONFIG = {
    "width": 1024,
    "height": 1024,
    "pixel_size": 12,
    "radius": 420,
    "solid_threshold": 0.65,        # Y-position where liquid becomes solid (0.0-1.0)
    "curvature_strength": 0.3,      # Meniscus curve intensity at edges
    "dissolve_power": 3.5,          # Gradient transition sharpness (higher = sharper)
    "fade_start": -0.2,             # Start position for particle fade (can be negative)
    "jitter_amount": 0.04,          # Random noise amplitude for organic look
    "fill_color": "#1a1a1a",
}
# fmt: on


def point_in_polygon(x, y, polygon):
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
    vertices = []
    for i in range(6):
        angle = math.radians(30 + 60 * i)
        vertices.append(
            {"x": cx + math.cos(angle) * r_radius, "y": cy + math.sin(angle) * r_radius}
        )
    return vertices


def get_cube_faces(cx, cy, vertices):
    top_face = [
        (cx, cy),
        (vertices[3]["x"], vertices[3]["y"]),
        (vertices[4]["x"], vertices[4]["y"]),
        (vertices[5]["x"], vertices[5]["y"]),
    ]

    left_face = [
        (cx, cy),
        (vertices[3]["x"], vertices[3]["y"]),
        (vertices[2]["x"], vertices[2]["y"]),
        (vertices[1]["x"], vertices[1]["y"]),
    ]

    right_face = [
        (cx, cy),
        (vertices[1]["x"], vertices[1]["y"]),
        (vertices[0]["x"], vertices[0]["y"]),
        (vertices[5]["x"], vertices[5]["y"]),
    ]

    return top_face, left_face, right_face


def generate_logo():
    rw = math.ceil(CONFIG["width"] / CONFIG["pixel_size"])
    rh = math.ceil(CONFIG["height"] / CONFIG["pixel_size"])
    r_radius = CONFIG["radius"] / CONFIG["pixel_size"]

    # The Y offset compensates for the isometric perspective imbalance.
    cx = rw / 2
    cy = (rh / 2) + (r_radius * 0.1)

    vertices = calculate_vertices(cx, cy, r_radius)
    top_face, left_face, right_face = get_cube_faces(cx, cy, vertices)

    top_y = cy - r_radius
    shape_height = (cy + r_radius) - top_y

    rects = []

    for y in range(rh):
        for x in range(rw):
            in_shape = (
                point_in_polygon(x, y, top_face)
                or point_in_polygon(x, y, left_face)
                or point_in_polygon(x, y, right_face)
            )
            if in_shape:
                norm_y = (y - top_y) / shape_height

                # Distance from the center raises the apparent liquid height.
                x_dist = abs(x - cx) / (r_radius * 0.866)
                perspective_y = norm_y + (x_dist * CONFIG["curvature_strength"])

                jitter = random.uniform(
                    -CONFIG["jitter_amount"], CONFIG["jitter_amount"]
                )
                final_y = perspective_y + jitter

                if final_y > CONFIG["solid_threshold"]:
                    density = 1.0
                else:
                    fade = (final_y - CONFIG["fade_start"]) / (
                        CONFIG["solid_threshold"] - CONFIG["fade_start"]
                    )
                    fade = max(0, min(1, fade))
                    density = fade ** CONFIG["dissolve_power"]

                if random.random() < density:
                    rects.append(
                        f'<rect x="{x * CONFIG["pixel_size"]}" y="{y * CONFIG["pixel_size"]}" width="{CONFIG["pixel_size"]}" height="{CONFIG["pixel_size"]}" fill="{CONFIG["fill_color"]}"/>'
                    )

    svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{CONFIG["width"]}" height="{CONFIG["height"]}" viewBox="0 0 {CONFIG["width"]} {CONFIG["height"]}" xmlns="http://www.w3.org/2000/svg">
{chr(10).join(rects)}
</svg>"""

    pathlib.Path("apps/docs/megaloader/public/logo.svg").write_text(svg_content)
    print("Logo generated: apps/docs/megaloader/public/logo.svg")


if __name__ == "__main__":
    generate_logo()
