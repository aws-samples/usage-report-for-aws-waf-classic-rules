# AWS WAF Classic Resource Report Generator

*tldr; This Python script generates a report of AWS WAF Classic resources, including Regional Web ACLs and CloudFront Web ACLs, along with their associated resources. The report is written to an S3 bucket or a local CSV file.*

This AWS Sample is an example of a Python script that generates a report of AWS WAF Classic resources, including Regional Web ACLs and CloudFront Web ACLs, along with their associated resources. It leverages the Boto3 library to interact with the AWS APIs.  The script retrieves the available regions, fetches the Web ACL details from AWS WAF and Amazon CloudFront, and gathers information about the associated resources. The report data is then written to either an S3 bucket or a local CSV file, providing visibility into the WAF Classic configuration across multiple AWS regions and services [Amazon CloudFront Distributions, Amazon Load Balancers, AWS API Gateways].

> PLEASE NOTE: It is recommended to [migrate from AWS WAF Classic to AWS WAF](https://docs.aws.amazon.com/waf/latest/developerguide/waf-migrating-procedure.html). This sample script will generate a report to help you identify WAF Classic in use across your accounts. Please test in test environments first and tailor these scripts for your use-case.

## Prerequisites

- Python 3.6 or later
- AWS CLI or AWS credentials configured with appropriate permissions to access WAF Classic, S3, and EC2 services

## Installation

1. Clone the repository:

```bash
git clone https://github.com/aws-samples/usage-report-for-aws-waf-classic-rules.git
```

2. Change to the project directory:

```bash
cd usage-report-for-aws-waf-classic-rules
```

3. Install the required Python packages in a virtual environment:

```bash
python3 -m venv  .
source ./bin/activate
python3 -m pip install -r requirements.txt 
```


### Usage

Run the script with the following command-line arguments. If the --bucket-name argument is not provided, the report will be written to a local CSV file named 
waf-classic-report.txt in the current directory.


```bash
python main.py --bucket-name <S3_BUCKET_NAME> --prefix <S3_PREFIX> --bucket-region <AWS_REGION>

--bucket-name: The name of the S3 bucket to write the report to (optional).
--prefix: The S3 prefix for the report file (default: waf-classic-report.txt).
--bucket-region: The AWS region for the S3 bucket (default: us-east-1).
```

### Requirements

It's recommended to create an IAM policy with the necessary permissions and attach it to the IAM role or user executing the script. Here's an example IAM policy that grants the required permissions, please ensure you review and test before using in production.

For this script to operate fully, the following IAM permissions are required:

#### CloudFront:

- cloudfront:ListDistributions
- cloudfront:GetDistributionConfig

#### WAF Classic:

- waf:ListWebACLs
- waf:GetWebACL

#### WAF Regional:

- waf-regional:ListWebACLs
- waf-regional:ListResourcesForWebACL

#### S3 (if writing the report to an S3 bucket):

s3:PutObject

#### Example Policy:

To create the required IAM role for this code, [create an IAM policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user.html) with the required permissions and then [assume the role](https://repost.aws/knowledge-center/iam-assume-role-cli):

```bash
aws iam create-policy \
  --policy-name WAFClassicReportToS3Policy \
  --policy-document file://waf-report-policy.json
```

The contents of the file waf-report-policy.json would be, however please review the role permissions and bucket name based on your-use case:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudfront:ListDistributions",
                "cloudfront:GetDistributionConfig"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "waf:ListWebACLs",
                "waf:GetWebACL"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "waf-regional:ListWebACLs",
                "waf-regional:ListResourcesForWebACL"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::<BUCKET_NAME>/*"
        }
    ]
}
```

### Report Structure

The report is generated in CSV format with the following columns:

- Region: The AWS region where the WAF Classic resource is located (or CLOUDFRONT for CloudFront Web ACLs).
- WebACLName: The name of the WAF Classic Web ACL.
- WebACLId: The ID of the WAF Classic Web ACL.
- AssociatedResources: The list of resources associated with the Web ACL.
- Enabled: Indicates if the CloudFront distribution is enabled or not (only applicable for CloudFront Web ACLs).

### License

This project is licensed under the MIT License.

### Contributing

Contributions are welcome! Please open an issue or submit a pull request.

### Acknowledgments

This script was developed using the AWS SDK for Python (Boto3) and the AWS WAF Classic API documentation.
