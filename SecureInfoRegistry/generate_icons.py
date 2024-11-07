from PIL import Image, ImageDraw, ImageFont

def create_icon(size, output_file):
    # Create a new image with a dark background
    image = Image.new('RGB', (size, size), color='#212529')
    draw = ImageDraw.Draw(image)

    # Add text to the icon
    font_size = size // 4
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # Changed to Zuvivor initials
    text = "ZV"
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    position = ((size - text_width) // 2, (size - text_height) // 2)
    draw.text(position, text, font=font, fill="#ffffff")

    # Save the icon
    image.save(output_file)

# Generate icons
create_icon(192, "static/icon-192x192.png")
create_icon(512, "static/icon-512x512.png")

print("App icons generated successfully.")
