# AWS Side — CDC Pipeline Setup

> **Note**: This is a one-time manual setup. The GCP infra (Terraform) must be applied first to get the Pub/Sub topic name.

---

## Prerequisites

- Owner access to the `deluxe-v2` AWS account
- AWS DMS service available in **us-east-1**
- RDS PostgreSQL instance (the `deluxe-v2` source database)
- AWS CLI configured with appropriate credentials

---

## Step 1: Enable Logical Replication on RDS

1. In the AWS Console, go to **RDS → Parameter Groups**.
2. Create (or edit) a custom parameter group for your RDS instance.
3. Set `rds.logical_replication = 1`.
4. Attach the parameter group to your RDS instance.
5. **Reboot the RDS instance** for the change to take effect.

Verify replication is active:

```sql
SHOW wal_level;  -- should return "logical"
```

---

## Step 2: Create S3 Bucket `deluxe-v2-cdc-out`

1. Go to **S3 → Create bucket**.
2. **Bucket name**: `deluxe-v2-cdc-out`
3. **Region**: `us-east-1`
4. **Versioning**: disabled
5. **Block all public access**: enabled (default)
6. Leave all other settings as default and create the bucket.

---

## Step 3: Create DMS Replication Instance

1. Go to **DMS → Replication instances → Create replication instance**.
2. **Name**: `deluxe-cdc-instance`
3. **Instance class**: `dms.t3.micro`
4. **VPC**: same VPC as your RDS instance
5. **Subnet group**: private subnet (same as RDS)
6. **Publicly accessible**: No
7. Create the instance and wait for it to become **Available**.

---

## Step 4: Create DMS Endpoints

### Source Endpoint (RDS PostgreSQL)

1. **DMS → Endpoints → Create endpoint**
2. **Endpoint type**: Source
3. **Engine**: PostgreSQL
4. **Server name**: your RDS instance hostname
5. **Port**: 5432
6. **Database name**: your database name
7. **Username / Password**: use a read-replica user with `REPLICATION` privilege

### Target Endpoint (S3 — Parquet)

1. **Endpoint type**: Target
2. **Engine**: Amazon S3
3. **Bucket name**: `deluxe-v2-cdc-out`
4. **Bucket folder**: `data`
5. **Service access role ARN**: ARN of the DMS instance role (with `aws/iam/dms-policy.json` attached)
6. **Extra connection attributes**:
   ```
   dataFormat=parquet;timestampColumnName=_dms_timestamp;includeOpForFullLoad=true;cdcInsertsAndUpdates=true
   ```

---

## Step 5: Create DMS Replication Task

1. **DMS → Database migration tasks → Create task**
2. **Task identifier**: `deluxe-cdc-task`
3. **Replication instance**: `deluxe-cdc-instance`
4. **Source endpoint**: your RDS endpoint
5. **Target endpoint**: your S3 endpoint
6. **Migration type**: Replicate data changes only (CDC)
7. **Table mappings**: paste contents of `aws/dms/task-mapping.json`
8. **Task settings**: paste contents of `aws/dms/task-settings.json`
9. Start the task after creation.

---

## Step 6: Deploy the Lambda Bridge (`s3-to-pubsub`)

1. Package the Lambda:
   ```bash
   pip install -r aws/lambda/requirements.txt -t aws/lambda/package/
   cp aws/lambda/s3_to_pubsub.py aws/lambda/package/
   cd aws/lambda/package && zip -r ../s3_to_pubsub.zip . && cd -
   ```
2. Create the Lambda function in AWS Console (or CLI):
   - **Runtime**: Python 3.11
   - **Handler**: `s3_to_pubsub.handler`
   - **Memory**: 256 MB, **Timeout**: 30s
3. Upload `s3_to_pubsub.zip`.
4. Set environment variables:
   - `GCP_PROJECT` — your GCP project ID
   - `PUBSUB_TOPIC` — Pub/Sub topic name (from `terraform output`)
5. **Add trigger**: S3 → bucket `deluxe-v2-cdc-out`, event type `s3:ObjectCreated:*`.

---

## Step 7: GCP Authentication for Lambda

The Lambda must authenticate to GCP Pub/Sub. Two options:

**Option A — GCP Service Account key in AWS SSM (simpler, academic)**

1. Create a GCP service account with `roles/pubsub.publisher`.
2. Download the JSON key.
3. Store the key in AWS SSM Parameter Store:
   ```bash
   aws ssm put-parameter --name /deluxe/gcp-sa-key --type SecureString --value "$(cat sa-key.json)"
   ```
4. Give the Lambda's execution role `ssm:GetParameter` permission.
5. In the Lambda code, load the key from SSM and use `service_account.Credentials.from_service_account_info(...)`.

**Option B — GCP Workload Identity Federation (production-grade)**

1. Create a Workload Identity Pool in GCP:
   - Provider type: AWS
   - AWS account ID: your AWS account
2. Grant the Lambda's execution role the Workload Identity User binding.
3. No JSON key needed; Application Default Credentials will work automatically.

---

## Step 8: IAM Setup

### DMS Instance Role

Attach `aws/iam/dms-policy.json` to the role used by your DMS replication instance (`dms-vpc-role` or a custom role).

### GCP CDC Reader User

1. Create IAM user `gcp-cdc-reader` (used by Dataproc with HMAC key for S3 access).
2. Attach `aws/iam/gcp-reader-policy.json` to this user.
3. Generate an access key pair and store the credentials as GCP Secret Manager secrets or Terraform variables.
