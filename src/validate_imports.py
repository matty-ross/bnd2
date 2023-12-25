import tkinter, tkinter.filedialog

from lib.bundle_v2 import BundleV2


def main() -> None:
    tkinter.Tk().withdraw()
    file_path = tkinter.filedialog.askopenfilename()

    bundle = BundleV2()
    
    print(f"Loading bundle from '{file_path}'")
    bundle.load(file_path)

    external_dependencies = []

    external_dependency_file_paths = tkinter.filedialog.askopenfilenames()
    for external_dependency_file_path in external_dependency_file_paths:
        b = BundleV2()
        b.load(external_dependency_file_path)
        external_dependencies.append(b)

    missing_imports = bundle.get_missing_imports(external_dependencies)

    if len(missing_imports) > 0:
        print("Missing imports:")
        for import_entry in missing_imports:
            print(f'{import_entry.id :X}')
    else:
        print("No missing imports")
    
    exit(0)


if __name__ == '__main__':
    main()
