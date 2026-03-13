from PIL import Image
import os

def calculate_capacity(image_path, r_bits, g_bits, b_bits):
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Plik {image_path} nie istnieje.")
    try:
        with Image.open(image_path) as img:
            width,height = img.size
            bits_per_pixel = r_bits + g_bits + b_bits
            total_bits = width * height * bits_per_pixel
            total_bytes = total_bits // 8
            return total_bytes
    except Exception as e:
        raise ValueError(f"Nie można otworzyć obrazu: {e}")
    
def format_size(bytes_size):
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024**2:
        return f"{bytes_size / 1024:.2f} KB"
    elif bytes_size < 1024**3:
        return f"{bytes_size / (1024**2):.2f} MB"
    else:
        return f"{bytes_size / (1024**3):.2f} GB"