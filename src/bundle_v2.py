import struct
import zlib


class BundleV2:

    class ResourceEntry:
        def __init__(self):
            self.type: int = None
            self.imports_offset: int = None
            self.imports_count: int = None
            self.data: list[bytearray] = []

    
    def __init__(self):
        self.is_compressed: bool = None
        self.debug_data: bytes = None
        self.resource_entries: dict[int, BundleV2.ResourceEntry] = {}

    
    def load(self, file_name: str) -> None:
        with open(file_name, 'rb') as fp:
            fp.seek(0x0)
            assert fp.read(4) == b'bnd2', "MagicNumber mismatch."

            version = struct.unpack('<L', fp.read(4))[0]
            platform = struct.unpack('<L', fp.read(4))[0]
            debug_data_offset = struct.unpack('<L', fp.read(4))[0]
            resource_entries_count = struct.unpack('<L', fp.read(4))[0]
            resource_entries_offset = struct.unpack('<L', fp.read(4))[0]
            resource_data_offsets = struct.unpack('<LLL', fp.read(3 * 4))
            flags = struct.unpack('<L', fp.read(4))[0]
            
            self.is_compressed = (flags & 0x1) != 0
            if (flags & 0x8) != 0:
                fp.seek(debug_data_offset)
                debug_data_size = resource_entries_offset - debug_data_offset
                self.debug_data = fp.read(debug_data_size).strip(b'\x00')
        
            for i in range(resource_entries_count):
                fp.seek(resource_entries_offset + i * 0x40)
                
                resource_id = struct.unpack('<Q', fp.read(8))[0]
                imports_hash = struct.unpack('<Q', fp.read(8))[0]
                uncompressed_sizes_and_alignments = struct.unpack('<LLL', fp.read(3 * 4))
                sizes_and_alignments_on_disk = struct.unpack('<LLL', fp.read(3 * 4))
                disk_offsets = struct.unpack('<LLL', fp.read(3 * 4))
                imports_offset = struct.unpack('<L', fp.read(4))[0]
                resource_type_id = struct.unpack('<L', fp.read(4))[0]
                imports_count = struct.unpack('<H', fp.read(2))[0]
                flags = struct.unpack('B', fp.read(1))[0]
                stream_index = struct.unpack('B', fp.read(1))[0]

                resource_entry = BundleV2.ResourceEntry()
                resource_entry.type = resource_type_id
                resource_entry.imports_offset = imports_offset
                resource_entry.imports_count = imports_count
                for j in range(3):
                    fp.seek(resource_data_offsets[j] + disk_offsets[j])
                    data = fp.read(sizes_and_alignments_on_disk[j])
                    if data and self.is_compressed:
                        data = zlib.decompress(data)
                    resource_entry.data.append(bytearray(data))

                self.resource_entries[resource_id] = resource_entry
    
    
    def save(self, file_name: str) -> None:
        pass


    def dump_debug_data(self, file_name: str) -> None:
        with open(file_name, 'wb') as fp:
            fp.write(self.debug_data)
