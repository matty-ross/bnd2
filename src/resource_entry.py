import struct
import zlib


class ResourceEntry:
    
    def __init__(self):
        self.type: int = None
        self.imports_offset: int = None
        self.imports_count: int = None
        self.data: list[bytes] = [b'', b'', b'']


    def get_imports_hash(self) -> int:
        imports_hash = 0x0000000000000000
        for i in range(self.imports_count):
            import_offset = self.imports_offset + 0x10 * i
            import_data = self.data[0][import_offset:import_offset + 0x10]
            import_id = struct.unpack('<Q', import_data[0x0:0x8])[0]
            imports_hash |= import_id
        return imports_hash & 0xFFFFFFFFFFFFFFFF
    

    def decompress_data(self) -> None:
        for i in range(3):
            if self.data[i]:
                self.data[i] = zlib.decompress(self.data[i])


    def compress_data(self) -> None:
        for i in range(3):
            if self.data[i]:
                self.data[i] = zlib.compress(self.data[i], 9)


    def change_import_id(self, old_import_id: int, new_import_id: int) -> None:
        for i in range(self.imports_count):
            import_offset = self.imports_offset + 0x10 * i
            import_data = self.data[0][import_offset:import_offset + 0x10]
            import_id = struct.unpack('<Q', import_data[0x0:0x8])[0]
            if import_id == old_import_id:
                bytearray(import_data)[0x0:0x8] = struct.pack('<Q', new_import_id)
