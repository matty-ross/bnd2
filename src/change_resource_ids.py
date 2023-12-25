import tkinter, tkinter.filedialog

from lib.bundle_v2 import BundleV2


def main() -> None:
    tkinter.Tk().withdraw()
    file_name = tkinter.filedialog.askopenfilename()

    bundle = BundleV2(file_name)
    bundle.load()

    while True:
        old_id = int(input("Old resource ID: "), 16)
        new_id = int(input("New resource ID: "), 16)
        bundle.change_resource_id(old_id, new_id)

        if input("Continue? y/n: ").lower() == 'n':
            break

    if input("Remove debug data? y/n: ").lower() == 'y':
        bundle.debug_data = b''

    bundle.save()
    print("Done.")


if __name__ == '__main__':
    main()
