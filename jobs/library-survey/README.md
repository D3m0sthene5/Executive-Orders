# Pilot: OCRmyPDF, pdfplumber and eyecite on actual EO research PDFs

The job reads actual preserved Stage 18 and Stage 21 official-source PDFs. It compares pypdf text against pdfplumber's layout-aware extraction, uses eyecite to locate reporter-citation leads, and runs OCRmyPDF only for a bounded number of image-only pages. Each OCR derivative retains its source SHA-256 and page number; original PDF bytes are never altered.

Run GitHub Actions > Run jobs > library-survey. Defaults: 20 PDFs, two pages per PDF, maximum four OCR pages. Override with LIBRARY_PDF_LIMIT, LIBRARY_MAX_PAGES, LIBRARY_OCR_MAX_PAGES. Outputs PAGE_COMPARE.csv, CITATION_LEADS.csv, OCR_DERIVATIVES.csv, SOURCE_CUSTODY.jsonl, SUMMARY.json, REPORT.md and retained derived text.

Adopt improvements into fr-originals/source-ladder only after checking measured recoverability and page-image correctness on varied scans. Citation matches are leads, not evidence that an EO is still operative. No census or legal status is changed.
