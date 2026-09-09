# DataCitation reporting scripts

This module can be used to create data citation reports from a data DOI
(Digital Object Identifier). The scripts queries various sources of 
metadata to build a graph of relations, which can be summarised into 
a report file.

## Usage
The module can be install using pip:
```
pip install git+https://github.com/BaptisteCecconi/DataCitation.git
```

Then run the following commands in python:

```
from data_citation_reporter import Report
doi = "10.25935/6jg4-mk86"
report = Report(doi=doi)
report.include_crossref_datacitations()
report.include_opencitations()
report.include_openaire_graph()
report.include_nasa_ads()
report.include_biblinks()
report.export_citations(format="md", filename=f"reports/{doi}/citations.md")
```

This will create a report (in markdown format) in a subdirectory `reports/10.25935/6jg4-mk86/citations.md`.
