import sys

if __name__ == "__main__":
    from devchat._cli.main import main as _main

    sys.exit(_main(windows_expand_args=False))
