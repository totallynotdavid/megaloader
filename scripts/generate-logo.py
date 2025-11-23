#!/usr/bin/env python3
"""
MEGALOADER - Logo Generator

Generates the project logo featuring an isometric cube with liquid fill effect.
Uses pixel-based rendering with dithering for retro aesthetic.

OUTPUT: logo.png (1024x1024 PNG with transparent background)
"""

from PIL import Image, ImageDraw
import math
import random

CONFIG = {
    # CANVAS SETTINGS
    'width': 1024,        # Output width in pixels
    'height': 1024,       # Output height in pixels

    # PIXEL ART CONFIGURATION
    'pixel_size': 13,      # Size of each "pixel" block (13px = ~79x79 grid)

    # CUBE GEOMETRY
    'radius': 420,        # Base radius of hexagon (42% of canvas width)

    # LIQUID FILL EFFECT
    'solid_threshold': 0.65,   # Y-position where liquid becomes solid (0.0-1.0)
    'curvature_strength': 0.3, # Meniscus curve intensity at edges

    # DITHERING & GRADIENT
    'dissolve_power': 3.5,     # Gradient transition sharpness (higher = sharper)
    'fade_start': -0.2,        # Start position for particle fade (can be negative)
    'jitter_amount': 0.04,     # Random noise amplitude for organic look

    # BRAND COLORS
    'fill_color': '#1a1a1a',   # Primary brand color (dark charcoal)
}

def generate_logo():
    # Initialize image with transparency
    img = Image.new('RGBA', (CONFIG['width'], CONFIG['height']), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # RESOLUTION SCALING
    # Convert to low-res grid for pixel art effect
    rw = math.ceil(CONFIG['width'] / CONFIG['pixel_size'])   # Scaled width
    rh = math.ceil(CONFIG['height'] / CONFIG['pixel_size'])  # Scaled height
    r_radius = CONFIG['radius'] / CONFIG['pixel_size']  # Scaled radius

    # Center point with visual weight adjustment
    # Note: Y offset compensates for isometric perspective imbalance
    cx = rw / 2
    cy = (rh / 2) + (r_radius * 0.1)

    # ISOMETRIC CUBE VERTEX CALCULATION
    # Generate 6 vertices of hexagon with 30° isometric offset
    vertices = []
    for i in range(6):
        angle = math.radians(30 + 60 * i)  # 30° offset + 60° increments
        vertices.append({
            'x': cx + math.cos(angle) * r_radius,
            'y': cy + math.sin(angle) * r_radius
        })

    # Create mask for the cube shape
    mask = Image.new('L', (rw, rh), 0)
    mask_draw = ImageDraw.Draw(mask)

    # CUBE FACE RENDERING
    # Construct three visible faces
    # Top face (vertices: center, 3, 4, 5)
    mask_draw.polygon([
        (cx, cy),
        (vertices[3]['x'], vertices[3]['y']),
        (vertices[4]['x'], vertices[4]['y']),
        (vertices[5]['x'], vertices[5]['y'])
    ], fill=255)

    # Left face (vertices: center, 3, 2, 1)
    mask_draw.polygon([
        (cx, cy),
        (vertices[3]['x'], vertices[3]['y']),
        (vertices[2]['x'], vertices[2]['y']),
        (vertices[1]['x'], vertices[1]['y'])
    ], fill=255)

    # Right face (vertices: center, 1, 0, 5)
    mask_draw.polygon([
        (cx, cy),
        (vertices[1]['x'], vertices[1]['y']),
        (vertices[0]['x'], vertices[0]['y']),
        (vertices[5]['x'], vertices[5]['y'])
    ], fill=255)

    # Convert brand color to RGB
    fill_color = CONFIG['fill_color'].lstrip('#')
    r = int(fill_color[0:2], 16)
    g = int(fill_color[2:4], 16)
    b = int(fill_color[4:6], 16)

    # Calculate vertical bounds for gradient mapping
    top_y = cy - r_radius
    shape_height = (cy + r_radius) - top_y

    # Process each pixel in the low-res grid
    mask_pixels = mask.load()
    for y in range(rh):
        for x in range(rw):
            if mask_pixels[x, y] > 128:  # Inside cube mask

                # LIQUID HEIGHT CALCULATION
                # Normalize Y position within cube (0.0 = top, 1.0 = bottom)
                norm_y = (y - top_y) / shape_height

                # Apply perspective curve to create meniscus effect
                # Distance from center affects apparent liquid height
                x_dist = abs(x - cx) / (r_radius * 0.866)
                perspective_y = norm_y + (x_dist * CONFIG['curvature_strength'])

                # Add noise for organic dithering
                jitter = random.uniform(-CONFIG['jitter_amount'], CONFIG['jitter_amount'])
                final_y = perspective_y + jitter

                # DENSITY CALCULATION
                if final_y > CONFIG['solid_threshold']:
                    # Solid region - always render pixel
                    density = 1.0
                else:
                    # Gradient region - calculate fade based on position
                    fade = (final_y - CONFIG['fade_start']) / (CONFIG['solid_threshold'] - CONFIG['fade_start'])
                    fade = max(0, min(1, fade))
                    density = fade ** CONFIG['dissolve_power']

                # PIXEL RENDERING DECISION
                # Use density value for probabilistic dithering
                if random.random() < density:
                    # Render solid pixel at full size
                    draw.rectangle([
                        x * CONFIG['pixel_size'],
                        y * CONFIG['pixel_size'],
                        (x + 1) * CONFIG['pixel_size'],
                        (y + 1) * CONFIG['pixel_size']
                    ], fill=(r, g, b, 255))
                # Else: leave transparent

    # Save the image
    img.save('logo.png')
    print('Logo generated: logo.png')

if __name__ == '__main__':
    generate_logo()
