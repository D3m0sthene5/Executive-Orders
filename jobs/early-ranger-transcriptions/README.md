# LOC transcription reuse

Reads the existing original-items metadata and downloads only its explicit HTTPS
`tile.loc.gov/storage-services/*.xml` fulltext links. Updated source metadata now
schedules this job after its producer. No catalog expansion or OCR is performed.

The previous exact-nine assertion failed when metadata grew to eleven links.
The plan now deduplicates item/URL pairs and allows zero through fifty links,
failing before acquisition above that bound (each response remains capped at 3 MB).
Zero links produces an explicit zero-result inventory, not an absence finding.
Multiple XML resources for one item get distinct URL-derived filenames.

Run `python -m unittest discover -s jobs/early-ranger-transcriptions` offline.
Transcriptions remain unreviewed derivatives; no census or legal status is inferred.
