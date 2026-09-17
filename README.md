# MedEx Bangladesh Medicine Database Scraper

An automated scraper and structured JSON database of Bangladeshi medicines sourced from [plus.medex.com.bd](https.plus.medex.com.bd).

## Features

- **Automated Scraping**: Asynchronous Python scraper built with `aiohttp` and `BeautifulSoup4` that retrieves medicine information across all ~847 brand list pages on MedEx.
- **Weekly Updates**: Integrated GitHub Actions workflow scheduled to run every Friday at 7:00 AM UTC (`0 7 * * 5`), automatically updating `list.json` if changes are detected.
- **Manual Trigger**: Supports manual execution via GitHub Actions (`workflow_dispatch`).

## Dataset (`list.json`)

The dataset contains a comprehensive JSON list of medicines in Bangladesh with the following structure:

```json
[
  {
    "brand_name": "3 Bion",
    "power": "100 mg+200 mg+200 mcg",
    "generic_names": [
      "Vitamin B1",
      "B6",
      "B12"
    ],
    "manufacturer": "Jenphar Bangladesh Ltd.",
    "dosage_form": "Tablet"
  }
]
```

### Fields Description

| Field | Type | Description |
| --- | --- | --- |
| `brand_name` | string | Commercial brand name of the medicine |
| `power` | string | Strength / dosage measurement (e.g. `20mg`, `100 mg+200 mg`, `2000 IU`) |
| `generic_names` | list of strings | Generic ingredient name(s), parsed separately |
| `manufacturer` | string | Producer company or pharmaceutical manufacturer |
| `dosage_form` | string | Form of dosage (e.g. `Tablet`, `Capsule`, `Syrup`, `Cream`) |

## Running the Scraper Locally

To run the scraper script manually on your local environment:

1. Install required dependencies:
   ```bash
   pip install aiohttp beautifulsoup4
   ```

2. Execute `scraper.py`:
   ```bash
   python scraper.py
   ```

3. The updated dataset will be output to `list.json`.

## License & Usage

This project is open-source under the terms of the [MIT License](LICENSE).

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software.
