import struct
from enum import Enum


class PlatformTypeException(ValueError):
    pass


class PlatformType(Enum):
    PC = 1
    XBOX_360 = 2
    PS3 = 3

    @classmethod
    def from_signature(cls, signature: bytes):
        if signature == b'\x01\x00\x00\x00':
            return cls.PC
        if signature == b'\x00\x00\x00\x02':
            return cls.XBOX_360
        if signature == b'\x00\x00\x00\x03':
            return cls.PS3
        raise PlatformTypeException(f"Unknown platform signature: {signature}")


class Platform:

    def __init__(self):
        self.platform_type: PlatformType = None


    def unpack(self, format: str, buffer: bytes):
        endianness = self._get_platform_endianness()
        value = struct.unpack(endianness + format, buffer)
        return value if len(value) > 1 else value[0]


    def pack(self, format: str, *value) -> bytes:
        endianness = self._get_platform_endianness()
        buffer = struct.pack(endianness + format, *value)
        return buffer


    def _get_platform_endianness(self) -> str:
        if self.platform_type == PlatformType.PC:
            return '<'
        if self.platform_type == PlatformType.XBOX_360:
            return '>'
        if self.platform_type == PlatformType.PS3:
            return '>'
        raise PlatformTypeException(f"Unknown platform type: {self.platform_type}")
