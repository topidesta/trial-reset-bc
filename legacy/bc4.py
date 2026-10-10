#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BC-RESET.exe — KODE ASLI + ANALISIS
=======================================================================
File        : C:\\Users\\asus\\Desktop\\BC-RESET.exe
Nama internal: "Beyond Compare Trial Reset.exe"
Ukuran      : 8.035.048 bytes (~7,66 MB)
Tipe        : PE32+ GUI executable, x86-64, Windows (no console)
Tanggal     : 30 November 2020
MD5         : 28298971c3ad5c1bd27b8093ec33d93e
SHA-256     : 40d44ed6e4e3cf4f8f035ea4a78ea4b2e910adfb25cfab8b5bc31376fb96fd79

CARA DIKEMAS
------------
Dibungkus dengan PyInstaller (layout CArchive versi 3.6, skrip 2.1+)
di atas CPython 3.6 (python36.dll) + tkinter.
  - CArchive  : 931 entri (DLL, tcl/tk, pyd, pyc)
  - Entry point: "Beyond Compare Trial Reset.pyc"
  - PYZ       : 139 modul — seluruhnya pustaka standar Python
                (TIDAK ada modul pihak ketiga / payload tersembunyi)
  - UPX       : tidak terdeteksi
  - Jaringan  : tidak ada socket/http/urllib yang dipakai skrip

APA YANG DILAKUKAN
------------------
Ini alat "trial reset" untuk Beyond Compare (Scooter Software).
Beyond Compare menyimpan ID instalasi di registry:
    HKCU\\Software\\Scooter Software\\<subkey numerik>\\CacheID
Program menghapus value "CacheID" tiap subkey yang diakhiri angka.
Akibatnya Beyond Compare menganggap dirinya instalasi baru, sehingga
hitungan trial 30 hari ter-reset (bisa dipakai lagi dari awal).

CATATAN RISIKO
--------------
- Menulis & menghapus value di registry Windows (HKCU) — tanpa backup.
- Hanya menyentuh HKCU milik user, bukan HKLM (tidak system-wide).
- Bukan malware jaringan; tidak mengunduh/mengirim apa pun.
- Namun tetap melanggar ToS Beyond Compare. Pakai dengan sadar.
"""

# =====================================================================
# KODE ASLI (dekompilasi bytecode Python 3.6, apa adanya)
# =====================================================================
# Anotasi "# <-" ditambahkan oleh saya; sisanya hasil dekompilasi mentah.

from winreg import *            # <- API registry Windows
import os, shutil               # <- di-import tapi TIDAK dipakai (sisa template)

keyVal = "Software\\Scooter Software"                   # <- HKCU\Software\Scooter Software
aKey = OpenKey(HKEY_CURRENT_USER, keyVal, 0, KEY_ALL_ACCESS)   # <- buka key induk

try:
    i = 0
    while True:
        # EnumKey melempar OSError/WindowsError saat index habis -> keluar loop
        asubkey = EnumKey(aKey, i)          # <- ambil subkey ke-i (mis. "3")
        last_asubkey = asubkey[-1]          # <- karakter terakhir subkey
        if last_asubkey.isdigit():          # <- hanya proses subkey yang berakhiran angka
            CloseKey(aKey)
            keyVal = keyVal + "\\" + asubkey
            aKey = OpenKey(HKEY_CURRENT_USER, keyVal, 0, KEY_ALL_ACCESS)
            DeleteValue(aKey, "CacheID")    # <- INTI: hapus CacheID = reset trial
            print("deleted: " + asubkey)
        i += 1

except WindowsError:                        # <- normal: loop berakhir karena index habis
    pass

# --- tampilkan dialog konfirmasi (GUI) ---
import tkinter
from tkinter import messagebox
root = tkinter.Tk()
root.withdraw()                             # <- sembunyikan window utama, hanya popup
messagebox.showinfo("Completed ...... ", "Trial Reset Completed")

# =====================================================================
# CATATAN BUG DI KODE ASLI
# =====================================================================
# 1) Variabel keyVal terus bertambah tiap iterasi ("...\3", lalu "..\3\4"...),
#    sehingga bila ada >1 subkey numerik, subkey kedua dst. kemungkinan gagal
#    dibuka (path menumpuk). Untuk kasus umum (1 subkey) tetap berfungsi.
# 2) `import os, shutil` tidak terpakai.
# 3) `last_asubkey = asubkey[-1]` bisa IndexError bila ada subkey ber-nama kosong
#    (tidak dibungkus try) — di praktik jarang terjadi.
