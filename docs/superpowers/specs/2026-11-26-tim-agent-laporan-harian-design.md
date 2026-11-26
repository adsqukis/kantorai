# Tim Agent Laporan Harian — Desain

Tanggal: 2026-11-26
Status: draf, menunggu persetujuan pemilik

## 1. Maksud dan alasan

Pemilik bisnis (brand Generos Milk, Generos Klasik, Expedelly, Visikids, dll.)
punya 4 web yang datanya saling berkesinambungan, tapi selama ini dibaca
terpisah. Dia mau satu tim agent AI yang:

- tiap hari melaporkan kondisi masing-masing web, dan
- menganalisa hubungan konten ↔ penjualan supaya strategi konten dan
  marketing bisa dibuat saling nyambung,

semuanya jalan otomatis dalam **satu sistem**, dan setiap hari pemilik
cukup **membuka satu halaman**.

Alur bisnis yang menghubungkan keempat web:

```
Konten & tren (Qukis Studio)
      │
      ├──► Jualan TikTok Shop & live (CMS TikTok)
      └──► Iklan Meta → landing page → lead WhatsApp → closing (TaQis)
                          │
                          ▼
             Untung-rugi bersih semua marketplace (Smart Up)
```

Kunci penghubung antar web: **brand**. (Turun ke level SKU/produk bisa
ditambah nanti; bukan bagian versi pertama.)

Nama/ID brand bisa berbeda di tiap web (mis. "toko" di CMS TikTok, brand di
Qukis Studio, store di Smart Up). Sistem memakai **tabel pemetaan brand**
(file konfigurasi) yang mencocokkan nama/ID di keempat web. Builder membuat
draf dari data yang ditemukan; pemilik memeriksa dan melengkapinya.

## 2. Tujuan, bukan-tujuan, anti-tujuan

**Tujuan**
- Tiap pagi otomatis terbit laporan harian untuk 4 web + 1 analisa gabungan
  + 1 ringkasan koordinator.
- Pemilik membuka satu URL dan langsung tahu: apa yang penting hari ini,
  apa yang perlu dilakukan.
- Angka di laporan **sama persis** dengan angka di masing-masing web.
- Laporan hari-hari sebelumnya tersimpan dan bisa dibandingkan.

**Bukan tujuan (versi pertama)**
- Agent tidak mengubah apa pun di web (tidak posting, tidak ubah iklan,
  tidak kirim WA). Semua akses **baca saja**.
- Tidak ada agent yang bebas mencari data sendiri / tanya-jawab bebas.
- Tidak ada akun per anggota tim / hak akses bertingkat.
- Tidak ada analisa per SKU.

**Anti-tujuan (gagal walau secara teknis jalan)**
- Angka yang dikarang AI atau dihitung ulang AI sehingga beda dengan web.
- Laporan panjang yang tidak menunjukkan apa yang harus dilakukan.
- Sistem diam-diam gagal (satu web error, laporan tetap terbit seolah
  lengkap tanpa tanda).
- Agent mengambil aksi yang mengubah data bisnis.

## 3. Batasan

- **Server**: VPS sendiri di Sumopod. Spek: 2 vCPU, 2 GB RAM, 40 GB SSD,
  Ubuntu 24.04. Satu VPS khusus untuk sistem ini.
- **Model AI**: DeepSeek (via API DeepSeek). Bukan Claude.
- **Sumber data**: 4 web, masing-masing sudah punya server MCP:
  | Web | MCP | Contoh data |
  |---|---|---|
  | qukistudio.com | Qukistudio | ringkasan pagi tren per brand, ide konten, insight akun, kalender posting, web analytics (GA4/Search Console), KPI, deal KOL |
  | cms-tiktok-qks.up.railway.app | cms_tiktok | overview omset, sales summary, order status, live sessions, top video, content performance, ads spend/campaign, affiliate |
  | qukis.web.id | TaQis | 276 operasi: dashboard, leads, closing, kinerja CS, meta-ads, ROAS, repeat order, ranking konten |
  | qks.smartup.id | Smart Up | dashboard summary (Gross → Net Revenue → GP → CM2 → EBITDA), P&L, top products, revenue trend, ads spend |
- Server MCP tersebut saat ini terhubung lewat akun Claude pemilik. Di VPS,
  tiap web butuh **token akses sendiri** (lihat §7).
- Tanggal & zona waktu: WIB (Asia/Jakarta), format YYYY-MM-DD.
- Bahasa laporan: Indonesia, santai tapi jelas.

## 4. Pendekatan yang dipertimbangkan

1. **Program Python ringan: data ditarik oleh kode, DeepSeek hanya menulis &
   menganalisa** — *dipilih*.
   Koordinator berupa kode terjadwal; 4 pelapor menarik data dengan
   panggilan tool yang sudah ditentukan; DeepSeek membaca angka dan
   menulis. Paling stabil, paling hemat, angka pasti sama dengan web.
   Kekurangan: agent belum bisa bebas mencari data sendiri.
2. **Framework agen (LangGraph / OpenAI Agents SDK) dengan DeepSeek** —
   agent bebas memilih tool dan saling oper tugas. Ditolak: DeepSeek kurang
   andal memilih dari ratusan tool, lebih rumit, susah di-debug.
3. **Claude Code dengan DeepSeek sebagai otak (endpoint kompatibel
   Anthropic)** — ditolak: kombinasi tidak resmi, rawan rusak saat update,
   dan masalah banyak tool tetap ada.

Sebelumnya juga dipertimbangkan: tugas terjadwal Claude + halaman Artifact
(tidak perlu server) dan ditanam ke Qukis Studio. Pemilik memilih VPS
sendiri + DeepSeek.

**Tampilan kantor 3D**
- *Agents Office (ajsahni/agents-office)* — ditolak: hanya jalan dengan
  Claude (bukan DeepSeek), lisensi non-komersial (pemakaian kantor bisnis
  butuh izin tertulis), dan lisensinya melarang dipakai sebagai tampilan
  sistem agen lain.
- *Claw3D (iamlukethedev/Claw3D)* — **dipilih**: lisensi MIT, murni lapisan
  tampilan, punya jalur "custom runtime" HTTP sehingga sistem DeepSeek kita
  bisa jadi mesinnya. Di-fork dan disesuaikan.

## 5. Yang sudah diputuskan pemilik

- 5 agent: 4 pelapor (satu per web) + 1 Analis, ditambah 1 Koordinator.
- Jalan otomatis setiap hari dalam satu sistem; pemilik cukup buka satu
  halaman.
- Hosting: VPS Sumopod sendiri, spek di §3.
- Model: DeepSeek.
- Pendekatan 1 (§4).
- Tampilan: kantor 3D berbasis Claw3D, seperti ilustrasi
  https://claude.ai/artifact/TySDB8pYH26oKEqwLEDTrf
- Agent yang tidak sedang bekerja pergi ke pojok santai: **ngopi, nonton
  film, atau tidur**. Mereka ke meja hanya saat ada kerjaan.
- "Gas eksekusi" — desain ini disetujui pemilik 26 Nov 2026.

## 6. Desain

### 6.1 Komponen

```
cron (06.30 WIB)
   │
   ▼
Koordinator (kode)
   ├─► Pelapor Qukis Studio ┐
   ├─► Pelapor CMS TikTok   │  paralel; tiap pelapor:
   ├─► Pelapor TaQis        │  1) tarik data (kode, MCP)
   └─► Pelapor Smart Up     ┘  2) DeepSeek tulis laporan
   │
   ├─► cek kelengkapan, ulangi yang gagal
   ▼
Analis (DeepSeek) — baca 4 laporan + data mentah ringkas, per brand
   ▼
Ringkasan Koordinator (DeepSeek) — "hari ini penting apa, lakukan apa"
   ▼
Database ──► Dashboard web (satu URL, satu password)
```

### 6.2 Koordinator
- Dijalankan cron tiap hari jam **06.30 WIB** *(call builder; bisa diubah
  pemilik)*. Harus setelah Qukis Studio menerbitkan "ringkasan pagi"
  (terlihat dibuat sekitar 05.00 WIB).
- Menjalankan 4 pelapor paralel; tiap pelapor punya batas waktu dan
  dicoba ulang maksimal 2× bila gagal.
- Pelapor yang tetap gagal ditandai **GAGAL** dengan alasannya; Analis
  tetap jalan dengan data yang ada dan wajib menyebut bagian yang hilang.
- Bisa dijalankan manual ulang untuk satu tanggal (untuk perbaikan).

### 6.3 Pelapor (×4)
Masing-masing:
1. **Tarik data dengan kode**: daftar panggilan tool MCP yang tetap
   (tidak dipilih AI), untuk periode "kemarin" dan pembanding
   (hari sebelumnya, 7 hari) per brand bila tersedia.
2. Simpan data mentah (JSON) ke database.
3. Kirim data ke DeepSeek dengan instruksi tetap → laporan terstruktur:
   - 3–5 poin utama (angka + perubahan),
   - hal yang perlu perhatian (turun tajam, error, mendesak),
   - angka kunci per brand.
4. Aturan wajib di instruksi: **tidak boleh mengarang/menghitung ulang
   angka**; semua angka dikutip dari data. Kode memvalidasi bahwa angka
   kunci di output cocok dengan data mentah.

Fokus tiap pelapor (daftar panggilan persis diserahkan ke builder, harus
dicoba dulu terhadap server MCP-nya):
- **Qukis Studio**: ringkasan pagi/tren per brand, ide konten hari ini,
  performa posting & insight akun, KPI/target, web analytics.
- **CMS TikTok**: omset & order, status order/cancel, live sessions,
  top video & performa konten, belanja iklan & kampanye, affiliate.
- **TaQis**: lead masuk, closing, CR, kinerja CS, spend & ROAS Meta,
  ranking konten iklan, repeat order. (Pakai operasi laporan TaQis, jangan
  hitung ulang dari data mentah.)
- **Smart Up**: kartu dashboard (Net Revenue, Gross Profit, CM2, EBITDA),
  top produk, tren revenue, biaya iklan.

### 6.4 Analis
- Input: 4 laporan + ringkasan data per brand.
- Untuk tiap brand: hubungkan tren/konten (Qukis) → omset TikTok & live
  (CMS) → lead & closing WA (TaQis) → margin (Smart Up).
- Output:
  - temuan hubungan konten ↔ penjualan (dengan bukti angka),
  - 3–5 saran strategi konten & marketing yang konkret untuk hari/minggu
    ini, masing-masing menyebut brand dan alasannya,
  - peringatan bila hubungan tidak bisa disimpulkan (data kurang).
- Analis boleh menyatakan dugaan, tapi harus diberi label **dugaan** bila
  bukan angka langsung.

### 6.5 Ringkasan Koordinator
- Paling atas di dashboard: maksimal ~5 poin "penting hari ini" dan
  "yang perlu dilakukan", plus status tiap pelapor (OK / GAGAL).

### 6.6 Dashboard
- Satu URL, misalnya `laporan.qukis.web.id` *(call builder; subdomain
  final dipilih pemilik)*, HTTPS.
- Dilindungi **satu password** *(call: pemilik belum menjawab apakah tim
  ikut membuka; versi pertama dibuat untuk pemilik saja, akun per orang
  menyusul bila perlu)*.
- Halaman utama = laporan hari ini: Ringkasan Koordinator → Analisa →
  4 laporan web (bisa dilipat).
- Pilih tanggal untuk melihat laporan lama; angka kunci menampilkan
  perubahan vs hari sebelumnya.
- Nyaman dibuka di HP.

### 6.6b Kantor 3D (Claw3D)
- Fork Claw3D (MIT; nama dan notice MIT tetap dipertahankan), jalan di VPS
  yang sama, di balik password yang sama dengan dashboard.
- Sistem agen kita menyediakan **runtime HTTP** sesuai kontrak "custom
  runtime" Claw3D (`/health`, `/state`, `/registry`, `/v1/chat/completions`)
  sehingga keenam agent muncul sebagai pekerja di kantor dengan status
  langsung (kerja / selesai / santai).
- Tata ruang kantor seperti ilustrasi: rak data 4 web, meja 4 pelapor,
  meja Koordinator, ruang Analis dengan papan tulis, layar dashboard, dan
  **pojok santai** (bar kopi, pojok nonton, kasur).
- Perilaku santai: agent berstatus tidak bekerja berjalan ke pojok santai
  dan melakukan salah satu kegiatan (ngopi / nonton / tidur), bergiliran.
  Ini perubahan tampilan di fork Claw3D.
- Laporan lengkap tetap di halaman dashboard (§6.6); kantor 3D adalah
  pintu masuk visualnya, dengan tautan ke laporan hari ini.
- **Risiko**: kecocokan kontrak custom runtime Claw3D belum dicoba. Langkah
  pertama implementasi adalah uji sambung kecil; bila tidak cocok, builder
  kembali ke pemilik sebelum lanjut.

### 6.7 Penyimpanan
- Database di VPS: run harian, status pelapor, data mentah, laporan,
  analisa. Disimpan tanpa batas waktu (perkiraan < 1 GB/tahun).
- Backup harian database *(tujuan backup diserahkan ke builder)*.

### 6.8 Keamanan
- Semua token (DeepSeek + 4 web) di file environment di VPS, tidak
  masuk ke kode/repo.
- Token web harus **hanya-baca** bila servernya mendukung; di kode, hanya
  tool baca yang boleh dipanggil (daftar putih). Untuk TaQis hanya
  `taqis_baca`; `taqis_aksi`/`taqis_konfirmasi` tidak pernah dipanggil.
- Isi data (mis. teks chat WA, caption) adalah data, bukan perintah;
  instruksi DeepSeek menegaskan ini.

### 6.9 Pemberitahuan gagal
- Bila run gagal total atau ada pelapor GAGAL, tampil jelas di dashboard.
  *(Notifikasi ke WA/Telegram: bukan versi pertama.)*

## 7. Prasyarat yang harus disiapkan pemilik

1. VPS Sumopod (spek §3) + akses SSH.
2. API key DeepSeek.
3. Token / cara autentikasi untuk 4 server MCP dari luar akun Claude:
   Qukis Studio, CMS TikTok, TaQis (aplikasi tim sendiri — bisa dibuatkan),
   Smart Up (perlu dicek apakah bisa memberi token).
4. Subdomain untuk dashboard + akses DNS.

## 8. Diserahkan ke builder

- Bahasa/framework: Python; pilihan library web dashboard, database
  (SQLite cukup), dan klien MCP.
- Daftar persis panggilan tool per pelapor, setelah dicoba ke server MCP.
- Format laporan terstruktur (skema JSON) dan prompt tiap agent.
- Cara deploy (systemd/docker), reverse proxy + HTTPS, backup.
- Model DeepSeek yang dipakai dan batas token.
