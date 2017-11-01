python -m cProfile -o pycp.cprof -s cumulative run.py
pyprof2calltree -k -i pycp.cprof
