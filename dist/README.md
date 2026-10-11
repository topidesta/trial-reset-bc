# BC-RESET — hasil build

Dua executable di sini dibangun dari `..\bc4.py` (PyInstaller 6.22.3,
Python 3.14, satu file / onefile, x86-64).

| File | Tipe | Kegunaan |
|---|---|---|
| `BC-RESET-fixed.exe` | GUI (tanpa jendela konsol) | Klik-dua-kali. Menampilkan dialog ringkasan. Default **DRY-RUN**. |
| `BC-RESET-fixed-console.exe` | Konsol | Untuk dipakai dari cmd/PowerShell dengan argumen. |

Keduanya **identik secara fungsi**; bedanya cuma bagaimana output ditampilkan.
Versi GUI tetap mencetak ke konsol bila dipanggil dari cmd (via `AttachConsole`).

## Cara pakai

```bat
:: Lihat saja, tidak mengubah apa pun (default, AMAN)
BC-RESET-fixed-console.exe

:: Backup lalu hapus sungguhan
BC-RESET-fixed-console.exe --backup ..\cacheid-backup.json --apply

:: Tanpa dialog GUI
BC-RESET-fixed-console.exe --apply --no-gui

:: Bantuan
BC-RESET-fixed-console.exe --help
```

Atau klik-dua-kali `..\jalankan-dry-run.bat`.

## Yang dilakukan

Menghapus value registry `CacheID` di
`HKCU\Software\Scooter Software\<subkey berakhiran angka>`.
Tanpa `--apply`, **tidak ada yang diubah** — hanya laporan.

## Verifikasi

- `BC-RESET-fixed.exe` : 11.760.590 bytes, MD5 `27365d23306598e568d1c5942a39f9a1`
- `BC-RESET-fixed-console.exe` : 11.764.478 bytes, MD5 `a5e3a724890e3668c537eae8ac220504`
- Keduanya terdeteksi sebagai `PE32+ executable (GUI/console) x86-64, for MS Windows`.

> Ukuran naik dari ~7,5 MB menjadi ~11,8 MB karena **tkinter/tcl/tk ikut
> terbundel**. Di build sebelumnya tkinter tidak ikut terbundel, jadi versi
> GUI gagal menampilkan dialog **tanpa pesan apa pun** — itulah bug "build
> tidak bisa dijalankan" lewat klik-dua-kali.

Diuji: dry-run tidak mengubah registry; `--apply` menghapus semua subkey
numerik pada key terisolasi; subkey non-numerik tidak tersentuh;
key asli `Beyond Compare 4` tidak pernah berubah selama pengujian.
Uji regresi ada di `..\test_bc4.py` (5/5 lulus).

## Build ulang

```bash
pip install pyinstaller
python build_exe.py          # dari akar repo
```

`build_exe.py` membangun kedua EXE **dan** memverifikasi bahwa tkinter/tcl/tk
benar-benar ikut terbundel; kalau tidak, build dianggap GAGAL. Ia juga
menjalankan uji asap pada build konsol.

Jangan membangun dengan perintah `pyinstaller` polos — lihat peringatan di bawah.

> **Penting:** `--collect-all tkinter` (dan `--hidden-import tkinter`) wajib ada.
> Tanpa itu PyInstaller menganggap tkinter tidak terpakai — karena `import
> tkinter` baru dijalankan di dalam `notify()` saat dibutuhkan — sehingga tcl/tk
> tidak ikut terbundel dan dialog GUI tidak akan muncul.
>
> Perintah manual (kalau tidak memakai `build_exe.py`):
>
> ```bash
> pyinstaller --noconfirm --clean --onefile --noconsole \
>   --hidden-import tkinter --hidden-import tkinter.messagebox --collect-all tkinter \
>   --name BC-RESET-fixed bc4.py
> pyinstaller --noconfirm --clean --onefile --console \
>   --hidden-import tkinter --hidden-import tkinter.messagebox --collect-all tkinter \
>   --name BC-RESET-fixed-console bc4.py
> ```
>
> Setelah build manual, pastikan sendiri: cari string `tcl86`/`tk86` di dalam
> EXE. Kalau tidak ada, versi GUI tidak akan menampilkan apa pun.

EXE **tidak** di-commit ke Git (lihat `..\.gitignore`); build ulang dari sumber.

## Peringatan

Ini alat *trial reset* Beyond Compare — melanggar ToS Beyond Compare.
Perbaikannya soal kode yang benar & aman, bukan soal legalitas.
