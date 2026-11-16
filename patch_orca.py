"""Patch OrcaSlicer.app so files sent to Bambu printers keep model geometry.

Plater::send_gcode exports with Silence|SkipModel|WithGcode|SkipAuxiliary (0x2B0);
this rewrites that constant to Silence|SplitModel|WithGcode (0x1034) in both slices
of the universal binary. Refuses to patch unless the constant occurs exactly once.

Usage: python3 patch_orca.py /path/to/OrcaSlicer.app
"""
import re
import struct
import subprocess
import sys

SYM = "__ZN6Slic3r3GUI6Plater10send_gcodeEiNSt3__18functionIFviiiRbEEE"
OLD, NEW = 0x2B0, 0x1034


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def slice_offsets(binary):
    out = run("lipo", "-detailed_info", binary)
    arches = re.findall(r"architecture (\S+)\n(?:.*\n)*?\s+offset (\d+)", out)
    return {a: int(o) for a, o in arches}


def text_base(binary, arch):
    out = run("otool", "-arch", arch, "-l", binary)
    m = re.search(r"segname __TEXT\n\s+vmaddr (0x[0-9a-f]+)\n\s+vmsize \S+\n\s+fileoff (\d+)", out)
    return int(m.group(1), 16), int(m.group(2))


def find_site(binary, arch):
    # Disassemble from the function start up to its first return.
    out = run("otool", "-arch", arch, "-tV", "-p", SYM, binary)
    body = []
    for line in out.splitlines()[1:]:
        body.append(line)
        if re.search(r"\s(ret|retq)\b", line):
            break
    pat = r"mov\s+w2, #0x2b0\b" if arch == "arm64" else r"movl\s+\$0x2b0, %edx"
    hits = [l for l in body if re.search(pat, l)]
    if len(hits) != 1:
        sys.exit(f"patch failed ({arch}): expected 1 SkipModel constant in send_gcode, found {len(hits)}")
    return int(hits[0].split()[0], 16)


def encode(arch, value):
    if arch == "arm64":  # movz w2, #value
        return struct.pack("<I", 0x52800000 | (value << 5) | 2)
    return b"\xba" + struct.pack("<I", value)  # movl $value, %edx


def main(app):
    binary = f"{app}/Contents/MacOS/OrcaSlicer"
    offsets = slice_offsets(binary)
    with open(binary, "r+b") as f:
        for arch in ("arm64", "x86_64"):
            addr = find_site(binary, arch)
            vmaddr, fileoff = text_base(binary, arch)
            pos = offsets[arch] + fileoff + (addr - vmaddr)
            f.seek(pos)
            current = f.read(len(encode(arch, OLD)))
            if current != encode(arch, OLD):
                sys.exit(f"patch failed ({arch}): unexpected bytes {current.hex()} at {pos:#x}")
            f.seek(pos)
            f.write(encode(arch, NEW))
            print(f"{arch}: patched {addr:#x}")
    run("codesign", "--force", "--deep", "--preserve-metadata=entitlements,flags,runtime", "--sign", "-", app)
    print("re-signed (ad-hoc)")
    # Drop the download quarantine flag so Gatekeeper doesn't block the first launch.
    run("xattr", "-dr", "com.apple.quarantine", app)
    print("quarantine flag removed")


if __name__ == "__main__":
    main(sys.argv[1].rstrip("/"))
