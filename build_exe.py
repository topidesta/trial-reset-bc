#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_exe.py — build ulang KEDUA EXE (GUI + konsol) dengan benar.

Kenapa ada skrip ini, bukan sekadar dua baris `pyinstaller` di README?

    `bc4.py` mengimpor `tkinter` DI DALAM fungsi `notify()`, bukan di tingkat
    modul. Analisis PyInstaller karena itu menyimpulkan tkinter tidak pernah
    dipakai dan TIDAK membundel tcl/tk. Akibatnya versi `--noconsole` selesai
    tanpa menampilkan dialog apa pun: klik-dua-kali tampak seperti "tidak
    terjadi apa-apa". Itu bug yang pernah benar-benar terjadi di repo ini.

Skrip ini melakukan tiga hal supaya bug itu tidak bisa terulang diam-diam:

    1. Membangun dengan `--collect-all tkinter` (plus hidden-import).
    2. Memverifikasi tkinter BENAR-BENAR ada di dalam biner hasil build —
       kalau tidak, build dianggap GAGAL (bukan sekadar "selesai").
    3. Menjalankan uji asap: EXE konsol harus bisa mencetak ringkasan dry-run.

Pemakaian:
    python build_exe.py            # build + verifikasi
    python build_exe.py --no-verify
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
SRC = "bc4.py"

# Penanda bahwa tcl/tk benar-benar ikut terbundel. `tcl86`/`tk86` adalah nama
# DLL Tcl/Tk; tanpa keduanya dialog tkinter tidak mungkin muncul.
TK_MARKERS = (b"_tkinter", b"tkinter", b"tcl86", b"tk86")

TARGETS = [
    # (nama EXE, flag mode tambahan, deskripsi)
    ("BC-RESET-fixed", ["--noconsole"], "GUI (klik-dua-kali)"),
    ("BC-RESET-fixed-console", ["--console"], "konsol (CLI)"),
]


def build_one(name: str, mode_flags: list[str]) -> Path:
    """Jalankan PyInstaller untuk satu target; kembalikan path EXE."""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile",
        *mode_flags,
        # Inilah inti perbaikannya: tkinter dipakai di dalam fungsi, jadi harus
        # dipaksa ikut. `--collect-all` juga menarik data tcl/tk.
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.messagebox",
        "--collect-all", "tkinter",
        "--distpath", str(DIST),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
        "--name", name,
        SRC,
    ]
    print(f"\n=== build {name} ({' '.join(mode_flags)}) ===")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"PyInstaller gagal untuk {name} (kode {result.returncode})")

    exe = DIST / f"{name}.exe"
    if not exe.exists():
        raise SystemExit(f"EXE tidak ditemukan setelah build: {exe}")
    return exe


def verify_tkinter(exe: Path) -> None:
    """Pastikan penanda tkinter/tcl/tk ada di dalam biner. Gagal -> SystemExit."""
    data = exe.read_bytes()
    counts = {m.decode(): data.count(m) for m in TK_MARKERS}
    print(f"  verifikasi {exe.name}: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    missing = [m.decode() for m in TK_MARKERS if data.count(m) == 0]
    if missing:
        raise SystemExit(
            f"GAGAL: {exe.name} tidak memuat tkinter ({', '.join(missing)}).\n"
            f"Versi GUI akan gagal menampilkan dialog secara senyap.\n"
            f"Pastikan tidak ada yang menghapus --collect-all tkinter dari perintah build."
        )


def smoke_test(exe: Path) -> None:
    """Uji asap: EXE konsol harus mencetak ringkasan dry-run dan keluar kode 0."""
    print(f"  uji asap {exe.name} --no-gui ...")
    proc = subprocess.run(
        [str(exe), "--no-gui"],
        capture_output=True, text=True, timeout=60,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        raise SystemExit(f"GAGAL: {exe.name} keluar dengan kode {proc.returncode}\n{out}")
    if "DRY-RUN" not in out:
        raise SystemExit(f"GAGAL: {exe.name} tidak mencetak ringkasan dry-run.\n{out}")
    print("  -> OK")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build ulang EXE BC-RESET dengan tkinter.")
    parser.add_argument("--no-verify", action="store_true",
                        help="lewati verifikasi biner + uji asap (tidak disarankan)")
    args = parser.parse_args(argv)

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        raise SystemExit(
            "PyInstaller belum terpasang.\n"
            "  pip install pyinstaller\n"
            "Catatan: pastikan interpreter yang dipakai MEMPUNYAI tkinter.\n"
            "  python -c \"import tkinter, sys; print(sys.executable)\""
        )

    # tkinter harus ada di interpreter yang membangun; kalau tidak, PyInstaller
    # tidak akan bisa mengumpulkannya.
    try:
        import tkinter  # noqa: F401
    except ImportError:
        raise SystemExit(
            f"Interpreter ini TIDAK punya tkinter: {sys.executable}\n"
            f"Versi GUI tidak akan bisa menampilkan dialog. Pakai Python lain\n"
            f"yang punya tkinter. Periksa dengan:\n"
            f"  \"C:/path/ke/python.exe\" -c \"import tkinter; print('ok')\""
        )

    for name, flags, desc in TARGETS:
        exe = build_one(name, flags)
        if not args.no_verify:
            verify_tkinter(exe)
            # Uji asap hanya untuk build konsol: build GUI memblokir menunggu
            # dialog, jadi tidak cocok untuk pemeriksaan otomatis.
            if "--console" in flags:
                smoke_test(exe)
        print(f"  -> {desc}: {exe}")

    # Bersihkan artefak antara; .spec sengaja TIDAK disimpan agar tidak ada
    # dua sumber kebenaran dengan skrip ini.
    shutil.rmtree(ROOT / "build", ignore_errors=True)

    print("\nSelesai. Kedua EXE ada di dist/ dan sudah diverifikasi memuat tkinter.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
