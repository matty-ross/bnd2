from dataclasses import dataclass, field

from src.import_entry import ImportEntry


@dataclass
class ResourceEntry:
    id: int = None
    type: int = None
    import_entries: list[ImportEntry] = field(default_factory=list)
    data: list[bytes] = field(default_factory=list)
