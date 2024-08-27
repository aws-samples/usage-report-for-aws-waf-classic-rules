import argparse
import boto3
from botocore.exceptions import ClientError
import csv
import os

# Create an argument parser
parser = argparse.ArgumentParser(description='Generate a report for WAF Classic resources.')

# Add command-line arguments
parser.add_argument('--bucket-name', help='The name of the S3 bucket to write the report to.')
parser.add_argument('--prefix', default='waf-classic-report.txt', help='S3 prefix for report files. (default: waf-classic-report.txt)')
parser.add_argument('--bucket-region', default='us-east-1', help='AWS region for the S3 bucket. (default: us-east-1)')

# Function to get all available regions
def get_available_regions(service):
    session = boto3.session.Session()
    return session.get_available_regions(service)

# Function to get WAF Classic Regional Web ACLs and associated resources
def get_regional_waf_classic_resources(region):
    waf_regional = boto3.client('waf-regional', region_name=region)
    
    regional_resources = []

    try:
        regional_web_acls = waf_regional.list_web_acls()['WebACLs']
    except ClientError as e:
        print(f"Error retrieving Regional Web ACLs for region {region}: {e}")
        regional_resources.append({'WebACLName': 'Error', 'WebACLId': 'Error', 'AssociatedResources': ['Failed to retrieve resources']})
        waf_regional.close()
        return regional_resources

    try:
        # Get Regional Web ACLs
        for regional_web_acl in regional_web_acls:
            web_acl_id = regional_web_acl['WebACLId']
            web_acl_name = regional_web_acl['Name']
            associated_resources = waf_regional.list_resources_for_web_acl(WebACLId=web_acl_id)['ResourceArns']
            regional_resources.append({'WebACLName': web_acl_name, 'WebACLId': web_acl_id, 'AssociatedResources': associated_resources})
    except ClientError as e:
        print(f"Error retrieving Regional Web ACLs for region {region}: {e}")
        regional_resources.append({'WebACLName': 'Error', 'WebACLId': 'Error', 'AssociatedResources': ['Failed to retrieve resources']})
    
    waf_regional.close()
    return regional_resources

# Function to get WAF Classic CloudFront Web ACLs and associated resources
def generate_waf_cloudfront_report():
    """
    Generates a report of CloudFront distributions and their associated WAF web ACLs.
    
    Returns:
        list: A list of tuples, where each tuple contains the WAF ID (or None) and the CloudFront Distribution ID.
    """
    try:
        # Create AWS client for CloudFront and WAF
        cloudfront = boto3.client('cloudfront', region_name='us-east-1')
        waf = boto3.client('waf')
        
        # Get CloudFront distributions
        distributions = cloudfront.list_distributions()['DistributionList']['Items']
        
        # Create a list to store the report data
        report_data = []
        
        # Iterate over distributions and check for associated web ACLs
        for distribution in distributions:
            distribution_id = distribution['Id']
            
            try:
                # Get the distribution configuration
                distribution_config = cloudfront.get_distribution_config(Id=distribution_id)['DistributionConfig']
                
                # Check if the distribution is associated with a WAF web ACL
                web_acl_arn = distribution_config.get('WebACLId')
                distribution_enabled = distribution_config.get('Enabled')
               
                # Add the web ACL ID (or None) and the distribution ID to the report data
                if web_acl_arn and not web_acl_arn.startswith("arn:aws:wafv2"):
                    waf_name = waf.get_web_acl(WebACLId=web_acl_arn)['WebACL']['Name']
                    report_data.append((web_acl_arn, waf_name, distribution_id, distribution_enabled))
                    
            except ClientError as e:
                print(f"Error retrieving distribution configuration for {distribution_id}: {e}")
        
        return report_data
    except ClientError as e:
        print(f"Error generating report: {e}")
        return None

# Function to write the report to S3
def write_report_to_s3(report_data, bucket_name, object_key, bucket_region):
    s3 = boto3.client('s3', region_name=bucket_region)
    
    try:
        with open('./report.csv', 'w', newline='') as csvfile:
            fieldnames = ['Region', 'WebACLName', 'WebACLId', 'AssociatedResources','Enabled']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(report_data)
        
        s3.upload_file('./report.csv', bucket_name, object_key)
        print(f"Report written to s3://{bucket_name}/{object_key}")
    except ClientError as e:
        print(f"Error writing report to S3: {e}")

# Main function
def main():
    # Parse command-line arguments
    args = parser.parse_args()
    bucket_name = args.bucket_name
    bucket_region = args.bucket_region
    object_key = args.prefix
    
    report_data = []
    
    # Get Regional Web ACLs and associated resources
    print("Processing Regional Web ACLs")
    for region in get_available_regions('waf-regional'):
        print(f"Processing region: {region}")
        regional_resources = get_regional_waf_classic_resources(region)
        for resource in regional_resources:
            report_data.append({'Region': region, 'WebACLName': resource['WebACLName'], 'WebACLId': resource['WebACLId'], 'AssociatedResources': resource['AssociatedResources'], 'Enabled':'n/a'})
            print(f"WAF ID: {resource['WebACLId']}, Name: {resource['WebACLName']} in {region}")
    
    # Get CloudFront Web ACLs and associated resources
    print("Processing CloudFront Web ACLs")
    cloudfront_resources = generate_waf_cloudfront_report()
    if cloudfront_resources:
        for waf_id, waf_name, distribution_id, distribution_enabled in cloudfront_resources:
            report_data.append({'Region': 'CLOUDFRONT', 'WebACLName': {waf_name}, 'WebACLId': {waf_id}, 'AssociatedResources': {distribution_id}, 'Enabled' : {distribution_enabled}})
            print(f"WAF ID: {waf_id}, CloudFront Distribution ID: {distribution_id}")

    if not bucket_name:
        write_report_to_s3(report_data, bucket_name, object_key, bucket_region)
        print("Report written to S3, report.csv in current folder.")
    else:
        print("No bucket name provided. Report not put to S3, report.csv in current folder.")

if __name__ == "__main__":
    main()










