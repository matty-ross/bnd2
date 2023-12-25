import tkinter, tkinter.filedialog

from lib.bundle_v2 import BundleV2


def main() -> None:
    tkinter.Tk().withdraw()
    file_name = tkinter.filedialog.askopenfilename()

    bundle = BundleV2(file_name)
    bundle.load()

    if not bundle.compressed:
        print("The bundle already isn't compressed.")
        return

    bundle.compressed = False
    bundle.save()
    
    print("Done.")


if __name__ == '__main__':
    main()
