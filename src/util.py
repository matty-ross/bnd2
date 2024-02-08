def align_offset(offset: int, alignment: int) -> int:
    if (offset % alignment) == 0:
        return offset
    return offset + alignment - (offset % alignment)


def unpack_size_and_alignment(dword: int) -> tuple[int, int]:
    size = dword & 0x0FFFFFFF
    alignment = dword >> 0x1C
    return size, alignment


def pack_size_and_alignment(size: int, alignment: int) -> int:
    if size == 0:
        return 0
    return size | (alignment << 0x1C)
