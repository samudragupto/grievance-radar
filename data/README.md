# Sample complaints dataset description and privacy assurance.

## Overview
This directory contains 1,200 synthetic grievance records modeled after typical municipal citizen complaints submitted through DARPG (Department of Administrative Reforms and Public Grievances) CPGRAMS format.

## Privacy & Synthetic Data Notice
All data in `sample_complaints.json` and `sample_complaints.csv` is completely synthetic and programmatically generated for demonstration, testing, and benchmarking purposes.
- No real citizen names, Aadhaar numbers, phone numbers, or residential addresses are present.
- Wards are structured generically as `Ward 1` through `Ward 12`.
- Coordinates for geospatial mapping represent standard municipal zone coordinates for Tiruchirappalli, Tamil Nadu.

## Deliberate Statistical Anomalies (Demo Verification)
To validate the statistical spike detection pipeline (Z-score against a 4-week rolling baseline), intentional spikes were injected in the recent two-week window:
1. **Water Supply in Ward 4**: Major surge (+340% increase, Z-Score &ge; 4.0&sigma;) simulating a burst pipeline or distribution failure.
2. **Sanitation in Ward 7**: Garbage clearance disruption (+210% increase, Z-Score &ge; 3.0&sigma;).
3. **Streetlights in Ward 5**: Power / lighting outage (+180% increase, Z-Score &ge; 2.8&sigma;).
