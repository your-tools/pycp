import sys

from pycp.main import main as pycp_main


def main() -> None:
    sys.argv = ["pycp", "src.dat", "dest.dat"]
    pycp_main()


if __name__ == "__main__":
    main()
