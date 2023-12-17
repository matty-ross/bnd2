from bundle_v2 import BundleV2


def main() -> None:
    bundle = BundleV2()
    bundle.load('data/bundle.input')
    bundle.dump_debug_data('data/debug_data.xml')
    bundle.save('data/bundle.output')


if __name__ == '__main__':
    main()
