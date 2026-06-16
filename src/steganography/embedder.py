import random
import logging

class SteganographyEmbedder:
    """
    Implements LSB (Least Significant Bit) steganography to hide metadata within packet payloads.
    Usually applied to 'dummy' packets to carry control signals or covert messages.
    """
    def __init__(self):
        pass

    def embed_data(self, cover_data: bytes, secret_data: bytes) -> bytes:
        """
        Embeds secret_data into cover_data using LSB.
        Args:
            cover_data: The carrier bytes (packet payload).
            secret_data: The data to hide.
        Returns:
            Modified payload with embedded data.
        """
        cover_len = len(cover_data)
        secret_len = len(secret_data)
        
        # 1 byte of secret needs 8 bytes of cover (1 bit per byte)
        if secret_len * 8 > cover_len:
            raise ValueError("Cover data too small to hold secret data.")

        # Convert cover to bytearray for mutability
        stego = bytearray(cover_data)
        
        # Convert secret to bits generator
        secret_bits = []
        for byte in secret_data:
            for i in range(8):
                secret_bits.append((byte >> (7 - i)) & 1)
        
        # Embed bits
        for i, bit in enumerate(secret_bits):
            # Clear LSB and set to secret bit
            stego[i] = (stego[i] & 0xFE) | bit
            
        return bytes(stego)

    def extract_data(self, stego_data: bytes, secret_len: int) -> bytes:
        """
        Extracts hidden data from stego payload.
        Args:
            stego_data: The packet payload containing hidden data.
            secret_len: Length of secret data in bytes to extract.
        """
        if secret_len * 8 > len(stego_data):
             raise ValueError("Requested extraction length exceeds payload capacity.")
             
        extracted_bytes = bytearray()
        
        current_byte = 0
        bit_count = 0
        
        for i in range(secret_len * 8):
            bit = stego_data[i] & 1
            current_byte = (current_byte << 1) | bit
            bit_count += 1
            
            if bit_count == 8:
                extracted_bytes.append(current_byte)
                current_byte = 0
                bit_count = 0
                
        return bytes(extracted_bytes)
