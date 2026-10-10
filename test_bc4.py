#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uji untuk bc4.py (alat trial-reset Beyond Compare).

Dijalankan di key registry TERISOLASI (HKCU\\Software\\WorkBuddyTest),
tidak pernah menyentuh key asli Beyond Compare.

Bukti utama: bug path-menumpuk di kode asli (keyVal += "\\" + subkey)
sudah tidak ada — dengan >=2 subkey numerik, semua subkey tetap
berhasil diproses.

Jalankan:  python test_bc4.py
"""

import importlib.util
import sys
import winreg
from pathlib import Path

HERE = Path(__file__).parent
ROOT = r"Software\WorkBuddyTest"

# muat modul yang diuji
spec = importlib.util.spec_from_file_location("bcreset", HERE / "bc4.py")
bcreset = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bcreset)
bcreset.ROOT_SUBKEY = ROOT


def _del_tree(path: str) -> None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_ALL_ACCESS) as k:
            while True:
                try:
                    sub = winreg.EnumKey(k, 0)
                except OSError:
                    break
                _del_tree(path + "\\" + sub)
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
    except FileNotFoundError:
        pass


def _make(sub: str, value) -> None:
    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER, ROOT + "\\" + sub, 0, winreg.KEY_ALL_ACCESS
    ) as k:
        vtype = winreg.REG_BINARY if isinstance(value, bytes) else winreg.REG_SZ
        winreg.SetValueEx(k, "CacheID", 0, vtype, value)


def _exists(sub: str) -> bool:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, ROOT + "\\" + sub, 0, winreg.KEY_QUERY_VALUE
        ) as k:
            winreg.QueryValueEx(k, "CacheID")
            return True
    except FileNotFoundError:
        return False


def setup():
    _del_tree(ROOT)
    _make("64", b"X" * 48)      # mirip key asli Beyond Compare 4 -> REG_BINARY
    _make("4", "short")
    _make("7", "another")
    _make("nope", "must-not-touch")   # berakhir NON-angka -> harus dilewati


def teardown():
    _del_tree(ROOT)


def test_dry_run_does_not_change():
    setup()
    try:
        r = bcreset.reset_trial(apply=False)
        assert r["dry_run"] is True
        assert not r["errors"], r["errors"]
        # ketiga subkey numerik terdeteksi
        assert r["checked"] == 3, r
        # tidak ada yang benar-benar terhapus
        assert all(_exists(s) for s in ("64", "4", "7")), "dry-run mengubah registry!"
    finally:
        teardown()


def test_apply_deletes_all_numeric_subkeys():
    """Ini menangkap bug path-menumpuk: dulu subkey ke-2 dst gagal."""
    setup()
    try:
        r = bcreset.reset_trial(apply=True)
        assert not r["errors"], r["errors"]
        assert r["deleted"] == 3, r
        for s in ("64", "4", "7"):
            assert not _exists(s), f"subkey {s} tidak terhapus -> bug path masih ada"
    finally:
        teardown()


def test_non_numeric_subkey_untouched():
    setup()
    try:
        bcreset.reset_trial(apply=True)
        assert _exists("nope"), "subkey non-numerik seharusnya tidak disentuh"
    finally:
        teardown()


def test_backup_handles_binary():
    """Nilai REG_BINARY harus bisa di-backup (dulu error: bytes not JSON serializable)."""
    setup()
    import json
    bpath = HERE / "_backup_test.json"
    if bpath.exists():
        bpath.unlink()
    try:
        r = bcreset.reset_trial(apply=True, backup=str(bpath))
        assert not r["errors"], r["errors"]
        data = json.loads(bpath.read_text(encoding="utf-8"))
        assert len(data) == 3, data
        binary = [d for d in data if d["type"] == winreg.REG_BINARY]
        assert binary and binary[0].get("encoding") == "base64", binary
    finally:
        if bpath.exists():
            bpath.unlink()
        teardown()


def test_missing_root_reports_cleanly():
    _del_tree(ROOT)
    r = bcreset.reset_trial(apply=False)
    assert r["checked"] == 0
    assert r["errors"], "seharusnya melaporkan key tidak ditemukan"


TESTS = [
    test_dry_run_does_not_change,
    test_apply_deletes_all_numeric_subkeys,
    test_non_numeric_subkey_untouched,
    test_backup_handles_binary,
    test_missing_root_reports_cleanly,
]


def main() -> int:
    failed = 0
    for t in TESTS:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    print("-" * 50)
    print(f"{len(TESTS) - failed}/{len(TESTS)} lulus")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
