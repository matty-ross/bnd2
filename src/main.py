from bundle_v2 import BundleV2


def main() -> None:
    bundle = BundleV2()
    bundle.load('bundle.input')
    bundle.save('bundle.output')


if __name__ == '__main__':
    main()
