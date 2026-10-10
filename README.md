# trial-reset-bc

Perbaikan (rewrite) dari alat "Beyond Compare Trial Reset" — sebuah skrip yang
mengosongkan penanda instalasi **Beyond Compare 4** di registry Windows, sehingga
aplikasi menganggap dirinya instalasi baru dan hitungan masa coba 30 hari mulai
dari nol lagi.

Repo: `github.com/topidesta/trial-reset-bc`

> **Peringatan lebih dulu.** Ini alat trial-reset. Tindakan ini **melanggar
> Terms of Service Beyond Compare** (Scooter Software), dan Anda menyunting
> registry Windows tanpa jaminan apa pun. Kalau Anda memakai Beyond Compare
> untuk bekerja, beli lisensinya — lebih murah daripada risiko data/konfigurasi
> rusak. Panduan di bawah tetap lengkap karena kode ini juga alat peraga yang
> berguna untuk belajar menulis registry Windows dengan benar.

---

## 1. Cara kerja Beyond Compare 4

Beyond Compare bukan aplikasi portabel: setiap instalasi menyimpan **ID
instalasi** yang unik di registry. Bentuknya:

```
HKEY_CURRENT_USER\Software\Scooter Software\<subkey numerik>\CacheID
```

Beberapa catatan penting:

| Hal | Keterangan |
|---|---|
| Hive | `HKEY_CURRENT_USER` (HKCU) — **per pengguna**, bukan `HKLM`, jadi tidak mengubah sistem secara global. |
| `<subkey numerik>` | Biasanya `3`, `4`, atau angka versi lain. Nama subkey **diakhiri angka**; itulah penandanya. |
| `CacheID` | Value bertipe `REG_BINARY` yang menjadi identitas instalasi. |
| Kapan dibuat | Saat BC4 pertama kali dijalankan. Kalau BC4 belum pernah dijalankan, key induknya belum ada. |

**Mekanisme reset:** hapus value `CacheID`. BC4 tidak lagi menemukan jejak
instalasi sebelumnya, lalu membuat `CacheID` baru dan memulai hitungan trial
30 hari dari awal.

Konsekuensinya: **jangan menganggap ini sekadar menjalankan exe satu klik.**
Menghapus `CacheID` juga menghapus kaitan profil/pengaturan lokal yang terikat
pada instalasi tersebut. Karena itulah versi di repo ini didesain agar tidak
pernah menghapus apa pun kecuali Anda memintanya secara eksplisit.

---

## 2. Isi repo

```
trial-reset-bc/
├── bc4.py                    # versi perbaikan (dipakai sekarang)
├── test_bc4.py               # uji otomatis (5 tes, key registry terisolasi)
├── jalankan-dry-run.bat      # launcher klik-dua-kali (default dry-run)
├── dist/
│   ├── BC-RESET-fixed.exe          # build GUI (tanpa konsol) — klik-dua-kali
│   ├── BC-RESET-fixed-console.exe  # build konsol — untuk CLI
│   └── README.md                   # cara pakai + cara build ulang
├── legacy/
│   ├── BC-RESET.exe          # binary asli rilis 2020 (PyInstaller, GUI, tanpa konsol)
│   └── bc4.py                # dekompilasi + analisis kode asli (bahan rujukan)
└── README.md
```

- **`bc4.py`** — versi yang dirawat. CLI, default aman (dry-run), punya backup.
- **`dist/`** — hasil build PyInstaller (onefile, x86-64). EXE **tidak** di-commit
  (lihat `.gitignore`); ada di folder ini supaya bisa langsung dipakai. Build ulang
  dengan perintah di `dist/README.md`.
- **`test_bc4.py`** — uji regresi yang memakai key terisolasi
  `HKCU\Software\WorkBuddyTest`; tidak pernah menyentuh key asli Beyond Compare.
- **`legacy/BC-RESET.exe`** — binary asli, 30 November 2020, ~7,66 MB, PE32+
  GUI x86-64. Berkas ini **disimpan hanya sebagai artefak sejarah** untuk
  membandingkan hasil dekompilasi. Jangan dijalankan; ia tidak punya mode
  dry-run dan langsung menghapus `CacheID` tanpa backup.
- **`legacy/bc4.py`** — hasil dekompilasi `.pyc` di dalam exe, lengkap dengan
  anotasi pada tiap baris dan daftar bug. Berguna kalau Anda ingin
  memverifikasi sendiri apa yang dilakukan binary itu sebelum memutuskan
  memakainya.

### Jejak forensik binary asli (dari `legacy/bc4.py`)

| Item | Nilai |
|---|---|
| MD5 | `28298971c3ad5c1bd27b8093ec33d93e` |
| SHA-256 | `40d44ed6e4e3cf4f8f035ea4a78ea4b2e910adfb25cfab8b5bc31376fb96fd79` |
| Dikemas dengan | PyInstaller (CArchive 3.6, skrip 2.1+) di atas CPython 3.6 + tkinter |
| Isi PYZ | 139 modul, seluruhnya pustaka standar Python |
| Modul pihak ketiga / payload tersembunyi | tidak ada |
| Jaringan | tidak ada socket/http/urllib yang dipakai skrip |
| UPX | tidak terdeteksi |

Kesimpulan audit: bukan malware jaringan, tidak akan mengunduh atau mengirim
apa pun. Yang dilakukannya murni menghapus `CacheID` di HKCU milik user sendiri.
Itu tetap tidak membuatnya sah — hanya membuatnya tidak menipu.

---

## 3. Apa yang diperbaiki dibanding versi asli

Kode asli bekerja untuk kasus umum, tapi punya bug nyata. Versi di repo ini
memperbaiki semuanya:

1. **Path subkey tidak lagi menumpuk.** Asli melakukan
   `keyVal = keyVal + "\\" + asubkey` di dalam loop, jadi path menjadi
   `...\3`, lalu `...\3\4`, dan seterusnya — subkey kedua dan seterusnya
   berpotensi gagal dibuka. Sekarang path dibangun ulang dari root tetap pada
   setiap iterasi.
2. **Handle registry selalu ditutup.** Asli membocorkan handle key induk bila
   tidak ada subkey numerik, dan tidak menutup handle subkey di setiap iterasi.
   Sekarang semuanya memakai `with`.
3. **Deteksi akhir enumerasi yang benar.** Asli mengandalkan `except
   WindowsError: pass` yang menelan *semua* error. Sekarang hanya
   `ERROR_NO_MORE_ITEMS` (259) yang dianggap akhir normal; error lain tetap
   dilaporkan.
4. **Import eksplisit.** Tidak lagi `from winreg import *`.
5. **`import os, shutil` yang tidak terpakai dihapus.**
6. **Hak akses minimum.** Asli memakai `KEY_ALL_ACCESS`; sekarang
   `KEY_QUERY_VALUE | KEY_ENUMERATE_SUB_KEYS | KEY_SET_VALUE` saja.
7. **Tidak lagi `IndexError`** pada subkey bernama kosong.
8. **Mode `--dry-run` (default)** untuk melihat apa yang akan dihapus, plus
   `--backup` untuk menyimpan nilai `CacheID` lama ke `.json` sebelum dihapus.
9. **Ringkasan hasil nyata** (berapa subkey diperiksa / dihapus / dilewati)
   alih-alih pesan "Completed" yang tanpa isi.
10. **Dialog GUI menampilkan ringkasan sebenarnya**, bukan teks statis.

---

## 4. Persyaratan

- **Windows** (wajib — memakai modul `winreg`).
- **Python 3.10+** (kode memakai anotasi `list[str] | None` dan
  `from __future__ import annotations`).
- Tidak ada dependensi pihak ketiga. `tkinter` opsional: kalau tidak tersedia,
  dialog GUI dilewati diam-diam dan hasil tetap dicetak di konsol.

## 5. Pemakaian

Selalu mulai dari dry-run. Tanpa `--apply`, tidak ada satu pun value yang
diubah.

### Versi Python

```bash
# 1) Lihat apa yang akan terjadi (default, aman)
python bc4.py

# 2) Lihat + simpan nilai lama ke berkas sebelum dihapus
python bc4.py --backup cacheid-backup.json

# 3) Baru benar-benar hapus (butuh --apply)
python bc4.py --apply --backup cacheid-backup.json

# Tanpa dialog GUI (mis. di sesi otomatis)
python bc4.py --apply --no-gui
```

### Versi EXE (tanpa perlu Python)

```bat
:: Lihat saja, tidak mengubah apa pun (default, AMAN)
dist\BC-RESET-fixed-console.exe

:: Backup lalu hapus sungguhan
dist\BC-RESET-fixed-console.exe --backup cacheid-backup.json --apply

:: Bantuan
dist\BC-RESET-fixed-console.exe --help
```

`dist\BC-RESET-fixed.exe` sama saja tapi tanpa jendela konsol (cocok untuk
klik-dua-kali; hasil tetap ditampilkan lewat dialog ringkasan). Atau klik-dua-kali
`jalankan-dry-run.bat`.

### Menjalankan uji

```bash
python test_bc4.py
```

Uji memakai key terisolasi `HKCU\Software\WorkBuddyTest` dan membersihkannya
setelah selesai — key Beyond Compare asli tidak pernah disentuh.

### Opsi

| Opsi | Arti |
|---|---|
| `--apply` | Benar-benar menghapus `CacheID`. Tanpa ini hanya simulasi. |
| `--backup FILE.json` | Simpan nilai `CacheID` lama ke `FILE.json` sebelum dihapus. Nilai biner disimpan sebagai base64 dengan penanda `"encoding": "base64"`. |
| `--no-gui` | Jangan tampilkan dialog tkinter di akhir. |

### Contoh keluaran dry-run

```
BC-RESET (versi perbaikan)
-------------------------------------------------------
[dry]   Software\Scooter Software\4  CacheID=<bytes 32>  -> akan dihapus
-------------------------------------------------------
Mode       : DRY-RUN (tidak ada perubahan)
Diperiksa  : 1 subkey
Akan dihapus: 1 value CacheID
Dilewati   : 0
```

### Exit code

| Kode | Arti |
|---|---|
| `0` | Normal — termasuk saat key induk tidak ditemukan atau tidak ada subkey numerik (bukan kegagalan fatal). |
| `1` | Ada error nyata saat membaca/menghapus registry. |

### Setelah menjalankan `--apply`

Tutup Beyond Compare sepenuhnya sebelum menjalankan, lalu buka kembali. BC4
akan membuat `CacheID` baru dan hitungan trial dimulai ulang.

Untuk mengembalikan nilai lama, buka `cacheid-backup.json` dan tulis ulang
value tersebut secara manual lewat `regedit` (nilai base64 harus di-decode
lebih dulu).

---

## 6. Verifikasi cepat tanpa registry

Kalau Anda hanya ingin memastikan skripnya berjalan dan logikanya benar tanpa
menyentuh registry, jalankan dry-run di mesin yang belum pernah memasang BC4 —
skrip akan berhenti dengan pesan yang jelas, bukan error mentah:

```
Catatan    : 1 masalah
  - Key "Software\Scooter Software" tidak ditemukan di HKCU
    (Beyond Compare belum pernah dijalankan?).
```

Itu perilaku yang diinginkan: skrip tidak menganggap "tidak ada yang bisa
dihapus" sebagai sukses yang buta.

---

## 7. Batasan & catatan

- Hanya menangani hive **HKCU**. Instalasi yang menulis penanda ke `HKLM`
  (mis. lewat installer system-wide) tidak tercakup.
- Hanya menghapus value bernama tepat `CacheID`. Nama value lain dari versi BC
  yang berbeda tidak disentuh.
- Tidak ada otomatisasi penghapusan key — hanya value, sesuai perilaku alat
  aslinya.
- Versi di `legacy/` **tidak dirawat** dan tidak akan diperbaiki.

## 7a. Build ulang EXE

Butuh `pyinstaller` (`pip install pyinstaller`). Dari akar repo:

```bash
pyinstaller --noconfirm --clean --onefile --noconsole --name BC-RESET-fixed bc4.py
pyinstaller --noconfirm --clean --onefile --console  --name BC-RESET-fixed-console bc4.py
```

Hasilnya di `dist/`. Salah satu trik yang dipakai `bc4.py`: pada build
`--noconsole`, `print()` tidak terlihat. Karena itu skrip memanggil
`AttachConsole(-1)` — kalau dipanggil dari cmd/PowerShell ia "menempel" ke
konsol pemanggil sehingga teks tetap muncul, tapi klik-dua-kali tidak
memunculkan jendela hitam.

## 8. Lisensi & etika

Kode di repo ini disediakan untuk keperluan pembelajaran dan analisis. Yang
dilakukannya — memakai Beyond Compare melewati masa coba — melanggar perjanjian
lisensinya. Tanggung jawab kepatuhan ada pada Anda.

Kalau Anda menemukan alat ini berguna, cara terbaik menghargai pembuatnya
adalah membeli lisensi Beyond Compare.
