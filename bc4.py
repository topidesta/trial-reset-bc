#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BC-RESET — versi PERBAIKAN
=======================================================================
Perbaikan dari kode asli "Beyond Compare Trial Reset.py".

YANG DIPERBAIKI
---------------
1. Path subkey tidak lagi menumpuk.  Asli:
       keyVal = keyVal + "\\" + asubkey     # jadi "...\\3", lalu "...\\3\\4" -> rusak
   Sekarang path dibangun ulang tiap iterasi dari root tetap.
2. Handle registry kini selalu ditutup (asli: key root bocor bila tidak ada
   subkey numerik, dan handle subkey tidak ditutup tiap iterasi).
3. Deteksi berakhirnya enumerasi tanpa mengandalkan exception di tengah
   try/except yang menelan semua error. Sekarang OSError spesifik
   (ERROR_NO_MORE_ITEMS) yang dihentikan; error lain tetap dilaporkan.
4. Tidak lagi memakai `from winreg import *` -> import eksplisit,
   lebih aman & jelas.
5. `import os, shutil` yang tidak terpakai dihapus.
6. Akses registry dibuka dengan hak minimum: KEY_QUERY_VALUE |
   KEY_ENUMERATE_SUB_KEYS | KEY_SET_VALUE (asli: KEY_ALL_ACCESS).
7. Subkey dengan nama kosong tidak lagi memicu IndexError.
8. Ada mode --dry-run (default) untuk MELIHAT apa yang akan dihapus tanpa
   mengubah apa pun, plus --backup untuk menyimpan nilai CacheID ke file
   .reg/.json sebelum dihapus.
9. Ringkasan hasil (jumlah subkey diperiksa / dihapus / dilewati) alih-alih
   pesan "Completed" yang buta.
10. Pesan dialog menampilkan ringkasan nyata, bukan teks statis.

CATATAN
-------
Ini tetap alat "trial reset" Beyond Compare. Menghapus CacheID membuat
aplikasi menganggap dirinya instalasi baru. Pakai dengan sadar: ini
melanggar ToS Beyond Compare, dan Anda mengubah registry tanpa jaminan.
Default sekarang AMAN (dry-run) — tidak menghapus apa pun sampai Anda
menjalankan dengan --apply.
=======================================================================
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path

import winreg
from winreg import HKEY_CURRENT_USER

# ---------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------
ROOT_SUBKEY = r"Software\Scooter Software"
VALUE_NAME = "CacheID"

# Hak akses minimum yang dibutuhkan untuk baca+enumerasi+hapus value.
ACCESS = winreg.KEY_QUERY_VALUE | winreg.KEY_ENUMERATE_SUB_KEYS | winreg.KEY_SET_VALUE

# Kode error Windows saat enumerasi sudah habis.
ERROR_NO_MORE_ITEMS = 259


# ---------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------
def list_numeric_subkeys(hive, root_path: str) -> list[str]:
    """Kembalikan nama subkey di bawah `root_path` yang berakhiran angka.

    Handle key root selalu ditutup (context manager), apa pun yang terjadi.
    """
    found: list[str] = []
    with winreg.OpenKey(hive, root_path, 0, winreg.KEY_READ) as root:
        index = 0
        while True:
            try:
                name = winreg.EnumKey(root, index)
            except OSError as exc:
                # 259 = ERROR_NO_MORE_ITEMS -> enumerasi normal selesai
                if getattr(exc, "winerror", None) == ERROR_NO_MORE_ITEMS:
                    break
                raise
            if name and name[-1].isdigit():
                found.append(name)
            index += 1
    return found


def read_value(hive, path: str, name: str):
    """Baca satu value registry; kembalikan (nilai, tipe) atau None bila tak ada."""
    try:
        with winreg.OpenKey(hive, path, 0, winreg.KEY_QUERY_VALUE) as key:
            return winreg.QueryValueEx(key, name)
    except FileNotFoundError:
        return None
    except OSError as exc:
        if getattr(exc, "winerror", None) == 2:  # ERROR_FILE_NOT_FOUND
            return None
        raise


def delete_value(hive, path: str, name: str) -> bool:
    """Hapus satu value registry. True bila terhapus, False bila memang tak ada."""
    try:
        with winreg.OpenKey(hive, path, 0, ACCESS) as key:
            winreg.DeleteValue(key, name)
        return True
    except FileNotFoundError:
        return False
    except OSError as exc:
        if getattr(exc, "winerror", None) == 2:
            return False
        raise


def backup_to_file(path: str, subkey: str, value, vtype) -> None:
    """Tulis nilai lama ke file .json agar bisa dikembalikan manual.

    Nilai biner (REG_BINARY) di-encode base64 dan ditandai encoding="base64"
    supaya tetap bisa di-JSON-kan dan dipulihkan apa adanya.
    """
    if isinstance(value, bytes):
        serialised = base64.b64encode(value).decode("ascii")
        encoding = "base64"
    else:
        serialised = value
        encoding = None

    out = Path(path)
    data = []
    if out.exists():
        try:
            data = json.loads(out.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = []
    record = {
        "subkey": subkey,
        "value": VALUE_NAME,
        "data": serialised,
        "type": int(vtype),
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if encoding:
        record["encoding"] = encoding
    data.append(record)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def notify(title: str, message: str) -> bool:
    """Dialog GUI opsional. Kembalikan True bila dialog benar-benar tampil.

    PENTING: pada build `--noconsole`, `print()` tidak terlihat. Jadi bila
    tkinter tidak ikut terbundel (mis. lupa `--hidden-import tkinter`), dulu
    fungsi ini gagal *diam-diam* dan pengguna yang klik-dua-kali tidak melihat
    apa pun sama sekali — seolah EXE rusak. Sekarang setiap kegagalan
    dilaporkan: bila modulnya hilang, tampilkan dialog MessageBox lewat ctypes
    (selalu tersedia di Windows, tanpa tkinter), dan bila itu pun gagal,
    tulis pesan ke berkas `bc-reset-notify-error.log` di sebelah EXE.
    """
    try:
        import tkinter
        from tkinter import messagebox

        root = tkinter.Tk()
        root.withdraw()
        messagebox.showinfo(title, message)
        root.destroy()
        return True
    except Exception as exc:
        _fallback_notify(title, message, exc)
        return False


def _fallback_notify(title: str, message: str, exc: BaseException) -> None:
    """Tampilkan pesan tanpa tkinter, supaya kegagalan tidak pernah senyap.

    Urutan: MessageBox Win32 (ctypes) -> berkas log di sebelah EXE -> stderr.
    """
    note = (
        f"{message}\n\n"
        f"[catatan] Dialog tkinter tidak tersedia ({type(exc).__name__}: {exc}).\n"
        f"Pesan ini ditampilkan lewat MessageBox darurat."
    )
    try:
        import ctypes

        MB_OK, MB_ICONWARNING = 0x0, 0x30
        ctypes.windll.user32.MessageBoxW(None, note, title, MB_OK | MB_ICONWARNING)
        return
    except Exception:
        pass

    try:
        base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path.cwd()
        log = base / "bc-reset-notify-error.log"
        with log.open("a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {title}\n{note}\n\n")
        return
    except Exception:
        pass

    print(note, file=sys.stderr)


# ---------------------------------------------------------------------
# Inti
# ---------------------------------------------------------------------
def reset_trial(*, apply: bool = False, backup: str | None = None) -> dict:
    """Cari subkey numerik dan (opsional) hapus CacheID-nya.

    apply=False -> dry-run: hanya melaporkan, tidak mengubah apa pun.
    """
    result = {"checked": 0, "deleted": 0, "skipped": 0, "errors": [], "dry_run": not apply}

    # Key induk mungkin tidak ada (Beyond Compare belum pernah dijalankan).
    try:
        subkeys = list_numeric_subkeys(HKEY_CURRENT_USER, ROOT_SUBKEY)
    except FileNotFoundError:
        result["errors"].append(
            f'Key "{ROOT_SUBKEY}" tidak ditemukan di HKCU '
            f"(Beyond Compare belum pernah dijalankan?)."
        )
        return result

    if not subkeys:
        result["errors"].append(
            f'Tidak ada subkey berakhiran angka di "{ROOT_SUBKEY}".'
        )
        return result

    for subkey in subkeys:
        # PENTING: path selalu dibangun dari root tetap, jadi tidak menumpuk.
        full_path = rf"{ROOT_SUBKEY}\{subkey}"
        result["checked"] += 1

        entry = read_value(HKEY_CURRENT_USER, full_path, VALUE_NAME)
        if entry is None:
            result["skipped"] += 1
            print(f"[skip]  {full_path}  (tidak punya value {VALUE_NAME})")
            continue

        value, vtype = entry
        shown = value if not isinstance(value, bytes) else f"<bytes {len(value)}>"
        if not apply:
            print(f"[dry]   {full_path}  {VALUE_NAME}={shown!r}  -> akan dihapus")
            result["deleted"] += 1  # dihitung sebagai "akan dihapus"
            continue

        if backup:
            backup_to_file(backup, full_path, value, vtype)
            print(f"[backup]{full_path}  -> {backup}")

        try:
            removed = delete_value(HKEY_CURRENT_USER, full_path, VALUE_NAME)
        except OSError as exc:
            result["errors"].append(f"{full_path}: {exc}")
            print(f"[error] {full_path}: {exc}")
            continue

        if removed:
            result["deleted"] += 1
            print(f"[hapus] {full_path}  {VALUE_NAME} dihapus")
        else:
            result["skipped"] += 1
            print(f"[skip]  {full_path}  (value sudah tidak ada)")

    return result


def build_summary(result: dict) -> str:
    mode = "DRY-RUN (tidak ada perubahan)" if result["dry_run"] else "APPLY"
    verb = "Akan dihapus" if result["dry_run"] else "Dihapus    "
    lines = [
        f"Mode       : {mode}",
        f"Diperiksa  : {result['checked']} subkey",
        f"{verb}: {result['deleted']} value {VALUE_NAME}",
        f"Dilewati   : {result['skipped']}",
    ]
    if result["errors"]:
        lines.append(f"Catatan    : {len(result['errors'])} masalah")
        lines += [f"  - {e}" for e in result["errors"]]
    return "\n".join(lines)


def _short_summary(result: dict, title: str) -> str:
    """Ringkasan human-friendly untuk dialog GUI (tanpa baris error verbose)."""
    if result["errors"]:
        return title + "\n\n" + "\n".join(f"- {e}" for e in result["errors"])
    if result["dry_run"]:
        return (
            f"{title}\n\n"
            f"DRY-RUN - tidak ada yang diubah.\n"
            f"{result['checked']} subkey diperiksa, "
            f"{result['deleted']} value {VALUE_NAME} AKAN dihapus.\n\n"
            f"Untuk benar-benar menghapus, jalankan:\n"
            f"  BC-RESET-fixed.exe --apply\n"
            f"(opsional tambahkan --backup data.json)"
        )
    return (
        f"{title}\n\n"
        f"{result['checked']} subkey diperiksa\n"
        f"{result['deleted']} value {VALUE_NAME} dihapus\n"
        f"{result['skipped']} dilewati"
    )


def _attach_console() -> bool:
    """Bila dijalankan dari .exe --noconsole tapi ada parent console, sambungkan.

    Trik standar Windows: AttachConsole(-1). Mengembalikan True bila berhasil.
    """
    try:
        import ctypes

        ATTACH_PARENT_PROCESS = -1
        if ctypes.windll.kernel32.AttachConsole(ATTACH_PARENT_PROCESS):
            # arahkan stdout/stderr ke console yang baru disambungkan
            sys.stdout = open("CONOUT$", "w", buffering=1, encoding="utf-8", errors="replace")
            sys.stderr = open("CONOUT$", "w", buffering=1, encoding="utf-8", errors="replace")
            return True
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reset trial Beyond Compare dengan menghapus value CacheID. "
        "Default DRY-RUN: tidak mengubah apa pun sampai --apply diberikan.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="benar-benar hapus CacheID (tanpa ini hanya simulasi)",
    )
    parser.add_argument(
        "--backup",
        metavar="FILE.json",
        help="simpan nilai CacheID lama ke FILE.json sebelum dihapus",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="jangan tampilkan dialog GUI di akhir",
    )
    args = parser.parse_args(argv)

    # .exe --noconsole: sambungkan ke console pemanggil bila ada, supaya CLI
    # (mis. dari cmd/PowerShell) tetap menampilkan teks.
    _attach_console()

    print("BC-RESET (versi perbaikan)")
    print("-" * 55)

    result = reset_trial(apply=args.apply, backup=args.backup)
    summary = build_summary(result)
    print("-" * 55)
    print(summary)

    if not args.no_gui:
        title = "BC-RESET: DRY-RUN (tidak ada perubahan)" if result["dry_run"] else "BC-RESET: selesai"
        if not notify(title, _short_summary(result, title)):
            result["errors"].append(
                "Dialog tkinter tidak tersedia; pesan darurat ditampilkan "
                "(build .exe butuh --hidden-import tkinter)."
            )

    # Exit code: 0 normal, 1 bila ada error nyata (bukan sekadar "tidak ada subkey")
    return 1 if any("Key" not in e and "Tidak ada" not in e for e in result["errors"]) else 0


if __name__ == "__main__":
    sys.exit(main())
