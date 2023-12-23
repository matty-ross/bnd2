import pathlib
import tkinter, tkinter.filedialog

from lib.bundle_v2 import BundleV2


def main() -> None:
    tkinter.Tk().withdraw()
    file_path = pathlib.Path(tkinter.filedialog.askopenfilename())

    bundle = BundleV2()
    
    print(f"Loading bundle from '{file_path}'")
    bundle.load(str(file_path.absolute()))

    while True:
        try:
            old_id = int(input("Old resource ID: "), 16)
            new_id = int(input("New resource ID: "), 16)
            bundle.change_resource_id(old_id, new_id)
            print(f"Changed resource ID from {old_id :X} to {new_id :X}")
        except KeyboardInterrupt:
            break

    remove_debug_data = input("Do you want to remove debug data? [yes] ").lower()
    if remove_debug_data == '' or (remove_debug_data in ('y', 'yes')):
        bundle.debug_data = b''

    bundle.save(str(file_path.absolute()))
    print(f"Saved bundle to '{file_path}'")
    
    exit(0)


if __name__ == '__main__':
    main()
