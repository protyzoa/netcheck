# NetCheck — Ringkasan Proyek

## Latar Belakang

Pengguna kesulitan memandu klien-klien non-teknis untuk troubleshooting jaringan via video call. Solusinya: membuat aplikasi desktop mandiri yang bisa dijalankan dengan satu klik tanpa perlu mengerti command prompt.

---

## Hasil Akhir

Aplikasi **NetCheck** — desktop app diagnostik jaringan berbasis Python + PyQt6.

**Lokasi proyek:** `D:\Projects\NetworkChecker\`

---

## Fitur yang Dibangun

### 🔍 6 Lapisan Diagnostik (berjalan otomatis berurutan)
| Layer | Checker | Yang Diperiksa |
|-------|---------|----------------|
| 1 | Koneksi Fisik | Adapter aktif, kabel, WiFi & kekuatan sinyal |
| 2 | Konfigurasi IP | IP address, subnet, DHCP, APIPA (169.254.x.x) |
| 3 | Router/Gateway | Ping ke default gateway, packet loss |
| 4 | Koneksi Internet | Ping ke 8.8.8.8 & 1.1.1.1, traceroute jika gagal |
| 5 | DNS | Resolusi via DNS lokal & publik (8.8.8.8) |
| 6 | Custom Target | Target tambahan buatan user (Ping/DNS/HTTP/Port) |

### 🎯 Custom Target Manager
- Tambah, edit, hapus target sendiri
- Tipe: Ping, DNS, HTTP, Port check
- Disimpan permanen di `%APPDATA%\NetCheck\targets.json`

### 🌐 Multi-bahasa
- Bahasa Indonesia (default) & English
- Switch real-time dari toolbar tanpa restart

### 📋 Laporan Diagnostik
- Generate laporan teks lengkap
- Copy ke clipboard satu klik
- Berisi: IP, gateway, latency, DNS server, dan rekomendasi

### 💡 Auto-Diagnosis
- Analisis root cause otomatis berdasarkan layer mana yang gagal
- Rekomendasi langkah perbaikan yang mudah dipahami

---

## Arsitektur

```
D:\Projects\NetworkChecker\
├── main.py                          # Entry point
├── requirements.txt                 # Dependencies
├── NetCheck.spec                    # PyInstaller build config
└── netcheck/
    ├── core/
    │   ├── models.py                # CheckResult, CheckStatus, DiagnosisResult
    │   ├── base_checker.py          # Abstract BaseChecker
    │   ├── engine.py                # CheckerEngine (QThread orchestrator)
    │   └── platform_utils.py        # OS wrappers (ping, traceroute, DNS, dll)
    ├── checkers/
    │   ├── adapter.py               # Layer 1: Fisik
    │   ├── ip_config.py             # Layer 2: IP Config
    │   ├── gateway.py               # Layer 3: Gateway
    │   ├── internet.py              # Layer 4: Internet
    │   ├── dns.py                   # Layer 5: DNS
    │   └── custom_target.py         # Layer 6: Custom
    ├── ui/
    │   ├── main_window.py           # Jendela utama
    │   ├── check_button.py          # Tombol PERIKSA besar
    │   ├── result_card.py           # Kartu hasil yang bisa expand
    │   ├── recommendation.py        # Panel diagnosis & rekomendasi
    │   ├── toolbar.py               # Toolbar (bahasa, about)
    │   ├── target_manager.py        # Dialog kelola target
    │   └── styles.py                # Warna & stylesheet
    ├── i18n/
    │   ├── translator.py            # Sistem terjemahan
    │   ├── id.json                  # 160+ string Bahasa Indonesia
    │   └── en.json                  # 160+ string English
    ├── config/
    │   ├── settings.py              # Pengaturan app (bahasa, dll)
    │   └── targets.py               # Manajemen custom target
    └── reporting/
        ├── generator.py             # Generator laporan teks
        └── templates.py             # Template format laporan
```

**Dependency chain checker:**
```
adapter → ip_config → gateway → internet → dns
custom_target (independent, no deps)
```
Jika satu layer gagal (FAIL), layer berikutnya otomatis di-SKIP.
Jika WARNING, layer berikutnya tetap dijalankan.

---

## Tech Stack

| Komponen | Library |
|----------|---------|
| GUI Framework | PyQt6 6.11 |
| DNS Resolution | dnspython 2.8 |
| Network Info | psutil |
| Ping/Traceroute | subprocess (native OS commands) |
| HTTP Check | urllib.request (stdlib) |
| Build EXE | PyInstaller |

---

## Bug yang Ditemukan & Diperbaiki

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| App hang "Memeriksa... (0/0)" | `_on_check_clicked` recreate engine baru, signal connections tetap ke engine lama | Pisah `_setup_engine()` (sekali) dan `_refresh_checkers()` (per klik) |
| Semua checker import error | Path `netcheck.platform.platform_utils` tidak ada | Fix ke `netcheck.core.platform_utils` |
| Engine skip downstream saat WARNING | Dependency check hanya allow PASS | Allow PASS **dan** WARNING untuk proceed |
| `{name} — OK` tampil literal | `summary_params` tidak diisi di custom_target | Add `summary_params={"name": target.name, ...}` |
| `check.custom.title.Google-DNS` tampil literal | `title_key` diisi f-string `f"check.custom.title.{name}"` | Pakai `"check.custom.title"` + params |
| App crash saat buka "Kelola Target" | `QSpinBox.setPlaceholderText()` tidak ada | Hapus baris tersebut |
| `"\\n".join(...)` tampil backslash-n | Double-escaped newline dari subagent | Fix ke `"\n".join(...)` |
| Report generator crash | Referensi `result.summary`, `result.details` sebagai dict | Rewrite: pakai `translator.t(result.summary_key, **params)` |
| 27 i18n key hilang | Checker pakai prefix berbeda dari JSON | Tambahkan semua key yang hilang |
| Custom target hanya tampil 1 kartu | `_on_check_completed` selalu pakai `results[0]` | Loop semua results, buat card per result |

---

## Cara Menjalankan

### Mode Development
```powershell
cd D:\Projects\NetworkChecker
python main.py
```

### Build EXE Portable
```powershell
cd D:\Projects\NetworkChecker
pyinstaller NetCheck.spec --clean
# Output: dist\NetCheck.exe
```

---

## Distribusi

- **`dist\NetCheck.exe`** — single file portable, tidak perlu install Python
- Ukuran estimasi: ~50-80 MB (termasuk PyQt6 runtime)
- Compatible: Windows 10/11 x64

---

*Dibuat: 16 September 2026 | Teknologi: Python 3.13 + PyQt6*
