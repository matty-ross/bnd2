import struct
import zlib
import math
from dataclasses import dataclass, field


@dataclass
class ResourceEntry:
    id: int = None
    type: int = None
    imports_offset: int = None
    imports_count: int = None
    data: list[bytes] = field(default_factory=list)

    def get_import_entry(self, index: int) -> bytes:
        if index >= self.imports_count:
            raise IndexError()
        import_entries = self.data[0][self.imports_offset:]
        return import_entries[index * 0x10 + 0x0:index * 0x10 + 0x10]
    
    def set_import_entry(self, index: int, import_entry: bytes) -> None:
        if index >= self.imports_count:
            raise IndexError()
        data = bytearray(self.data[0])
        import_entries = data[self.imports_offset:]
        import_entries[index * 0x10 + 0x0:index * 0x10 + 0x10] = import_entry
        data[self.imports_offset:] = import_entries
        self.data[0] = data


class BundleV2:
    
    def __init__(self):
        self.is_compressed: bool = False
        self.debug_data: bytes = b''
        self.resource_entries: list[ResourceEntry] = []

    
    def load(self, file_name: str) -> None:
        with open(file_name, 'rb') as fp:
            fp.seek(0x0)
            assert fp.read(4) == b'bnd2', "MagicNumber mismatch."

            _ = struct.unpack('<L', fp.read(4))[0]
            _ = struct.unpack('<L', fp.read(4))[0]
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
                _ = struct.unpack('<Q', fp.read(8))[0]
                _ = [BundleV2._unpack_size_and_alignment(dword) for dword in struct.unpack('<LLL', fp.read(3 * 4))]
                sizes_and_alignments_on_disk = [BundleV2._unpack_size_and_alignment(dword) for dword in struct.unpack('<LLL', fp.read(3 * 4))]
                disk_offsets = struct.unpack('<LLL', fp.read(3 * 4))
                imports_offset = struct.unpack('<L', fp.read(4))[0]
                resource_type_id = struct.unpack('<L', fp.read(4))[0]
                imports_count = struct.unpack('<H', fp.read(2))[0]
                _ = struct.unpack('B', fp.read(1))[0]
                _ = struct.unpack('B', fp.read(1))[0]

                resource_entry = ResourceEntry()
                resource_entry.id = resource_id
                resource_entry.type = resource_type_id
                resource_entry.imports_offset = imports_offset
                resource_entry.imports_count = imports_count
                for j in range(3):
                    fp.seek(resource_data_offsets[j] + disk_offsets[j])
                    data = fp.read(sizes_and_alignments_on_disk[j][0])
                    if self.is_compressed and data:
                        data = zlib.decompress(data)
                    resource_entry.data.append(data)
                
                self.resource_entries.append(resource_entry)
    
    
    def save(self, file_name: str) -> None:
        with open(file_name, 'wb') as fp:
            fp.seek(0x0)
            fp.write(b'bnd2')

            debug_data_offset = BundleV2._align_offset(0x28, 0x10)
            resource_entries_offset = BundleV2._align_offset(debug_data_offset + len(self.debug_data), 0x10)
            
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
            fp.write(struct.pack('<LLL', 0, 0, 0))
            fp.write(struct.pack('<L', flags))

            fp.seek(debug_data_offset)
            fp.write(self.debug_data)

            resource_data = [b'', b'', b'']
            resource_data_offsets = [None, None, None]

            fp.seek(resource_entries_offset)
            for resource_entry in sorted(self.resource_entries, key=lambda resource_entry: resource_entry.id):
                fp.write(struct.pack('<Q', resource_entry.id))
                fp.write(struct.pack('<Q', BundleV2._compute_imports_hash(resource_entry)))
                
                disk_offsets = [None, None, None]
                
                for i in range(3):
                    fp.write(struct.pack('<L', BundleV2._pack_size_and_alignment(len(resource_entry.data[i]), 0x10)))
                
                for i in range(3):
                    data = resource_entry.data[i]
                    if self.is_compressed and data:
                        data = zlib.compress(data, zlib.Z_BEST_COMPRESSION)
                    fp.write(struct.pack('<L', BundleV2._pack_size_and_alignment(len(data), 0x1)))
                    disk_offsets[i] = len(resource_data[i])
                    resource_data[i] += data + bytes(BundleV2._align_offset(len(data), 0x10) - len(data))
                                    
                for i in range(3):
                    fp.write(struct.pack('<L', disk_offsets[i]))
                
                fp.write(struct.pack('<L', resource_entry.imports_offset))
                fp.write(struct.pack('<L', resource_entry.type))
                fp.write(struct.pack('<H', resource_entry.imports_count))
                fp.write(struct.pack('B', 0))
                fp.write(struct.pack('B', 0))

            for i in range(3):
                resource_data_offsets[i] = BundleV2._align_offset(fp.tell(), (0x10, 0x80, 0x80)[i])
                fp.seek(resource_data_offsets[i])
                fp.write(resource_data[i])

            fp.seek(0x18)
            fp.write(struct.pack('<LLL', *resource_data_offsets))


    def dump_debug_data(self, file_name: str) -> None:
        with open(file_name, 'wb') as fp:
            fp.write(self.debug_data)


    def change_resource_id(self, old_id: int, new_id: int) -> None:
        for resource_entry in self.resource_entries:
            if resource_entry.id == old_id:
                resource_entry.id = new_id
                
            for i in range(resource_entry.imports_count):
                import_entry = bytearray(resource_entry.get_import_entry(i))
                import_id = struct.unpack('<Q', import_entry[0x0:0x8])[0]
                if import_id == old_id:
                    import_entry[0x0:0x8] = struct.pack('<Q', new_id)
                    resource_entry.set_import_entry(i, import_entry)


    @staticmethod
    def _align_offset(offset: int, alignment: int) -> int:
        if (offset % alignment) != 0:
            offset += alignment - (offset % alignment)
        return offset
    

    @staticmethod
    def _unpack_size_and_alignment(dword: int) -> tuple[int, int]:
        size = dword & 0x0FFFFFFF
        alignment = 2 ** (dword >> 0x1C)
        return size, alignment
    

    @staticmethod
    def _pack_size_and_alignment(size: int, alignment: int) -> int:
        if size == 0:
            return 0
        alignment = int(math.log2(alignment))
        return size | (alignment << 0x1C)
    

    @staticmethod
    def _compute_imports_hash(resource_entry: ResourceEntry) -> int:
        imports_hash = 0x0000000000000000
        for i in range(resource_entry.imports_count):
            import_entry = resource_entry.get_import_entry(i)
            import_id = struct.unpack('<Q', import_entry[0x0:0x8])[0]
            imports_hash |= import_id
        return imports_hash
