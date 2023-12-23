from bundle_v2 import BundleV2


def main() -> None:
    bundle = BundleV2()
    bundle.load('data/bundle.input')
    bundle.change_resource_id(0xA118C370, 0xDEADBEEF)
    print(bundle.get_missing_imports([]))
    bundle.compressed = False
    bundle.debug_data = b''
    bundle.save('data/bundle.output')


if __name__ == '__main__':
    main()
