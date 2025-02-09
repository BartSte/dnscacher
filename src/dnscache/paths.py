from os.path import abspath, dirname, join

root: str = abspath(dirname(__file__))
debug: str = join(root, "debug.txt")
