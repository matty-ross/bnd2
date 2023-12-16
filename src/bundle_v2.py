import struct
import zlib


def read(data: bytes, offset: int, format: str) -> int:
    size = struct.calcsize(f'<{format}')
    buff = data[offset:offset + size]
    return struct.unpack(f'<{format}', buff)[0]


class BundleV2:

    class ResourceEntry:
        def __init__(self):
            self.type: int = None
            self.imports_offset: int = None
            self.imports_count: int = None
            self.data: list[bytes] = []

    
    def __init__(self):
        self.is_compressed: bool = None
        self.debug_data: str = None
        self.resource_entries: dict[int, BundleV2.ResourceEntry] = {}

    
    def load(self, file_name: str) -> None:
        with open(file_name, 'rb') as fp:
            data = fp.read()    
        
        assert data[0x0:0x4] == b'bnd2', "MagicNumber mismatch."

        flags = read(data, 0x24, 'L')
        
        self.is_compressed = (flags & 0x1) != 0
        if (flags & 0x8) != 0:
            debug_data_begin_offset = read(data, 0xC, 'L')
            debug_data_end_offset = data.find(b'\x00', debug_data_begin_offset)
            self.debug_data = data[debug_data_begin_offset:debug_data_end_offset].decode()

        resource_entries_count = read(data, 0x10, 'L')
        resource_entries_offset = read(data, 0x14, 'L')
        resource_data_offsets = [
            read(data, 0x18, 'L'),
            read(data, 0x1C, 'L'),
            read(data, 0x20, 'L'),
        ]
        
        for i in range(resource_entries_count):
            resournce_entry_offset = resource_entries_offset + i * 0x40
            
            resource_id = read(data, resournce_entry_offset + 0x0, 'L')
            
            resource_entry = BundleV2.ResourceEntry()
            resource_entry.type = read(data, resournce_entry_offset + 0x38, 'L')
            resource_entry.imports_offset = read(data, resournce_entry_offset + 0x34, 'L')
            resource_entry.imports_count = read(data, resournce_entry_offset + 0x3C, 'H')
            for j in range(3):
                resource_size = read(data, resournce_entry_offset + 0x1C + j * 0x4, 'L')
                resource_offset = read(data, resournce_entry_offset + 0x28 + j * 0x4, 'L')
                resource_data = data[resource_data_offsets[j] + resource_offset:resource_data_offsets[j] + resource_offset + resource_size]
                if self.is_compressed:
                    resource_data = zlib.decompress(resource_data)
                resource_entry.data.append(resource_data)

            self.resource_entries[resource_id] = resource_entry
    
    
    def save(self, file_name: str) -> None:
        pass
