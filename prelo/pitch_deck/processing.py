import base64
import os

import fitz


def pdf_to_images(pdf_path, output_folder):
    imgs = []
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)  # number of page
        pix = page.get_pixmap()
        output_path = f"{output_folder}/page_{page_num + 1}.png"
        pix.save(output_path)
        imgs.append({
            "path": output_path,
            "page": page_num + 1
        })
    return imgs


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def cleanup_local_file(path):
    """
    Delete a file from the local filesystem.

    :param path: str, the path to the file to be deleted
    """
    if os.path.exists(path):
        os.remove(path)
