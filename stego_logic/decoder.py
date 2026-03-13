import struct
import zlib
from PIL import Image
from bitarray import bitarray
from bitarray.util import int2ba, ba2int

def extract_bits(value, num_bits):
    if num_bits == 0:
        return bitarray()
    mask = (1 << num_bits) - 1
    
    return int2ba(value & mask, length=num_bits)

def decode_data(carrier_path):
    try:
        img = Image.open(carrier_path).convert('RGB')
    except Exception as e:
        raise ValueError(f"Nie można otworzyć obrazu: {e}")
    
    pixels = list(img.getdata())
    header_bits = bitarray()
    pixels_read = 0
    
    #odczyt headera (64 bajty = 512 bitów)
    for r,g,b in pixels:
        header_bits.extend(extract_bits(r, 1))
        header_bits.extend(extract_bits(g, 1))
        header_bits.extend(extract_bits(b, 1))
        pixels_read += 1
        
        if len(header_bits) >= 512:
            break
    overflow_bits = header_bits[512:] # nadmiarowe bity, które mogą być częścią payloadu
    header_bits = header_bits[:512] # obcięcie nadmiarowych bitów
    header_bytes = header_bits.tobytes()
    try:
        sig, payload_size, r_bits, g_bits, b_bits, ext_bytes = struct.unpack('<4sI3B16s37x', header_bytes)
    except Exception as e:
        raise ValueError(f"Nie można odczytać headera: {e}")
    if sig != b'STEG':
        raise ValueError("Nie znaleziono ukrytych danych (nieprawidłowy sygnatura).")
    
    #odczyt payloadu
    file_extension = ext_bytes.rstrip(b'\x00').rstrip(b' ').decode('utf-8')
    if r_bits + g_bits + b_bits == 0:
        raise ValueError("Nie można odczytać danych (nieprawidłowa liczba bitów w kanałach).")
    target_bits = payload_size * 8
    payload_bits = bitarray()
    payload_bits.extend(overflow_bits) # dodanie nadmiarowych bitów z headera
    
    #pętla odczytująca dane aż do odczytania całego payloadu
    for r,g,b in pixels[pixels_read:]:
        payload_bits.extend(extract_bits(r, r_bits))
        if len(payload_bits) >= target_bits:
            break
        payload_bits.extend(extract_bits(g, g_bits))
        if len(payload_bits) >= target_bits:
            break
        payload_bits.extend(extract_bits(b, b_bits))
        if len(payload_bits) >= target_bits:
            break
        
    payload_bits = payload_bits[:target_bits] # obcięcie nadmiarowych bitów
    
    if len(payload_bits) < target_bits:
        raise ValueError("Nie można odczytać danych (niepełny payload).")
    
    compressed_data = payload_bits.tobytes()
    try:
        secret_data = zlib.decompress(compressed_data)
    except Exception as e:
        raise ValueError(f"Nie można zdekompresować danych: {e}")
    
    return secret_data, file_extension, r_bits, g_bits, b_bits
    
    

def check_if_encoded(carrier_path):
    try:
        img = Image.open(carrier_path).convert('RGB')
    except Exception as e:
        raise ValueError(f"Nie można otworzyć obrazu: {e}")
    
    pixels = list(img.getdata())
    header_bits = bitarray()
    pixels_read = 0
    
    #odczyt headera (64 bajty = 512 bitów)
    for r,g,b in pixels:
        header_bits.extend(extract_bits(r, 1))
        header_bits.extend(extract_bits(g, 1))
        header_bits.extend(extract_bits(b, 1))
        pixels_read += 1
        
        if len(header_bits) >= 512:
            break
    header_bits = header_bits[:512]
    header_bytes = header_bits.tobytes()
    try:
        sig, payload_size, r_bits, g_bits, b_bits, ext_bytes = struct.unpack('<4sI3B16s37x', header_bytes)
    except Exception as e:
        raise ValueError(f"Nie można odczytać headera: {e}")
    
    return sig == b'STEG'