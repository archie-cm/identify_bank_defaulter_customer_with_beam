# Identify Bank Defaulter Customers with Dataflow

This project builds a data pipeline to identify bank defaulter customers based on credit card and loan payment data using Google Dataflow. It processes two datasets (`cards.txt` and `loan.txt`) to calculate defaulter scores and output the results.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Project Requirements](#project-requirements)
- [Setup](#setup)
  - [1. Upload Source Files](#1-upload-source-files)
  - [2. Set Up Dataflow](#2-set-up-dataflow)
  - [3. Run the Python Script](#3-run-the-python-script)
  - [4. Sink to BigQuery](#4-sink-to-bigquery)
- [Output](#output)
- [License](#license)

---

## Overview
This project identifies defaulters based on:
1. **Credit Card Defaulters:** Customers with insufficient or missed payments.
2. **Loan Defaulters:** Customers failing to meet loan repayment requirements based on the loan type.

The processed data is outputted to a file, summarizing defaulter scores for customers.

## Prerequisites
- Google Cloud account
- GCP SDK installed
- `gcloud` CLI configured
- Python 3.x installed locally
- Google Cloud Storage bucket for uploading source files

## Project Requirements

### Credit Card Defaulters
1. Assign 1 point if a customer makes a short payment (less than 70% of monthly spends).
2. Assign 1 point if a customer spends 100% of their credit limit but does not clear the full amount.
3. If both conditions are met in a single month, assign 1 additional point.
4. Sum all points for each customer and output the results.

### Loan Defaulters
#### Loan File Key Points
- **Personal Loans:**
  - No short or late payments are accepted.
  - Missing monthly installment implies no entry for that month.
- **Medical Loans:**
  - Late payments are accepted only if the full amount is paid.
  - Every month’s data is present for medical loans.

#### Loan Defaulter Rules
1. **Medical Loan Defaulters:** A customer is a defaulter if they make 3 or more late payments.
2. **Personal Loan Defaulters:**
   - A customer is a defaulter if they miss 4 or more installments.
   - Alternatively, a customer is a defaulter if they miss 2 consecutive installments.

## Setup

### 1. Upload Source Files
1. Prepare the source files `cards.txt` and `loan.txt` with customer data.
2. Upload the files to a Google Cloud Storage bucket:
   ```bash
   gsutil cp cards.txt gs://<your-bucket-name>/
   gsutil cp loan.txt gs://<your-bucket-name>/
   ```

### 2. Set Up Dataflow
1. Enable Dataflow API:
   ```bash
   gcloud services enable dataflow.googleapis.com
   ```

2. Create a Dataflow job to process the data:
   - Use the provided `defaulters.py` script to define the pipeline.
   - Specify the input files and output location in the script or via arguments.

### 3. Run the Python Script
Run the `defaulters.py` script to execute the pipeline:
```bash
python defaulters.py \
    --input_cards=gs://<your-bucket-name>/cards.txt \
    --input_loans=gs://<your-bucket-name>/loan.txt \
    --output=gs://<your-bucket-name>/output/
```

### 4. Sink to BigQuery
To sink the results to BigQuery, modify the pipeline in `defaulters.py` to include BigQuery as a sink.

1. Enable the BigQuery API:
   ```bash
   gcloud services enable bigquery.googleapis.com
   ```

2. Create a BigQuery dataset to store the results:
   ```bash
   bq mk <your-dataset-name>
   ```

3. Modify the `defaulters.py` script to write outputs to BigQuery:
   ```python
   card_defaulter | 'Write card defaulters to BigQuery' >> beam.io.WriteToBigQuery(
       table='project_id:dataset_id.card_defaulters',
       schema='customer_id:STRING, fraud_points:INTEGER',
       write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
       create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
   )

   final_loan_defaulters | 'Write loan defaulters to BigQuery' >> beam.io.WriteToBigQuery(
       table='project_id:dataset_id.loan_defaulters',
       schema='customer_id:STRING, missed_months:INTEGER',
       write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
       create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
   )

   both_defaulters | 'Write combined defaulters to BigQuery' >> beam.io.WriteToBigQuery(
       table='project_id:dataset_id.combined_defaulters',
       schema='customer_id:STRING, card_defaulter:INTEGER, loan_defaulter:INTEGER',
       write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
       create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
   )
   ```

4. Run the pipeline again to process and store the results in BigQuery.

## Output
The output includes:
1. Credit card defaulter scores in BigQuery.
2. Loan defaulter statuses (Medical or Personal Loan) in BigQuery.
3. Combined defaulter results in BigQuery.

Check the results in your specified BigQuery tables.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
