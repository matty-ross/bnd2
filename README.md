# Burnout Paradise BundleV2

![](https://img.shields.io/badge/Python-3670A0?style=for-the-badge&logo=python&logoColor=FFDD54)

A library for processing Burnout Paradise's BundleV2 files.


## Usage
```py
import bnd2

# create a BundleV2 object
bundle = bnd2.BundleV2('file.bndl')

# load the bundle
bundle.load()

# add a new resource entry to the bundle
resource_entry = bnd2.ResourceEntry()
resource_entry.id = 0xDEADBEEF
resource_entry.type = 12 # Renderable
resource_entry.data = [b'...', b'...']
resource_entry.import_entries = [
    bnd2.ImportEntry(
        id=0xFACEFEED,
        offset=0x20,
    ),
    bnd2.ImportEntry(
        id=0xC0FFEE77,
        offset=0x40,
    ),
]
bundle.resource_entries.append(resource_entry)

# change a resource ID (this includes all import entries too)
bundle.change_resource_id(0xFACEFEED, 0x12345678)

# don't use zlib compression
bundle.compressed = False

# change platform (this doesn't change the endianness of the resources!)
bundle.platform.platform_type = bnd2.PlatformType.PS3

# save the bundle
bundle.save()
```
