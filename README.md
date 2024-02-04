# Burnout Paradise BundleV2

![](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

A library for processing Burnout Paradise's BundleV2 files.


## Usage
```py
import bnd2

# create a BundleV2 object
bundle = bnd2.BundleV2('file.bndl')

# load the bundle
bundle.load()

# create a new ResourceEntry object
resource_entry = bnd2.ResourceEntry()
resource_entry.id = 0xDEADBEEF
resource_entry.type = 12 # Renderable
resource_entry.data = [b'...', b'...']
resource_entry.import_entries = []

# create a new ImportEntry object
import_entry = bnd2.ImportEntry()
import_entry.id = 0xFACEFEED
import_entry.offset = 0x20

# add the ImportEntry object to the ResourceEntry object
resource_entry.import_entries.append(import_entry)

# add the ResourceEntry object to the BundleV2 object
bundle.resource_entries.append(resource_entry)

# don't use zlib compression
bundle.compressed = False

# save the bundle
bundle.save()
```
