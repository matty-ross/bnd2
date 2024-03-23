import io
import zlib
from dataclasses import dataclass

from . import util
from . import platform_util


MAGIC_NUMBER = b'bnd2'
ALIGNMENTS = (0x10, 0x80, 0x80)


@dataclass
class ImportEntry:
    id: int = None
    offset: int = None


@dataclass
class ResourceEntry:
    id: int = None
    type: int = None
    data: list[bytes] = None
    import_entries: list[ImportEntry] = None


class BundleV2:

    def __init__(self, file_name: str):
        self.file_name = file_name
        self.platform = platform_util.Platform()
        self.compressed = False
        self.debug_data = None
        self.resource_entries: list[ResourceEntry] = []


    def load(self) -> None:
        with open(self.file_name, 'rb') as fp:
            fp.seek(0x0)
            assert fp.read(4) == MAGIC_NUMBER, "Magic Number mismatch."

            _ = fp.read(4)
            self.platform.platform_type = platform_util.PlatformType.from_signature(fp.read(4))
            debug_data_offset = self.platform.unpack('L', fp.read(4))
            resource_entries_count = self.platform.unpack('L', fp.read(4))
            resource_entries_offset = self.platform.unpack('L', fp.read(4))
            resource_data_offsets = self.platform.unpack('LLL', fp.read(3 * 4))
            flags = self.platform.unpack('L', fp.read(4))

            if flags & 0x1:
                self.compressed = True

            if flags & 0x8:
                fp.seek(debug_data_offset)
                debug_data_size = resource_entries_offset - debug_data_offset
                self.debug_data = fp.read(debug_data_size).strip(b'\x00')

            for i in range(resource_entries_count):
                fp.seek(resource_entries_offset + i * 0x40)

                resource_entry = ResourceEntry()
                resource_entry.id = self.platform.unpack('Q', fp.read(8))
                _ = fp.read(8)
                _ = fp.read(3 * 4)
                sizes_and_alignments_on_disk = [util.unpack_size_and_alignment(dword) for dword in self.platform.unpack('LLL', fp.read(3 * 4))]
                disk_offsets = self.platform.unpack('LLL', fp.read(3 * 4))
                imports_offset = self.platform.unpack('L', fp.read(4))
                resource_entry.type = self.platform.unpack('L', fp.read(4))
                imports_count = self.platform.unpack('H', fp.read(2))
                _ = fp.read(1)
                _ = fp.read(1)

                resource_entry.data = []
                for j in range(3):
                    fp.seek(resource_data_offsets[j] + disk_offsets[j])
                    data = fp.read(sizes_and_alignments_on_disk[j][0])
                    if self.compressed and data:
                        data = zlib.decompress(data)
                    resource_entry.data.append(data)

                self.load_import_entries(resource_entry, imports_offset, imports_count)

                self.resource_entries.append(resource_entry)


    def save(self) -> None:
        with open(self.file_name, 'wb') as fp:
            fp.seek(0x0)
            fp.write(MAGIC_NUMBER)

            flags = 0x2 | 0x4
            if self.compressed:
                flags |= 0x1
            if self.debug_data:
                flags |= 0x8

            fp.write(self.platform.pack('L', 2))
            fp.write(self.platform.pack('L', self.platform.platform_type.value))
            fp.write(self.platform.pack('L', 0))
            fp.write(self.platform.pack('L', 0))
            fp.write(self.platform.pack('L', 0))
            fp.write(self.platform.pack('LLL', 0, 0, 0))
            fp.write(self.platform.pack('L', flags))

            debug_data_offset = util.align_offset(fp.tell(), 0x10)
            if self.debug_data:
                fp.seek(debug_data_offset)
                fp.write(self.debug_data)

            resource_entries_offset = util.align_offset(fp.tell(), 0x10)

            resource_data = [io.BytesIO(), io.BytesIO(), io.BytesIO()]
            resource_data_offsets = [None, None, None]

            fp.seek(resource_entries_offset)
            for resource_entry in sorted(self.resource_entries, key=lambda resource_entry: resource_entry.id):
                for i in range(3):
                    data = io.BytesIO(resource_entry.data[i])
                    util.align_data(data, ALIGNMENTS[i])
                    resource_entry.data[i] = data.getvalue()

                imports_offset = len(resource_entry.data[0]) if len(resource_entry.import_entries) > 0 else 0

                self.store_import_entries(resource_entry, imports_offset)

                fp.write(self.platform.pack('Q', resource_entry.id))
                fp.write(self.platform.pack('Q', BundleV2._compute_imports_hash(resource_entry)))

                for i in range(3):
                    fp.write(self.platform.pack('L', util.pack_size_and_alignment(len(resource_entry.data[i]), 0x4)))

                disk_offsets = [None, None, None]
                for i in range(3):
                    data = resource_entry.data[i]
                    if self.compressed and data:
                        data = zlib.compress(data, zlib.Z_BEST_COMPRESSION)
                    fp.write(self.platform.pack('L', util.pack_size_and_alignment(len(data), 0x0)))
                    disk_offsets[i] = resource_data[i].tell() if data else 0
                    resource_data[i].write(data)
                    util.align_data(resource_data[i], ALIGNMENTS[i])

                for i in range(3):
                    fp.write(self.platform.pack('L', disk_offsets[i]))

                fp.write(self.platform.pack('L', imports_offset))
                fp.write(self.platform.pack('L', resource_entry.type))
                fp.write(self.platform.pack('H', len(resource_entry.import_entries)))
                fp.write(self.platform.pack('B', 0))
                fp.write(self.platform.pack('B', 0))

            for i in range(3):
                resource_data_offsets[i] = util.align_offset(fp.tell(), ALIGNMENTS[i])
                fp.seek(resource_data_offsets[i])
                fp.write(resource_data[i].getvalue())

            fp.seek(0xC)
            fp.write(self.platform.pack('L', debug_data_offset))
            fp.write(self.platform.pack('L', len(self.resource_entries)))
            fp.write(self.platform.pack('L', resource_entries_offset))
            fp.write(self.platform.pack('LLL', *resource_data_offsets))


    def get_resource_entry(self, id: int) -> ResourceEntry:
        for resource_entry in self.resource_entries:
            if resource_entry.id == id:
                return resource_entry
        return None


    def change_resource_id(self, old_id: int, new_id: int) -> None:
        assert self.get_resource_entry(new_id) is None, f"Resource entry with ID {new_id :08X} already exists."
        for resource_entry in self.resource_entries:
            if resource_entry.id == old_id:
                resource_entry.id = new_id
            for import_entry in resource_entry.import_entries:
                if import_entry.id == old_id:
                    import_entry.id = new_id


    def get_external_resource_ids(self) -> set[int]:
        external_resource_ids = set()
        for resource_entry in self.resource_entries:
            for import_entry in resource_entry.import_entries:
                if self.get_resource_entry(import_entry.id) is None:
                    external_resource_ids.add(import_entry.id)
        return external_resource_ids


    def load_import_entries(self, resource_entry: ResourceEntry, imports_offset: int, imports_count: int) -> None:
        resource_entry.import_entries = []
        data = io.BytesIO(resource_entry.data[0])
        for i in range(imports_count):
            data.seek(imports_offset + i * 0x10)
            import_entry = ImportEntry()
            import_entry.id = self.platform.unpack('Q', data.read(8))
            import_entry.offset = self.platform.unpack('L', data.read(4))
            resource_entry.import_entries.append(import_entry)
        if imports_count > 0:
            data.truncate(imports_offset)
            resource_entry.data[0] = data.getvalue()


    def store_import_entries(self, resource_entry: ResourceEntry, imports_offset: int) -> None:
        data = io.BytesIO(resource_entry.data[0])
        data.seek(imports_offset)
        for import_entry in resource_entry.import_entries:
            data.write(self.platform.pack('Q', import_entry.id))
            data.write(self.platform.pack('L', import_entry.offset))
            data.write(bytes(4)) # padding
        resource_entry.data[0] = data.getvalue()


    @staticmethod
    def _compute_imports_hash(resource_entry: ResourceEntry) -> int:
        imports_hash = 0x0000000000000000
        for import_entry in resource_entry.import_entries:
            imports_hash |= import_entry.id
        return imports_hash
