# clause_inventory — H6-w09 (EO:830, 5917, 2655, 276, 351)

All five: done. Sources opened: views/EO_N.json, held text files, PACKET.json (only to read the ORIGINAL span bounds, 0..full text, for override limits), wikisource SOURCES/FRAGMENTS rows and originals/EO_N.html (sha256 matched the catalogued sha for 830, 2655, 276).

- EO:830 (Wikisource rev 1908907): identity confirmed (title, date 24 Jun 1908, subject, text). Packet clause span 34-109 was page chrome; one corrected clause 599-763 (grant: Basil Miles may be appointed without examination). working_text identity/complete/pages set true (pages = SOURCES row sha, revision and text hash agree; no page images exist for a web transcription). original_confirmed false (transcription).
- EO:2655 (rev 1784551): same; one clause 602-803 (appointment grant, salary cap $900). Recitals in paragraphs 2-3 are not commands.
- EO:276 (rev 1838811): same; one clause 605-739 (permanent appointment of Clare A. Cooper as matron).
- EO:5917 (OFR Hoover PEO vol. II p.1303, OCR layer): number [No. 5917], date and subject agree with register/WPA. One exemption clause; packet span 933-1483 kept, no override. original_confirmed true; original_pages_confirmed left false (source does not require a page check; the PDF is a Git LFS pointer, so page images are not held).
- EO:351 (ICC 1911 volume, printed p.52, OCR): no printed number; identity rests on crosswalk + date 8 Sep 1905 + subject + WPA "1905 CSR 101". original_confirmed true, pages left false (not required; PDF is an LFS pointer). Inventory split into 3 clauses (1080-1231 exemption from Rule XII cl.2 procedure; 1232-1374 recording duty; 1375-1477 furnishing duty). Packet lead "target provision not located: EO:8393" is a false lead: 8393 cites Hawaii Governor's EO 351 of 1929.

Tool defects: dossier segmentation for Wikisource texts takes page chrome as the clause (all three). Source PDFs in releases/source_books are LFS pointers. Offsets computed from the held text files as unicode chars; I did not run assemble.
