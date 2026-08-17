import sys, pathlib

src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
lines = src.read_text(encoding="utf-8").splitlines()
out = []
stamped = injected = False
for line in lines:
    if line.startswith('STAMP="$(date'):
        out.append('STAMP="FIXEDSTAMP"')
        stamped = True
        continue
    out.append(line)
    if line.startswith('COMMAND="TRANSFORMERS_OFFLINE=1') and not injected:
        out.append("printf '%s\\n' \"${COMMAND}\"")
        out.append("exit 0")
        injected = True
assert stamped, "STAMP line not found"
assert injected, "COMMAND line not found"
dst.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"instrumented {src} -> {dst}")
