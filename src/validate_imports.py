import tkinter, tkinter.filedialog

from lib.bundle_v2 import BundleV2


def main() -> None:
    tkinter.Tk().withdraw()
    file_name = tkinter.filedialog.askopenfilename()

    bundle = BundleV2(file_name)
    bundle.load()

    external_dependencies = []
    if input("Load external dependencies? y/n: ").lower() == 'y':
        for file_name in tkinter.filedialog.askopenfilenames():
            b = BundleV2(file_name)
            b.load()
            external_dependencies.append(b)

    missing_imports = bundle.get_missing_imports(external_dependencies)
    
    if len(missing_imports) == 0:
        print("No missing imports.")
        return
    
    print("Missing imports:")
    for import_entry in missing_imports:
        print(f'{import_entry.id :08X}')

    print("Done.")


if __name__ == '__main__':
    main()
