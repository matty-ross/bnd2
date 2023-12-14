from bundle_v2 import BundleV2


if __name__ == '__main__':
    bundle = BundleV2()
    bundle.load('bundle.input')
    bundle.save('bundle.output')
