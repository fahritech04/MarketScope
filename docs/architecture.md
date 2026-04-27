# Architecture Ringkas (MVP)

## Alur
1. User membuat analisis melalui frontend.
2. Backend menyimpan data ke tabel `analyses`.
3. Endpoint `POST /analyses/{id}/run` menjalankan pipeline background:
   - keyword builder
   - source discovery + AI query planner + profile rules dari DB (`discovery_profiles`) + penalti konflik lokasi
   - Scrapy batch crawl (first pass)
   - Playwright + BeautifulSoup fallback (untuk URL gagal/dinamis)
   - cleaning
   - AI analyzer
4. Hasil tersimpan ke `sources`, `scraped_items`, `insights`.
5. Frontend polling endpoint detail sampai status `completed`/`failed`.
6. Scheduler opsional dijalankan dari endpoint `/api/v1/jobs/run-scheduler` atau GitHub Actions cron.

## Komponen
- Next.js web dashboard (Bahasa Indonesia)
- FastAPI API layer + orchestrator
- Worker crawling/scraping/cleaning/analyzer modular
- Domain adapter (topic-aware relevance scoring) berbasis data DB
- Scheduler trigger endpoint + GitHub Actions cron
- Supabase PostgreSQL sebagai persistence utama
- Test suite backend (`pytest`) untuk unit + E2E mock pipeline
