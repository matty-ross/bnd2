import pathlib
import tkinter, tkinter.filedialog

from lib.bundle_v2 import BundleV2


def main() -> None:
    tkinter.Tk().withdraw()
    file_path = pathlib.Path(tkinter.filedialog.askopenfilename())

    bundle = BundleV2()
    
    print(f"Loading bundle from '{file_path}'")
    bundle.load(str(file_path.absolute()))

    if not bundle.debug_data:
        print("The bundle doesn't have any debug data!")
        exit(1)

    debug_data_file_path = file_path.with_name(file_path.stem + '_debug').with_suffix('.xml')
    with open(str(debug_data_file_path), 'wb') as fp:
        fp.write(bundle.debug_data)
    print(f"Dumped debug data to {debug_data_file_path}")
    
    exit(0)


if __name__ == '__main__':
    main()
