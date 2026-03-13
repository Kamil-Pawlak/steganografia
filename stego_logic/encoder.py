import os
import struct
import zlib
from PIL import Image
from bitarray import bitarray
from bitarray.util import int2ba, ba2int

def build_header(payload_size, r_bits, g_bits, b_bits, file_extension):
    sig = b'STEG'
    
    ext_bytes = file_extension.encode('utf-8').ljust(16, b'\x00')
    #4 bajty sygnatura
    #4 bajty rozmiar payloadu
    #3 bajty liczba bitów w R,G,B
    #16 bajtów rozszerzenie pliku
    #37 bajtów paddingu
    header = struct.pack('<4sI3B16s37x', sig, payload_size, r_bits, g_bits, b_bits, ext_bytes)
    return header


def encode_data(carrier_path, secret_path, r_bits, g_bits, b_bits):
    with open(secret_path, 'rb') as f:
        secret_data = f.read()
    
    compressed_data = zlib.compress(secret_data)
    payload_size = len(compressed_data)
    file_extension = os.path.splitext(secret_path)[1]
    header = build_header(payload_size, r_bits, g_bits, b_bits, file_extension)
    
    all_data = bitarray()
    all_data.frombytes(header + compressed_data)
    all_data.extend([0] * 24)
    
    bits_iterator = iter(all_data)
    
    img = Image.open(carrier_path).convert('RGB')
    pixels = list(img.getdata())
    new_pixels = []
    
    header_bits_count = len(header) * 8
    bits_processed = 0
    
    for r,g,b in pixels:
        try:
            if bits_processed < header_bits_count:
                curr_r_bits, curr_g_bits, curr_b_bits = 1,1,1
            else:
                curr_r_bits, curr_g_bits, curr_b_bits = r_bits, g_bits, b_bits
            
            r_embed = bitarray([next(bits_iterator) for _ in range(curr_r_bits)])
            g_embed = bitarray([next(bits_iterator) for _ in range(curr_g_bits)])
            b_embed = bitarray([next(bits_iterator) for _ in range(curr_b_bits)])
            
            new_r = modify_channel(r, r_embed, curr_r_bits)
            new_g = modify_channel(g, g_embed, curr_g_bits)
            new_b = modify_channel(b, b_embed, curr_b_bits)
            
            new_pixels.append((new_r, new_g, new_b))
            bits_processed += (curr_r_bits + curr_g_bits + curr_b_bits)
            
        except StopIteration:
            new_pixels.append((r, g, b))
    
    new_img = Image.new(img.mode, img.size)
    new_img.putdata(new_pixels)
    return new_img
            

def modify_channel(value, bits_to_embed, num_bits):
    if num_bits == 0 or len(bits_to_embed) == 0:
        return value
    
    embed_value = ba2int(bits_to_embed)
    mask = ~((1 << num_bits) - 1) & 0xFF
    
    return (value & mask) | embed_value