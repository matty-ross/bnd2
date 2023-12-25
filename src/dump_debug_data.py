import tkinter, tkinter.filedialog

from lib.bundle_v2 import BundleV2


def main() -> None:
    tkinter.Tk().withdraw()
    file_name = tkinter.filedialog.askopenfilename()

    bundle = BundleV2(file_name)
    bundle.load()

    if not bundle.debug_data:
        print("The bundle doesn't have any debug data.")
        return

    with open('debug_data.xml', 'wb') as fp:
        fp.write(bundle.debug_data)
    
    print("Done.")


if __name__ == '__main__':
    main()
