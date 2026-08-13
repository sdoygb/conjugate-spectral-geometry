#!/usr/bin/env python3
"""Repack zip with UTF-8 filename flags (bit 11) so any extractor decodes names correctly."""
import zipfile, shutil, sys

SRC = "GeometryAI-Linux-SubAI-v1.0.0.0812.zip"
TMP = "GeometryAI-Linux-SubAI-v1.0.0.0812.utf8.zip"

zin = zipfile.ZipFile(SRC, "r")
zout = zipfile.ZipFile(TMP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9)

fixed = 0
for item in zin.infolist():
    raw_name = item.filename
    if not (item.flag_bits & 0x800):
        # filename was decoded as cp437; recover original bytes
        try:
            raw_bytes = item.filename.encode("cp437")
            name = raw_bytes.decode("utf-8")
            if name != item.filename:
                fixed += 1
            item.filename = name
            item.flag_bits |= 0x800
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
    data = zin.read(item)
    zout.writestr(item, data)

zout.close()
zin.close()
print(f"fixed {fixed} entries with UTF-8 flag")

# verify round-trip
z = zipfile.ZipFile(TMP, "r")
names = z.namelist()
cn = [n for n in names if any('\u4e00' <= c <= '\u9fff' for c in n)]
print(f"total={len(names)} chinese-named={len(cn)}")
sample = [n for n in cn if '260808' in n][:3]
print("samples:", sample)
z.close()

shutil.move(TMP, SRC)
print("replaced", SRC)
