# Access request drafts (owner to send; nothing has been sent)

Fill in the bracketed parts. Do not paste passwords, keys or tokens into this repository.

---

## 1. NYU Libraries: bulk access to ProQuest Congressional executive orders

**To:** NYU Libraries, your subject librarian for government information / law, or NYU Data Services
(they can route a ProQuest text-and-data-mining request to e-resources licensing).

**Subject:** Text-and-data-mining request: ProQuest Congressional, Numbered Executive Orders before 1937

Hello,

I am [name, NYU role and department]. I run a non-commercial research project that is tracing the legal
status of every U.S. executive order, i.e. whether each one is still in effect. For about 3,560 orders issued
between 1862 and 1936 (mostly EO 1-5075, Lincoln to Coolidge), I have found no public full-text copy.
ProQuest Congressional's Presidential Materials collection ("Numbered Executive Orders, 1862-Present")
holds a scanned PDF of each one.

To stay within NYU's license, I have not downloaded them in bulk. I would like to ask:

1. Does NYU's ProQuest Congressional license allow text and data mining or bulk download for
   non-commercial research? If so, under what conditions (rate, volume, retention)?
2. Could NYU request the files from ProQuest as a dataset? That could be through ProQuest TDM Studio or as a
   one-time delivery of the PDFs and metadata (accession number, title, date, signed status, item number) for
   the orders on my list. I can send the list of executive order numbers (3,563 ids).
3. If neither is possible, what download rate would the library consider normal individual research use?

The orders themselves are U.S. government works. I would keep the PDFs in a private repository for my own
research and would not redistribute ProQuest's files.

Thank you,
[name]
[NYU email]

---

## 2. National Archives: Catalog API key (RG 11 Executive Orders, NAID 299999)

**To:** the NARA Catalog API team. Check the current address on the Catalog API help page
(catalog.archives.gov) before sending.

**Subject:** API key request: research on U.S. executive orders (RG 11)

Hello,

I am [name], researching the legal status of every U.S. executive order. I would like an API key to look
up item-level digitized records in the Executive Orders series of Record Group 11 (NAID 299999) for about
3,560 orders from 1862 to 1936. I expect fewer than 10,000 queries in total, made at a slow rate, and I will
follow the API's terms on bulk downloading.

Thank you,
[name]

If a key is granted, store it as a GitHub Actions secret, never in the repository. A bounded `jobs/` job
can then read it from the environment.

---

## 3. NYU Data Services: TDM Studio workbench for the pre-1937 executive orders

**To:** NYU Data Services, data.services@nyu.edu (contact named on guides.nyu.edu/TDMStudio). Create the account
first at tdmstudio.proquest.com/createaccount with your NYU email.

**Subject:** TDM Studio: ProQuest Congressional executive orders (1862-1936) for a research workbench

Hello,

I am [name, NYU role and department]. I have requested a TDM Studio account with my NYU email for a
non-commercial research project tracing the legal status of every U.S. executive order.

I need ProQuest Congressional's Presidential Materials, specifically "Numbered Executive Orders,
1862-Present", for orders issued up to 1936. About 3,560 of them (mostly EO 1-5075) have no public full-text
copy I can find. I would like to ask:

1. Can this collection be added as a TDM Studio dataset source under NYU's ProQuest Congressional
   subscription? If it is not available yet, could you ask ProQuest whether it can be?
2. Within the export limits, may I export a metadata table for these records: accession number, order number,
   date, title, signed / not signed, page count and descriptors?
3. The orders are U.S. government works in the public domain. Would ProQuest allow export of the OCR text for
   this collection (not the page images), or deliver the PDFs once for the ~3,560 orders on my list? I can send
   the list of order numbers.

I will work inside the workbench and follow its export limits and terms, and I will not redistribute
ProQuest's files.

Thank you,
[name]
[NYU email]
