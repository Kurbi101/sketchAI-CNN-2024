import numpy as np
from rdp import rdp
from PIL import Image, ImageDraw
import io

def simplify_strokes(strokes, epsilon=300.0):
    simplified_strokes = []
    for stroke in strokes:
        points = list(stroke)
        simplified_stroke = rdp(points, epsilon=2.0)
        simplified_strokes.append(simplified_stroke)
    return simplified_strokes

def vector_to_raster(vector_images, side=28, line_diameter=16, bg_color=0, fg_color=255):
    original_side = 400
    img = Image.new('L', ((original_side), (original_side)), color=bg_color)
    draw = ImageDraw.Draw(img)

    for stroke in vector_images:
        if len(stroke) > 1:
            for i in range(len(stroke) - 1):
                x0, y0 = stroke[i][0], stroke[i][1]
                x1, y1 = stroke[i + 1][0], stroke[i + 1][1]
                draw.line([x0, y0, x1, y1], fill=fg_color, width=line_diameter)
        else:
            draw.point(stroke[0], fill=fg_color)
    large_img = img
    img = img.resize((side, side), Image.LANCZOS)
    print("rasterized image:")
    print(np.array(img))
    return  np.array(img)


def convert_image(image_array):
    # Convert numpy array to PIL image
    pil_image = Image.fromarray(image_array)

    # Convert to PNG
    png_buffer = io.BytesIO()
    pil_image.save(png_buffer, format="PNG")
    png_buffer.seek(0)
    png_image = Image.open(png_buffer)
    png_image.load()

    # Convert to 16-color BMP
    bmp_buffer = io.BytesIO()
    png_image.convert("P", palette=Image.ADAPTIVE, colors=16).save(bmp_buffer, format="BMP")
    bmp_buffer.seek(0)
    bmp_image = Image.open(bmp_buffer)
    bmp_image.load()

    # Convert back to PNG
    final_png_buffer = io.BytesIO()
    bmp_image.save(final_png_buffer, format="PNG")
    final_png_buffer.seek(0)
    final_image = Image.open(final_png_buffer).convert("L")  # Ensure it's grayscale
    final_image.load()

    # Close buffers
    png_buffer.close()
    bmp_buffer.close()
    final_png_buffer.close()

    return final_image


def process_strokes(strokes):
    strokes = simplify_strokes(strokes)
    raster_image, large_raster_image = vector_to_raster(strokes)

    raster_image = convert_image(raster_image)
    large_raster_image = convert_image(large_raster_image)

    return raster_image, large_raster_image