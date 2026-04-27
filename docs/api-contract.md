# API Contract MVP

Base URL: `/api/v1`

## POST /analyses
Body:
```json
{
  "topic": "topik analisis bebas",
  "location": "lokasi opsional",
  "category": "kategori opsional"
}
```

## GET /analyses
Mengembalikan daftar project analisis.

## GET /analyses/{id}
Mengembalikan detail analisis + jumlah source/item.

## POST /analyses/{id}/run
Menjalankan pipeline crawler -> scraper -> cleaner -> AI.

## GET /analyses/{id}/sources
Daftar sumber URL hasil discovery.

## GET /analyses/{id}/items
Daftar item hasil scraping yang sudah dibersihkan.

## GET /analyses/{id}/insights
Hasil insight AI dalam bentuk JSON terstruktur.

## POST /jobs/run-scheduler
Menjalankan scheduler untuk memproses analisis berstatus `pending` (opsional `failed`) dalam batch.
