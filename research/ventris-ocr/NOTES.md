# Ventris (OCR pilot) notes for the coordinator

Open questions for the owner (coordinator: please record in Kean):

1. **The agreement rule leaves 1 reference passage out of 43.** GPO's layer and Surya read identically on P020 only (strict;
   2 with lenient folding). Almost every non-owner passage differs by a few characters (apostrophes, "credit., Each", joined or
   split hyphens, comma read as full stop), CER 0.3% to 3% on clean prose. Options, none applied: (a) keep the rule and
   enlarge the owner set (the worksheet generator takes any id list in `OWNER_SET.json`); (b) agree at a CER threshold
   (information only in `SCORES.json`: 8, 18, 25, 34 passages at 0.5%, 1%, 2%, 5%); (c) agree = GPO, Surya and Claude all match
   after lenient folding. Option (b) or (c) needs an owner ruling because it changes what "exactly" meant.
2. Section 2 of the worksheet (spot-check) therefore has 1 passage, not 10.
3. The owner's 15 take roughly an hour only if the fractions buttons are used; the fraction-heavy passages have 10-16 lines of
   dense descriptions each.
4. PaddleOCR-VL and any hosted VLM (Gemini, olmOCR, Chandra) were not run; ask if the coordinator wants them before the
   adoption decision.

Findings (leads, not settled facts): GPO's layer contained 0 of the 335 fraction glyphs Claude read on the 15 passages that contain fractions;
Surya read 134, PaddleOCR 22, Tesseract 0. No accuracy claim until the owner's references exist.

Tokens and time (estimates, not measured): about 2.5 hours wall clock for the whole stream, of which the Claude transcription was
roughly 40 minutes and the Surya/PaddleOCR/Tesseract runs under 15 minutes of compute.
