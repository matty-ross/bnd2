import struct

from resource_entry import ResourceEntry


def align_offset(offset: int) -> int:
    if (offset % 0x10) != 0:
        offset += 0x10 - (offset % 0x10)
    return offset


class BundleV2:
    
    def __init__(self):
        self.is_compressed: bool = False
        self.debug_data: bytes = b''
        self.resource_entries: dict[int, ResourceEntry] = {}

    
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

                resource_entry = ResourceEntry()
                resource_entry.type = resource_type_id
                resource_entry.imports_offset = imports_offset
                resource_entry.imports_count = imports_count
                for j in range(3):
                    fp.seek(resource_data_offsets[j] + disk_offsets[j])
                    resource_entry.data[j] = fp.read(sizes_and_alignments_on_disk[j])
                if self.is_compressed:
                    resource_entry.decompress_data()
                
                self.resource_entries[resource_id] = resource_entry
    
    
    def save(self, file_name: str) -> None:
        with open(file_name, 'wb') as fp:
            fp.seek(0x0)
            fp.write(b'bnd2')
            
            debug_data_offset = align_offset(0x28)
            resource_entries_offset = align_offset(debug_data_offset + len(self.debug_data))
            resource_data_offsets = 0x0, 0x0, 0x0
            
            flags = 0x6
            if self.is_compressed:
                flags |= 0x1
            if self.debug_data:
                flags |= 0x8
            
            fp.write(struct.pack('<L', 2))
            fp.write(struct.pack('<L', 1))
            fp.write(struct.pack('<L', debug_data_offset))
            fp.write(struct.pack('<L', len(self.resource_entries)))
            fp.write(struct.pack('<L', resource_entries_offset))
            fp.write(struct.pack('<LLL', *resource_data_offsets))
            fp.write(struct.pack('<L', flags))

            fp.seek(align_offset(fp.tell()))
            fp.write(self.debug_data)
            
            fp.seek(align_offset(fp.tell()))
            for resource_id, resource_entry in sorted(self.resource_entries.items()):
                fp.write(struct.pack('<Q', resource_id))
                fp.write(struct.pack('<Q', resource_entry.get_imports_hash()))
                for i in range(3):
                    fp.write(struct.pack('<L', len(resource_entry.data[i])))
                if self.is_compressed:
                    resource_entry.compress_data()
                for i in range(3):
                    fp.write(struct.pack('<L', len(resource_entry.data[i])))
                for i in range(3):
                    fp.write(struct.pack('<L', 0)) # TODO: store the data and calculate offset (len without the new data)
                fp.write(struct.pack('<L', resource_entry.imports_offset))
                fp.write(struct.pack('<L', resource_entry.type))
                fp.write(struct.pack('<H', resource_entry.imports_count))
                fp.write(struct.pack('B', 0))
                fp.write(struct.pack('B', 0))


    def dump_debug_data(self, file_name: str) -> None:
        with open(file_name, 'wb') as fp:
            fp.write(self.debug_data)
