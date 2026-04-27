# MarketScope AI

MarketScope AI adalah dashboard intelijen pasar multi-topik berbasis web scraping + AI untuk membantu analisis peluang bisnis, kompetitor, harga, dan insight strategi.

## 1. Tech Stack
- Frontend: Next.js (App Router) + Tailwind CSS + Recharts
- Backend: FastAPI (Python)
- Scraping/Crawling:
  - Scrapy sebagai crawler batch utama
  - Playwright + BeautifulSoup sebagai fallback scraper dinamis
  - discovery URL via search engine publik (Bing / DuckDuckGo)
- self-adaptive rule engine via tabel `discovery_profiles` (database-driven)
- AI query planner (Gemini) untuk membuat query dinamis lintas topik
  - Tidak ada seed profile statis bawaan; rule dibentuk dinamis dari input + AI planner
- Data processing: Pandas
- Database: Supabase PostgreSQL
- AI: Google Gemini API (free tier)

## 2. Struktur Folder
```txt
MarketScope_AI/
  apps/
    api/
      app/
        api/v1/analyses.py
        api/v1/jobs.py
        core/
        repositories/
        schemas/
        services/pipeline_service.py
        workers/
          keyword_builder.py
          domain_adapter.py
          source_discovery.py
          query_planner.py
          scraper.py
          cleaner.py
          ai_analyzer.py
          prompts/insight_prompt.txt
          prompts/query_planner_prompt.txt
        utils/manual_scrape.py
      tests/
        workers/test_domain_adapter.py
        workers/test_source_discovery.py
        services/test_pipeline_e2e.py
      requirements.txt
      scrapy_project/
        scrapy.cfg
        marketscope_scrapy/
          settings.py
          items.py
          pipelines.py
          spiders/marketscope_batch_spider.py
    web/
      src/app/
        page.tsx
        analisis/page.tsx
        analisis/baru/page.tsx
        analisis/[id]/page.tsx
      src/components/
      src/lib/
      package.json
  database/
    schema.sql
  docs/
    architecture.md
    api-contract.md
    scraping-policy.md
  .env.example
  .gitignore
  README.md
```

## 3. Setup Environment
1. Copy `.env.example` menjadi `.env` di root project.
2. Isi variabel:
   - `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
   - `SUPABASE_URL=...`
   - `SUPABASE_SERVICE_ROLE_KEY=...`
   - `SUPABASE_DB_URL=postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres?sslmode=require`
   - `GEMINI_API_KEY=...`
   - `OBEY_ROBOTS_TXT=true`
   - `ALLOW_INSECURE_SSL=false`
   - `SCHEDULER_AUTH_TOKEN=`
   - `MAX_SOURCES_PER_ANALYSIS=1000`
   - `MAX_ITEMS_PER_ANALYSIS=1000`
   - `SCRAPY_CONCURRENT_REQUESTS=24`
   - `SCRAPY_BATCH_CHUNK_SIZE=200`
   - `FALLBACK_MAX_WORKERS=10`
   - `FALLBACK_ENABLE_PLAYWRIGHT=false`
   - `DISCOVERY_MAX_QUERIES=120`
   - `DISCOVERY_MAX_REQUESTS=1200`
   - `DISCOVERY_PAGES_PER_QUERY=8`
   - `DISCOVERY_DOMAIN_CAP=0`
   - `DISCOVERY_MIN_SCORE=8`
   - `DISCOVERY_ALLOW_ALL_DOMAINS=true`

Catatan:
- Backend membaca `.env` dari root saat dijalankan dari root project.
- Frontend membaca `NEXT_PUBLIC_API_URL` dari environment saat `npm run dev`.
- Jika `SUPABASE_URL` dan `SUPABASE_SERVICE_ROLE_KEY` belum diisi, backend otomatis fallback ke penyimpanan lokal file `apps/api/local_store.json` agar MVP tetap bisa dites lokal.
- Default policy aman untuk production adalah `OBEY_ROBOTS_TXT=true` dan `ALLOW_INSECURE_SSL=false`.
- Jika jaringan lokal punya SSL interception/proxy dan request sering gagal handshake, set sementara `ALLOW_INSECURE_SSL=true` khusus environment dev.

## 4. Setup Supabase (PostgreSQL)
1. Buat project baru di Supabase.
2. Buka SQL Editor Supabase.
3. Jalankan file [`database/schema.sql`](database/schema.sql).
4. Ambil nilai:
   - Project URL -> `SUPABASE_URL`
   - Service Role Key -> `SUPABASE_SERVICE_ROLE_KEY`

## 5. Setup Backend FastAPI
Dari root project:

```bash
cd apps/api
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload --port 8000
```

Catatan: gunakan Python 3.12 agar dependency `pandas==2.2.3` terpasang stabil.

Backend endpoint base: `http://localhost:8000/api/v1`

## 6. Setup Frontend Next.js
Dari root project:

```bash
cd apps/web
npm install
npm run dev
```

Frontend berjalan di `http://localhost:3000`.

## 6A. One-Click Local Run (Windows PowerShell)
Dari root project:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-local.ps1
```

Script ini akan:
- menyiapkan dependency backend/frontend,
- apply `database/schema.sql` ke Supabase (jika `SUPABASE_DB_URL` tersedia),
- menjalankan backend (`127.0.0.1:8000`) dan frontend (`127.0.0.1:3000`) di background.

Untuk stop service:

```powershell
powershell -ExecutionPolicy Bypass -File .\stop-local.ps1
```

## 7. Cara Menjalankan Scraper
### Opsi A (via API run pipeline)
1. Buat analisis baru `POST /api/v1/analyses`
2. Jalankan pipeline `POST /api/v1/analyses/{id}/run`
3. Cek hasil:
   - `GET /api/v1/analyses/{id}/sources`
   - `GET /api/v1/analyses/{id}/items`
   - `GET /api/v1/analyses/{id}/insights`

### Opsi B (manual script tanpa simpan DB)
```bash
cd apps/api
python -m app.utils.manual_scrape --topic "topik analisis bebas"
```

## 8. Cara Menjalankan Analisis End-to-End
1. Buka frontend `http://localhost:3000`
2. Klik `Mulai Analisis`
3. Isi topik (lokasi dan kategori opsional)
4. Submit -> sistem membuat project + menjalankan pipeline
5. Buka halaman detail analisis untuk melihat:
   - jumlah sumber
   - jumlah data terambil
   - insight AI
   - rekomendasi strategi
   - tabel sumber
   - tabel hasil scraping
   - chart distribusi rating/harga

## 9. API Endpoint MVP
- `POST /analyses` - membuat project analisis baru
- `GET /analyses` - mengambil semua project
- `GET /analyses/{id}` - detail project
- `POST /analyses/{id}/run` - jalankan crawling/scraping/cleaning/analyzing
- `GET /analyses/{id}/sources` - daftar sumber
- `GET /analyses/{id}/items` - hasil scraping
- `GET /analyses/{id}/insights` - insight AI
- `POST /jobs/run-scheduler` - trigger scheduler (pending job queue)

## 10. Scheduler (GitHub Actions Cron)
- Workflow: `.github/workflows/marketscope-scheduler.yml`
- Secrets yang perlu diset di repository GitHub:
  - `MARKETSCOPE_SCHEDULER_URL` contoh: `https://your-api-domain/api/v1/jobs/run-scheduler`
  - `MARKETSCOPE_SCHEDULER_TOKEN` opsional, cocokkan dengan `SCHEDULER_AUTH_TOKEN` di backend
- Cron default: setiap 30 menit.

## 11. Catatan Etika Scraping
- Tidak bypass CAPTCHA/login/paywall.
- Hanya scraping halaman publik.
- Menggunakan jeda request + user-agent transparan.
- Cek `robots.txt` sebelum scraping halaman sumber.
- Batasi jumlah sumber per analisis untuk mengurangi beban server target.

## 12. Menjalankan Test Otomatis
```bash
cd apps/api
.venv\Scripts\activate
pytest
```

Test yang tersedia:
- Unit test domain-adapter berbasis profile dinamis.
- Unit test relevansi source discovery.
- Unit test fallback query planner.
- E2E pipeline mock (tanpa ketergantungan jaringan eksternal) untuk validasi status `completed`.

## 14. High-Volume Crawl (1000+)
- Sistem sekarang dituning untuk target `1000` source dan `1000` item per analisis.
- Discovery diperluas lewat pagination query dan limit request yang lebih besar.
- Tetap berlaku batas eksternal: robots.txt, timeout jaringan, anti-bot website publik, dan kualitas index search engine.

## 13. Catatan MVP
- Fokus lokal dan sederhana, belum ada auth/login.
- Discovery memakai search engine publik (Bing / DuckDuckGo) tanpa API berbayar.
- Insight AI fallback ke default bila API key tidak tersedia atau respons tidak valid.
