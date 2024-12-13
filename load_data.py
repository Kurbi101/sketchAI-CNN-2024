from PIL import Image
import numpy as np
import os
from tqdm import tqdm
import io

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
    final_image = Image.open(final_png_buffer).convert("L")  
    final_image.load()

    # Close buffers
    png_buffer.close()
    bmp_buffer.close()
    final_png_buffer.close()

    return final_image

def load_data(data_dir, categories, images_per_category):
    data = []
    labels = []

    # Iterate over all categories, use tqdm to visualize progress
    for idx, category in enumerate(tqdm(categories, desc="Loading categories")):
        category_path = os.path.join(data_dir, category)
        npy_file_path = os.path.join(category_path, f"{category}.npy")

        # If file exists, load the data
        if os.path.exists(npy_file_path):
            category_data = np.load(npy_file_path)

            # Check if requested number of images is not greater than available images
            if images_per_category > len(category_data):
                print(f"Warning: Requested {images_per_category} images for {category} but only {len(category_data)} available.")
                images_per_category = len(category_data)

            # Add selected data to data and labels
            selected_data = category_data[:images_per_category]
            for image in selected_data:

                # Convert the image using the defined process
                processed_image = convert_image(image)
                processed_image = np.array(processed_image)
                data.append(processed_image)
            
            labels.extend([idx] * images_per_category)
        else:
            print(f"File not found: {npy_file_path}")

    data = np.array(data)
    labels = np.array(labels)
    return data, labels
