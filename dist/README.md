# BC-RESET — hasil build

Dua executable di sini dibangun dari `..\bc4.py` (PyInstaller 6.22.3,
Python 3.13, satu file / onefile, x86-64).

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

- `BC-RESET-fixed.exe` : 7.534.379 bytes, MD5 `ed050e2a90eb5d6009a7039b7a2f8e86`
- `BC-RESET-fixed-console.exe` : 7.537.376 bytes, MD5 `5da40ac529e9e6e6e188a9c67e7a6132`
- Keduanya terdeteksi sebagai `PE32+ executable (GUI/console) x86-64, for MS Windows`.

Diuji: dry-run tidak mengubah registry; `--apply` menghapus semua subkey
numerik pada key terisolasi; subkey non-numerik tidak tersentuh;
key asli `Beyond Compare 4` tidak pernah berubah selama pengujian.
Uji regresi ada di `..\test_bc4.py` (5/5 lulus).

## Build ulang

```bash
pip install pyinstaller
pyinstaller --noconfirm --clean --onefile --noconsole --name BC-RESET-fixed bc4.py
pyinstaller --noconfirm --clean --onefile --console  --name BC-RESET-fixed-console bc4.py
```

EXE **tidak** di-commit ke Git (lihat `..\.gitignore`); build ulang dari sumber.

## Peringatan

Ini alat *trial reset* Beyond Compare — melanggar ToS Beyond Compare.
Perbaikannya soal kode yang benar & aman, bukan soal legalitas.
