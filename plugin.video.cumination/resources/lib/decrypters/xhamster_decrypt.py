# source: https://github.com/yt-dlp/yt-dlp/issues/14395#issuecomment-3346818930

def deobfuscate_url(hex_string: str) -> str:
    """
    Deobfuscates a URL from a hex string, replicating the logic
    from the original JavaScript function.
    """

    def to_signed_32(n: int) -> int:
        """Converts a number to a 32-bit signed integer using bitwise math."""
        n &= 0xFFFFFFFF
        if n & 0x80000000:
            return n - 0x100000000
        return n

    def create_prng(algo_id: int, seed: int):
        s = to_signed_32(seed)

        def algo1():
            nonlocal s
            s = to_signed_32(s * 1664525 + 1013904223)
            return s & 0xFF

        def algo2():
            nonlocal s
            s = to_signed_32(s ^ (s << 13))
            s = to_signed_32(s ^ ((s & 0xFFFFFFFF) >> 17))
            s = to_signed_32(s ^ (s << 5))
            return s & 0xFF

        def algo3():
            nonlocal s
            s = to_signed_32(s + 0x9e3779b9)
            e = s
            e = to_signed_32(e ^ ((e & 0xFFFFFFFF) >> 16))
            e = to_signed_32(e * to_signed_32(0x85ebca77))
            e = to_signed_32(e ^ ((e & 0xFFFFFFFF) >> 13))
            e = to_signed_32(e * to_signed_32(0xc2b2ae3d))
            e = to_signed_32(e ^ ((e & 0xFFFFFFFF) >> 16))
            return e & 0xFF

        if algo_id == 1:
            return algo1
        if algo_id == 2:
            return algo2
        if algo_id == 3:
            return algo3
        raise ValueError(f'Unknown algorithm ID: {algo_id}')

    try:
        byte_data = bytes.fromhex(hex_string)
    except ValueError as e:
        raise ValueError(f"Invalid hex string provided: {e}")

    if len(byte_data) < 5:
        raise ValueError("Hex string is too short.")

    algo_id = byte_data[0]
    seed = int.from_bytes(byte_data[1:5], byteorder='little', signed=True)

    get_next_byte = create_prng(algo_id, seed)

    decrypted_bytes = bytearray(
        byte_data[i] ^ get_next_byte() for i in range(5, len(byte_data))
    )

    temp_string = decrypted_bytes.decode('latin-1')
    return temp_string
