# BC-RESET — hasil build

Dua executable di sini dibangun dari `..\bc4.py` (PyInstaller, Python 3.12+,
satu file / onefile, x86-64).

> **Catatan:** folder `dist/` di repo **tidak** memuat `.exe`. Biner dibangun
> ulang oleh GitHub Actions (`.github/workflows/release.yml`) saat tag `v*`
> di-push, lalu dilampirkan ke GitHub Release. Unduh dari halaman Releases,
> atau build sendiri dengan `python build_exe.py`.

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

Build yang dipublikasikan lewat GitHub Release **tidak** dicatat di sini,
karena hash-nya berubah tiap build. Yang berlaku adalah salah satu dari:

- Unduhan dari GitHub Release → cocokkan dengan `SHA256SUMS.txt` yang
  dilampirkan di rilis yang sama. GitHub Actions membuatnya otomatis.
- Build lokal → hitung sendiri: `Get-FileHash dist\*.exe -Algorithm SHA256`.

Keduanya terdeteksi sebagai `PE32+ executable (GUI/console) x86-64, for MS Windows`
dan berukuran ~11,8 MB.

> Ukuran itu (~11,8 MB, bukan ~7,5 MB) karena **tkinter/tcl/tk ikut terbundel**.
> Di build lama tkinter tidak ikut, jadi versi GUI gagal menampilkan dialog
> **tanpa pesan apa pun** — itulah bug "build tidak bisa dijalankan" lewat
> klik-dua-kali. `build_exe.py` sekarang menolak menghasilkan build seperti itu.

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

EXE **tidak** di-commit ke Git (lihat `..\.gitignore`). Untuk merilis versi
baru, cukup push tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions akan menjalankan uji, membangun kedua EXE, dan melampirkannya
(plus `SHA256SUMS.txt`) ke GitHub Release secara otomatis.

## Peringatan

Ini alat *trial reset* Beyond Compare — melanggar ToS Beyond Compare.
Perbaikannya soal kode yang benar & aman, bukan soal legalitas.
