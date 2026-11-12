# Bodley: sweep of large public collections for executive orders

Leads only. A hit is examined by a person before it counts as any witness; nothing here changes a status or count.

```json
{
  "sites": {
    "commons": {
      "calls": 535,
      "seconds": 20085,
      "leads": 19067,
      "leads_with_eo_number": 1063,
      "volumes": 10449,
      "new_volumes": 10433,
      "filtered_not_us": 7930,
      "errors": 7,
      "notes": [],
      "first_errors": [
        "gave up https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&titles=File%3AAssassination+Attempt+-+03-30-1981+%282%29+-+DPLA+-+5c6d47c444fe87e3f088b5c2e3",
        "gave up https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&titles=File%3ADraft+environmental+assessment%2C+Section+340+Glen+Morgan+wastewater+treatment",
        "gave up https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&titles=File%3AExecutive+Order+-+President%27s+Commission+on+Olympic+Sports+%28Executive+Orde",
        "gave up https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&titles=File%3AExecutive+Order+14429.pdf%7CFile%3AExecutive+Order+14430.pdf%7CFile%3AExecutiv",
        "gave up https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&titles=File%3AFinal+environmental+statement-+Beach+erosion+control+improvements%2C+Waikiki+B"
      ]
    },
    "internet_archive": {
      "calls": 15,
      "seconds": 70,
      "leads": 5798,
      "leads_with_eo_number": 1518,
      "volumes": 3628,
      "new_volumes": 3595,
      "filtered_not_us": 1743,
      "errors": 0,
      "notes": [],
      "first_errors": []
    },
    "loc": {
      "calls": 2,
      "seconds": 14818,
      "leads": 198,
      "leads_with_eo_number": 74,
      "volumes": 5,
      "new_volumes": 5,
      "filtered_not_us": 1,
      "errors": 5,
      "notes": [],
      "first_errors": [
        "gave up https://www.loc.gov/search/?q=executive+order&fo=json&c=100&sp=1&at=results%2Cpagination",
        "gave up https://www.loc.gov/search/?q=executive+orders&fo=json&c=100&sp=2&at=results%2Cpagination",
        "gave up https://www.loc.gov/search/?q=presidential+executive+orders&fo=json&c=100&sp=2&at=results%2Cpagination",
        "gave up https://www.loc.gov/search/?q=executive+order+no&fo=json&c=100&sp=1&at=results%2Cpagination",
        "gave up https://www.loc.gov/search/?q=proclamations+and+executive+orders&fo=json&c=100&sp=1&at=results%2Cpagination"
      ]
    },
    "google_books": {
      "calls": 0,
      "seconds": 16942,
      "leads": 0,
      "leads_with_eo_number": 0,
      "volumes": 0,
      "new_volumes": 0,
      "filtered_not_us": 0,
      "errors": 7,
      "notes": [],
      "first_errors": [
        "gave up https://www.googleapis.com/books/v1/volumes?q=intitle%3A%22executive+orders%22&filter=full&maxResults=40&startIndex=0&printType=books",
        "gave up https://www.googleapis.com/books/v1/volumes?q=intitle%3A%22executive+order%22&filter=full&maxResults=40&startIndex=0&printType=books",
        "gave up https://www.googleapis.com/books/v1/volumes?q=%22executive+order+no%22&filter=full&maxResults=40&startIndex=0&printType=books",
        "gave up https://www.googleapis.com/books/v1/volumes?q=intitle%3A%22proclamations+and+executive+orders%22&filter=full&maxResults=40&startIndex=0&printType=books",
        "gave up https://www.googleapis.com/books/v1/volumes?q=intitle%3A%22executive+orders+relating%22&filter=full&maxResults=40&startIndex=0&printType=books"
      ]
    },
    "hathitrust": {
      "calls": 0,
      "seconds": 0,
      "leads": 0,
      "leads_with_eo_number": 0,
      "volumes": 0,
      "new_volumes": 0,
      "filtered_not_us": 0,
      "errors": 0,
      "notes": [
        "robots.txt disallows https://catalog.hathitrust.org/Search/Home?lookfor=executive+orders&type=title&ft=ft&page=1",
        "robots.txt disallows https://catalog.hathitrust.org/Search/Home?lookfor=executive+order&type=title&ft=ft&page=1",
        "robots.txt disallows https://catalog.hathitrust.org/Search/Home?lookfor=proclamations+executive+orders&type=title&ft=ft&page=1",
        "robots.txt disallows https://catalog.hathitrust.org/Search/Home?lookfor=United+States.+President.+Executive+orders&type=all&ft=ft&page=1",
        "robots.txt disallows https://catalog.hathitrust.org/Search/Home?lookfor=presidential+executive+orders&type=all&ft=ft&page=1"
      ],
      "first_errors": []
    },
    "wikidata": {
      "calls": 14,
      "seconds": 4666,
      "leads": 19762,
      "leads_with_eo_number": 4392,
      "volumes": 0,
      "new_volumes": 0,
      "filtered_not_us": 75,
      "errors": 1,
      "notes": [
        "classes tried: ['Q105999387', 'Q114476299', 'Q116771906', 'Q1298239', 'Q1338798', 'Q2061228', 'Q2159918', 'Q28543928', 'Q64605204', 'Q77796360', 'Q814169', 'Q95998597']"
      ],
      "first_errors": [
        "gave up https://query.wikidata.org/sparql?query=SELECT+%3Fitem+%3FitemLabel+%3Ford+%3Fdate+%3Fscan+%3Fws+%3Ffull+%3Fimg+WHERE+%7B+%3Fitem+wdt%3AP31+wd%3AQ114476299+.%0A"
      ]
    }
  },
  "distinct_eo_numbers": 4588,
  "in_tracker": 4539,
  "needing_official_copy_with_a_lead": 1382,
  "needing_official_copy_with_a_new_lead": 1382,
  "needed_by_site": {
    "commons": 67,
    "internet_archive": 82,
    "loc": 2,
    "google_books": 0,
    "hathitrust": 0,
    "wikidata": 1367
  },
  "needed_by_film709_reel": {
    "": 39,
    "1": 578,
    "11": 5,
    "2": 321,
    "3": 246,
    "4": 99,
    "5": 74,
    "6": 17,
    "8": 1,
    "None": 2
  },
  "total_needing_official_copy": 2251
}
```

## Orders still needing an official copy that have a lead

| EO | reel | new | sites | kinds | example |
|---|---|---|---|---|---|
| 1 | 1 | yes | commons;internet_archive;wikidata | image;item;item with scan/text link;volume;web | https://commons.wikimedia.org/wiki/File:Montana_Executive_Order_1-2021.pdf |
| 2 | 1 | yes | commons;internet_archive;loc;wikidata | item;periodical;volume | https://commons.wikimedia.org/wiki/File:Montana_Executive_Order_2-2021.pdf |
| 3 | 1 | yes | commons;internet_archive;loc;wikidata | image;item;periodical;volume | https://commons.wikimedia.org/wiki/File:Eeo-3%3DNYC-2026-Feb-22.pdf |
| 5 | 1 | yes | commons;internet_archive;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Virginia_Executive_Order_5_(2026).pdf |
| 6 | 1 | yes | commons;internet_archive;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Virginia_Executive_Order_6_(2026).pdf |
| 8 | 1 | yes | commons;internet_archive;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Virginia_Executive_Order_8_(2026).pdf |
| 9 | 1 | yes | commons;internet_archive;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Bolinao_Executive_Orders_No._9_-_2020.pdf |
| 11 | 1 | yes | commons;internet_archive;wikidata | item;volume;web | https://commons.wikimedia.org/wiki/File:Bolinao_Executive_Order_No._11_-_2020.pdf |
| 16 | 1 | yes | commons;internet_archive;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Aringay_Executive_Order_No._16_-_2020.pdf |
| 18 | 1 | yes | commons;internet_archive;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Aringay_Executive_Order_No._18_-_2020.pdf |
| 19 | 1 | yes | commons;internet_archive;wikidata | item;volume;web | https://commons.wikimedia.org/wiki/File:Agoo_Executive_Order_No._19_-_2020.pdf |
| 20 | 1 | yes | commons;internet_archive;wikidata | item;volume;web | https://commons.wikimedia.org/wiki/File:Bacnotan_Executive_Order_No._20_-_2020.pdf |
| 21 | 1 | yes | commons;internet_archive;wikidata | item;volume;web | https://commons.wikimedia.org/wiki/File:Balaoan_Executive_Order_No._21_-_2020.pdf |
| 24 | 1 | yes | commons;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Agoo_Executive_Order_No._24_-_2020.pdf |
| 25 | 1 | yes | commons;internet_archive;wikidata | item;item with scan/text link;volume;web | https://commons.wikimedia.org/wiki/File:Balaoan_Executive_Order_No._25_-_2020.pdf |
| 27 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106477 |
| 30 | 1 | yes | commons;internet_archive;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Agno_Executive_Order_No._30_-_2021.pdf |
| 31 | 1 | yes | commons;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Agno_Executive_Order_No._31_-_2021.pdf |
| 32 | 1 | yes | commons;internet_archive;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Agno_Executive_Order_No._32_-_2021.pdf |
| 33 | 1 | yes | commons;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Bolinao_Executive_Order_No._33_-_2020.pdf |
| 34 | 1 | yes | commons;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Bolinao_Executive_Order_No._34_-_2019.pdf |
| 35 | 1 | yes | commons;wikidata | image;item | https://commons.wikimedia.org/wiki/File:Office_of_Early_Childhood_executive_order_signing_(9127580018).jpg |
| 50 | 1 | yes | internet_archive;wikidata | item;web | https://archive.org/details/perma_cc_QHD6-CFK7 |
| 54 | 1 | yes | internet_archive;wikidata | item;volume | https://archive.org/details/6981574-Williamson-County-Executive-Order-54 |
| 55 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107571 |
| 56 | 1 | yes | commons;wikidata | image;item | https://commons.wikimedia.org/wiki/File:Agno_Executive_Order_No._56_-_2021.jpg |
| 57 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107636 |
| 58 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107662 |
| 59 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107685 |
| 60 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107717 |
| 61 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107769 |
| 62 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107804 |
| 63 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107829 |
| 64 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107859 |
| 65 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107895 |
| 66 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107939 |
| 67 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107972 |
| 68 | 1 | yes | wikidata | item;item with scan/text link | http://www.wikidata.org/entity/Q19107994 |
| 69 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108015 |
| 70 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108042 |
| 71 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108067 |
| 73 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108112 |
| 74 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108143 |
| 75 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108162 |
| 76 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108179 |
| 77 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108197 |
| 78 | 1 | yes | internet_archive;wikidata | item;web | https://archive.org/details/perma_cc_PFT9-6S9Y |
| 79 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108238 |
| 80 | 1 | yes | internet_archive;wikidata | item;web | https://archive.org/details/perma_cc_3CWM-XVUR |
| 81 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108302 |
| 82 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108317 |
| 83 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108335 |
| 84 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108357 |
| 85 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108372 |
| 86 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108390 |
| 87 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108404 |
| 88 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108422 |
| 89 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108434 |
| 90 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108446 |
| 93 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108536 |
| 94 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108569 |
| 95 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108604 |
| 96 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108624 |
| 97 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108648 |
| 98 | 1 | yes | internet_archive;wikidata | item;volume | https://archive.org/details/2008EO9812Rpt |
| 101 | 1 | yes | internet_archive;wikidata | item;volume;web | https://archive.org/details/cia-readingroom-document-cia-rdp59-00882r000100290015-1 |
| 102 | 1 | yes | commons;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Eeo-102%3DNYC-2020-mar-20.pdf |
| 103 | 1 | yes | wikidata | item;item with scan/text link | http://www.wikidata.org/entity/Q19098842 |
| 104 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19098959 |
| 105 | 1 | yes | internet_archive;wikidata | item;volume | https://archive.org/details/cia-readingroom-document-cia-rdp84-00780r004300060042-5 |
| 106 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19099197 |
| 107 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19099295 |
| 108 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19099378 |
| 109 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19099485 |
| 110 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19099594 |
| 114 | 1 | yes | commons;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Eeo-114%3DNYC-2020-may-19.pdf |
| 115 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19100007 |
| 116 | 1 | yes | commons;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Eeo-116%3DNYC-2020-may-29.pdf |
| 117 | 1 | yes | commons;wikidata | item;item with scan/text link;volume | https://commons.wikimedia.org/wiki/File:Eeo-117%3DNYC-2020-june-01.pdf |
| 118 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19100214 |
| 120 | 1 | yes | commons;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Eeo-120%3DNYC-2020-june-03.pdf |
| 123 | 1 | yes | commons;internet_archive;wikidata | item;volume;web | https://commons.wikimedia.org/wiki/File:Eeo-123%3DNYC-2020-june-07.pdf |
| 124 | 1 | yes | commons;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Eeo-124%3DNYC-2020-june-12.pdf |
| 125 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19101470 |
| 126 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19101888 |
| 128 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19102707 |
| 129 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19103128 |
| 130 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19103524 |
| 130B | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19103923 |
| 130D | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19103926 |
| 131 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19103928 |
| 132 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19104294 |
| 133 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19104605 |
| 134 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19104824 |
| 135 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105028 |
| 136 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105235 |
| 137 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105415 |
| 138 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105428 |
| 139 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105444 |
| 140 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105460 |
| 141 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105474 |
| 142 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105492 |
| 143 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105506 |
| 144 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105520 |
| 145 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105532 |
| 146 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105542 |
| 147 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105564 |
| 148 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105584 |
| 149 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105606 |
| 150 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105618 |
| 151 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105628 |
| 152 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105642 |
| 153 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105656 |
| 154 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105670 |
| 155 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105690 |
| 156 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105700 |
| 157 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105712 |
| 158 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105726 |
| 159 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105741 |
| 160 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105757 |
| 161 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105773 |
| 162 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105782 |
| 163 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105793 |
| 164 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105810 |
| 165 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105815 |
| 166 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105834 |
| 167 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105850 |
| 168 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105864 |
| 169 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105885 |
| 171 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105918 |
| 172 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105930 |
| 173 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105950 |
| 174 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105970 |
| 175 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105976 |
| 176 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105986 |
| 177 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105990 |
| 178 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19105996 |
| 179 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106001 |
| 180 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106009 |
| 181 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106011 |
| 182 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106021 |
| 183 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106023 |
| 184 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106027 |
| 185 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106029 |
| 186 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106033 |
| 187 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106038 |
| 188 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106041 |
| 189 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106052 |
| 190 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106061 |
| 191 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106066 |
| 192 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106070 |
| 193 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106073 |
| 195 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106081 |
| 196 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106083 |
| 197 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106088 |
| 198 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106092 |
| 199 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106098 |
| 200 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106110 |
| 201 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106118 |
| 202 | 1 | yes | internet_archive;wikidata | item;volume;web | https://archive.org/details/6283277-Scott-Walker-Executive-Order-202-Wisconsin |
| 203 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106139 |
| 204 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106143 |
| 205 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106151 |
| 207 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106162 |
| 208 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106165 |
| 209 | 1 | yes | internet_archive;wikidata | item;web | https://archive.org/details/perma_cc_D9PN-EHF8 |
| 210 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106173 |
| 211 | 1 | yes | internet_archive;wikidata | item;volume | https://archive.org/details/executiveorder210000wrob |
| 212 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106181 |
| 214 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106188 |
| 215 | 1 | yes | internet_archive;wikidata | item;volume | https://archive.org/details/localhousingpoli00king |
| 216 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106196 |
| 218 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106200 |
| 220 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106206 |
| 221 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106212 |
| 222 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106216 |
| 223 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106218 |
| 224 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106220 |
| 225 | 1 | yes | internet_archive;wikidata | item;web | https://archive.org/details/perma_cc_565J-TUV8 |
| 226 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106224 |
| 227 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106228 |
| 228 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106230 |
| 229 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106234 |
| 230 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106238 |
| 231 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106240 |
| 232 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106244 |
| 233 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106246 |
| 234 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106248 |
| 235 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106250 |
| 236 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106251 |
| 237 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106253 |
| 238 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106255 |
| 239 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106259 |
| 241 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106265 |
| 242 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106270 |
| 243 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19115255 |
| 244 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106274 |
| 245 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106277 |
| 246 | 1 | yes | wikidata | item;item with scan/text link | http://www.wikidata.org/entity/Q19106284 |
| 247 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106286 |
| 248 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106291 |
| 250 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106299 |
| 252 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106305 |
| 253 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106311 |
| 255 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106315 |
| 256 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106322 |
| 257 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106327 |
| 258 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106336 |
| 259 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106346 |
| 260 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106356 |
| 261 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106369 |
| 262 | 1 | yes | commons;wikidata | item;volume | https://commons.wikimedia.org/wiki/File:Executive_Order_Number_262_(New_Jersey).pdf |
| 263 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106396 |
| 264 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106400 |
| 265 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106406 |
| 266 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106426 |
| 268 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106455 |
| 269 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106463 |
| 270 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106479 |
| 271 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106481 |
| 272 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106487 |
| 273 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106491 |
| 274 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106501 |
| 275 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106519 |
| 276 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106532 |
| 277 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106552 |
| 278 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106564 |
| 279 | 1 | yes | internet_archive;wikidata | item;item with scan/text link;web | https://archive.org/details/perma_cc_5GJR-URQS |
| 280 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106577 |
| 281 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106580 |
| 282 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106586 |
| 284 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106596 |
| 285 | 1 | yes | wikidata | item;item with scan/text link | http://www.wikidata.org/entity/Q19106609 |
| 286 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106616 |
| 287 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106618 |
| 288 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106622 |
| 290 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106642 |
| 291 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106647 |
| 293 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106661 |
| 294 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106665 |
| 295 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106671 |
| 296A | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106689 |
| 297 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106691 |
| 298 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106696 |
| 299 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106700 |
| 300 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106713 |
| 301 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106715 |
| 302 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106724 |
| 303 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106730 |
| 304 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106741 |
| 305 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106742 |
| 306 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q29651559 |
| 307 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106749 |
| 308 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106755 |
| 309 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106757 |
| 312 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106769 |
| 313 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106774 |
| 315 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106782 |
| 316 | 1 | yes | internet_archive;wikidata | item;web | https://archive.org/details/perma_cc_T58Z-H5FN |
| 317 | 1 | yes | internet_archive;wikidata | item;web | https://archive.org/details/perma_cc_NV9K-GJZM |
| 318 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106798 |
| 319 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106802 |
| 320 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106806 |
| 320A | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106814 |
| 321 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106816 |
| 321B | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106824 |
| 322 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106826 |
| 323 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106832 |
| 323A | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106838 |
| 324 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106840 |
| 324C | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106850 |
| 324D | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106852 |
| 324E | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106854 |
| 325 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106856 |
| 326 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106864 |
| 327 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106868 |
| 328 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106872 |
| 328B | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106876 |
| 328C | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106878 |
| 329 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106880 |
| 330A | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106891 |
| 330B | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106893 |
| 331 | 1 | yes | internet_archive;wikidata | item;web | https://archive.org/details/perma_cc_F87R-NJ7H |
| 332 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106903 |
| 333 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106907 |
| 334 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106911 |
| 335 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106917 |
| 336 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106923 |
| 337 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106929 |
| 337A | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106931 |
| 337B | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106932 |
| 337C | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106936 |
| 338 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106937 |
| 340 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106947 |
| 341 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106949 |
| 341A | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106951 |
| 341C | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106955 |
| 342 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106958 |
| 343 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106961 |
| 344 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106968 |
| 344A | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106971 |
| 347 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106984 |
| 348 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106987 |
| 348A | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106990 |
| 350 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19106996 |
| 351B | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107001 |
| 352 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107004 |
| 352A | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107007 |
| 352B | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107010 |
| 353 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107011 |
| 354 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107014 |
| 355 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107022 |
| 356 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107023 |
| 357 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107027 |
| 357A | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107034 |
| 357B | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107036 |
| 357C | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107037 |
| 358 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107041 |
| 359 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107046 |
| 360 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107051 |
| 361 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107054 |
| 362 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107058 |
| 363 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107059 |
| 364 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107061 |
| 365 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107064 |
| 366 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107068 |
| 366B | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107069 |
| 367 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107071 |
| 368 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107073 |
| 369 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107075 |
| 369A | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107077 |
| 369B | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107079 |
| 371 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107085 |
| 372 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107087 |
| 373 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107089 |
| 374 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107093 |
| 375 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107099 |
| 375B | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107101 |
| 376 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107103 |
| 377 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107107 |
| 377A | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107114 |
| 378 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107117 |
| 379 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107119 |
| 380 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107123 |
| 381 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107127 |
| 382 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107128 |
| 383 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107130 |
| 385 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107135 |
| 386 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107136 |
| 387 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107138 |
| 388 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107141 |
| 389 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107143 |
| 390 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107150 |
| 392 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107154 |
| 394A | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107162 |
| 395 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107163 |
| 395A | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107166 |
| 396 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107168 |
| 397 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107169 |
| 398 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107173 |
| 399 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107180 |
| 402 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107189 |
| 403 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107191 |
| 404 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107193 |
| 405 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107197 |
| 405A | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107199 |
| 405B | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107201 |
| 406 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107204 |
| 408 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107207 |
| 409 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107209 |
| 410 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107213 |
| 411 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107215 |
| 415 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107222 |
| 416 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107223 |
| 417 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107226 |
| 419 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107233 |
| 420 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107236 |
| 421 | 1 | yes | internet_archive;wikidata | item;volume | https://archive.org/details/executiveorder4200mass |
| 422 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107240 |
| 423 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107242 |
| 424 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107243 |
| 425 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107246 |
| 426 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107247 |
| 427 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107249 |
| 428 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107251 |
| 432 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107257 |
| 434 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107259 |
| 435 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107261 |
| 436 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107267 |
| 437 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107269 |
| 438 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107271 |
| 439 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q29651577 |
| 440 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107275 |
| 441 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107277 |
| 444 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107281 |
| 448 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107283 |
| 449 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107285 |
| 450 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107289 |
| 451 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107291 |
| 453 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107299 |
| 456 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107303 |
| 458 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107305 |
| 460 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107309 |
| 461 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107312 |
| 462 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q29651575 |
| 464 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107315 |
| 466 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107317 |
| 467 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107320 |
| 468 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107322 |
| 469 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107324 |
| 470 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107328 |
| 471 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107329 |
| 472 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107333 |
| 473 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107337 |
| 475 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107341 |
| 476 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107343 |
| 477 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107345 |
| 478 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107349 |
| 479 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107351 |
| 480 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107355 |
| 482 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107359 |
| 483 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107361 |
| 484 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107363 |
| 485 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107365 |
| 486 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107367 |
| 488 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107369 |
| 489 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107371 |
| 491 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107375 |
| 492 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107377 |
| 496 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107381 |
| 497 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107383 |
| 498 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107385 |
| 499 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107389 |
| 501 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107396 |
| 502 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107398 |
| 504 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107404 |
| 505 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107406 |
| 507 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107410 |
| 508 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107416 |
| 511 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q29651560 |
| 512 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107429 |
| 513 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107433 |
| 515 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107437 |
| 516 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107447 |
| 517 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107449 |
| 518 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107453 |
| 520 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107463 |
| 521 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107469 |
| 523 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107480 |
| 524 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107482 |
| 526 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107492 |
| 528 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107500 |
| 530 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107506 |
| 531 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107508 |
| 532 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107518 |
| 533 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107524 |
| 534 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107526 |
| 535 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107528 |
| 536 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107531 |
| 538 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107539 |
| 539 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107541 |
| 540 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107547 |
| 541 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107550 |
| 542 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107552 |
| 543 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107554 |
| 544 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107556 |
| 545 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107557 |
| 546 | 1 | yes | wikidata | item;item with scan/text link | http://www.wikidata.org/entity/Q19107559 |
| 547 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107562 |
| 548 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107565 |
| 549 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107567 |
| 551 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107573 |
| 553 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107579 |
| 555 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107583 |
| 557 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107587 |
| 558 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107589 |
| 559 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107591 |
| 560 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107597 |
| 562 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107609 |
| 563 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107613 |
| 564 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107615 |
| 565 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107621 |
| 566 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107626 |
| 567 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107629 |
| 568 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107632 |
| 572 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107642 |
| 573 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107643 |
| 574 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107646 |
| 577 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107651 |
| 578 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107660 |
| 580 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107663 |
| 581 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107665 |
| 582 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107667 |
| 583 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107672 |
| 585 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107674 |
| 590 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107687 |
| 591 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107689 |
| 594 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107697 |
| 596 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107701 |
| 597 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107703 |
| 598 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107705 |
| 599 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107713 |
| 601 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107727 |
| 602 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107729 |
| 603 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107737 |
| 604 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107738 |
| 608 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107758 |
| 609 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107764 |
| 610 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107771 |
| 611 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107776 |
| 612 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107781 |
| 614 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107783 |
| 617 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107790 |
| 618 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107797 |
| 619 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q29651561 |
| 620 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107806 |
| 621 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107808 |
| 622 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107809 |
| 623 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107811 |
| 624 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107814 |
| 627 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107825 |
| 629 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107827 |
| 630 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107831 |
| 631 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107833 |
| 632 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107835 |
| 633 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107837 |
| 634 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107841 |
| 636 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107849 |
| 637 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107853 |
| 638 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107855 |
| 639 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107857 |
| 640 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107861 |
| 642 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107867 |
| 644 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107875 |
| 645 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107879 |
| 646 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107881 |
| 648 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107889 |
| 651 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107898 |
| 652 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107907 |
| 654 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107911 |
| 655 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107918 |
| 656 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107926 |
| 657 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107930 |
| 658 | 1 | yes | internet_archive;wikidata | item;volume | https://archive.org/details/ERIC_ED382505 |
| 660 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107940 |
| 662 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107946 |
| 667 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107960 |
| 668 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107964 |
| 669 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107968 |
| 670 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107974 |
| 671 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107976 |
| 672 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107981 |
| 675 | 1 | yes | commons;wikidata | image;item | https://commons.wikimedia.org/wiki/File:Tern_Islands_Reservation_EO_675_illustration.jpg |
| 676 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107985 |
| 677 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107987 |
| 679 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107992 |
| 680 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107995 |
| 681 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19107999 |
| 682 | 1 | yes | commons;wikidata | image;item | https://commons.wikimedia.org/wiki/File:Shell_Keys_Reservation_EO_682_illustration.jpg |
| 684 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108005 |
| 685 | 1 | yes | wikidata | item;item with scan/text link | http://www.wikidata.org/entity/Q19108007 |
| 686 | 1 | yes | wikidata | item;item with scan/text link | http://www.wikidata.org/entity/Q19108009 |
| 688 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108011 |
| 689 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108013 |
| 690 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108017 |
| 691 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108019 |
| 693 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108022 |
| 694 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108027 |
| 695 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108030 |
| 696 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108032 |
| 697 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108033 |
| 698 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108035 |
| 699 | 1 | yes | commons;wikidata | image;item | https://commons.wikimedia.org/wiki/File:Three_Arch_Rocks_Reservation_EO_699_illustration.jpg |
| 700 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108044 |
| 702 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108047 |
| 704 | 1 | yes | commons;wikidata | image;item | https://commons.wikimedia.org/wiki/File:Copalis_Rock_Reservation_EO_704_illustration.jpg |
| 706 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108060 |
| 707 | 1 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108061 |
| 710 | 2 | yes | wikidata | item;item with scan/text link | http://www.wikidata.org/entity/Q19108069 |
| 712 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108072 |
| 713 | 2 | yes | internet_archive;wikidata | item;volume | https://archive.org/details/5625631-executive |
| 714 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108077 |
| 715 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108078 |
| 716 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108080 |
| 717 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108082 |
| 718 | 2 | yes | commons;wikidata | image;item | https://commons.wikimedia.org/wiki/File:East_Timbalier_Island_Reservation_EO_718_illustration.jpg |
| 719 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108087 |
| 721 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108090 |
| 722 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108093 |
| 723 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108094 |
| 727 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108103 |
| 728 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108104 |
| 733 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108129 |
| 734 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108132 |
| 737 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108137 |
| 738 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108139 |
| 740 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108145 |
| 742 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108149 |
| 747 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108159 |
| 748 | 2 | yes | wikidata | item | http://www.wikidata.org/entity/Q19108160 |

## New volumes (books and scans not yet named anywhere the project tracks sources)

- commons: [File:"Freedom", May-June, 1955.pdf](https://commons.wikimedia.org/wiki/File:%22Freedom%22,_May-June,_1955.pdf) 1 May 1955
- commons: [File:'EMERGING TRENDS IN EMPLOYMENT AND LABOR LAW- LABOR-MANAGEMENT RELATIONS IN A GLOBAL ECONOMY' (IA gov.gpo.fdsys.CHRG-107hhrg82896).pdf](https://commons.wikimedia.org/wiki/File:%27EMERGING_TRENDS_IN_EMPLOYMENT_AND_LABOR_LAW-_LABOR-MANAGEMENT_RELATIONS_IN_A_GLOBAL_ECONOMY%27_(IA_gov.gpo.fdsys.CHRG-107hhrg82896).pdf) 
- commons: [File:(Affirmative Action Studies) (3) - DPLA - be33e93038ae5c4eb1d7a28d5858d984.pdf](https://commons.wikimedia.org/wiki/File:(Affirmative_Action_Studies)_(3)_-_DPLA_-_be33e93038ae5c4eb1d7a28d5858d984.pdf) 
- commons: [File:(Affirmative Action Studies) (4) - DPLA - e4d5c9b0c0e9c18731b2af771758050e.pdf](https://commons.wikimedia.org/wiki/File:(Affirmative_Action_Studies)_(4)_-_DPLA_-_e4d5c9b0c0e9c18731b2af771758050e.pdf) 
- commons: [File:(American Indians) - DPLA - d1f8f9ad2abe4e73621549df1e955e9b.pdf](https://commons.wikimedia.org/wiki/File:(American_Indians)_-_DPLA_-_d1f8f9ad2abe4e73621549df1e955e9b.pdf) 
- commons: [File:(Cicconi Memos – July 1982-December 1982) (4) - DPLA - 69d0e83b7e523fb006baee2783167270.pdf](https://commons.wikimedia.org/wiki/File:(Cicconi_Memos_%E2%80%93_July_1982-December_1982)_(4)_-_DPLA_-_69d0e83b7e523fb006baee2783167270.pdf) 
- commons: [File:(Correspondence - Miscellaneous (02-08-1983-02-28-1983)) - DPLA - 9fec34cc9a16267d7bf967989849ddab.pdf](https://commons.wikimedia.org/wiki/File:(Correspondence_-_Miscellaneous_(02-08-1983-02-28-1983))_-_DPLA_-_9fec34cc9a16267d7bf967989849ddab.pdf) 
- commons: [File:(Government Organization) - Reorganization Plans - Executive Branch, 1968-1971 (2 of 2) - DPLA - e2c36ad7b8e930b231d8c683bbde71ab.pdf](https://commons.wikimedia.org/wiki/File:(Government_Organization)_-_Reorganization_Plans_-_Executive_Branch,_1968-1971_(2_of_2)_-_DPLA_-_e2c36ad7b8e930b231d8c683bbde71ab.pdf) 
- commons: [File:(Government Organization) - Summary Report and Recommendations- Governoräó»s Survey of Efficiency and Cost Control, February 1968 (1 of](https://commons.wikimedia.org/wiki/File:(Government_Organization)_-_Summary_Report_and_Recommendations-_Governor%C3%A4%C3%B3%C2%BBs_Survey_of_Efficiency_and_Cost_Control,_February_1968_(1_of_2)_-_DPLA_-_3bd3dcd509ab188a1ea62d8627bfe1e8.pdf) 
- commons: [File:(H.A.S.C. No. 109-128) APPLYING LESSONS LEARNED FROM HURRICANE KATRINA- HOW THE DEPARTMENT OF DEFENSE IS PREPARING FOR THE UPCOMING HUR](https://commons.wikimedia.org/wiki/File:(H.A.S.C._No._109-128)_APPLYING_LESSONS_LEARNED_FROM_HURRICANE_KATRINA-_HOW_THE_DEPARTMENT_OF_DEFENSE_IS_PREPARING_FOR_THE_UPCOMING_HURRICANE_SEASON_(IA_gov.gpo.fdsys.CHRG-109hhrg33595).pdf) 
- commons: [File:(H.A.S.C. No. 109-13) MILITARY CONSTRUCTION, FAMILY HOUSING, BASE CLOSURES AND FACILITIES OPERATIONS AND MAINTENANCE (IA gov.gpo.fdsys.](https://commons.wikimedia.org/wiki/File:(H.A.S.C._No._109-13)_MILITARY_CONSTRUCTION,_FAMILY_HOUSING,_BASE_CLOSURES_AND_FACILITIES_OPERATIONS_AND_MAINTENANCE_(IA_gov.gpo.fdsys.CHRG-109hhrg33787).pdf) 
- commons: [File:(Higher Education Desegregation Plan, 1978) (3) - DPLA - 899b35e0f1d3c57dc203c1dd3f2cd895.pdf](https://commons.wikimedia.org/wiki/File:(Higher_Education_Desegregation_Plan,_1978)_(3)_-_DPLA_-_899b35e0f1d3c57dc203c1dd3f2cd895.pdf) 
- commons: [File:(Homeless, Health and Human Services Working Group on the) - DPLA - 9d8f9d4e9495717b84c85a2b30315726.pdf](https://commons.wikimedia.org/wiki/File:(Homeless,_Health_and_Human_Services_Working_Group_on_the)_-_DPLA_-_9d8f9d4e9495717b84c85a2b30315726.pdf) 
- commons: [File:(JGR-Appointee Clearances - 02-01-1984-02-24-1984) - DPLA - 569ece688167f0f89e3889bb51dc7f27.pdf](https://commons.wikimedia.org/wiki/File:(JGR-Appointee_Clearances_-_02-01-1984-02-24-1984)_-_DPLA_-_569ece688167f0f89e3889bb51dc7f27.pdf) 
- commons: [File:(JGR-Appointee Clearances - 05-01-1985-06-30-1985) - DPLA - ac021c901ad19c1ea604fb2ddfc1cc1d.pdf](https://commons.wikimedia.org/wiki/File:(JGR-Appointee_Clearances_-_05-01-1985-06-30-1985)_-_DPLA_-_ac021c901ad19c1ea604fb2ddfc1cc1d.pdf) 
- commons: [File:(JGR-Appointee Clearances - 06-24-1983-07-08-1983) - DPLA - 044007293fa8be18cb6ca55276989824.pdf](https://commons.wikimedia.org/wiki/File:(JGR-Appointee_Clearances_-_06-24-1983-07-08-1983)_-_DPLA_-_044007293fa8be18cb6ca55276989824.pdf) 
- commons: [File:(JGR-Appointee Clearances - 08-29-1985-09-30-1985) - DPLA - a66d15eb9ade5e7eedfb5de800906c4e.pdf](https://commons.wikimedia.org/wiki/File:(JGR-Appointee_Clearances_-_08-29-1985-09-30-1985)_-_DPLA_-_a66d15eb9ade5e7eedfb5de800906c4e.pdf) 
- commons: [File:(JGR-Drug Abuse, Enforcement, Legislation & Prevention) (9 of 9) - DPLA - cf842e86d9201875247844823f78291f.pdf](https://commons.wikimedia.org/wiki/File:(JGR-Drug_Abuse,_Enforcement,_Legislation_%26_Prevention)_(9_of_9)_-_DPLA_-_cf842e86d9201875247844823f78291f.pdf) 
- commons: [File:(Judicial Selections- Federal Judicial Selections Committee 02-28-1984) - DPLA - cbc2ffa7de961c4f3b34028f87ba4986.pdf](https://commons.wikimedia.org/wiki/File:(Judicial_Selections-_Federal_Judicial_Selections_Committee_02-28-1984)_-_DPLA_-_cbc2ffa7de961c4f3b34028f87ba4986.pdf) 
- commons: [File:(Miscellaneous Sensitive Materials) (1 of 3) - DPLA - f4e43e898cec5bdf9d8d90251ae68e46.pdf](https://commons.wikimedia.org/wiki/File:(Miscellaneous_Sensitive_Materials)_(1_of_3)_-_DPLA_-_f4e43e898cec5bdf9d8d90251ae68e46.pdf) 
- commons: [File:(Miscellaneous Sensitive Materials) (2 of 3) - DPLA - 71f234de45c1a4577ceb0f80c901086e.pdf](https://commons.wikimedia.org/wiki/File:(Miscellaneous_Sensitive_Materials)_(2_of_3)_-_DPLA_-_71f234de45c1a4577ceb0f80c901086e.pdf) 
- commons: [File:(Miscellaneous Sensitive Materials) (3 of 3) - DPLA - fb1a2b4242eb7c12435490c463813315.pdf](https://commons.wikimedia.org/wiki/File:(Miscellaneous_Sensitive_Materials)_(3_of_3)_-_DPLA_-_fb1a2b4242eb7c12435490c463813315.pdf) 
- commons: [File:(Paine, Michael Ralph and Ruth) 2-1-1 Associates and Relatives - cd - 610-626 - DPLA - a2d0b3f43eb38dbe0e64e6f71cbc424e (page 1).pdf](https://commons.wikimedia.org/wiki/File:(Paine,_Michael_Ralph_and_Ruth)_2-1-1_Associates_and_Relatives_-_cd_-_610-626_-_DPLA_-_a2d0b3f43eb38dbe0e64e6f71cbc424e_(page_1).pdf) 
- commons: [File:(Paine, Michael Ralph and Ruth) 2-1-2 Paines - Affiliations - DPLA - 6405cd878780f6cda544def0695c017f.pdf](https://commons.wikimedia.org/wiki/File:(Paine,_Michael_Ralph_and_Ruth)_2-1-2_Paines_-_Affiliations_-_DPLA_-_6405cd878780f6cda544def0695c017f.pdf) 
- commons: [File:(Part IV. A. 2.) Evolution of the War. Aid for France in Indochina, 1950-54.pdf](https://commons.wikimedia.org/wiki/File:(Part_IV._A._2.)_Evolution_of_the_War._Aid_for_France_in_Indochina,_1950-54.pdf) between 1945 and 1967 date QS:P,+1950-00-00T00:00:00Z/7,P1319,+1945-00-00T00:00:00Z/9,P1326,+1967-00-00T00:00:00Z/9 
- commons: [File:(Part IV. C. 7. b.) Evolution of the War. Air War in the North 1965 - 1968. Volume II.pdf](https://commons.wikimedia.org/wiki/File:(Part_IV._C._7._b.)_Evolution_of_the_War._Air_War_in_the_North_1965_-_1968._Volume_II.pdf) between 1945 and 1967 date QS:P,+1950-00-00T00:00:00Z/7,P1319,+1945-00-00T00:00:00Z/9,P1326,+1967-00-00T00:00:00Z/9 
- commons: [File:(Part IV. C. 8.) Evolution of the War. Re-emphasis on Pacification 1965-1967.pdf](https://commons.wikimedia.org/wiki/File:(Part_IV._C._8.)_Evolution_of_the_War._Re-emphasis_on_Pacification_1965-1967.pdf) between 1945 and 1967 date QS:P,+1950-00-00T00:00:00Z/7,P1319,+1945-00-00T00:00:00Z/9,P1326,+1967-00-00T00:00:00Z/9 
- commons: [File:(Part IV. C. 9. b.) Evolution of the War. U.S.-GVN Relations. Volume 2 July 1965 - December 1967.pdf](https://commons.wikimedia.org/wiki/File:(Part_IV._C._9._b.)_Evolution_of_the_War._U.S.-GVN_Relations._Volume_2_July_1965_-_December_1967.pdf) between 1945 and 1967 date QS:P,+1950-00-00T00:00:00Z/7,P1319,+1945-00-00T00:00:00Z/9,P1326,+1967-00-00T00:00:00Z/9 
- commons: [File:(Part V. A.) Justification of the War. Public Statements. Volume I B--The Eisenhower Administration.pdf](https://commons.wikimedia.org/wiki/File:(Part_V._A.)_Justification_of_the_War._Public_Statements._Volume_I_B--The_Eisenhower_Administration.pdf) between 1945 and 1967 date QS:P,+1950-00-00T00:00:00Z/7,P1319,+1945-00-00T00:00:00Z/9,P1326,+1967-00-00T00:00:00Z/9 
- commons: [File:(Part V. B. 2. a.) Justification of the War. Internal Documents. The Truman Administration. Volume I 1945 - 1949.pdf](https://commons.wikimedia.org/wiki/File:(Part_V._B._2._a.)_Justification_of_the_War._Internal_Documents._The_Truman_Administration._Volume_I_1945_-_1949.pdf) between 1945 and 1967 date QS:P,+1950-00-00T00:00:00Z/7,P1319,+1945-00-00T00:00:00Z/9,P1326,+1967-00-00T00:00:00Z/9 
- commons: [File:(Part V. B. 3. d.) Justification of the War. Internal Documents. The Eisenhower Administration. Volume IV 1956 French Withdrawal - 1960](https://commons.wikimedia.org/wiki/File:(Part_V._B._3._d.)_Justification_of_the_War._Internal_Documents._The_Eisenhower_Administration._Volume_IV_1956_French_Withdrawal_-_1960.pdf) between 1945 and 1967 date QS:P,+1950-00-00T00:00:00Z/7,P1319,+1945-00-00T00:00:00Z/9,P1326,+1967-00-00T00:00:00Z/9 
- commons: [File:(Women’s Issues- Report of the Attorney General …As Required by Executive Order 12336 (Legal Equity for Women) Third Quarterly, July 19](https://commons.wikimedia.org/wiki/File:(Women%E2%80%99s_Issues-_Report_of_the_Attorney_General_%E2%80%A6As_Required_by_Executive_Order_12336_(Legal_Equity_for_Women)_Third_Quarterly,_July_1983)_(1)_-_DPLA_-_9a274b1cc5eecd387c173acacd701370.pdf) 
- commons: [File:(Women’s Issues- Report of the Attorney General …As Required by Executive Order 12336 (Legal Equity for Women) Third Quarterly, July 19](https://commons.wikimedia.org/wiki/File:(Women%E2%80%99s_Issues-_Report_of_the_Attorney_General_%E2%80%A6As_Required_by_Executive_Order_12336_(Legal_Equity_for_Women)_Third_Quarterly,_July_1983)_(2)_-_DPLA_-_bcafbfa09dcfcd4dbbcf869c56839ef8.pdf) 
- commons: [File:(Women’s Issues- Report of the Attorney General …As Required by Executive Order 12336 (Legal Equity for Women) Third Quarterly, July 19](https://commons.wikimedia.org/wiki/File:(Women%E2%80%99s_Issues-_Report_of_the_Attorney_General_%E2%80%A6As_Required_by_Executive_Order_12336_(Legal_Equity_for_Women)_Third_Quarterly,_July_1983)_(3)_-_DPLA_-_64062cf50651df508a968d7c16e1073b.pdf) 
- commons: [File:(Women’s Issues- Report of the Attorney General …As Required by Executive Order 12336 (Legal Equity for Women) Third Quarterly, July 19](https://commons.wikimedia.org/wiki/File:(Women%E2%80%99s_Issues-_Report_of_the_Attorney_General_%E2%80%A6As_Required_by_Executive_Order_12336_(Legal_Equity_for_Women)_Third_Quarterly,_July_1983)_(4)_-_DPLA_-_2c4c5835d6f007b44f9f4e87cf6323b8.pdf) 
- commons: [File:(Women’s Issues- Report of the Attorney General …As Required by Executive Order 12336 (Legal Equity for Women) Third Quarterly, July 19](https://commons.wikimedia.org/wiki/File:(Women%E2%80%99s_Issues-_Report_of_the_Attorney_General_%E2%80%A6As_Required_by_Executive_Order_12336_(Legal_Equity_for_Women)_Third_Quarterly,_July_1983)_(5)_-_DPLA_-_ba0ce1c9f5db847fea7215de5ae5602d.pdf) 
- commons: [File:(Women’s Issues- Report of the Attorney General …As Required by Executive Order 12336 (Legal Equity for Women) Third Quarterly, July 19](https://commons.wikimedia.org/wiki/File:(Women%E2%80%99s_Issues-_Report_of_the_Attorney_General_%E2%80%A6As_Required_by_Executive_Order_12336_(Legal_Equity_for_Women)_Third_Quarterly,_July_1983)_(6)_-_DPLA_-_7be3cad5a50cb56ac835845618bee865.pdf) 
- commons: [File:(Women’s Issues- Task Force on Legal Equity for Women) - DPLA - 8a1033ca5c858335b921044da43608dd.pdf](https://commons.wikimedia.org/wiki/File:(Women%E2%80%99s_Issues-_Task_Force_on_Legal_Equity_for_Women)_-_DPLA_-_8a1033ca5c858335b921044da43608dd.pdf) 
- commons: [File:01-06-1982 (case file 056745) (2) - DPLA - 7d604f0bf59bef155effb13de3a404eb.pdf](https://commons.wikimedia.org/wiki/File:01-06-1982_(case_file_056745)_(2)_-_DPLA_-_7d604f0bf59bef155effb13de3a404eb.pdf) 
- commons: [File:01-27-1981 (case file 043307) - DPLA - 3718add4b4a50942a15423a46446dc52.pdf](https://commons.wikimedia.org/wiki/File:01-27-1981_(case_file_043307)_-_DPLA_-_3718add4b4a50942a15423a46446dc52.pdf) 
- commons: [File:01-30-1981 (case file 043310) - DPLA - eaa67ae4b93d3cb785c33a40453f5e12.pdf](https://commons.wikimedia.org/wiki/File:01-30-1981_(case_file_043310)_-_DPLA_-_eaa67ae4b93d3cb785c33a40453f5e12.pdf) 
- commons: [File:02-11-1982 (case file 059220) (1) - DPLA - 2dbc312286766a62fda17d9a0d72b031.pdf](https://commons.wikimedia.org/wiki/File:02-11-1982_(case_file_059220)_(1)_-_DPLA_-_2dbc312286766a62fda17d9a0d72b031.pdf) 
- commons: [File:03302020-Executive-Order-of-the-Governor-of-the-State-of-Maryland (Korean translation).pdf](https://commons.wikimedia.org/wiki/File:03302020-Executive-Order-of-the-Governor-of-the-State-of-Maryland_(Korean_translation).pdf) 2020-03-30
- commons: [File:05-04-1982 (case file 082784) (2) - DPLA - a9a188cedcaa0b43933e98317a333e4a.pdf](https://commons.wikimedia.org/wiki/File:05-04-1982_(case_file_082784)_(2)_-_DPLA_-_a9a188cedcaa0b43933e98317a333e4a.pdf) 
- commons: [File:09-14-1982 (case file 099524) (1) - DPLA - 3695a6caee7d0dd2f6fc83b9a0b809a6.pdf](https://commons.wikimedia.org/wiki/File:09-14-1982_(case_file_099524)_(1)_-_DPLA_-_3695a6caee7d0dd2f6fc83b9a0b809a6.pdf) 
- commons: [File:1) Negotiations 2) Escalation 3) De-Escalation Vietnam H.A. Kissinger - DPLA - a0fae3863308e93ce13ae3e05bbd155e.pdf](https://commons.wikimedia.org/wiki/File:1)_Negotiations_2)_Escalation_3)_De-Escalation_Vietnam_H.A._Kissinger_-_DPLA_-_a0fae3863308e93ce13ae3e05bbd155e.pdf) 
- commons: [File:10-08-1981 (case file 043561) - DPLA - 2cd4c25d171f15afdd1dda277601a8ea.pdf](https://commons.wikimedia.org/wiki/File:10-08-1981_(case_file_043561)_-_DPLA_-_2cd4c25d171f15afdd1dda277601a8ea.pdf) 
- commons: [File:10-25-1982 (case file 103645) - DPLA - cc6be4563003091705ef073530322186.pdf](https://commons.wikimedia.org/wiki/File:10-25-1982_(case_file_103645)_-_DPLA_-_cc6be4563003091705ef073530322186.pdf) 
- commons: [File:1001 tests of foods, beverages and toilet accessories, good and otherwise; why they are so (IA cu31924031247798).pdf](https://commons.wikimedia.org/wiki/File:1001_tests_of_foods,_beverages_and_toilet_accessories,_good_and_otherwise;_why_they_are_so_(IA_cu31924031247798).pdf) 
- commons: [File:100224 Proliferation Security Initiative (PSI) (IA 100224ProliferationSecurityInitiativePSI-crs).pdf](https://commons.wikimedia.org/wiki/File:100224_Proliferation_Security_Initiative_(PSI)_(IA_100224ProliferationSecurityInitiativePSI-crs).pdf) 
- commons: [File:102629 Proliferation Security Initiative (PSI) (IA 102629ProliferationSecurityInitiativePSI-crs).pdf](https://commons.wikimedia.org/wiki/File:102629_Proliferation_Security_Initiative_(PSI)_(IA_102629ProliferationSecurityInitiativePSI-crs).pdf) 
- commons: [File:104704 Foreign Investment, CFIUS, and Homeland Security An Overview (IA 104704ForeignInvestmentCFIUSandHomelandSecurityAnOverview-crs).](https://commons.wikimedia.org/wiki/File:104704_Foreign_Investment,_CFIUS,_and_Homeland_Security_An_Overview_(IA_104704ForeignInvestmentCFIUSandHomelandSecurityAnOverview-crs).pdf) 
- commons: [File:104723 Intelligence Issues for Congress (IA 104723IntelligenceIssuesforCongress-crs).pdf](https://commons.wikimedia.org/wiki/File:104723_Intelligence_Issues_for_Congress_(IA_104723IntelligenceIssuesforCongress-crs).pdf) 
- commons: [File:106170 National Security Strategy Legislative Mandates, Execution to Date and Consideration for Congress (IA 106170NationalSecurityStra](https://commons.wikimedia.org/wiki/File:106170_National_Security_Strategy_Legislative_Mandates,_Execution_to_Date_and_Consideration_for_Congress_(IA_106170NationalSecurityStrategyLegislativeMandatesExecutiontoDateandConsiderationforCongress-crs).pdf) 
- commons: [File:108307 Suits Against Terrorist States by Victims of Terrorism (IA 108307SuitsAgainstTerroristStatesbyVictimsofTerrorism-crs).pdf](https://commons.wikimedia.org/wiki/File:108307_Suits_Against_Terrorist_States_by_Victims_of_Terrorism_(IA_108307SuitsAgainstTerroristStatesbyVictimsofTerrorism-crs).pdf) 
- commons: [File:108965 National Security Strategy Legislative Mandates, Execution to Date, and Considerations for Congress (IA 108965NationalSecuritySt](https://commons.wikimedia.org/wiki/File:108965_National_Security_Strategy_Legislative_Mandates,_Execution_to_Date,_and_Considerations_for_Congress_(IA_108965NationalSecurityStrategyLegislativeMandatesExecutiontoDateandConsiderationsforCongress-crs).pdf) 
- commons: [File:10TH ANNIVERSARY OF THE CONGRESSIONAL REVIEW ACT (IA gov.gpo.fdsys.CHRG-109hhrg26770).pdf](https://commons.wikimedia.org/wiki/File:10TH_ANNIVERSARY_OF_THE_CONGRESSIONAL_REVIEW_ACT_(IA_gov.gpo.fdsys.CHRG-109hhrg26770).pdf) 
- commons: [File:11 CFR 1985.pdf](https://commons.wikimedia.org/wiki/File:11_CFR_1985.pdf) 1985-01-01
- commons: [File:116583 The National Security Council An Organizational Assessment (IA 116583TheNationalSecurityCouncilAnOrganizationalAssessment-crs).p](https://commons.wikimedia.org/wiki/File:116583_The_National_Security_Council_An_Organizational_Assessment_(IA_116583TheNationalSecurityCouncilAnOrganizationalAssessment-crs).pdf) 
- commons: [File:116th United States Congress H. R. 0000267 (1st session) - Transportation, Housing and Urban Development, and Related Agencies Appropri](https://commons.wikimedia.org/wiki/File:116th_United_States_Congress_H._R._0000267_(1st_session)_-_Transportation,_Housing_and_Urban_Development,_and_Related_Agencies_Appropriations_Act,_2019_A_-_Introduced_in_House.pdf) 2019-01-08
- commons: [File:116th United States Congress H. R. 0000267 (1st session) - Transportation, Housing and Urban Development, and Related Agencies Appropri](https://commons.wikimedia.org/wiki/File:116th_United_States_Congress_H._R._0000267_(1st_session)_-_Transportation,_Housing_and_Urban_Development,_and_Related_Agencies_Appropriations_Act,_2019_B_-_Engrossed_in_House.pdf) 2019-01-10
- commons: [File:12-08-1981 (case file 051417) - DPLA - 6430aaa875aa6b8d3a769ec9d14ea932.pdf](https://commons.wikimedia.org/wiki/File:12-08-1981_(case_file_051417)_-_DPLA_-_6430aaa875aa6b8d3a769ec9d14ea932.pdf) 
- commons: [File:12-14-1982 (case file 115114) - DPLA - f4faea7b45941dceb63cff49e3eb780d.pdf](https://commons.wikimedia.org/wiki/File:12-14-1982_(case_file_115114)_-_DPLA_-_f4faea7b45941dceb63cff49e3eb780d.pdf) 
- commons: [File:12-21-1981 (case file 051430) (1) - DPLA - 163661ba96e4d22f60245a0ad00dc66b.pdf](https://commons.wikimedia.org/wiki/File:12-21-1981_(case_file_051430)_(1)_-_DPLA_-_163661ba96e4d22f60245a0ad00dc66b.pdf) 
- commons: [File:120598 Enemy Combatant Detainees Habeas Corpus Challenges in Federal Court (IA 120598EnemyCombatantDetaineesHabeasCorpusChallengesinFed](https://commons.wikimedia.org/wiki/File:120598_Enemy_Combatant_Detainees_Habeas_Corpus_Challenges_in_Federal_Court_(IA_120598EnemyCombatantDetaineesHabeasCorpusChallengesinFederalCourt-crs).pdf) 
- commons: [File:122456 Nuclear Cooperation with Other Countries A Primer (IA 122456NuclearCooperationwithOtherCountriesAPrimer-crs).pdf](https://commons.wikimedia.org/wiki/File:122456_Nuclear_Cooperation_with_Other_Countries_A_Primer_(IA_122456NuclearCooperationwithOtherCountriesAPrimer-crs).pdf) 
- commons: [File:125948 The National Security Council An Organizational Assessment (IA 125948TheNationalSecurityCouncilAnOrganizationalAssessment-crs).p](https://commons.wikimedia.org/wiki/File:125948_The_National_Security_Council_An_Organizational_Assessment_(IA_125948TheNationalSecurityCouncilAnOrganizationalAssessment-crs).pdf) 
- commons: [File:128821 Don't Ask, Don't Tell The Law and Military Policy on Same-Sex Behavior (IA 128821DontAskDontTellTheLawandMilitaryPolicyonSame-Se](https://commons.wikimedia.org/wiki/File:128821_Don%27t_Ask,_Don%27t_Tell_The_Law_and_Military_Policy_on_Same-Sex_Behavior_(IA_128821DontAskDontTellTheLawandMilitaryPolicyonSame-SexBehavior-crs).pdf) 
- commons: [File:128833 Intelligence Issues for Congress (IA 128833IntelligenceIssuesforCongress-crs).pdf](https://commons.wikimedia.org/wiki/File:128833_Intelligence_Issues_for_Congress_(IA_128833IntelligenceIssuesforCongress-crs).pdf) 
- commons: [File:130 Days of Elon Musk.pdf](https://commons.wikimedia.org/wiki/File:130_Days_of_Elon_Musk.pdf) 2025-06-04
- commons: [File:133509 Comparison of Rights in Military Commission Trials and Trials in Federal Criminal Court (IA 133509ComparisonofRightsinMilitaryCo](https://commons.wikimedia.org/wiki/File:133509_Comparison_of_Rights_in_Military_Commission_Trials_and_Trials_in_Federal_Criminal_Court_(IA_133509ComparisonofRightsinMilitaryCommissionTrialsandTrialsinFederalCriminalCourt-crs).pdf) 
- commons: [File:133876 Foreign Investment, CFIUS, and Homeland Security An Overview (IA 133876ForeignInvestmentCFIUSandHomelandSecurityAnOverview-crs).](https://commons.wikimedia.org/wiki/File:133876_Foreign_Investment,_CFIUS,_and_Homeland_Security_An_Overview_(IA_133876ForeignInvestmentCFIUSandHomelandSecurityAnOverview-crs).pdf) 
- commons: [File:134833 dodi 2016.pdf](https://commons.wikimedia.org/wiki/File:134833_dodi_2016.pdf) 2016-12
- commons: [File:137178 Nuclear Cooperation with Other Countries A Primer (IA 137178NuclearCooperationwithOtherCountriesAPrimer-crs).pdf](https://commons.wikimedia.org/wiki/File:137178_Nuclear_Cooperation_with_Other_Countries_A_Primer_(IA_137178NuclearCooperationwithOtherCountriesAPrimer-crs).pdf) 
- commons: [File:140671 Military Personnel and Freedom of Religious Expression Selected Legal Issues (IA 140671MilitaryPersonnelandFreedomofReligiousExp](https://commons.wikimedia.org/wiki/File:140671_Military_Personnel_and_Freedom_of_Religious_Expression_Selected_Legal_Issues_(IA_140671MilitaryPersonnelandFreedomofReligiousExpressionSelectedLegalIssues-crs).pdf) 
- commons: [File:140826 U ISN037 Unclassified summary of the Final determination of the PRB for ISN 37.pdf](https://commons.wikimedia.org/wiki/File:140826_U_ISN037_Unclassified_summary_of_the_Final_determination_of_the_PRB_for_ISN_37.pdf) 2014-08-26
- commons: [File:141612 Guantanamo Detention Center Legislative Activity in the 111th Congress (IA 141612GuantanamoDetentionCenterLegislativeActivityint](https://commons.wikimedia.org/wiki/File:141612_Guantanamo_Detention_Center_Legislative_Activity_in_the_111th_Congress_(IA_141612GuantanamoDetentionCenterLegislativeActivityinthe111thCongress-crs).pdf) 
- commons: [File:145599 Guantanamo Detention Center Legislative Activity in the 111th Congress (IA 145599GuantanamoDetentionCenterLegislativeActivityint](https://commons.wikimedia.org/wiki/File:145599_Guantanamo_Detention_Center_Legislative_Activity_in_the_111th_Congress_(IA_145599GuantanamoDetentionCenterLegislativeActivityinthe111thCongress-crs).pdf) 
- commons: [File:153312 Securing America's Borders The Role of the Intelligence Community (IA 153312SecuringAmericasBordersTheRoleoftheIntelligenceCommu](https://commons.wikimedia.org/wiki/File:153312_Securing_America%27s_Borders_The_Role_of_the_Intelligence_Community_(IA_153312SecuringAmericasBordersTheRoleoftheIntelligenceCommunity-crs).pdf) 
- commons: [File:153313 Classified Information Policy and Executive Order 13526 (IA 153313ClassifiedInformationPolicyandExecutiveOrder13526-crs).pdf](https://commons.wikimedia.org/wiki/File:153313_Classified_Information_Policy_and_Executive_Order_13526_(IA_153313ClassifiedInformationPolicyandExecutiveOrder13526-crs).pdf) 
- commons: [File:15January2007.pdf](https://commons.wikimedia.org/wiki/File:15January2007.pdf) January 15, 2007
- commons: [File:1650.1H - Navy and Marine Corps Award Manual (August 2008).pdf](https://commons.wikimedia.org/wiki/File:1650.1H_-_Navy_and_Marine_Corps_Award_Manual_(August_2008).pdf) 2008-08-22
- commons: [File:17-35105 Per Curiam Order by Ninth Circuit denying the Appeal of the TRO.pdf](https://commons.wikimedia.org/wiki/File:17-35105_Per_Curiam_Order_by_Ninth_Circuit_denying_the_Appeal_of_the_TRO.pdf) 2017-02-09
- commons: [File:17-35105 Reply In Support of Emergency Motion for Stay.pdf](https://commons.wikimedia.org/wiki/File:17-35105_Reply_In_Support_of_Emergency_Motion_for_Stay.pdf) 2017-02-06
- commons: [File:17June2006.pdf](https://commons.wikimedia.org/wiki/File:17June2006.pdf) June 17, 2006
- commons: [File:1890-1990 - a century of service - United States Board on Geographic Names (IA 18901990centuryo1484burr).pdf](https://commons.wikimedia.org/wiki/File:1890-1990_-_a_century_of_service_-_United_States_Board_on_Geographic_Names_(IA_18901990centuryo1484burr).pdf) 
- commons: [File:18july2005.pdf](https://commons.wikimedia.org/wiki/File:18july2005.pdf) July 18, 2005
- commons: [File:1900; or, The last President (IA 1900orlastpresid00lock).pdf](https://commons.wikimedia.org/wiki/File:1900;_or,_The_last_President_(IA_1900orlastpresid00lock).pdf) 
- commons: [File:1910 to July 1 1913 (IA cfaminutes19nov1910).pdf](https://commons.wikimedia.org/wiki/File:1910_to_July_1_1913_(IA_cfaminutes19nov1910).pdf) 
- commons: [File:194798 Nuclear Cooperation with Other Countries A Primer (IA 194798NuclearCooperationwithOtherCountriesAPrimer-crs).pdf](https://commons.wikimedia.org/wiki/File:194798_Nuclear_Cooperation_with_Other_Countries_A_Primer_(IA_194798NuclearCooperationwithOtherCountriesAPrimer-crs).pdf) 
- commons: [File:1967 Census of Mineral Industries. Summary Statistics, and Major Groups 10-14 (IA 1967censusofmine01uns).pdf](https://commons.wikimedia.org/wiki/File:1967_Census_of_Mineral_Industries._Summary_Statistics,_and_Major_Groups_10-14_(IA_1967censusofmine01uns).pdf) 
- commons: [File:1975-01-03 HR12884 Omnibus Wilderness Designations - DPLA - affc0d1651e1f9de0ef2bbf03cb83586.pdf](https://commons.wikimedia.org/wiki/File:1975-01-03_HR12884_Omnibus_Wilderness_Designations_-_DPLA_-_affc0d1651e1f9de0ef2bbf03cb83586.pdf) 1974-12-01/1975-01-31
- commons: [File:1984 annual water quality analyses report for Nevada (IA 1984annualwaterq00sula).pdf](https://commons.wikimedia.org/wiki/File:1984_annual_water_quality_analyses_report_for_Nevada_(IA_1984annualwaterq00sula).pdf) 
- commons: [File:1985 Federal Register notice of MDMA scheduling.pdf](https://commons.wikimedia.org/wiki/File:1985_Federal_Register_notice_of_MDMA_scheduling.pdf) 1985-05-31
- commons: [File:200 Years Of Military Medicine (IA 200YearsOfMilitaryMedicinebooklet).pdf](https://commons.wikimedia.org/wiki/File:200_Years_Of_Military_Medicine_(IA_200YearsOfMilitaryMedicinebooklet).pdf) 
- commons: [File:2000 Annual Report Water Resources Division Natural Resources Program Center National Park Service... Department of the Interior (IA do](https://commons.wikimedia.org/wiki/File:2000_Annual_Report_Water_Resources_Division_Natural_Resources_Program_Center_National_Park_Service..._Department_of_the_Interior_(IA_doi-report_i-2989nrwrd-nrr-01-10).pdf) 
- commons: [File:2001 Tennessee NWR - DPLA - c786d90d8f6de4986b6ec6322161875b.pdf](https://commons.wikimedia.org/wiki/File:2001_Tennessee_NWR_-_DPLA_-_c786d90d8f6de4986b6ec6322161875b.pdf) 
- commons: [File:2001 The Controversial Pardon of International Fugitive Marc Rich.pdf](https://commons.wikimedia.org/wiki/File:2001_The_Controversial_Pardon_of_International_Fugitive_Marc_Rich.pdf) 2001-02-08
- commons: [File:2009 Open Government Directive.pdf](https://commons.wikimedia.org/wiki/File:2009_Open_Government_Directive.pdf) 2009-12-08
- commons: [File:2010 Budget justification - USACE-p16021coll6-896.pdf](https://commons.wikimedia.org/wiki/File:2010_Budget_justification_-_USACE-p16021coll6-896.pdf) 
- commons: [File:2011 "Lawfulness of a Lethal Operation Directed Against a U.S. Citizen who is a Senior Operational Leader of Al Qa'ida or An Associated](https://commons.wikimedia.org/wiki/File:2011_%22Lawfulness_of_a_Lethal_Operation_Directed_Against_a_U.S._Citizen_who_is_a_Senior_Operational_Leader_of_Al_Qa%27ida_or_An_Associated_Force%22.pdf) 2011-11-08
- commons: [File:2013-tri-national-analysis-complete.pdf](https://commons.wikimedia.org/wiki/File:2013-tri-national-analysis-complete.pdf) 2013
- commons: [File:2018 Civil Works Programs stakeholder satisfaction survey - USACE-p16021coll11-4119.pdf](https://commons.wikimedia.org/wiki/File:2018_Civil_Works_Programs_stakeholder_satisfaction_survey_-_USACE-p16021coll11-4119.pdf) 
- commons: [File:2018-2029 Quillayute Spit repair and Clallam County, Washington- Finding of No Significant Impact (FONSI) and Clean Water Act Section 4](https://commons.wikimedia.org/wiki/File:2018-2029_Quillayute_Spit_repair_and_Clallam_County,_Washington-_Finding_of_No_Significant_Impact_(FONSI)_and_Clean_Water_Act_Section_404_statement_of_findings_-_USACE-p16021coll7-10079.pdf) 
- commons: [File:2019 Levee Rehabilitation Program Assistance, Public Law 84-99- Heise-Roberts Levee System, Upper Snake River, Jefferson County, Idaho-](https://commons.wikimedia.org/wiki/File:2019_Levee_Rehabilitation_Program_Assistance,_Public_Law_84-99-_Heise-Roberts_Levee_System,_Upper_Snake_River,_Jefferson_County,_Idaho-_Environmental_assessment_in_compliance_with_the_National_En_..._-_USACE-p16021coll7-12672.pdf) 
- commons: [File:2020-07-29 PSI Staff Report - The Art Industry and U.S. Policies that Undermine Sanctions.pdf](https://commons.wikimedia.org/wiki/File:2020-07-29_PSI_Staff_Report_-_The_Art_Industry_and_U.S._Policies_that_Undermine_Sanctions.pdf) 2020-07-28
- commons: [File:20200302-INTERVIEW-WITH-PCOO-SECRETARY-MARTIN-ANDANAR-BY-HENRY-URI-AND-MISSY-HISTA-COFFEEBREAK-–-DZRH.pdf](https://commons.wikimedia.org/wiki/File:20200302-INTERVIEW-WITH-PCOO-SECRETARY-MARTIN-ANDANAR-BY-HENRY-URI-AND-MISSY-HISTA-COFFEEBREAK-%E2%80%93-DZRH.pdf) 2020-03-02
- commons: [File:2021 Nationwide permits, regional conditions, Omaha District, required best management practices - USACE-p16021coll11-4870.pdf](https://commons.wikimedia.org/wiki/File:2021_Nationwide_permits,_regional_conditions,_Omaha_District,_required_best_management_practices_-_USACE-p16021coll11-4870.pdf) 
- commons: [File:2021 Omaha District permits, regional conditions, Omaha District, required best management practices - USACE-p16021coll11-4971.pdf](https://commons.wikimedia.org/wiki/File:2021_Omaha_District_permits,_regional_conditions,_Omaha_District,_required_best_management_practices_-_USACE-p16021coll11-4971.pdf) 
- commons: [File:206157 The 2013 Cybersecurity Executive Order Overview and Considerations for Congress (IA 206157The2013CybersecurityExecutiveOrderOver](https://commons.wikimedia.org/wiki/File:206157_The_2013_Cybersecurity_Executive_Order_Overview_and_Considerations_for_Congress_(IA_206157The2013CybersecurityExecutiveOrderOverviewandConsiderationsforCongress-crs).pdf) 
- commons: [File:21 CFR 1990.pdf](https://commons.wikimedia.org/wiki/File:21_CFR_1990.pdf) 1990-04-01
- commons: [File:214923 Cybersecurity Authoritative Reports and Resources (IA 214923CybersecurityAuthoritativeReportsandResources-crs).pdf](https://commons.wikimedia.org/wiki/File:214923_Cybersecurity_Authoritative_Reports_and_Resources_(IA_214923CybersecurityAuthoritativeReportsandResources-crs).pdf) 
- commons: [File:21ST CENTURY CURES- EXAMINING WAYS TO COMBAT ANTIBIOTIC RESISTANCE AND FOSTER NEW DRUG DEVELOPMENT (IA gov.gpo.fdsys.CHRG-113hhrg93933)](https://commons.wikimedia.org/wiki/File:21ST_CENTURY_CURES-_EXAMINING_WAYS_TO_COMBAT_ANTIBIOTIC_RESISTANCE_AND_FOSTER_NEW_DRUG_DEVELOPMENT_(IA_gov.gpo.fdsys.CHRG-113hhrg93933).pdf) 
- commons: [File:225104 Nuclear Cooperation with Other Countries A Primer (IA 225104NuclearCooperationwithOtherCountriesAPrimer-crs).pdf](https://commons.wikimedia.org/wiki/File:225104_Nuclear_Cooperation_with_Other_Countries_A_Primer_(IA_225104NuclearCooperationwithOtherCountriesAPrimer-crs).pdf) 
- commons: [File:22December2005.pdf](https://commons.wikimedia.org/wiki/File:22December2005.pdf) 2005-12-22
- commons: [File:234348 Nuclear Cooperation with Other Countries A Primer (IA 234348NuclearCooperationwithOtherCountriesAPrimer-crs).pdf](https://commons.wikimedia.org/wiki/File:234348_Nuclear_Cooperation_with_Other_Countries_A_Primer_(IA_234348NuclearCooperationwithOtherCountriesAPrimer-crs).pdf) 
- commons: [File:24June2006.pdf](https://commons.wikimedia.org/wiki/File:24June2006.pdf) 2006-06-24
- commons: [File:29January2006.pdf](https://commons.wikimedia.org/wiki/File:29January2006.pdf) 2006-01-29
- commons: [File:30 CFR 1959.pdf](https://commons.wikimedia.org/wiki/File:30_CFR_1959.pdf) 1959-01-01
- commons: [File:30 CFR 1974.pdf](https://commons.wikimedia.org/wiki/File:30_CFR_1974.pdf) 1974-07-01
- commons: [File:30 CFR 1993.pdf](https://commons.wikimedia.org/wiki/File:30_CFR_1993.pdf) 1993-07-01
- commons: [File:33857 Sensitive Security Information and Transportation Security Issues and Congressional Options (IA 33857SensitiveSecurityInformation](https://commons.wikimedia.org/wiki/File:33857_Sensitive_Security_Information_and_Transportation_Security_Issues_and_Congressional_Options_(IA_33857SensitiveSecurityInformationandTransportationSecurityIssuesandCongressionalOptions-crs).pdf) 
- commons: [File:35 CFR 1992.pdf](https://commons.wikimedia.org/wiki/File:35_CFR_1992.pdf) 1992-07-01
- commons: [File:42 CFR 1940.pdf](https://commons.wikimedia.org/wiki/File:42_CFR_1940.pdf) 1940
- commons: [File:43 CFR 1992.pdf](https://commons.wikimedia.org/wiki/File:43_CFR_1992.pdf) 1992-10-01
- commons: [File:45449 Military Construction in Support of Afghanistan and Iraq (IA 45449MilitaryConstructioninSupportofAfghanistanandIraq-crs).pdf](https://commons.wikimedia.org/wiki/File:45449_Military_Construction_in_Support_of_Afghanistan_and_Iraq_(IA_45449MilitaryConstructioninSupportofAfghanistanandIraq-crs).pdf) 
- commons: [File:47 CFR 1970.pdf](https://commons.wikimedia.org/wiki/File:47_CFR_1970.pdf) 1970-01-01
- commons: [File:5-14-76 - Azalea Festival Committee - DPLA - 8037c26eca7f2010e29e871d6d7a3d9e.pdf](https://commons.wikimedia.org/wiki/File:5-14-76_-_Azalea_Festival_Committee_-_DPLA_-_8037c26eca7f2010e29e871d6d7a3d9e.pdf) 1976-05-01/1976-05-31
- commons: [File:5September2005.pdf](https://commons.wikimedia.org/wiki/File:5September2005.pdf) 2005-09-05
- commons: [File:7 CFR 1973.pdf](https://commons.wikimedia.org/wiki/File:7_CFR_1973.pdf) 1973-01-01
- commons: [File:75 FR 43825 anti-circumvention exemption.pdf](https://commons.wikimedia.org/wiki/File:75_FR_43825_anti-circumvention_exemption.pdf) 2010-07-27
- commons: [File:76919 Interrogation of Detainees Overview of the McCain Amendment (IA 76919InterrogationofDetaineesOverviewoftheMcCainAmendment-crs).pd](https://commons.wikimedia.org/wiki/File:76919_Interrogation_of_Detainees_Overview_of_the_McCain_Amendment_(IA_76919InterrogationofDetaineesOverviewoftheMcCainAmendment-crs).pdf) 
- commons: [File:86th Congress, 1st Session, Report Number 38, Design of the United States Flag - DPLA - f09b110e8791e55625960f3cd30dd0e0.pdf](https://commons.wikimedia.org/wiki/File:86th_Congress,_1st_Session,_Report_Number_38,_Design_of_the_United_States_Flag_-_DPLA_-_f09b110e8791e55625960f3cd30dd0e0.pdf) 18 February 1959
- commons: [File:9.0 Index - USACE-p16021coll7-20710.pdf](https://commons.wikimedia.org/wiki/File:9.0_Index_-_USACE-p16021coll7-20710.pdf) 
- commons: [File:95% Draft Elk Creek master plan, Jackson County, Oregon - USACE-p16021coll7-8492.pdf](https://commons.wikimedia.org/wiki/File:95%25_Draft_Elk_Creek_master_plan,_Jackson_County,_Oregon_-_USACE-p16021coll7-8492.pdf) 
- commons: [File:97-589 (IA 97-589-crs).pdf](https://commons.wikimedia.org/wiki/File:97-589_(IA_97-589-crs).pdf) 
- commons: [File:97-696 (IA 97-696-crs).pdf](https://commons.wikimedia.org/wiki/File:97-696_(IA_97-696-crs).pdf) 
- commons: [File:97-771 (IA 97-771-crs).pdf](https://commons.wikimedia.org/wiki/File:97-771_(IA_97-771-crs).pdf) 
- commons: [File:98-1904.pet.app.pdf](https://commons.wikimedia.org/wiki/File:98-1904.pet.app.pdf) 1998-10-06
- commons: [File:98-215 (IA 98-215-crs).pdf](https://commons.wikimedia.org/wiki/File:98-215_(IA_98-215-crs).pdf) 
- commons: [File:98-299 (IA 98-299-crs).pdf](https://commons.wikimedia.org/wiki/File:98-299_(IA_98-299-crs).pdf) 
- commons: [File:98-486 (IA 98-486-crs).pdf](https://commons.wikimedia.org/wiki/File:98-486_(IA_98-486-crs).pdf) 
- commons: [File:98-611 (IA 98-611-crs).pdf](https://commons.wikimedia.org/wiki/File:98-611_(IA_98-611-crs).pdf) 
- commons: [File:98-654 Internships, Fellowships, and Other Work Experience Opportunities in the Federal Government (IA 98-654InternshipsFellowshipsandO](https://commons.wikimedia.org/wiki/File:98-654_Internships,_Fellowships,_and_Other_Work_Experience_Opportunities_in_the_Federal_Government_(IA_98-654InternshipsFellowshipsandOtherWorkExperienceOpportunitiesintheFederalGovernment-crs).pdf) 
- commons: [File:98-691 (IA 98-691-crs).pdf](https://commons.wikimedia.org/wiki/File:98-691_(IA_98-691-crs).pdf) 
- commons: [File:98-766 (IA 98-766-crs).pdf](https://commons.wikimedia.org/wiki/File:98-766_(IA_98-766-crs).pdf) 
- commons: [File:98-86 (IA 98-86-crs).pdf](https://commons.wikimedia.org/wiki/File:98-86_(IA_98-86-crs).pdf) 
- commons: [File:A Brief history of the rural electric and telephone programs (IA CAT10657632).pdf](https://commons.wikimedia.org/wiki/File:A_Brief_history_of_the_rural_electric_and_telephone_programs_(IA_CAT10657632).pdf) 
- commons: [File:A Documentary history of American industrial society; (IA documentaryhisto08amer).pdf](https://commons.wikimedia.org/wiki/File:A_Documentary_history_of_American_industrial_society;_(IA_documentaryhisto08amer).pdf) 
- commons: [File:A FORTRAN analyzer (IA fortrananalyzer849lyon).pdf](https://commons.wikimedia.org/wiki/File:A_FORTRAN_analyzer_(IA_fortrananalyzer849lyon).pdf) 
- commons: [File:A GLOBAL PERSPECTIVE. ON CYBER THREATS (IA gov.gpo.fdsys.CHRG-114hhrg96993).pdf](https://commons.wikimedia.org/wiki/File:A_GLOBAL_PERSPECTIVE._ON_CYBER_THREATS_(IA_gov.gpo.fdsys.CHRG-114hhrg96993).pdf) 
- commons: [File:A PERSPECTIVE ON THE ENDANGERED SPECIES ACT'S IMPACTS ON THE OIL AND GAS INDUSTRY (IA gov.gpo.fdsys.CHRG-110shrg61983).pdf](https://commons.wikimedia.org/wiki/File:A_PERSPECTIVE_ON_THE_ENDANGERED_SPECIES_ACT%27S_IMPACTS_ON_THE_OIL_AND_GAS_INDUSTRY_(IA_gov.gpo.fdsys.CHRG-110shrg61983).pdf) 
- commons: [File:A REVIEW OF RECENTLY COMPLETED UNITED STATES ARMY CORPS OF ENGINEERS CHIEF'S REPORTS, PART 2 (IA gov.gpo.fdsys.CHRG-114hhrg20215).pdf](https://commons.wikimedia.org/wiki/File:A_REVIEW_OF_RECENTLY_COMPLETED_UNITED_STATES_ARMY_CORPS_OF_ENGINEERS_CHIEF%27S_REPORTS,_PART_2_(IA_gov.gpo.fdsys.CHRG-114hhrg20215).pdf) 
- commons: [File:A REVIEW OF REGULATORY REFORM PROPOSALS (IA gov.gpo.fdsys.CHRG-114shrg22377).pdf](https://commons.wikimedia.org/wiki/File:A_REVIEW_OF_REGULATORY_REFORM_PROPOSALS_(IA_gov.gpo.fdsys.CHRG-114shrg22377).pdf) 
- commons: [File:A Report on Health Disparities and Hispanics Leadership Summit Series (IA reportonhealthdi00unse).pdf](https://commons.wikimedia.org/wiki/File:A_Report_on_Health_Disparities_and_Hispanics_Leadership_Summit_Series_(IA_reportonhealthdi00unse).pdf) 
- commons: [File:A World of Names, U.S. Department of the Interior, 1992 (IA doi-report 1332n15).pdf](https://commons.wikimedia.org/wiki/File:A_World_of_Names,_U.S._Department_of_the_Interior,_1992_(IA_doi-report_1332n15).pdf) 
- commons: [File:A basis for standardization of user-terminal protocols for computer network access (IA basisforstandard877neum).pdf](https://commons.wikimedia.org/wiki/File:A_basis_for_standardization_of_user-terminal_protocols_for_computer_network_access_(IA_basisforstandard877neum).pdf) 
- commons: [File:A catalogue of the exhibit of the Department of state at the Louisiana purchase exposition, St. Louis, 1904 (IA catalogueofexhib02unit)](https://commons.wikimedia.org/wiki/File:A_catalogue_of_the_exhibit_of_the_Department_of_state_at_the_Louisiana_purchase_exposition,_St._Louis,_1904_(IA_catalogueofexhib02unit).pdf) 
- commons: [File:A catalogue of the exhibit of the Department of state at the Pan-American exposition, Buffalo, 1901 (IA catalogueofexhi00unit).pdf](https://commons.wikimedia.org/wiki/File:A_catalogue_of_the_exhibit_of_the_Department_of_state_at_the_Pan-American_exposition,_Buffalo,_1901_(IA_catalogueofexhi00unit).pdf) 
- commons: [File:A chronological history of the Soil Conservation Sevice and related events - our soil our strength (IA CAT10840527).pdf](https://commons.wikimedia.org/wiki/File:A_chronological_history_of_the_Soil_Conservation_Sevice_and_related_events_-_our_soil_our_strength_(IA_CAT10840527).pdf) 
- commons: [File:A comparative study of government and non-government ethics programs, practices, and policies. (IA comparativestudygov00mcke).pdf](https://commons.wikimedia.org/wiki/File:A_comparative_study_of_government_and_non-government_ethics_programs,_practices,_and_policies._(IA_comparativestudygov00mcke).pdf) 
- commons: [File:A comparison of the fully burdened cost of fuel methodologies used across the Department of Defense (IA acomparisonofful109455135).pdf](https://commons.wikimedia.org/wiki/File:A_comparison_of_the_fully_burdened_cost_of_fuel_methodologies_used_across_the_Department_of_Defense_(IA_acomparisonofful109455135).pdf) 
- commons: [File:A compilation of the messages and papers of the presidents (IA compilationofmes11inunit).pdf](https://commons.wikimedia.org/wiki/File:A_compilation_of_the_messages_and_papers_of_the_presidents_(IA_compilationofmes11inunit).pdf) 
- commons: [File:A compilation of the messages and papers of the presidents, 1789-1922 (IA cu31924052157967).pdf](https://commons.wikimedia.org/wiki/File:A_compilation_of_the_messages_and_papers_of_the_presidents,_1789-1922_(IA_cu31924052157967).pdf) 
- commons: [File:A comprehensive analysis of the environmental remediation industry (IA comprehensiveana00hill).pdf](https://commons.wikimedia.org/wiki/File:A_comprehensive_analysis_of_the_environmental_remediation_industry_(IA_comprehensiveana00hill).pdf) 
- commons: [File:A cost-benefit analysis for revision and reimplementation of the office paper recycling program at the Naval Postgraduate School, Monte](https://commons.wikimedia.org/wiki/File:A_cost-benefit_analysis_for_revision_and_reimplementation_of_the_office_paper_recycling_program_at_the_Naval_Postgraduate_School,_Monterey_(IA_costbenefitanaly00brow).pdf) 
- commons: [File:A cultural resource summary of the east central portion of the Moab District (IA culturalresource00pier).pdf](https://commons.wikimedia.org/wiki/File:A_cultural_resource_summary_of_the_east_central_portion_of_the_Moab_District_(IA_culturalresource00pier).pdf) 
- commons: [File:A digest of opinions of the Judge-Advocates General of the Army (IA digestofopinions00wintrich).pdf](https://commons.wikimedia.org/wiki/File:A_digest_of_opinions_of_the_Judge-Advocates_General_of_the_Army_(IA_digestofopinions00wintrich).pdf) 
- commons: [File:A flood plain management study for the town of West Fairlee, Vermont (IA CAT10757184).pdf](https://commons.wikimedia.org/wiki/File:A_flood_plain_management_study_for_the_town_of_West_Fairlee,_Vermont_(IA_CAT10757184).pdf) 
- commons: [File:A framework for synthesizing the United States Code in support of cyberspace operations (IA aframeworkforsyn1094548480).pdf](https://commons.wikimedia.org/wiki/File:A_framework_for_synthesizing_the_United_States_Code_in_support_of_cyberspace_operations_(IA_aframeworkforsyn1094548480).pdf) 
- commons: [File:A guide for the prospective Navy contractor. (IA guideforprospect00mann).pdf](https://commons.wikimedia.org/wiki/File:A_guide_for_the_prospective_Navy_contractor._(IA_guideforprospect00mann).pdf) 
- commons: [File:A handbook of economic agencies of the war of 1917 (IA handbookofeconom00unitrich).pdf](https://commons.wikimedia.org/wiki/File:A_handbook_of_economic_agencies_of_the_war_of_1917_(IA_handbookofeconom00unitrich).pdf) 
- commons: [File:A history of United States Department of Agriculture water resource activities (IA CAT81759618).pdf](https://commons.wikimedia.org/wiki/File:A_history_of_United_States_Department_of_Agriculture_water_resource_activities_(IA_CAT81759618).pdf) 
- commons: [File:A history of trade unionism in the United States (IA cu31924002700254).pdf](https://commons.wikimedia.org/wiki/File:A_history_of_trade_unionism_in_the_United_States_(IA_cu31924002700254).pdf) 
- commons: [File:A history of trade unionism in the United States (IA historyoftradeun00perliala).pdf](https://commons.wikimedia.org/wiki/File:A_history_of_trade_unionism_in_the_United_States_(IA_historyoftradeun00perliala).pdf) 
- commons: [File:A layman's philosophy of federal budget formulation. (IA laymansphilosoph19554fitz).pdf](https://commons.wikimedia.org/wiki/File:A_layman%27s_philosophy_of_federal_budget_formulation._(IA_laymansphilosoph19554fitz).pdf) 
- commons: [File:A management overview of software reuse (IA managementovervi5001wong).pdf](https://commons.wikimedia.org/wiki/File:A_management_overview_of_software_reuse_(IA_managementovervi5001wong).pdf) 
- commons: [File:A manual for courts-martial (IA cu31924020025221).pdf](https://commons.wikimedia.org/wiki/File:A_manual_for_courts-martial_(IA_cu31924020025221).pdf) 
- commons: [File:A manual wafer probe station for an integrated circuit test system (IA manualwaferprobe4006carv).pdf](https://commons.wikimedia.org/wiki/File:A_manual_wafer_probe_station_for_an_integrated_circuit_test_system_(IA_manualwaferprobe4006carv).pdf) 
- commons: [File:A marginal analysis for minimizing shortage in a multi-item inventory system with a constraint for a single period (IA marginalanalysis](https://commons.wikimedia.org/wiki/File:A_marginal_analysis_for_minimizing_shortage_in_a_multi-item_inventory_system_with_a_constraint_for_a_single_period_(IA_marginalanalysis00park).pdf) 
- commons: [File:A metric evaluation approach for the Defense Acquisition Workforce Improvement Act (IA metricevaluation00gord).pdf](https://commons.wikimedia.org/wiki/File:A_metric_evaluation_approach_for_the_Defense_Acquisition_Workforce_Improvement_Act_(IA_metricevaluation00gord).pdf) 
- commons: [File:A new Lewis and Clark map (IA cu31924028908287).pdf](https://commons.wikimedia.org/wiki/File:A_new_Lewis_and_Clark_map_(IA_cu31924028908287).pdf) 
- commons: [File:A new philosophy for stockpiling. (IA newphilosophyfor00gord).pdf](https://commons.wikimedia.org/wiki/File:A_new_philosophy_for_stockpiling._(IA_newphilosophyfor00gord).pdf) 
- commons: [File:A register of the General Assembly of Virginia, 1776-1918, and of the Constitutional Conventions (IA registerofgenera00virg).pdf](https://commons.wikimedia.org/wiki/File:A_register_of_the_General_Assembly_of_Virginia,_1776-1918,_and_of_the_Constitutional_Conventions_(IA_registerofgenera00virg).pdf) 
- commons: [File:A report of findings for the 52nd meeting, Chief of Engineers Environmental Advisory Board, June 7-10, 1994, Omaha, Nebraska - USACE-p2](https://commons.wikimedia.org/wiki/File:A_report_of_findings_for_the_52nd_meeting,_Chief_of_Engineers_Environmental_Advisory_Board,_June_7-10,_1994,_Omaha,_Nebraska_-_USACE-p266001coll1-9837.pdf) 
- commons: [File:A review of Federal income taxation developments affecting active duty military personnel, 1862-1949. (IA reviewoffederali00jurk).pdf](https://commons.wikimedia.org/wiki/File:A_review_of_Federal_income_taxation_developments_affecting_active_duty_military_personnel,_1862-1949._(IA_reviewoffederali00jurk).pdf) 
- commons: [File:A review of centralized readiness reporting systems and their impact upon the U.S. Marine division. (IA reviewofcentrali00shav).pdf](https://commons.wikimedia.org/wiki/File:A_review_of_centralized_readiness_reporting_systems_and_their_impact_upon_the_U.S._Marine_division._(IA_reviewofcentrali00shav).pdf) 
- commons: [File:A satellite-controlled digital clock (IA satellitecontrol681cate).pdf](https://commons.wikimedia.org/wiki/File:A_satellite-controlled_digital_clock_(IA_satellitecontrol681cate).pdf) 
- commons: [File:A study of the impact of the lack of a Cost Accounting Standards Board. (IA studyofimpactofl00sumn).pdf](https://commons.wikimedia.org/wiki/File:A_study_of_the_impact_of_the_lack_of_a_Cost_Accounting_Standards_Board._(IA_studyofimpactofl00sumn).pdf) 
- commons: [File:A study of the implementation of current cost accounting in the Republic of Korea Army procurement systems. (IA studyofimplement00leej)](https://commons.wikimedia.org/wiki/File:A_study_of_the_implementation_of_current_cost_accounting_in_the_Republic_of_Korea_Army_procurement_systems._(IA_studyofimplement00leej).pdf) 
- commons: [File:A survey for the collection of professional opinion on selected fire protection engineering topics (IA surveyforcollect861harr).pdf](https://commons.wikimedia.org/wiki/File:A_survey_for_the_collection_of_professional_opinion_on_selected_fire_protection_engineering_topics_(IA_surveyforcollect861harr).pdf) 
- commons: [File:A treatise on the law of naturalization of the United States (IA lawofnaturalizat00vand).pdf](https://commons.wikimedia.org/wiki/File:A_treatise_on_the_law_of_naturalization_of_the_United_States_(IA_lawofnaturalizat00vand).pdf) 
- commons: [File:A vessel inspection information system. (IA vesselinspection00wils).pdf](https://commons.wikimedia.org/wiki/File:A_vessel_inspection_information_system._(IA_vesselinspection00wils).pdf) 
- commons: [File:A,E,C CAD standard- Release 4.0 - USACE-p266001coll1-2810.pdf](https://commons.wikimedia.org/wiki/File:A,E,C_CAD_standard-_Release_4.0_-_USACE-p266001coll1-2810.pdf) 
- commons: [File:A.R.S. & S.C.S. Watershed Modeling Workshop - March 16, 178(sic), 18, 1970, Tuscon, Arizona (IA CAT31112758001).pdf](https://commons.wikimedia.org/wiki/File:A.R.S._%26_S.C.S._Watershed_Modeling_Workshop_-_March_16,_178(sic),_18,_1970,_Tuscon,_Arizona_(IA_CAT31112758001).pdf) 
- commons: [File:ACCESS DELAYED- FIXING THE SECURITY CLEARANCE PROCESS (IA gov.gpo.fdsys.CHRG-109shrg22198).pdf](https://commons.wikimedia.org/wiki/File:ACCESS_DELAYED-_FIXING_THE_SECURITY_CLEARANCE_PROCESS_(IA_gov.gpo.fdsys.CHRG-109shrg22198).pdf) 
- commons: [File:ACCESS DELAYED- FIXING THE SECURITY CLEARANCE PROCESS - PART II (IA gov.gpo.fdsys.CHRG-109shrg24930).pdf](https://commons.wikimedia.org/wiki/File:ACCESS_DELAYED-_FIXING_THE_SECURITY_CLEARANCE_PROCESS_-_PART_II_(IA_gov.gpo.fdsys.CHRG-109shrg24930).pdf) 
- commons: [File:ACCOUNTING FOR THE TRUE COST OF REGULATION- EXPLORING THE POSSIBILITY OF A REGULATORY BUDGET (IA gov.gpo.fdsys.CHRG-114shrg20564).pdf](https://commons.wikimedia.org/wiki/File:ACCOUNTING_FOR_THE_TRUE_COST_OF_REGULATION-_EXPLORING_THE_POSSIBILITY_OF_A_REGULATORY_BUDGET_(IA_gov.gpo.fdsys.CHRG-114shrg20564).pdf) 
- commons: [File:ADMINISTRATIVE LAW, PROCESS AND PROCEDURE PROJECT (IA gov.gpo.fdsys.CHRG-109hhrg24282).pdf](https://commons.wikimedia.org/wiki/File:ADMINISTRATIVE_LAW,_PROCESS_AND_PROCEDURE_PROJECT_(IA_gov.gpo.fdsys.CHRG-109hhrg24282).pdf) 
- commons: [File:AFRICAN ORGANIZATIONS AND INSTITUTIONS- CROSS-CONTINENTAL PROGRESS (IA gov.gpo.fdsys.CHRG-109shrg33724).pdf](https://commons.wikimedia.org/wiki/File:AFRICAN_ORGANIZATIONS_AND_INSTITUTIONS-_CROSS-CONTINENTAL_PROGRESS_(IA_gov.gpo.fdsys.CHRG-109shrg33724).pdf) 
- commons: [File:AGENTS OF OPPORTUNITY- RESPONDING TO THE THREAT OF CHEMICAL TERRORISM (IA gov.gpo.fdsys.CHRG-114hhrg94581).pdf](https://commons.wikimedia.org/wiki/File:AGENTS_OF_OPPORTUNITY-_RESPONDING_TO_THE_THREAT_OF_CHEMICAL_TERRORISM_(IA_gov.gpo.fdsys.CHRG-114hhrg94581).pdf) 
- commons: [File:AGRICULTURE, RURAL DEVELOPMENT, AND RELATED AGENCIES APPROPRIATIONS FOR FISCAL YEAR 2006 (IA gov.gpo.fdsys.CHRG-109shrg39104150).pdf](https://commons.wikimedia.org/wiki/File:AGRICULTURE,_RURAL_DEVELOPMENT,_AND_RELATED_AGENCIES_APPROPRIATIONS_FOR_FISCAL_YEAR_2006_(IA_gov.gpo.fdsys.CHRG-109shrg39104150).pdf) 
- commons: [File:AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES APPROPRIATIONS FOR 2001 (IA gov.gpo.fdsys.CHRG-106hh](https://commons.wikimedia.org/wiki/File:AGRICULTURE,_RURAL_DEVELOPMENT,_FOOD_AND_DRUG_ADMINISTRATION,_AND_RELATED_AGENCIES_APPROPRIATIONS_FOR_2001_(IA_gov.gpo.fdsys.CHRG-106hhrg64001).pdf) 
- commons: [File:AMENDING EXECUTIVE ORDER 12866- GOOD GOVERNANCE OR REGULATORY USURPATION? (IA gov.gpo.fdsys.CHRG-110hhrg33312).pdf](https://commons.wikimedia.org/wiki/File:AMENDING_EXECUTIVE_ORDER_12866-_GOOD_GOVERNANCE_OR_REGULATORY_USURPATION%3F_(IA_gov.gpo.fdsys.CHRG-110hhrg33312).pdf) 
- commons: [File:AMENDING EXECUTIVE ORDER 12866- GOOD GOVERNANCE OR REGULATORY USURPATION? PART I AND PART II (IA gov.gpo.fdsys.CHRG-110hhrg33105).pdf](https://commons.wikimedia.org/wiki/File:AMENDING_EXECUTIVE_ORDER_12866-_GOOD_GOVERNANCE_OR_REGULATORY_USURPATION%3F_PART_I_AND_PART_II_(IA_gov.gpo.fdsys.CHRG-110hhrg33105).pdf) 
- commons: [File:AMS instruction (IA CAT11098984020).pdf](https://commons.wikimedia.org/wiki/File:AMS_instruction_(IA_CAT11098984020).pdf) 
- commons: [File:ANNUAL OPEN HEARING ON CURRENT AND PROJECTED NATIONAL SECURITY THREATS TO THE UNITED STATES (IA gov.gpo.fdsys.CHRG-113shrg93211).pdf](https://commons.wikimedia.org/wiki/File:ANNUAL_OPEN_HEARING_ON_CURRENT_AND_PROJECTED_NATIONAL_SECURITY_THREATS_TO_THE_UNITED_STATES_(IA_gov.gpo.fdsys.CHRG-113shrg93211).pdf) 
- commons: [File:ANSWERING THE ADMINISTRATION'S CALL FOR POSTAL REFORM-PART I (IA gov.gpo.fdsys.CHRG-108hhrg93087).pdf](https://commons.wikimedia.org/wiki/File:ANSWERING_THE_ADMINISTRATION%27S_CALL_FOR_POSTAL_REFORM-PART_I_(IA_gov.gpo.fdsys.CHRG-108hhrg93087).pdf) 
- commons: [File:ARB Round 1 Factors 000895-000943.pdf](https://commons.wikimedia.org/wiki/File:ARB_Round_1_Factors_000895-000943.pdf) 2005
- commons: [File:ARB Transcript Set 6 20255-20496 (2005).pdf](https://commons.wikimedia.org/wiki/File:ARB_Transcript_Set_6_20255-20496_(2005).pdf) 2005
- commons: [File:ASSESSING EFFECTS OF U.S. SANCTIONS ON HEZBOLLAH'S JIHAD AL-BINA' (IA assessingeffects1094561249).pdf](https://commons.wikimedia.org/wiki/File:ASSESSING_EFFECTS_OF_U.S._SANCTIONS_ON_HEZBOLLAH%27S_JIHAD_AL-BINA%27_(IA_assessingeffects1094561249).pdf) 
- commons: [File:ASSESSING U.S. PREPAREDNESS AND RESPONSE IN THE ARCTIC- THE OPPORTUNITIES AND CHALLENGES OF INCREASED MARINE ACTIVITY (IA gov.gpo.fdsys](https://commons.wikimedia.org/wiki/File:ASSESSING_U.S._PREPAREDNESS_AND_RESPONSE_IN_THE_ARCTIC-_THE_OPPORTUNITIES_AND_CHALLENGES_OF_INCREASED_MARINE_ACTIVITY_(IA_gov.gpo.fdsys.CHRG-113shrg85764).pdf) 
- commons: [File:ASTM metric practice guide (IA astmmetricpracti102amer).pdf](https://commons.wikimedia.org/wiki/File:ASTM_metric_practice_guide_(IA_astmmetricpracti102amer).pdf) 
- commons: [File:Abandoned mine lands - a decade of progress reclaiming hardrock mines (IA abandonedminelan00unit).pdf](https://commons.wikimedia.org/wiki/File:Abandoned_mine_lands_-_a_decade_of_progress_reclaiming_hardrock_mines_(IA_abandonedminelan00unit).pdf) 
- commons: [File:Abraham Lincoln's vice presidents (IA abrahamlincolnsvajlinc).pdf](https://commons.wikimedia.org/wiki/File:Abraham_Lincoln%27s_vice_presidents_(IA_abrahamlincolnsvajlinc).pdf) 
- commons: [File:Abridged chronology of agriculture's part in the war (IA CAT1108450904).pdf](https://commons.wikimedia.org/wiki/File:Abridged_chronology_of_agriculture%27s_part_in_the_war_(IA_CAT1108450904).pdf) 
- commons: [File:Abridged chronology of agriculture's part in the war (IA CAT1108450910).pdf](https://commons.wikimedia.org/wiki/File:Abridged_chronology_of_agriculture%27s_part_in_the_war_(IA_CAT1108450910).pdf) 
- commons: [File:Abridged chronology of agriculture's part in the war (IA CAT1108450911).pdf](https://commons.wikimedia.org/wiki/File:Abridged_chronology_of_agriculture%27s_part_in_the_war_(IA_CAT1108450911).pdf) 
- commons: [File:Abridged list of federal laws applicable to agriculture (IA CAT1108451001).pdf](https://commons.wikimedia.org/wiki/File:Abridged_list_of_federal_laws_applicable_to_agriculture_(IA_CAT1108451001).pdf) 
- commons: [File:Abridged list of federal laws applicable to agriculture (IA CAT1108451002).pdf](https://commons.wikimedia.org/wiki/File:Abridged_list_of_federal_laws_applicable_to_agriculture_(IA_CAT1108451002).pdf) 
- commons: [File:Abridged list of federal laws applicable to agriculture (IA CAT1108451004).pdf](https://commons.wikimedia.org/wiki/File:Abridged_list_of_federal_laws_applicable_to_agriculture_(IA_CAT1108451004).pdf) 
- commons: [File:Abridged list of federal laws applicable to agriculture (IA CAT1108451009).pdf](https://commons.wikimedia.org/wiki/File:Abridged_list_of_federal_laws_applicable_to_agriculture_(IA_CAT1108451009).pdf) 
- commons: [File:Abridged list of federal laws applicable to agriculture (IA CAT1108451011).pdf](https://commons.wikimedia.org/wiki/File:Abridged_list_of_federal_laws_applicable_to_agriculture_(IA_CAT1108451011).pdf) 
- commons: [File:Acquiring combat capability through innovative uses of public private partnerships (IA acquiringcombatc1094538035).pdf](https://commons.wikimedia.org/wiki/File:Acquiring_combat_capability_through_innovative_uses_of_public_private_partnerships_(IA_acquiringcombatc1094538035).pdf) 
- commons: [File:Active projects report - research and demonstrations in health care financing (IA activeprojectsre20unit 4).pdf](https://commons.wikimedia.org/wiki/File:Active_projects_report_-_research_and_demonstrations_in_health_care_financing_(IA_activeprojectsre20unit_4).pdf) 
- commons: [File:Administrative History, Castillo De San Marcos Fort Matanzas, National Monuments-Florida... National Park Service, United States Depart](https://commons.wikimedia.org/wiki/File:Administrative_History,_Castillo_De_San_Marcos_Fort_Matanzas,_National_Monuments-Florida..._National_Park_Service,_United_States_Department_of_the_Interior..._July_1986_(IA_doi-report_i-292c-27-3).pdf) 
- commons: [File:Administrative Notes (IA 568391 07 20).pdf](https://commons.wikimedia.org/wiki/File:Administrative_Notes_(IA_568391_07_20).pdf) 
- commons: [File:Administrative Notes (IA 568391 10 15).pdf](https://commons.wikimedia.org/wiki/File:Administrative_Notes_(IA_568391_10_15).pdf) 
- commons: [File:Administrative action, final environmental impact,Section 4(f) statement- U.S. Department of Transportation, Federal Highway Administra](https://commons.wikimedia.org/wiki/File:Administrative_action,_final_environmental_impact,Section_4(f)_statement-_U.S._Department_of_Transportation,_Federal_Highway_Administration_and_Florida_Department_of_Transportation_-_USACE-p16021coll7-24756.pdf) 
- commons: [File:Administrative appeal decision, Alan Montane - Select Motor Car, file no. SAJ-2012-03337, Jacksonville District - USACE-p16021coll5-360](https://commons.wikimedia.org/wiki/File:Administrative_appeal_decision,_Alan_Montane_-_Select_Motor_Car,_file_no._SAJ-2012-03337,_Jacksonville_District_-_USACE-p16021coll5-36039.pdf) 
- commons: [File:Administrative appeal decision, Alton Davis, file no. SAW-2016-01017, Wilmington District - USACE-p16021coll5-36036.pdf](https://commons.wikimedia.org/wiki/File:Administrative_appeal_decision,_Alton_Davis,_file_no._SAW-2016-01017,_Wilmington_District_-_USACE-p16021coll5-36036.pdf) 
- commons: [File:Administrative appeal decision, Clean Water Act, JTR- file no. MVS-2011-00178, St. Louis District - USACE-p16021coll5-1322.pdf](https://commons.wikimedia.org/wiki/File:Administrative_appeal_decision,_Clean_Water_Act,_JTR-_file_no._MVS-2011-00178,_St._Louis_District_-_USACE-p16021coll5-1322.pdf) 
- commons: [File:Administrative appeal decision, Clean Water Act, KAS Farms & Managed Investments - MVP-2015-02665, St. Paul District - USACE-p16021coll](https://commons.wikimedia.org/wiki/File:Administrative_appeal_decision,_Clean_Water_Act,_KAS_Farms_%26_Managed_Investments_-_MVP-2015-02665,_St._Paul_District_-_USACE-p16021coll5-1390.pdf) 
- commons: [File:Administrative appeal decision, Clean Water Act, Marmaton Watershed District - file NWK-2014-00061-Ericson, Kansas City District - USAC](https://commons.wikimedia.org/wiki/File:Administrative_appeal_decision,_Clean_Water_Act,_Marmaton_Watershed_District_-_file_NWK-2014-00061-Ericson,_Kansas_City_District_-_USACE-p16021coll5-3803.pdf) 
- commons: [File:Administrative appeal decision, Clean Water Act, Missouri River commercial dredgers appeal, Missouri River, Kansas and Missouri, Kansas](https://commons.wikimedia.org/wiki/File:Administrative_appeal_decision,_Clean_Water_Act,_Missouri_River_commercial_dredgers_appeal,_Missouri_River,_Kansas_and_Missouri,_Kansas_City_and_St._Louis_Districts_-_USACE-p16021coll5-3800.pdf) 
- commons: [File:Administrative appeal decision, Cone's Folly Timber Farm, LLC., file no. SAW-2013-1234, Wilmington District - USACE-p16021coll9-2590.pd](https://commons.wikimedia.org/wiki/File:Administrative_appeal_decision,_Cone%27s_Folly_Timber_Farm,_LLC.,_file_no._SAW-2013-1234,_Wilmington_District_-_USACE-p16021coll9-2590.pdf) 
- commons: [File:Administrative appeal decision, David Sullivan, file. no. SAM-2011-1242-LET, Mobile District - USACE-p16021coll5-37133.pdf](https://commons.wikimedia.org/wiki/File:Administrative_appeal_decision,_David_Sullivan,_file._no._SAM-2011-1242-LET,_Mobile_District_-_USACE-p16021coll5-37133.pdf) 
- commons: [File:Administrative appeal decision, Mike Harris, file number SAW-2009-909, Wilmington District - USACE-p16021coll5-37186.pdf](https://commons.wikimedia.org/wiki/File:Administrative_appeal_decision,_Mike_Harris,_file_number_SAW-2009-909,_Wilmington_District_-_USACE-p16021coll5-37186.pdf) 
- commons: [File:Administrative appeal decision, River of Life, Inc., file. no. SAW-2012-599, Wilmington District - USACE-p16021coll5-37130.pdf](https://commons.wikimedia.org/wiki/File:Administrative_appeal_decision,_River_of_Life,_Inc.,_file._no._SAW-2012-599,_Wilmington_District_-_USACE-p16021coll5-37130.pdf) 
- commons: [File:Administrative appeal decision, Russell Fox, file number SAW-2009-909, Wilmington District - USACE-p16021coll5-37134.pdf](https://commons.wikimedia.org/wiki/File:Administrative_appeal_decision,_Russell_Fox,_file_number_SAW-2009-909,_Wilmington_District_-_USACE-p16021coll5-37134.pdf) 
- commons: [File:Administrative appeal decision, Wilda Taylor, file number SAW-2009-909, Wilmington District - USACE-p16021coll5-37185.pdf](https://commons.wikimedia.org/wiki/File:Administrative_appeal_decision,_Wilda_Taylor,_file_number_SAW-2009-909,_Wilmington_District_-_USACE-p16021coll5-37185.pdf) 
- commons: [File:Administrative control of funds- the anti-deficiency story ; a group research project ... in a Research Seminary in Comptrollership (B.](https://commons.wikimedia.org/wiki/File:Administrative_control_of_funds-_the_anti-deficiency_story_;_a_group_research_project_..._in_a_Research_Seminary_in_Comptrollership_(B.A.295)_..._(IA_administrativeco00teic).pdf) 
- commons: [File:Administrator's memorandum (IA CAT11084522010).pdf](https://commons.wikimedia.org/wiki/File:Administrator%27s_memorandum_(IA_CAT11084522010).pdf) 
- commons: [File:Administrator's memorandum (IA CAT11084522020).pdf](https://commons.wikimedia.org/wiki/File:Administrator%27s_memorandum_(IA_CAT11084522020).pdf) 
- commons: [File:Administrator's memorandum (IA CAT11084522031).pdf](https://commons.wikimedia.org/wiki/File:Administrator%27s_memorandum_(IA_CAT11084522031).pdf) 
- commons: [File:Administrator's memorandum (IA CAT11084522045).pdf](https://commons.wikimedia.org/wiki/File:Administrator%27s_memorandum_(IA_CAT11084522045).pdf) 
- commons: [File:Adoption of Bureau of Land Management prepared Environmental Assessmemt (EA) and Finding of No Significant Impact (FONSI)- City of Iona](https://commons.wikimedia.org/wiki/File:Adoption_of_Bureau_of_Land_Management_prepared_Environmental_Assessmemt_(EA)_and_Finding_of_No_Significant_Impact_(FONSI)-_City_of_Iona_water_system_improvements_project,_City_of_Iona,_Bonneville_..._-_USACE-p16021coll7-17700.pdf) 
- commons: [File:Aeronautics and Space Report of the President - 2017 Activities.pdf](https://commons.wikimedia.org/wiki/File:Aeronautics_and_Space_Report_of_the_President_-_2017_Activities.pdf) 2018
- commons: [File:Aeronautics and Space Report of the President - 2020 Activities.pdf](https://commons.wikimedia.org/wiki/File:Aeronautics_and_Space_Report_of_the_President_-_2020_Activities.pdf) 2021
- commons: [File:Aeronautics and Space Report of the President - 2023 Activities.pdf](https://commons.wikimedia.org/wiki/File:Aeronautics_and_Space_Report_of_the_President_-_2023_Activities.pdf) 2024
- commons: [File:Ag student (IA SER73925050211).pdf](https://commons.wikimedia.org/wiki/File:Ag_student_(IA_SER73925050211).pdf) 
- commons: [File:Agency financial report Fiscal Year 2011 (IA agencyfinancialr00unit 0).pdf](https://commons.wikimedia.org/wiki/File:Agency_financial_report_Fiscal_Year_2011_(IA_agencyfinancialr00unit_0).pdf) 
- commons: [File:Agency financial report Fiscal Year 2012 (IA agencyfinancialr00unit 1).pdf](https://commons.wikimedia.org/wiki/File:Agency_financial_report_Fiscal_Year_2012_(IA_agencyfinancialr00unit_1).pdf) 
- commons: [File:Agency financial report Fiscal Year 2014 (IA agencyfinancialr00unit 3).pdf](https://commons.wikimedia.org/wiki/File:Agency_financial_report_Fiscal_Year_2014_(IA_agencyfinancialr00unit_3).pdf) 
- commons: [File:Agendas for Senior Staff Meetings - 1982 (1) - DPLA - 091906b7943ea480927fa8afaf668788.pdf](https://commons.wikimedia.org/wiki/File:Agendas_for_Senior_Staff_Meetings_-_1982_(1)_-_DPLA_-_091906b7943ea480927fa8afaf668788.pdf) 
- commons: [File:Agno Executive Order No. 30 - 2021.pdf](https://commons.wikimedia.org/wiki/File:Agno_Executive_Order_No._30_-_2021.pdf) 2021-04-05
- commons: [File:Agno Executive Order No. 31 - 2021.pdf](https://commons.wikimedia.org/wiki/File:Agno_Executive_Order_No._31_-_2021.pdf) 2021-04-07
- commons: [File:Agno Executive Order No. 32 - 2021.pdf](https://commons.wikimedia.org/wiki/File:Agno_Executive_Order_No._32_-_2021.pdf) 2021-04-15
- commons: [File:Agno Executive Order No. 36 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Agno_Executive_Order_No._36_-_2020.pdf) 2020-06-09
- commons: [File:Agno Executive Order No. 39 - 2021.pdf](https://commons.wikimedia.org/wiki/File:Agno_Executive_Order_No._39_-_2021.pdf) 2021-06-18
- commons: [File:Agno Executive Order No. 40 - 2021.pdf](https://commons.wikimedia.org/wiki/File:Agno_Executive_Order_No._40_-_2021.pdf) 2021-07-29
- commons: [File:Agoo Executive Order No. 10 - 2016.pdf](https://commons.wikimedia.org/wiki/File:Agoo_Executive_Order_No._10_-_2016.pdf) 2016-07-05
- commons: [File:Agoo Executive Order No. 15 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Agoo_Executive_Order_No._15_-_2020.pdf) 2020-03-09
- commons: [File:Agoo Executive Order No. 17 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Agoo_Executive_Order_No._17_-_2020.pdf) 2020-03-09
- commons: [File:Agoo Executive Order No. 19 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Agoo_Executive_Order_No._19_-_2020.pdf) 2020-03-17
- commons: [File:Agoo Executive Order No. 22 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Agoo_Executive_Order_No._22_-_2020.pdf) 2020-03-18
- commons: [File:Agoo Executive Order No. 24 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Agoo_Executive_Order_No._24_-_2020.pdf) 2020-03-21
- commons: [File:Agreement between the Department of State and the Department of Agriculture on foreign agricultural acitivities (IA CAT10683525).pdf](https://commons.wikimedia.org/wiki/File:Agreement_between_the_Department_of_State_and_the_Department_of_Agriculture_on_foreign_agricultural_acitivities_(IA_CAT10683525).pdf) 
- commons: [File:Agricultural economics literature (IA agriculturalecon09unit).pdf](https://commons.wikimedia.org/wiki/File:Agricultural_economics_literature_(IA_agriculturalecon09unit).pdf) 
- commons: [File:Agricultural libraries information notes (IA CAT75654148170).pdf](https://commons.wikimedia.org/wiki/File:Agricultural_libraries_information_notes_(IA_CAT75654148170).pdf) 
- commons: [File:Agricultural marketing (IA SER71900025057).pdf](https://commons.wikimedia.org/wiki/File:Agricultural_marketing_(IA_SER71900025057).pdf) 
- commons: [File:Air Traffic Controllers - DPLA - 0733cc145cb338d77a987a174e22441f.pdf](https://commons.wikimedia.org/wiki/File:Air_Traffic_Controllers_-_DPLA_-_0733cc145cb338d77a987a174e22441f.pdf) 
- commons: [File:Air quality technical report for the Halligan water supply project environmental impact statement - USACE-p16021coll7-12847.pdf](https://commons.wikimedia.org/wiki/File:Air_quality_technical_report_for_the_Halligan_water_supply_project_environmental_impact_statement_-_USACE-p16021coll7-12847.pdf) 
- commons: [File:All About HRSA- A Guide for Hispanic Serving Institutions (IA allabouthrsaguid00heal).pdf](https://commons.wikimedia.org/wiki/File:All_About_HRSA-_A_Guide_for_Hispanic_Serving_Institutions_(IA_allabouthrsaguid00heal).pdf) 
- commons: [File:Almond Lake, NY - USACE-p16021coll11-1127.pdf](https://commons.wikimedia.org/wiki/File:Almond_Lake,_NY_-_USACE-p16021coll11-1127.pdf) 
- commons: [File:Almond Lake, NY - USACE-p16021coll11-1175.pdf](https://commons.wikimedia.org/wiki/File:Almond_Lake,_NY_-_USACE-p16021coll11-1175.pdf) 
- commons: [File:Almond Lake, NY - USACE-p16021coll11-2213.pdf](https://commons.wikimedia.org/wiki/File:Almond_Lake,_NY_-_USACE-p16021coll11-2213.pdf) 
- commons: [File:Almond Lake, NY - USACE-p16021coll11-3553.pdf](https://commons.wikimedia.org/wiki/File:Almond_Lake,_NY_-_USACE-p16021coll11-3553.pdf) 
- commons: [File:Alward 1 and Bridge Street levee rehabilitations, Pierce County, Washington- Finding of no significant impact - USACE-p16021coll7-9927.](https://commons.wikimedia.org/wiki/File:Alward_1_and_Bridge_Street_levee_rehabilitations,_Pierce_County,_Washington-_Finding_of_no_significant_impact_-_USACE-p16021coll7-9927.pdf) 
- commons: [File:Amended finding of no significant impact- Quillayute River federal navigation channel maintenance dredging 2009-14 La Push, Clallam Cou](https://commons.wikimedia.org/wiki/File:Amended_finding_of_no_significant_impact-_Quillayute_River_federal_navigation_channel_maintenance_dredging_2009-14_La_Push,_Clallam_County,_Washington_-_USACE-p16021coll7-11035.pdf) 
- commons: [File:Amending Executive Order No. 11647 Relating to Federal Regional Councils (Executive Order) - DPLA - a039bf0365e0aa2d1ba5ed9e538476f9.pd](https://commons.wikimedia.org/wiki/File:Amending_Executive_Order_No._11647_Relating_to_Federal_Regional_Councils_(Executive_Order)_-_DPLA_-_a039bf0365e0aa2d1ba5ed9e538476f9.pdf) 31 December 1975 date QS:P571,+1975-12-31T00:00:00Z/11 
- commons: [File:Amending Executive Order No. 11861, As Amended, Placing Certain Positions in Levels IV and V of the Executive Schedule - DPLA - 98d767f](https://commons.wikimedia.org/wiki/File:Amending_Executive_Order_No._11861,_As_Amended,_Placing_Certain_Positions_in_Levels_IV_and_V_of_the_Executive_Schedule_-_DPLA_-_98d767f43ee997576638d4ac2b65b2cf.pdf) 15 October 1975 date QS:P571,+1975-10-15T00:00:00Z/11 
- commons: [File:America's priceless heritage - cultural and fossil resources on public lands (IA americaspriceles00unit).pdf](https://commons.wikimedia.org/wiki/File:America%27s_priceless_heritage_-_cultural_and_fossil_resources_on_public_lands_(IA_americaspriceles00unit).pdf) 
- commons: [File:America's priceless heritage - cultural and fossil resources on public lands, Arizona (IA americaspriceles00unit 0).pdf](https://commons.wikimedia.org/wiki/File:America%27s_priceless_heritage_-_cultural_and_fossil_resources_on_public_lands,_Arizona_(IA_americaspriceles00unit_0).pdf) 
- commons: [File:America's priceless heritage - cultural and fossil resources on public lands, Idaho. (IA americaspriceles00unit 4).pdf](https://commons.wikimedia.org/wiki/File:America%27s_priceless_heritage_-_cultural_and_fossil_resources_on_public_lands,_Idaho._(IA_americaspriceles00unit_4).pdf) 
- commons: [File:America's priceless heritage - cultural and fossil resources on public lands, Nevada. (IA americaspriceles00unit 10).pdf](https://commons.wikimedia.org/wiki/File:America%27s_priceless_heritage_-_cultural_and_fossil_resources_on_public_lands,_Nevada._(IA_americaspriceles00unit_10).pdf) 
- commons: [File:America's priceless heritage - cultural and fossil resources on public lands, New Mexico (IA americaspriceles00unit 5).pdf](https://commons.wikimedia.org/wiki/File:America%27s_priceless_heritage_-_cultural_and_fossil_resources_on_public_lands,_New_Mexico_(IA_americaspriceles00unit_5).pdf) 
- commons: [File:American Samoa, a general report by the governor (IA cu31924028692543).pdf](https://commons.wikimedia.org/wiki/File:American_Samoa,_a_general_report_by_the_governor_(IA_cu31924028692543).pdf) 
- commons: [File:American national standard N43.2 - radiation safety for x-ray diffraction and fluorescence analysis equipment (IA americannational1111u](https://commons.wikimedia.org/wiki/File:American_national_standard_N43.2_-_radiation_safety_for_x-ray_diffraction_and_fluorescence_analysis_equipment_(IA_americannational1111unit).pdf) 
- commons: [File:American planning and civic annual (IA americanplanning14amerrich).pdf](https://commons.wikimedia.org/wiki/File:American_planning_and_civic_annual_(IA_americanplanning14amerrich).pdf) 
- commons: [File:American planning and civic annual (IA americanplanning20amerrich).pdf](https://commons.wikimedia.org/wiki/File:American_planning_and_civic_annual_(IA_americanplanning20amerrich).pdf) 
- commons: [File:American tobacco types, uses, and markets (IA americantobacco249gage).pdf](https://commons.wikimedia.org/wiki/File:American_tobacco_types,_uses,_and_markets_(IA_americantobacco249gage).pdf) 
- commons: [File:An Act of August 10, 1988, Public Law 100-383, 102 STAT 903, to Implement Recommendations of the Commission on Wartime Relocation and I](https://commons.wikimedia.org/wiki/File:An_Act_of_August_10,_1988,_Public_Law_100-383,_102_STAT_903,_to_Implement_Recommendations_of_the_Commission_on_Wartime_Relocation_and_Internment_of_Civilians_-_DPLA_-_96fa2dfd1e611ca8fe6a35fbe704cf8c.pdf) 1988-08-10
- commons: [File:An Analysis of the DoD Certification and Accreditation Process (IA ananalysisofdodc1094545357).pdf](https://commons.wikimedia.org/wiki/File:An_Analysis_of_the_DoD_Certification_and_Accreditation_Process_(IA_ananalysisofdodc1094545357).pdf) 
- commons: [File:An Analysis of the outdoor recreation and wilderness situation in the United States, 1989-2040 - a technical document supporting the 19](https://commons.wikimedia.org/wiki/File:An_Analysis_of_the_outdoor_recreation_and_wilderness_situation_in_the_United_States,_1989-2040_-_a_technical_document_supporting_the_1989_RPA_Assessment_(IA_CAT91959391).pdf) 
- commons: [File:An act making consolidated appropriations for the fiscal year ending September 30, 2000, and for other purposes (IA actmakingconsoli00u](https://commons.wikimedia.org/wiki/File:An_act_making_consolidated_appropriations_for_the_fiscal_year_ending_September_30,_2000,_and_for_other_purposes_(IA_actmakingconsoli00unit).pdf) 
- commons: [File:An act to provide that meetings of Government agencies shall be open to the public, and for other purposes (IA acttoprovidethat00unit).](https://commons.wikimedia.org/wiki/File:An_act_to_provide_that_meetings_of_Government_agencies_shall_be_open_to_the_public,_and_for_other_purposes_(IA_acttoprovidethat00unit).pdf) 
- commons: [File:An analysis of Department of Defense financial and acquisition policies in support of military contingency requirements. (IA analysisof](https://commons.wikimedia.org/wiki/File:An_analysis_of_Department_of_Defense_financial_and_acquisition_policies_in_support_of_military_contingency_requirements._(IA_analysisofdepart00proc).pdf) 
- commons: [File:An analysis of accrual accounting and cost-based budgeting with applications in the Atomic Energy Commission and Department of Defense.](https://commons.wikimedia.org/wiki/File:An_analysis_of_accrual_accounting_and_cost-based_budgeting_with_applications_in_the_Atomic_Energy_Commission_and_Department_of_Defense._(IA_analysisofaccrua00fors).pdf) 
- commons: [File:An analysis of the Department of Defense's use of other transaction authority (10 U.S.C. 2371) (IA annalysisofdepar1094549391).pdf](https://commons.wikimedia.org/wiki/File:An_analysis_of_the_Department_of_Defense%27s_use_of_other_transaction_authority_(10_U.S.C._2371)_(IA_annalysisofdepar1094549391).pdf) 
- commons: [File:An analysis of the Navy's alternative disputes resolution program (IA annalysisofnavys1094539320).pdf](https://commons.wikimedia.org/wiki/File:An_analysis_of_the_Navy%27s_alternative_disputes_resolution_program_(IA_annalysisofnavys1094539320).pdf) 
- commons: [File:An analysis of the effectiveness evaluation measurements for Coast Guard general law enforcement helicopters. (IA analysisofeffect00bro](https://commons.wikimedia.org/wiki/File:An_analysis_of_the_effectiveness_evaluation_measurements_for_Coast_Guard_general_law_enforcement_helicopters._(IA_analysisofeffect00brok).pdf) 
- commons: [File:An analysis of the impact of non-DOD conference policy change (IA annalysisofimpac1094550580).pdf](https://commons.wikimedia.org/wiki/File:An_analysis_of_the_impact_of_non-DOD_conference_policy_change_(IA_annalysisofimpac1094550580).pdf) 
- commons: [File:An analysis of the operational level in the combined intermediate and depot level maintenance concept for airborne missile systems. (IA](https://commons.wikimedia.org/wiki/File:An_analysis_of_the_operational_level_in_the_combined_intermediate_and_depot_level_maintenance_concept_for_airborne_missile_systems._(IA_analysisofoperat00klim).pdf) 
- commons: [File:An analysis of the reasons why nonferrous foundry subcontractors refuse to participate in DOD business. (IA analysisofreason00scha).pdf](https://commons.wikimedia.org/wiki/File:An_analysis_of_the_reasons_why_nonferrous_foundry_subcontractors_refuse_to_participate_in_DOD_business._(IA_analysisofreason00scha).pdf) 
- commons: [File:An analysis of the value of Naval Air Combat Readiness Training. (IA analysisofvalueo00dunn).pdf](https://commons.wikimedia.org/wiki/File:An_analysis_of_the_value_of_Naval_Air_Combat_Readiness_Training._(IA_analysisofvalueo00dunn).pdf) 
- commons: [File:An archaeological research design project for the Abo Oil and Gas Field, southeastern New Mexico (IA archaeologicalre00kemr).pdf](https://commons.wikimedia.org/wiki/File:An_archaeological_research_design_project_for_the_Abo_Oil_and_Gas_Field,_southeastern_New_Mexico_(IA_archaeologicalre00kemr).pdf) 
- commons: [File:An assessment of vulnerabilities for ship-based control systems (IA anssessmentofvul109454646).pdf](https://commons.wikimedia.org/wiki/File:An_assessment_of_vulnerabilities_for_ship-based_control_systems_(IA_anssessmentofvul109454646).pdf) 
- commons: [File:An examination of acquisition ethical dilemmas- case studies for ethics training (IA anexaminationofc109457456).pdf](https://commons.wikimedia.org/wiki/File:An_examination_of_acquisition_ethical_dilemmas-_case_studies_for_ethics_training_(IA_anexaminationofc109457456).pdf) 
- commons: [File:An examination of alternative methods for employing booms to contain oil spills in Navy harbors. (IA examinationofalt00lars).pdf](https://commons.wikimedia.org/wiki/File:An_examination_of_alternative_methods_for_employing_booms_to_contain_oil_spills_in_Navy_harbors._(IA_examinationofalt00lars).pdf) 
- commons: [File:An identification and possible method of collection-reporting of under-reported small business utilization data for the Space and Naval](https://commons.wikimedia.org/wiki/File:An_identification_and_possible_method_of_collection-reporting_of_under-reported_small_business_utilization_data_for_the_Space_and_Naval_Warfare_Systems_Command_(IA_anidentification10945969).pdf) 
- commons: [File:An inquiry concerning A fourth service of supply. (IA inquiryconcernin00smil).pdf](https://commons.wikimedia.org/wiki/File:An_inquiry_concerning_A_fourth_service_of_supply._(IA_inquiryconcernin00smil).pdf) 
- commons: [File:An introduction to computer security - the NIST handbook (IA introductiontoco80012gutt).pdf](https://commons.wikimedia.org/wiki/File:An_introduction_to_computer_security_-_the_NIST_handbook_(IA_introductiontoco80012gutt).pdf) 
- commons: [File:An investigation into fraud and unethical conduct in the construction industry. (IA investigationint00gent).pdf](https://commons.wikimedia.org/wiki/File:An_investigation_into_fraud_and_unethical_conduct_in_the_construction_industry._(IA_investigationint00gent).pdf) 
- commons: [File:An isolated empire - a history of northwest Colorado (IA isolatedempirehi00athe 2).pdf](https://commons.wikimedia.org/wiki/File:An_isolated_empire_-_a_history_of_northwest_Colorado_(IA_isolatedempirehi00athe_2).pdf) 
- commons: [File:An open letter to the Honorable Lyman J. Gage, secretary of the Treasury (IA openlettertohono00mcan 1).pdf](https://commons.wikimedia.org/wiki/File:An_open_letter_to_the_Honorable_Lyman_J._Gage,_secretary_of_the_Treasury_(IA_openlettertohono00mcan_1).pdf) 
- commons: [File:Anacostia watershed restoration, Montgomery County, MD - USACE-p16021coll11-2054.pdf](https://commons.wikimedia.org/wiki/File:Anacostia_watershed_restoration,_Montgomery_County,_MD_-_USACE-p16021coll11-2054.pdf) 
- commons: [File:Anacostia watershed restoration, Montgomery County, MD - USACE-p16021coll11-4381.pdf](https://commons.wikimedia.org/wiki/File:Anacostia_watershed_restoration,_Montgomery_County,_MD_-_USACE-p16021coll11-4381.pdf) 
- commons: [File:Anacostia watershed restoration, Montgomery County, MD - USACE-p16021coll11-452.pdf](https://commons.wikimedia.org/wiki/File:Anacostia_watershed_restoration,_Montgomery_County,_MD_-_USACE-p16021coll11-452.pdf) 
- commons: [File:Anacostia watershed restoration, Montgomery County, MD - USACE-p16021coll11-5132.pdf](https://commons.wikimedia.org/wiki/File:Anacostia_watershed_restoration,_Montgomery_County,_MD_-_USACE-p16021coll11-5132.pdf) 
- commons: [File:Anacostia watershed restoration, Montgomery County, MD - USACE-p16021coll11-5686.pdf](https://commons.wikimedia.org/wiki/File:Anacostia_watershed_restoration,_Montgomery_County,_MD_-_USACE-p16021coll11-5686.pdf) 
- commons: [File:Anacostia watershed restoration, Prince George's County, MD - USACE-p16021coll11-2288.pdf](https://commons.wikimedia.org/wiki/File:Anacostia_watershed_restoration,_Prince_George%27s_County,_MD_-_USACE-p16021coll11-2288.pdf) 
- commons: [File:Analysis of NPS contracting service quality (IA analysisofnpscon1094544520).pdf](https://commons.wikimedia.org/wiki/File:Analysis_of_NPS_contracting_service_quality_(IA_analysisofnpscon1094544520).pdf) 
- commons: [File:Analysis of Naval Facilities Engineering Command's (NAVFAC) contracting processes using the Contract Management Maturity Model (CMMM) (](https://commons.wikimedia.org/wiki/File:Analysis_of_Naval_Facilities_Engineering_Command%27s_(NAVFAC)_contracting_processes_using_the_Contract_Management_Maturity_Model_(CMMM)_(IA_analysisofnavalf109452466).pdf) 
- commons: [File:Analysis of United States Marine Corps operations in support of humanitarian assistance and disaster relief (IA analysisofunited1094538](https://commons.wikimedia.org/wiki/File:Analysis_of_United_States_Marine_Corps_operations_in_support_of_humanitarian_assistance_and_disaster_relief_(IA_analysisofunited1094538954).pdf) 
- commons: [File:Analysis of design-build processes, best practices, and applications to the Department of Defense (IA analysisofdesign1094510123).pdf](https://commons.wikimedia.org/wiki/File:Analysis_of_design-build_processes,_best_practices,_and_applications_to_the_Department_of_Defense_(IA_analysisofdesign1094510123).pdf) 
- commons: [File:Analysis of lithic artifacts from the Gila National Forest near Reserve, New Mexico, and an archeological survey of the Reserve land ex](https://commons.wikimedia.org/wiki/File:Analysis_of_lithic_artifacts_from_the_Gila_National_Forest_near_Reserve,_New_Mexico,_and_an_archeological_survey_of_the_Reserve_land_exchanges,_Gila_National_Forest,_New_Mexico_(IA_CAT80727677).pdf) 
- commons: [File:Analysis of the Department of Defense Homeland Security Support Organization (IA analysisofdepart109454135).pdf](https://commons.wikimedia.org/wiki/File:Analysis_of_the_Department_of_Defense_Homeland_Security_Support_Organization_(IA_analysisofdepart109454135).pdf) 
- commons: [File:And Millwood Lake, Little River, Arkansas, operation and maintenance program - USACE-p16021coll7-18387.pdf](https://commons.wikimedia.org/wiki/File:And_Millwood_Lake,_Little_River,_Arkansas,_operation_and_maintenance_program_-_USACE-p16021coll7-18387.pdf) 
- commons: [File:Andrews Grazing Management Program - draft environmental impact statement (IA andrewsgrazingma06unit).pdf](https://commons.wikimedia.org/wiki/File:Andrews_Grazing_Management_Program_-_draft_environmental_impact_statement_(IA_andrewsgrazingma06unit).pdf) 
- commons: [File:Animal Care annual report of activities - fiscal year 2007 (IA CAT31019450).pdf](https://commons.wikimedia.org/wiki/File:Animal_Care_annual_report_of_activities_-_fiscal_year_2007_(IA_CAT31019450).pdf) 
- commons: [File:Annex F, invasive and nuisance species management plan - USACE-p16021coll7-20060.pdf](https://commons.wikimedia.org/wiki/File:Annex_F,_invasive_and_nuisance_species_management_plan_-_USACE-p16021coll7-20060.pdf) 
- commons: [File:Annex F, invasive and nuisance species management plan - USACE-p16021coll7-20853.pdf](https://commons.wikimedia.org/wiki/File:Annex_F,_invasive_and_nuisance_species_management_plan_-_USACE-p16021coll7-20853.pdf) 
- commons: [File:Annex F- Invasive and nuisance species management plan - USACE-p16021coll7-15193.pdf](https://commons.wikimedia.org/wiki/File:Annex_F-_Invasive_and_nuisance_species_management_plan_-_USACE-p16021coll7-15193.pdf) 
- commons: [File:Annex G, CEPP PACR invasive and nuisance species management plan - USACE-p16021coll7-7182.pdf](https://commons.wikimedia.org/wiki/File:Annex_G,_CEPP_PACR_invasive_and_nuisance_species_management_plan_-_USACE-p16021coll7-7182.pdf) 
- commons: [File:Annex to Executive Order 13694.pdf](https://commons.wikimedia.org/wiki/File:Annex_to_Executive_Order_13694.pdf) 2016-12-29
- commons: [File:Annual Report of the Commissioner of Education (IA annualreportofco00unit 6).pdf](https://commons.wikimedia.org/wiki/File:Annual_Report_of_the_Commissioner_of_Education_(IA_annualreportofco00unit_6).pdf) 
- commons: [File:Annual Report of the Department of the Interior (IA annualreportofde00unit).pdf](https://commons.wikimedia.org/wiki/File:Annual_Report_of_the_Department_of_the_Interior_(IA_annualreportofde00unit).pdf) 
- commons: [File:Annual Report of the Secretary of the Interior (IA annualreportofse00unit 7).pdf](https://commons.wikimedia.org/wiki/File:Annual_Report_of_the_Secretary_of_the_Interior_(IA_annualreportofse00unit_7).pdf) 
- commons: [File:Annual Report of the U.S. Department of Health, Education and Welfare (IA annualreportofus00unit 1).pdf](https://commons.wikimedia.org/wiki/File:Annual_Report_of_the_U.S._Department_of_Health,_Education_and_Welfare_(IA_annualreportofus00unit_1).pdf) 
- commons: [File:Annual Report- U.S. Department of Education (IA annualreportusde00unit 1).pdf](https://commons.wikimedia.org/wiki/File:Annual_Report-_U.S._Department_of_Education_(IA_annualreportusde00unit_1).pdf) 
- commons: [File:Annual Report- U.S. Department of Education (IA annualreportusde00unit 8).pdf](https://commons.wikimedia.org/wiki/File:Annual_Report-_U.S._Department_of_Education_(IA_annualreportusde00unit_8).pdf) 
- commons: [File:Annual report (IA aaf4005.1917.001.umich.edu).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_(IA_aaf4005.1917.001.umich.edu).pdf) 
- commons: [File:Annual report (IA annualreport46unituoft).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_(IA_annualreport46unituoft).pdf) 
- commons: [File:Annual report (United States. Fixed Nitrogen Research Laboratory) (IA CAT11088369001).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_(United_States._Fixed_Nitrogen_Research_Laboratory)_(IA_CAT11088369001).pdf) 
- commons: [File:Annual report (United States. Fixed Nitrogen Research Laboratory) (IA CAT11088369002).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_(United_States._Fixed_Nitrogen_Research_Laboratory)_(IA_CAT11088369002).pdf) 
- commons: [File:Annual report - Eastern States fiscal year 2004 (IA annualreporteast00unit 0).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_-_Eastern_States_fiscal_year_2004_(IA_annualreporteast00unit_0).pdf) 
- commons: [File:Annual report - Franklin County (IA CAT85267425013).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_-_Franklin_County_(IA_CAT85267425013).pdf) 
- commons: [File:Annual report - Franklin County (IA CAT85267425017).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_-_Franklin_County_(IA_CAT85267425017).pdf) 
- commons: [File:Annual report - U.S. National Arboretum (IA CAT76677425006).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_-_U.S._National_Arboretum_(IA_CAT76677425006).pdf) 
- commons: [File:Annual report FY 82 of the Chief of Engineers on Civil Works activities - USACE-p16021coll6-638.pdf](https://commons.wikimedia.org/wiki/File:Annual_report_FY_82_of_the_Chief_of_Engineers_on_Civil_Works_activities_-_USACE-p16021coll6-638.pdf) 
- commons: [File:Annual report covering military activities of the Office of the Chief of Engineers for the fiscal year ending June 30, 1927 - USACE-p16](https://commons.wikimedia.org/wiki/File:Annual_report_covering_military_activities_of_the_Office_of_the_Chief_of_Engineers_for_the_fiscal_year_ending_June_30,_1927_-_USACE-p16021coll6-1862.pdf) 
- commons: [File:Annual report covering military activities of the Office of the Chief of Engineers for the fiscal year ending June 30, 1928 - USACE-p16](https://commons.wikimedia.org/wiki/File:Annual_report_covering_military_activities_of_the_Office_of_the_Chief_of_Engineers_for_the_fiscal_year_ending_June_30,_1928_-_USACE-p16021coll6-1863.pdf) 
- commons: [File:Annual report fiscal year 1994 of the Secretary of the Army on Civil Works activities (1 October 1993 - 30 September 1994), volume II -](https://commons.wikimedia.org/wiki/File:Annual_report_fiscal_year_1994_of_the_Secretary_of_the_Army_on_Civil_Works_activities_(1_October_1993_-_30_September_1994),_volume_II_-_USACE-p16021coll6-793.pdf) 
- commons: [File:Annual report fiscal year 1995 of the Secretary of the Army on Civil Works activities (1 October 1994 - 30 September 1995), volume II -](https://commons.wikimedia.org/wiki/File:Annual_report_fiscal_year_1995_of_the_Secretary_of_the_Army_on_Civil_Works_activities_(1_October_1994_-_30_September_1995),_volume_II_-_USACE-p16021coll6-810.pdf) 
- commons: [File:Annual report fiscal year 1996 of the Secretary of the Army on Civil Works activities (1 October 1995 - 30 September 1996), volume II -](https://commons.wikimedia.org/wiki/File:Annual_report_fiscal_year_1996_of_the_Secretary_of_the_Army_on_Civil_Works_activities_(1_October_1995_-_30_September_1996),_volume_II_-_USACE-p16021coll6-827.pdf) 
- commons: [File:Annual report fiscal year 1997 of the Secretary of the Army on Civil Works activities (1 October 1996 - 30 September 1997), volume II -](https://commons.wikimedia.org/wiki/File:Annual_report_fiscal_year_1997_of_the_Secretary_of_the_Army_on_Civil_Works_activities_(1_October_1996_-_30_September_1997),_volume_II_-_USACE-p16021coll6-840.pdf) 
- commons: [File:Annual report fiscal year 1998 of the Secretary of the Army on Civil Works activities (1 October 1997 - 30 September 1998), volume II -](https://commons.wikimedia.org/wiki/File:Annual_report_fiscal_year_1998_of_the_Secretary_of_the_Army_on_Civil_Works_activities_(1_October_1997_-_30_September_1998),_volume_II_-_USACE-p16021coll6-854.pdf) 
- commons: [File:Annual report fiscal year 2003 of the Secretary of the Army on Civil Works activities (1 October 2002 - 30 September 2003) - USACE-p160](https://commons.wikimedia.org/wiki/File:Annual_report_fiscal_year_2003_of_the_Secretary_of_the_Army_on_Civil_Works_activities_(1_October_2002_-_30_September_2003)_-_USACE-p16021coll6-310.pdf) 
- commons: [File:Annual report fiscal year 2005 of the Secretary of the Army on Civil Works activities (1 October 2004 - 30 September 2005) - USACE-p160](https://commons.wikimedia.org/wiki/File:Annual_report_fiscal_year_2005_of_the_Secretary_of_the_Army_on_Civil_Works_activities_(1_October_2004_-_30_September_2005)_-_USACE-p16021coll6-337.pdf) 
- commons: [File:Annual report fiscal year 2007 of the Secretary of the Army on Civil Works activities (1 October 2006 - 30 September 2007) - USACE-p160](https://commons.wikimedia.org/wiki/File:Annual_report_fiscal_year_2007_of_the_Secretary_of_the_Army_on_Civil_Works_activities_(1_October_2006_-_30_September_2007)_-_USACE-p16021coll6-365.pdf) 
- commons: [File:Annual report fiscal year 2008 of the Secretary of the Army on Civil Works activities (1 October 2007 - 30 September 2008) - USACE-p160](https://commons.wikimedia.org/wiki/File:Annual_report_fiscal_year_2008_of_the_Secretary_of_the_Army_on_Civil_Works_activities_(1_October_2007_-_30_September_2008)_-_USACE-p16021coll6-379.pdf) 
- commons: [File:Annual report fiscal year 2009 of the Secretary of the Army on Civil Works activities (1 October 2008 - 30 September 2009) - USACE-p160](https://commons.wikimedia.org/wiki/File:Annual_report_fiscal_year_2009_of_the_Secretary_of_the_Army_on_Civil_Works_activities_(1_October_2008_-_30_September_2009)_-_USACE-p16021coll6-393.pdf) 
- commons: [File:Annual report fiscal year 2011 of the Secretary of the Army on Civil Works activities (1 October 2010 - 30 September 2011) - USACE-p160](https://commons.wikimedia.org/wiki/File:Annual_report_fiscal_year_2011_of_the_Secretary_of_the_Army_on_Civil_Works_activities_(1_October_2010_-_30_September_2011)_-_USACE-p16021coll6-1542.pdf) 
- commons: [File:Annual report fiscal year 2011 of the Secretary of the Army on Civil Works activities (1 October 2010 - 30 September 2011) - USACE-p160](https://commons.wikimedia.org/wiki/File:Annual_report_fiscal_year_2011_of_the_Secretary_of_the_Army_on_Civil_Works_activities_(1_October_2010_-_30_September_2011)_-_USACE-p16021coll6-1545.pdf) 
- commons: [File:Annual report of the Administrator (IA CAT11115774).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Administrator_(IA_CAT11115774).pdf) 
- commons: [File:Annual report of the Board of Indian Commissioners (IA annualreportofbo33unitrich).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Board_of_Indian_Commissioners_(IA_annualreportofbo33unitrich).pdf) 
- commons: [File:Annual report of the Board of Indian commissioners to the secretary of the interior .. (IA annualreportofbo02unitrich).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Board_of_Indian_commissioners_to_the_secretary_of_the_interior_.._(IA_annualreportofbo02unitrich).pdf) 
- commons: [File:Annual report of the Board of Regents of the Smithsonian Institution (IA annualreportofbo1919smithso).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Board_of_Regents_of_the_Smithsonian_Institution_(IA_annualreportofbo1919smithso).pdf) 
- commons: [File:Annual report of the Bureau of American Ethnology to the Secretary of the Smithsonian Institution (IA annualreportofbu0000smit l8e8).pd](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Bureau_of_American_Ethnology_to_the_Secretary_of_the_Smithsonian_Institution_(IA_annualreportofbu0000smit_l8e8).pdf) 
- commons: [File:Annual report of the Bureau of American Ethnology to the Secretary of the Smithsonian Institution (IA annualreportofbu1911smit).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Bureau_of_American_Ethnology_to_the_Secretary_of_the_Smithsonian_Institution_(IA_annualreportofbu1911smit).pdf) 
- commons: [File:Annual report of the Bureau of American Ethnology to the Secretary of the Smithsonian Institution (IA annualreportofbu3319smit).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Bureau_of_American_Ethnology_to_the_Secretary_of_the_Smithsonian_Institution_(IA_annualreportofbu3319smit).pdf) 
- commons: [File:Annual report of the Bureau of American Ethnology to the Secretary of the Smithsonian Institution (IA annualreportofbu33smit).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Bureau_of_American_Ethnology_to_the_Secretary_of_the_Smithsonian_Institution_(IA_annualreportofbu33smit).pdf) 
- commons: [File:Annual report of the Commissioner of Indian Affairs, for the year 1872 (IA usindianaffairs72usdorich).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Commissioner_of_Indian_Affairs,_for_the_year_1872_(IA_usindianaffairs72usdorich).pdf) 
- commons: [File:Annual report of the Commissioner of Indian Affairs, for the year 1879 (IA usindianaffairs79usdorich).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Commissioner_of_Indian_Affairs,_for_the_year_1879_(IA_usindianaffairs79usdorich).pdf) 
- commons: [File:Annual report of the Farm Credit Administration. (IA CAT84381087001).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Farm_Credit_Administration._(IA_CAT84381087001).pdf) 
- commons: [File:Annual report of the Farm Credit Administration. (IA CAT84381087003).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Farm_Credit_Administration._(IA_CAT84381087003).pdf) 
- commons: [File:Annual report of the Farm Credit Administration. (IA CAT84381087006).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Farm_Credit_Administration._(IA_CAT84381087006).pdf) 
- commons: [File:Annual report of the Farm Credit Administration. (IA CAT84381087010).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Farm_Credit_Administration._(IA_CAT84381087010).pdf) 
- commons: [File:Annual report of the Farm Credit Administration. (IA CAT84381087011).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Farm_Credit_Administration._(IA_CAT84381087011).pdf) 
- commons: [File:Annual report of the Office of experiment stations for the year ended June 30, 1908 (IA CAT11088335009).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Office_of_experiment_stations_for_the_year_ended_June_30,_1908_(IA_CAT11088335009).pdf) 
- commons: [File:Annual report of the Secretary of the Interior for the fiscal year ended June 30, 1934 (IA annualreportofsec00unit).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Secretary_of_the_Interior_for_the_fiscal_year_ended_June_30,_1934_(IA_annualreportofsec00unit).pdf) 
- commons: [File:Annual report of the Secretary of the Interior for the fiscal year ended June 30.. (IA annualreportofse8227unit).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Secretary_of_the_Interior_for_the_fiscal_year_ended_June_30.._(IA_annualreportofse8227unit).pdf) 
- commons: [File:Annual report of the Secretary of the Interior for the fiscal year ended June 30.. (IA annualreportofse8230unit).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Secretary_of_the_Interior_for_the_fiscal_year_ended_June_30.._(IA_annualreportofse8230unit).pdf) 
- commons: [File:Annual report of the Secretary of the Interior for the fiscal year ended June 30.. (IA annualreportofse8236unit).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Secretary_of_the_Interior_for_the_fiscal_year_ended_June_30.._(IA_annualreportofse8236unit).pdf) 
- commons: [File:Annual report of the Street Dept. of the City of Boston (IA annualreportofst1908bost).pdf](https://commons.wikimedia.org/wiki/File:Annual_report_of_the_Street_Dept._of_the_City_of_Boston_(IA_annualreportofst1908bost).pdf) 
- commons: [File:Annual report on Medicare for fiscal year ... - communication from Secretary, Health, Education, and Welfare, transmitting the ... annu](https://commons.wikimedia.org/wiki/File:Annual_report_on_Medicare_for_fiscal_year_..._-_communication_from_Secretary,_Health,_Education,_and_Welfare,_transmitting_the_..._annual_report_on_Medicare_.._(IA_annualreportonme00unit_1).pdf) 
- commons: [File:Annual reports War Department, fiscal year ended June 30, 1927- Report of the Secretary of War to the President, 1927 - USACE-p16021col](https://commons.wikimedia.org/wiki/File:Annual_reports_War_Department,_fiscal_year_ended_June_30,_1927-_Report_of_the_Secretary_of_War_to_the_President,_1927_-_USACE-p16021coll5-38199.pdf) 
- commons: [File:Annual reports War Department, fiscal year ended June 30, 1932- Report of the Secretary of War to the President, 1932 - USACE-p16021col](https://commons.wikimedia.org/wiki/File:Annual_reports_War_Department,_fiscal_year_ended_June_30,_1932-_Report_of_the_Secretary_of_War_to_the_President,_1932_-_USACE-p16021coll5-38206.pdf) 
- commons: [File:Annual reports War Department, fiscal year ended June 30, 1934- Report of the Secretary of War to the President, 1934 - USACE-p16021col](https://commons.wikimedia.org/wiki/File:Annual_reports_War_Department,_fiscal_year_ended_June_30,_1934-_Report_of_the_Secretary_of_War_to_the_President,_1934_-_USACE-p16021coll5-38212.pdf) 
- commons: [File:Annual reports of the Department of Agriculture for the fiscal year ended ... - report of the Secretary of Agriculture, miscellaneous r](https://commons.wikimedia.org/wiki/File:Annual_reports_of_the_Department_of_Agriculture_for_the_fiscal_year_ended_..._-_report_of_the_Secretary_of_Agriculture,_miscellaneous_reports_(IA_annualreportsofd1901unitrich).pdf) 
- commons: [File:Annual reports of the War Department (IA annualreportswa33deptgoog).pdf](https://commons.wikimedia.org/wiki/File:Annual_reports_of_the_War_Department_(IA_annualreportswa33deptgoog).pdf) 
- commons: [File:Annual reports, War Department, fiscal year ended June 30, 1926- Report of the Secretary of War to the President, 1926 - USACE-p16021co](https://commons.wikimedia.org/wiki/File:Annual_reports,_War_Department,_fiscal_year_ended_June_30,_1926-_Report_of_the_Secretary_of_War_to_the_President,_1926_-_USACE-p16021coll5-38197.pdf) 
- commons: [File:Anticipated socio-economic impacts in the Uintah basin of Utah resulting from oil shale development in the area (IA anticipatedsociolog](https://commons.wikimedia.org/wiki/File:Anticipated_socio-economic_impacts_in_the_Uintah_basin_of_Utah_resulting_from_oil_shale_development_in_the_area_(IA_anticipatedsociologa_0).pdf) 
- commons: [File:Appendices A through J - USACE-p16021coll9-2585.pdf](https://commons.wikimedia.org/wiki/File:Appendices_A_through_J_-_USACE-p16021coll9-2585.pdf) 
- commons: [File:Appendices I through IV - USACE-p16021coll7-12278.pdf](https://commons.wikimedia.org/wiki/File:Appendices_I_through_IV_-_USACE-p16021coll7-12278.pdf) 
- commons: [File:Appendix 7 - USACE-p16021coll7-8092.pdf](https://commons.wikimedia.org/wiki/File:Appendix_7_-_USACE-p16021coll7-8092.pdf) 
- commons: [File:Appendix A, legislative history of Little Goose project - USACE-p16021coll7-16782.pdf](https://commons.wikimedia.org/wiki/File:Appendix_A,_legislative_history_of_Little_Goose_project_-_USACE-p16021coll7-16782.pdf) 
- commons: [File:Appendix A- Environmental correspondence - USACE-p16021coll7-7978.pdf](https://commons.wikimedia.org/wiki/File:Appendix_A-_Environmental_correspondence_-_USACE-p16021coll7-7978.pdf) 
- commons: [File:Appendix A- Pertinent correspondence - USACE-p16021coll7-24955.pdf](https://commons.wikimedia.org/wiki/File:Appendix_A-_Pertinent_correspondence_-_USACE-p16021coll7-24955.pdf) 
- commons: [File:Appendix A- Pertinent correspondence - USACE-p16021coll7-4678.pdf](https://commons.wikimedia.org/wiki/File:Appendix_A-_Pertinent_correspondence_-_USACE-p16021coll7-4678.pdf) 
- commons: [File:Appendix A- Pertinent correspondence- Draft Environmental Assessment (EA) for maintenance dredging and dredged material placement for M](https://commons.wikimedia.org/wiki/File:Appendix_A-_Pertinent_correspondence-_Draft_Environmental_Assessment_(EA)_for_maintenance_dredging_and_dredged_material_placement_for_Miami_Harbor_Navigation_Project_at_Port_Miami_in_Miami-Dade_C_..._-_USACE-p16021coll7-21623.pdf) 
- commons: [File:Appendix A- Preliminary Section 7(a) evaluation - USACE-p16021coll7-2366.pdf](https://commons.wikimedia.org/wiki/File:Appendix_A-_Preliminary_Section_7(a)_evaluation_-_USACE-p16021coll7-2366.pdf) 
- commons: [File:Appendix B- Public and agency comments- Draft Environmental Assessment (EA) for maintenance dredging and dredged material placement for](https://commons.wikimedia.org/wiki/File:Appendix_B-_Public_and_agency_comments-_Draft_Environmental_Assessment_(EA)_for_maintenance_dredging_and_dredged_material_placement_for_Miami_Harbor_Navigation_Project_at_Port_Miami_in_Miami-Dade_..._-_USACE-p16021coll7-21580.pdf) 
- commons: [File:Appendix C - environmental justice analysis - USACE-p16021coll7-23125.pdf](https://commons.wikimedia.org/wiki/File:Appendix_C_-_environmental_justice_analysis_-_USACE-p16021coll7-23125.pdf) 
- commons: [File:Appendix C- Environmental justice analysis- Environmental Assessment (EA) for maintenance dredging and dredged material placement for M](https://commons.wikimedia.org/wiki/File:Appendix_C-_Environmental_justice_analysis-_Environmental_Assessment_(EA)_for_maintenance_dredging_and_dredged_material_placement_for_Miami_Harbor_Navigation_Project_at_Port_Miami_in_Miami-Dade_C_..._-_USACE-p16021coll7-25065.pdf) 
- commons: [File:Appendix D- Correspondence - USACE-p16021coll7-23481.pdf](https://commons.wikimedia.org/wiki/File:Appendix_D-_Correspondence_-_USACE-p16021coll7-23481.pdf) 
- commons: [File:Appendix D- Environmental appendix- Draft integrated feasibility report,environmental assessment, Salud Creek at San German Continuing ](https://commons.wikimedia.org/wiki/File:Appendix_D-_Environmental_appendix-_Draft_integrated_feasibility_report,environmental_assessment,_Salud_Creek_at_San_German_Continuing_Authorities_Program_(CAP),_Section_14_project_in_municipality_of_..._-_USACE-p16021coll7-7619.pdf) 
- commons: [File:Appendix D.3- National Historic Preservation Act compliance - USACE-p16021coll7-13353.pdf](https://commons.wikimedia.org/wiki/File:Appendix_D.3-_National_Historic_Preservation_Act_compliance_-_USACE-p16021coll7-13353.pdf) 
- commons: [File:Appendix D.3- National Historic Preservation Act compliance - USACE-p16021coll7-14722.pdf](https://commons.wikimedia.org/wiki/File:Appendix_D.3-_National_Historic_Preservation_Act_compliance_-_USACE-p16021coll7-14722.pdf) 
- commons: [File:Appendix E - adjoining property owners - USACE-p16021coll7-15287.pdf](https://commons.wikimedia.org/wiki/File:Appendix_E_-_adjoining_property_owners_-_USACE-p16021coll7-15287.pdf) 
- commons: [File:Appendix E, real estate plan - USACE-p16021coll7-6963.pdf](https://commons.wikimedia.org/wiki/File:Appendix_E,_real_estate_plan_-_USACE-p16021coll7-6963.pdf) 
- commons: [File:Appendix E- Compliance with environmental laws and regulations - USACE-p16021coll7-19845.pdf](https://commons.wikimedia.org/wiki/File:Appendix_E-_Compliance_with_environmental_laws_and_regulations_-_USACE-p16021coll7-19845.pdf) 
- commons: [File:Appendix F - USACE-p16021coll7-25844.pdf](https://commons.wikimedia.org/wiki/File:Appendix_F_-_USACE-p16021coll7-25844.pdf) 
- commons: [File:Appendix F - WG, Weir Gulch hydraulic analysis report - USACE-p16021coll7-11213.pdf](https://commons.wikimedia.org/wiki/File:Appendix_F_-_WG,_Weir_Gulch_hydraulic_analysis_report_-_USACE-p16021coll7-11213.pdf) 
- commons: [File:Appendix F flood risk & floodplain management - USACE-p16021coll7-12156.pdf](https://commons.wikimedia.org/wiki/File:Appendix_F_flood_risk_%26_floodplain_management_-_USACE-p16021coll7-12156.pdf) 
- commons: [File:Appendix F, significant laws & executive orders - USACE-p16021coll7-2629.pdf](https://commons.wikimedia.org/wiki/File:Appendix_F,_significant_laws_%26_executive_orders_-_USACE-p16021coll7-2629.pdf) 
- commons: [File:Appendix F- *Significant laws & executive orders - USACE-p16021coll7-2104.pdf](https://commons.wikimedia.org/wiki/File:Appendix_F-_*Significant_laws_%26_executive_orders_-_USACE-p16021coll7-2104.pdf) 
- commons: [File:Appendix F- Wetlands and other waters of the U.S. technical memorandum - USACE-p16021coll7-2371.pdf](https://commons.wikimedia.org/wiki/File:Appendix_F-_Wetlands_and_other_waters_of_the_U.S._technical_memorandum_-_USACE-p16021coll7-2371.pdf) 
- commons: [File:Appendix G, nonstructural analysis and floodplain management - USACE-p16021coll7-7357.pdf](https://commons.wikimedia.org/wiki/File:Appendix_G,_nonstructural_analysis_and_floodplain_management_-_USACE-p16021coll7-7357.pdf) 
- commons: [File:Appendix I- Environmental - USACE-p16021coll7-25206.pdf](https://commons.wikimedia.org/wiki/File:Appendix_I-_Environmental_-_USACE-p16021coll7-25206.pdf) 
- commons: [File:Appendix K- Tribal and public coordination for Papillion Creek general reevaluation report, Douglas, Sarpy and Washington Counties, Neb](https://commons.wikimedia.org/wiki/File:Appendix_K-_Tribal_and_public_coordination_for_Papillion_Creek_general_reevaluation_report,_Douglas,_Sarpy_and_Washington_Counties,_Nebraska_-_USACE-p16021coll7-17036.pdf) 
- commons: [File:Applicability of floodplain management and FFRMS executive orders to USACE permitting authorities - USACE-p16021coll2-2927.pdf](https://commons.wikimedia.org/wiki/File:Applicability_of_floodplain_management_and_FFRMS_executive_orders_to_USACE_permitting_authorities_-_USACE-p16021coll2-2927.pdf) 
- commons: [File:Application of infrared frequency synthesis techniques with metal-insulator-metal diodes to the spin flip raman laser (IA applicationof](https://commons.wikimedia.org/wiki/File:Application_of_infrared_frequency_synthesis_techniques_with_metal-insulator-metal_diodes_to_the_spin_flip_raman_laser_(IA_applicationofinf680well).pdf) 
- commons: [File:Applying organization development to Coast Guard affirmative action for black officers. (IA applyingorganiza00thor).pdf](https://commons.wikimedia.org/wiki/File:Applying_organization_development_to_Coast_Guard_affirmative_action_for_black_officers._(IA_applyingorganiza00thor).pdf) 
- commons: [File:Applying risk and resilience metrics to energy investments (IA applyingriskndre1094547883).pdf](https://commons.wikimedia.org/wiki/File:Applying_risk_and_resilience_metrics_to_energy_investments_(IA_applyingriskndre1094547883).pdf) 
- commons: [File:Approved Nellis Air Force Range resource plan and record of decision (IA approvednellisai25unit).pdf](https://commons.wikimedia.org/wiki/File:Approved_Nellis_Air_Force_Range_resource_plan_and_record_of_decision_(IA_approvednellisai25unit).pdf) 
- commons: [File:Archaeological resources of southwestern Colorado (IA archaeologicalre00unit).pdf](https://commons.wikimedia.org/wiki/File:Archaeological_resources_of_southwestern_Colorado_(IA_archaeologicalre00unit).pdf) 
- commons: [File:Archaeology of Oregon (IA archaeologyofore00aike).pdf](https://commons.wikimedia.org/wiki/File:Archaeology_of_Oregon_(IA_archaeologyofore00aike).pdf) 
- commons: [File:Archeological investigations of the Deer Creek Site, 48BH18, Big Horn County, Wyoming (IA archeologicalinv00lars).pdf](https://commons.wikimedia.org/wiki/File:Archeological_investigations_of_the_Deer_Creek_Site,_48BH18,_Big_Horn_County,_Wyoming_(IA_archeologicalinv00lars).pdf) 
- commons: [File:Archeological survey in the Jefferson Planning Unit of Jefferson County, southwestern Montana (IA archeologicalsur00scar).pdf](https://commons.wikimedia.org/wiki/File:Archeological_survey_in_the_Jefferson_Planning_Unit_of_Jefferson_County,_southwestern_Montana_(IA_archeologicalsur00scar).pdf) 
- commons: [File:Argument of Asa Bird Gardner, counsel for government, after conclusion of the evidence in the case of Fitz-John Porter before the Board](https://commons.wikimedia.org/wiki/File:Argument_of_Asa_Bird_Gardner,_counsel_for_government,_after_conclusion_of_the_evidence_in_the_case_of_Fitz-John_Porter_before_the_Board_of_Army_officers_at_West_Point,_January,_1879_(IA_argumentofasabir00gard).pdf) 
- commons: [File:Aringay Executive Order No. 16 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Aringay_Executive_Order_No._16_-_2020.pdf) 2020-03-11
- commons: [File:Aringay Executive Order No. 18 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Aringay_Executive_Order_No._18_-_2020.pdf) 2020-03-16
- commons: [File:Arkansas River Corridor feasibility report- Draft report - USACE-p16021coll7-4791.pdf](https://commons.wikimedia.org/wiki/File:Arkansas_River_Corridor_feasibility_report-_Draft_report_-_USACE-p16021coll7-4791.pdf) 
- commons: [File:Arkansas River Watershed, Nimrod Dam, Fouche La Fave River, Arkansas- Specifications for construction of dam - USACE-p266001coll1-11367](https://commons.wikimedia.org/wiki/File:Arkansas_River_Watershed,_Nimrod_Dam,_Fouche_La_Fave_River,_Arkansas-_Specifications_for_construction_of_dam_-_USACE-p266001coll1-11367.pdf) 
- commons: [File:Arkansas River Watershed, Nimrod Dam, Fouche La Fave River, Arkansas- Specifications for operators' quarters - USACE-p266001coll1-11369](https://commons.wikimedia.org/wiki/File:Arkansas_River_Watershed,_Nimrod_Dam,_Fouche_La_Fave_River,_Arkansas-_Specifications_for_operators%27_quarters_-_USACE-p266001coll1-11369.pdf) 
- commons: [File:Arkansas River and tributaries, Great Bend, Kansas to Tulsa, Oklahoma City, Kansas flood control of the Arkansas and Walnut Rivers - US](https://commons.wikimedia.org/wiki/File:Arkansas_River_and_tributaries,_Great_Bend,_Kansas_to_Tulsa,_Oklahoma_City,_Kansas_flood_control_of_the_Arkansas_and_Walnut_Rivers_-_USACE-p16021coll7-22760.pdf) 
- commons: [File:Armstrong, Andrew - DPLA - 0a758ae4eda08b62289cb3ec24a36d72.pdf](https://commons.wikimedia.org/wiki/File:Armstrong,_Andrew_-_DPLA_-_0a758ae4eda08b62289cb3ec24a36d72.pdf) 
- commons: [File:Army Civil Works Program, FY 2014 work plan -- investigations - USACE-p16021coll6-2024.pdf](https://commons.wikimedia.org/wiki/File:Army_Civil_Works_Program,_FY_2014_work_plan_--_investigations_-_USACE-p16021coll6-2024.pdf) 
- commons: [File:Arnett, Charles Oliver - DPLA - b12069ade01aa4b2e0665a96dfe2d747.pdf](https://commons.wikimedia.org/wiki/File:Arnett,_Charles_Oliver_-_DPLA_-_b12069ade01aa4b2e0665a96dfe2d747.pdf) 
- commons: [File:Art and industry. Education in the industrial and fine arts in the United States (IA cu31924021451293).pdf](https://commons.wikimedia.org/wiki/File:Art_and_industry._Education_in_the_industrial_and_fine_arts_in_the_United_States_(IA_cu31924021451293).pdf) 
- commons: [File:Astronautics and aeronautics- chronology of science, technology, and policy. (1986-1990).pdf](https://commons.wikimedia.org/wiki/File:Astronautics_and_aeronautics-_chronology_of_science,_technology,_and_policy._(1986-1990).pdf) between 1986 and 1990 date QS:P,+1950-00-00T00:00:00Z/7,P1319,+1986-00-00T00:00:00Z/9,P1326,+1990-00-00T00:00:00Z/9 
- commons: [File:Atlanta, Georgia; New Hampshire, 6-2-5-79 - DPLA - 5fc752d3f420fbe14785933fb1ef41c3.pdf](https://commons.wikimedia.org/wiki/File:Atlanta,_Georgia;_New_Hampshire,_6-2-5-79_-_DPLA_-_5fc752d3f420fbe14785933fb1ef41c3.pdf) 
- commons: [File:Attachment 1- Biological assessment - USACE-p16021coll7-12147.pdf](https://commons.wikimedia.org/wiki/File:Attachment_1-_Biological_assessment_-_USACE-p16021coll7-12147.pdf) 
- commons: [File:Attachment A- Executive Order 13212- 66 FR 28357 (22 May 2001), Executive Order 13212--actions to expedite energy-related projects - US](https://commons.wikimedia.org/wiki/File:Attachment_A-_Executive_Order_13212-_66_FR_28357_(22_May_2001),_Executive_Order_13212--actions_to_expedite_energy-related_projects_-_USACE-p16021coll11-2490.pdf) 
- commons: [File:Attorney General William Saxbe's letter to President on historical materials retained by White House Office from Nixon administration -](https://commons.wikimedia.org/wiki/File:Attorney_General_William_Saxbe%27s_letter_to_President_on_historical_materials_retained_by_White_House_Office_from_Nixon_administration_-_DPLA_-_0ee86bc93ea2019eb1d323c8419a6d59.pdf) 6 September 1974 date QS:P571,+1974-09-06T00:00:00Z/11 
- commons: [File:Attribution in influence- relative power and the use of attribution (IA attributionininf1094556787).pdf](https://commons.wikimedia.org/wiki/File:Attribution_in_influence-_relative_power_and_the_use_of_attribution_(IA_attributionininf1094556787).pdf) 
- commons: [File:Audit Of NRC's Freedom Of Information Act Process (IA us-inspectors-general.nrc-2014-OIG-14-A-17).pdf](https://commons.wikimedia.org/wiki/File:Audit_Of_NRC%27s_Freedom_Of_Information_Act_Process_(IA_us-inspectors-general.nrc-2014-OIG-14-A-17).pdf) 
- commons: [File:Avery Brook Watershed, Hartford County, Connecticut - final watershed plan and environmental impact statement (IA CAT78694505).pdf](https://commons.wikimedia.org/wiki/File:Avery_Brook_Watershed,_Hartford_County,_Connecticut_-_final_watershed_plan_and_environmental_impact_statement_(IA_CAT78694505).pdf) 
- commons: [File:Award and recommendations of the United States Bituminous coal commission (IA awardrecommendat00unit).pdf](https://commons.wikimedia.org/wiki/File:Award_and_recommendations_of_the_United_States_Bituminous_coal_commission_(IA_awardrecommendat00unit).pdf) 
- commons: [File:Aylesworth Creek Lake, PA - USACE-p16021coll11-2228.pdf](https://commons.wikimedia.org/wiki/File:Aylesworth_Creek_Lake,_PA_-_USACE-p16021coll11-2228.pdf) 
- commons: [File:Azad Hind - English - Vol. 1 - No. 502 - 1944-12-30.pdf](https://commons.wikimedia.org/wiki/File:Azad_Hind_-_English_-_Vol._1_-_No._502_-_1944-12-30.pdf) 
- commons: [File:BAILEY, KEYS, AND MAINELLA NOMINATIONS (IA gov.gpo.fdsys.CHRG-107shrg76085).pdf](https://commons.wikimedia.org/wiki/File:BAILEY,_KEYS,_AND_MAINELLA_NOMINATIONS_(IA_gov.gpo.fdsys.CHRG-107shrg76085).pdf) 
- commons: [File:BECK RIGHTS 2001- ARE WORKERS BEING HEARD (IA gov.gpo.fdsys.CHRG-107hhrg77906).pdf](https://commons.wikimedia.org/wiki/File:BECK_RIGHTS_2001-_ARE_WORKERS_BEING_HEARD_(IA_gov.gpo.fdsys.CHRG-107hhrg77906).pdf) 
- commons: [File:BIOLOGICAL WARFARE DEFENSE VACCINE RESEARCH AND DEVELOPMENT PROGRAM (IA gov.gpo.fdsys.CHRG-107hhrg81780).pdf](https://commons.wikimedia.org/wiki/File:BIOLOGICAL_WARFARE_DEFENSE_VACCINE_RESEARCH_AND_DEVELOPMENT_PROGRAM_(IA_gov.gpo.fdsys.CHRG-107hhrg81780).pdf) 
- commons: [File:BLACKWATER NATIONAL WILDLIFE REFUGE (IA gov.gpo.fdsys.CHRG-107hhrg71815).pdf](https://commons.wikimedia.org/wiki/File:BLACKWATER_NATIONAL_WILDLIFE_REFUGE_(IA_gov.gpo.fdsys.CHRG-107hhrg71815).pdf) 
- commons: [File:BLM facts & figures for Utah (IA blmfactsfiguresf0725unit).pdf](https://commons.wikimedia.org/wiki/File:BLM_facts_%26_figures_for_Utah_(IA_blmfactsfiguresf0725unit).pdf) 
- commons: [File:BRAC AND BEYOND- AN EXAMINATION OF THE RATIONALE BEHIND FEDERAL SECURITY STANDARDS FOR LEASED SPACE (IA gov.gpo.fdsys.CHRG-109hhrg23041](https://commons.wikimedia.org/wiki/File:BRAC_AND_BEYOND-_AN_EXAMINATION_OF_THE_RATIONALE_BEHIND_FEDERAL_SECURITY_STANDARDS_FOR_LEASED_SPACE_(IA_gov.gpo.fdsys.CHRG-109hhrg23041).pdf) 
- commons: [File:Bacnotan Executive Order No. 20 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Bacnotan_Executive_Order_No._20_-_2020.pdf) 2020-03-14
- commons: [File:Bacnotan Executive Order No. 22 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Bacnotan_Executive_Order_No._22_-_2020.pdf) 2020-03-17
- commons: [File:Baht timber sale - record of decision II - United States Department of Agriculture, Forest Service, Tongass National Forest (IA CAT3101](https://commons.wikimedia.org/wiki/File:Baht_timber_sale_-_record_of_decision_II_-_United_States_Department_of_Agriculture,_Forest_Service,_Tongass_National_Forest_(IA_CAT31010478).pdf) 
- commons: [File:Balaoan Executive Order No. 21 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Balaoan_Executive_Order_No._21_-_2020.pdf) 2020-03-13
- commons: [File:Balaoan Executive Order No. 22 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Balaoan_Executive_Order_No._22_-_2020.pdf) 2020-03-13
- commons: [File:Balaoan Executive Order No. 23 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Balaoan_Executive_Order_No._23_-_2020.pdf) 2020-03-17
- commons: [File:Balaoan Executive Order No. 24 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Balaoan_Executive_Order_No._24_-_2020.pdf) 2020-03-20
- commons: [File:Balaoan Executive Order No. 25 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Balaoan_Executive_Order_No._25_-_2020.pdf) 2020-03-22
- commons: [File:Baltimore Harbor and channels, MD & VA, Dredged Material Management Plan update - USACE-p16021coll11-736.pdf](https://commons.wikimedia.org/wiki/File:Baltimore_Harbor_and_channels,_MD_%26_VA,_Dredged_Material_Management_Plan_update_-_USACE-p16021coll11-736.pdf) 
- commons: [File:Baltimore Harbor, MD, collection and removal of drift - USACE-p16021coll11-4475.pdf](https://commons.wikimedia.org/wiki/File:Baltimore_Harbor,_MD,_collection_and_removal_of_drift_-_USACE-p16021coll11-4475.pdf) 
- commons: [File:Baltimore metropolitan water resources, Gwynns Falls Watershed, MD - USACE-p16021coll11-1196.pdf](https://commons.wikimedia.org/wiki/File:Baltimore_metropolitan_water_resources,_Gwynns_Falls_Watershed,_MD_-_USACE-p16021coll11-1196.pdf) 
- commons: [File:Baltimore metropolitan water resources, Gwynns Falls Watershed, MD - USACE-p16021coll11-462.pdf](https://commons.wikimedia.org/wiki/File:Baltimore_metropolitan_water_resources,_Gwynns_Falls_Watershed,_MD_-_USACE-p16021coll11-462.pdf) 
- commons: [File:Bani SB Resolution No. 11 - 2010.pdf](https://commons.wikimedia.org/wiki/File:Bani_SB_Resolution_No._11_-_2010.pdf) 2010-11-22
- commons: [File:Bank stabilization, Bethel, Alaska - USACE-p16021coll7-22854.pdf](https://commons.wikimedia.org/wiki/File:Bank_stabilization,_Bethel,_Alaska_-_USACE-p16021coll7-22854.pdf) 
- commons: [File:Banking 1919-07- Vol 12 Iss 1 (IA sim american-bankers-association-aba-banking-journal 1919-07 12 1).pdf](https://commons.wikimedia.org/wiki/File:Banking_1919-07-_Vol_12_Iss_1_(IA_sim_american-bankers-association-aba-banking-journal_1919-07_12_1).pdf) 
- commons: [File:Banking 1934-09- Vol 27 Iss 3 (IA sim american-bankers-association-aba-banking-journal 1934-09 27 3).pdf](https://commons.wikimedia.org/wiki/File:Banking_1934-09-_Vol_27_Iss_3_(IA_sim_american-bankers-association-aba-banking-journal_1934-09_27_3).pdf) 
- commons: [File:Basic Law of Hong Kong.djvu](https://commons.wikimedia.org/wiki/File:Basic_Law_of_Hong_Kong.djvu) 1990-04
- commons: [File:Basic-ARNG-Facts.pdf](https://commons.wikimedia.org/wiki/File:Basic-ARNG-Facts.pdf) 2006-05-03
- commons: [File:Bayambang Ordinance No. 07 - 2018.pdf](https://commons.wikimedia.org/wiki/File:Bayambang_Ordinance_No._07_-_2018.pdf) 2018-08-20
- commons: [File:Beach Erosion Control and Hurricane Protection, Folly Beach, South Carolina - USACE-p16021coll7-21848.pdf](https://commons.wikimedia.org/wiki/File:Beach_Erosion_Control_and_Hurricane_Protection,_Folly_Beach,_South_Carolina_-_USACE-p16021coll7-21848.pdf) 
- commons: [File:Beach erosion control and hurricane protection study for Sara Sota County, Florida - USACE-p16021coll7-22844.pdf](https://commons.wikimedia.org/wiki/File:Beach_erosion_control_and_hurricane_protection_study_for_Sara_Sota_County,_Florida_-_USACE-p16021coll7-22844.pdf) 
- commons: [File:Bell telephone magazine (IA belltvol20elephonemag00amerrich).pdf](https://commons.wikimedia.org/wiki/File:Bell_telephone_magazine_(IA_belltvol20elephonemag00amerrich).pdf) 
- commons: [File:Better Health Information System Act of 2006 - report together with dissenting views (to accompany H.R. 4157) (including cost estimate ](https://commons.wikimedia.org/wiki/File:Better_Health_Information_System_Act_of_2006_-_report_together_with_dissenting_views_(to_accompany_H.R._4157)_(including_cost_estimate_of_the_Congressional_Budget_Office)_(IA_betterhealthinfo00unit_0).pdf) 
- commons: [File:Beyond the Wasatch. .. The History of Irrigation in the Uinta Basin and Upper Provo River Area of Utah... U.S. Department of the Interi](https://commons.wikimedia.org/wiki/File:Beyond_the_Wasatch._.._The_History_of_Irrigation_in_the_Uinta_Basin_and_Upper_Provo_River_Area_of_Utah..._U.S._Department_of_the_Interior_(IA_doi-report_i-292-w-26-2).pdf) 
- commons: [File:Bi - United States. Bureau of Biological Survey (IA CAT11088674062).pdf](https://commons.wikimedia.org/wiki/File:Bi_-_United_States._Bureau_of_Biological_Survey_(IA_CAT11088674062).pdf) 
- commons: [File:Bi - United States. Bureau of Biological Survey (IA CAT11088674277).pdf](https://commons.wikimedia.org/wiki/File:Bi_-_United_States._Bureau_of_Biological_Survey_(IA_CAT11088674277).pdf) 
- commons: [File:Bi - United States. Bureau of Biological Survey (IA CAT11088674295).pdf](https://commons.wikimedia.org/wiki/File:Bi_-_United_States._Bureau_of_Biological_Survey_(IA_CAT11088674295).pdf) 
- commons: [File:Bi - United States. Bureau of Biological Survey (IA CAT11088674353).pdf](https://commons.wikimedia.org/wiki/File:Bi_-_United_States._Bureau_of_Biological_Survey_(IA_CAT11088674353).pdf) 
- commons: [File:Bieberdorf, Frederick - DPLA - 5e8ab6d426d39b0b425e6289d04f2c49.pdf](https://commons.wikimedia.org/wiki/File:Bieberdorf,_Frederick_-_DPLA_-_5e8ab6d426d39b0b425e6289d04f2c49.pdf) 
- commons: [File:Biennial Report to the President of the United States... Federal Agency Implementation of Executive Order,... Department of the Interio](https://commons.wikimedia.org/wiki/File:Biennial_Report_to_the_President_of_the_United_States..._Federal_Agency_Implementation_of_Executive_Order,..._Department_of_the_Interior_(IA_doi-report_i-491-8996-97).pdf) 
- commons: [File:Big dam era- A legislative and institutional history of the Pick-Sloan Missouri Basin Program - USACE-p16021coll4-160.pdf](https://commons.wikimedia.org/wiki/File:Big_dam_era-_A_legislative_and_institutional_history_of_the_Pick-Sloan_Missouri_Basin_Program_-_USACE-p16021coll4-160.pdf) 
- commons: [File:Big game on BLM administered public lands of the United States in Arizona (IA biggameonblmadmi75unit).pdf](https://commons.wikimedia.org/wiki/File:Big_game_on_BLM_administered_public_lands_of_the_United_States_in_Arizona_(IA_biggameonblmadmi75unit).pdf) 
- commons: [File:Billings and Pompeys Pillar National Monument proposed resource management plan and final environmental impact statement (IA billingspo](https://commons.wikimedia.org/wiki/File:Billings_and_Pompeys_Pillar_National_Monument_proposed_resource_management_plan_and_final_environmental_impact_statement_(IA_billingspompeysp01unit).pdf) 
- commons: [File:Billings and Pompeys Pillar National Monument proposed resource management plan and final environmental impact statement (IA billingspo](https://commons.wikimedia.org/wiki/File:Billings_and_Pompeys_Pillar_National_Monument_proposed_resource_management_plan_and_final_environmental_impact_statement_(IA_billingspompeysp03unit).pdf) 
- commons: [File:Billings and Pompeys Pillar National Monument proposed resource management plan and final environmental impact statement (IA billingspo](https://commons.wikimedia.org/wiki/File:Billings_and_Pompeys_Pillar_National_Monument_proposed_resource_management_plan_and_final_environmental_impact_statement_(IA_billingspompeysp04unit).pdf) 
- commons: [File:Bird refuges and big-game preserves administered by the Bureau of Biological Survey (IA birdrefugesbigga16unit).pdf](https://commons.wikimedia.org/wiki/File:Bird_refuges_and_big-game_preserves_administered_by_the_Bureau_of_Biological_Survey_(IA_birdrefugesbigga16unit).pdf) 
- commons: [File:Blister rust news (IA CAT11088973065).pdf](https://commons.wikimedia.org/wiki/File:Blister_rust_news_(IA_CAT11088973065).pdf) 
- commons: [File:Blueprint-for-an-AI-Bill-of-Rights.pdf](https://commons.wikimedia.org/wiki/File:Blueprint-for-an-AI-Bill-of-Rights.pdf) 2022-10-03
- commons: [File:Bolinao Executive Order No. 01 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Bolinao_Executive_Order_No._01_-_2020.pdf) 2020-01-29
- commons: [File:Bolinao Executive Order No. 06 - 2021.pdf](https://commons.wikimedia.org/wiki/File:Bolinao_Executive_Order_No._06_-_2021.pdf) 2021-03-25
- commons: [File:Bolinao Executive Order No. 10 - 2020.pdf](https://commons.wikimedia.org/wiki/File:Bolinao_Executive_Order_No._10_-_2020.pdf) 2020-02-27
