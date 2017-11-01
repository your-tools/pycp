import pycp.transfer


def main():
    with open("src.dat", "wb") as fp:
        for i in range(0, 5):
            data = [i] * pycp.transfer.BUFFER_SIZE
            fp.write(bytes(data))


if __name__ == "__main__":
    main()
