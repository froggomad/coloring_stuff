from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfWriter, PdfReader
import os
import argparse
from tqdm import tqdm

# Disable the decompression bomb check
Image.MAX_IMAGE_PIXELS = None

def create_coloring_book(image_folder, output_file):
    writer = PdfWriter()

    image_files = sorted([os.path.join(image_folder, f) for f in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, f))])

    # Set the size of the page (in inches)
    page_size = (8.75, 11.25)  # 8.75" x 11.25"

    for i in tqdm(range(len(image_files)), desc="Creating PDF", unit="page"):
        image_file = image_files[i]
        # Open the image file
        img = Image.open(image_file)
        # Resize the image
        img = img.resize((int(page_size[0]*300), int(page_size[1]*300)), Image.Resampling.LANCZOS)
        # Convert the image file to PDF
        img.save("temp.jpg")
        c = canvas.Canvas("temp.pdf", pagesize=(page_size[0]*72, page_size[1]*72))  # reportlab uses points (1/72 inch) as units
        c.drawImage("temp.jpg", 0, 0, width=page_size[0]*72, height=page_size[1]*72)
        c.showPage()
        c.save()
        # Read the image PDF
        img_pdf = PdfReader("temp.pdf")
        # Add the image PDF to the writer
        writer.add_page(img_pdf.pages[0])
        # Add a blank page if it's not the last image
        if i != len(image_files) - 1:
            writer.add_blank_page()

    # Write the output file
    with open(output_file, 'wb') as f:
        writer.write(f)

    # Remove the temporary files
    os.remove("temp.pdf")
    os.remove("temp.jpg")

    # Empty the image folder
    # for image_file in image_files:
    #     os.remove(image_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create a coloring book PDF from images in a folder.')
    parser.add_argument('image_folder', type=str, help='The folder containing the images.')
    parser.add_argument('output_file', type=str, help='The output PDF file.')
    args = parser.parse_args()

    create_coloring_book(args.image_folder, args.output_file)
