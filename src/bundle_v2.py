import io
import struct
import zlib

from src.resource_entry import ResourceEntry
from src.import_entry import ImportEntry


class BundleV2:

    MAGIC_NUMBER = b'bnd2'

    
    def __init__(self, file_name: str):
        self.file_name: str = file_name
        self.compressed: bool = False
        self.debug_data: bytes = None
        self.resource_entries: list[ResourceEntry] = []

    
    def load(self) -> None:
        with open(self.file_name, 'rb') as fp:
            fp.seek(0x0)
            assert fp.read(4) == BundleV2.MAGIC_NUMBER, "Magic Number mismatch."

            _ = struct.unpack('<L', fp.read(4))[0]
            _ = struct.unpack('<L', fp.read(4))[0]
            debug_data_offset = struct.unpack('<L', fp.read(4))[0]
            resource_entries_count = struct.unpack('<L', fp.read(4))[0]
            resource_entries_offset = struct.unpack('<L', fp.read(4))[0]
            resource_data_offsets = struct.unpack('<LLL', fp.read(3 * 4))
            flags = struct.unpack('<L', fp.read(4))[0]
            
            if (flags & 0x1) != 0:
                self.compressed = True
            
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
                
                for j in range(3):
                    fp.seek(resource_data_offsets[j] + disk_offsets[j])
                    data = fp.read(sizes_and_alignments_on_disk[j][0])
                    if self.compressed and data:
                        data = zlib.decompress(data)
                    resource_entry.data.append(data)

                data = io.BytesIO(resource_entry.data[0])
                for j in range(imports_count):
                    data.seek(imports_offset + j * 0x10)
                    import_entry = ImportEntry()
                    import_entry.id = struct.unpack('<Q', data.read(8))[0]
                    import_entry.offset = struct.unpack('<L', data.read(4))[0]
                    resource_entry.import_entries.append(import_entry)
                
                self.resource_entries.append(resource_entry)
    
    
    def save(self) -> None:
        return
        # with open(self.file_name, 'wb') as fp:
        #     fp.seek(0x0)
        #     fp.write(b'bnd2')

        #     debug_data_offset = BundleV2._align_offset(0x28, 0x10)
        #     resource_entries_offset = BundleV2._align_offset(debug_data_offset + len(self.debug_data), 0x10)
            
        #     flags = 0x6
        #     if self.compressed:
        #         flags |= 0x1
        #     if self.debug_data:
        #         flags |= 0x8
            
        #     fp.write(struct.pack('<L', 2))
        #     fp.write(struct.pack('<L', 1))
        #     fp.write(struct.pack('<L', debug_data_offset))
        #     fp.write(struct.pack('<L', len(self.resource_entries)))
        #     fp.write(struct.pack('<L', resource_entries_offset))
        #     fp.write(struct.pack('<LLL', 0, 0, 0))
        #     fp.write(struct.pack('<L', flags))

        #     fp.seek(debug_data_offset)
        #     fp.write(self.debug_data)

        #     resource_data = [b'', b'', b'']
        #     resource_data_offsets = [None, None, None]

        #     fp.seek(resource_entries_offset)
        #     for resource_entry in sorted(self.resource_entries, key=lambda resource_entry: resource_entry.id):
        #         fp.write(struct.pack('<Q', resource_entry.id))
        #         fp.write(struct.pack('<Q', BundleV2._compute_imports_hash(resource_entry)))
                
        #         disk_offsets = [None, None, None]
                
        #         for i in range(3):
        #             fp.write(struct.pack('<L', BundleV2._pack_size_and_alignment(len(resource_entry.data[i]), 0x10)))
                
        #         for i in range(3):
        #             data = resource_entry.data[i]
        #             if i == 0 and data:
        #                 for import_entry in resource_entry.import_entries:
        #                     data += struct.pack('<Q', import_entry.id)
        #                     data += struct.pack('<L', import_entry.offset)
        #                     data += bytes(BundleV2._align_offset(len(data), 0x10) - len(data))
        #             if self.compressed and data:
        #                 data = zlib.compress(data, zlib.Z_BEST_COMPRESSION)
        #             fp.write(struct.pack('<L', BundleV2._pack_size_and_alignment(len(data), 0x1)))
        #             disk_offsets[i] = len(resource_data[i])
        #             resource_data[i] += data + bytes(BundleV2._align_offset(len(data), 0x10) - len(data))
                
        #         for i in range(3):
        #             fp.write(struct.pack('<L', disk_offsets[i]))
                
        #         imports_offset = len(resource_entry.data[0]) if len(resource_entry.import_entries) > 0 else 0
        #         fp.write(struct.pack('<L', imports_offset))
        #         fp.write(struct.pack('<L', resource_entry.type))
        #         fp.write(struct.pack('<H', len(resource_entry.import_entries)))
        #         fp.write(struct.pack('B', 0))
        #         fp.write(struct.pack('B', 0))

        #     for i in range(3):
        #         resource_data_offsets[i] = BundleV2._align_offset(fp.tell(), (0x10, 0x80, 0x80)[i])
        #         fp.seek(resource_data_offsets[i])
        #         fp.write(resource_data[i])

        #     fp.seek(0x18)
        #     fp.write(struct.pack('<LLL', *resource_data_offsets))


    def get_resource_entry(self, id: int) -> ResourceEntry:
        for resource_entry in self.resource_entries:
            if resource_entry.id == id:
                return resource_entry
        return None


    def change_resource_id(self, old_id: int, new_id: int) -> None:
        for resource_entry in self.resource_entries:
            if resource_entry.id == old_id:
                resource_entry.id = new_id
            for import_entry in resource_entry.import_entries:
                if import_entry.id == old_id:
                    import_entry.id = new_id


    @staticmethod
    def _align_offset(offset: int, alignment: int) -> int:
        if (offset % alignment) != 0:
            offset += alignment - (offset % alignment)
        return offset
    

    @staticmethod
    def _unpack_size_and_alignment(dword: int) -> tuple[int, int]:
        size = dword & 0x0FFFFFFF
        alignment = dword >> 0x1C
        return size, alignment
    

    @staticmethod
    def _pack_size_and_alignment(size: int, alignment: int) -> int:
        if size == 0:
            return 0
        return size | (alignment << 0x1C)
    

    @staticmethod
    def _compute_imports_hash(resource_entry: ResourceEntry) -> int:
        imports_hash = 0x0000000000000000
        for import_entry in resource_entry.import_entries:
            imports_hash |= import_entry.id
        return imports_hash
