from flask import Flask, jsonify, request, session
from Authentication import login, check_credentials
from datetime import datetime
import boto3, os
from botocore.exceptions import ClientError

app = Flask(__name__)

app.secret_key = os.urandom(24)


@app.post('/api/v1/login')
def login_route():
    return login()


def get_aws_client(service, session_token, region):
    
    return boto3.client(
        service,
        aws_session_token=session_token,
        region_name=region
    )


@app.get('/api/v1/ecs/clusters')
def get_clusters():
    
    credentials_check = check_credentials()
    if not isinstance(credentials_check, bool):
        return credentials_check  

    session_token = session.get("aws_session_token")
    region = session.get("region")

    ecs_client = get_aws_client("ecs", session_token, region)

    try:
        response = ecs_client.list_clusters()
        cluster_arns = response.get("clusterArns", [])

        if not cluster_arns:
            return jsonify({"message": "No clusters found"}), 404

        detailed_response = ecs_client.describe_clusters(clusters=cluster_arns)
        clusters = detailed_response.get("clusters", [])

        cluster_data = []
        for cluster in clusters:
            cluster_data.append({
                "cluster_name": cluster.get("clusterName"),
                "cluster_arn": cluster.get("clusterArn"),
                "status": cluster.get("status"),
                "running_tasks_count": cluster.get("runningTasksCount"),
                "pending_tasks_count": cluster.get("pendingTasksCount"),
                "active_services_count": cluster.get("activeServicesCount")
            })

        return jsonify({"clusters": cluster_data})

    except Exception as e:
        return jsonify({"error": f"Failed to fetch clusters: {str(e)}"}), 500


@app.get('/api/v1/ecs/clusters/<cluster_name>/services')
def get_services(cluster_name):

    credentials_check = check_credentials()
    if not isinstance(credentials_check, bool):
        return credentials_check  

    session_token = session.get("aws_session_token")
    region = session.get("region")
    
    ecs_client = get_aws_client("ecs", session_token, region)

    try:
        response = ecs_client.describe_clusters(clusters=[cluster_name])
        clusters = response.get("clusters", [])

        if not clusters:
            return jsonify({"error": "Cluster not found"}), 404

        response = ecs_client.list_services(cluster=cluster_name)
        service_arns = response.get("serviceArns", [])

        if not service_arns:
            return jsonify({"message": "No services found in this cluster", "services": []}), 404

        response = ecs_client.describe_services(cluster=cluster_name, services=service_arns)
        services = response.get("services", [])

        service_data = []
        for service in services:
            deployment_status = "UNKNOWN"
            for deployment in service.get("deployments", []):
                if deployment.get("status") == "PRIMARY":
                    deployment_status = "PRIMARY"
                    break

            service_data.append({
                "service_name": service.get("serviceName"),
                "service_arn": service.get("serviceArn"),
                "status": service.get("status"),
                "desired_count": service.get("desiredCount"),
                "running_count": service.get("runningCount"),
                "pending_count": service.get("pendingCount"),
                "deployment_status": deployment_status
            })

        return jsonify({"services": service_data})

    except Exception as e:
        return jsonify({"error": f"Failed to fetch services: {str(e)}"}), 500


def get_bucket_details_logic(bucket_name, s3_client):
    try:
        location = s3_client.get_bucket_location(Bucket=bucket_name)['LocationConstraint']
        response = s3_client.list_buckets()
        creation_date = None
        for bucket in response['Buckets']:
            if bucket['Name'] == bucket_name:
                creation_date = bucket['CreationDate']
                break

        version_response = s3_client.get_bucket_versioning(Bucket=bucket_name)
        version_enabled = version_response.get('Status') == 'Enabled'

        public_access_response = s3_client.get_public_access_block(Bucket=bucket_name)
        public_access_blocked = public_access_response.get('PublicAccessBlockConfiguration') is not None

        objects_list = s3_client.get_paginator('list_objects_v2')
        pages = objects_list.paginate(Bucket=bucket_name)
        object_count = 0
        total_size_bytes = 0
        for page in pages:
            if 'Contents' in page:
                object_count += len(page['Contents'])
                for obj in page['Contents']:
                    total_size_bytes += obj['Size']

        return {
            "name": bucket_name,
            "creation_date": creation_date.strftime('%Y-%m-%dT%H:%M:%SZ') if creation_date else None,
            "region": location,
            "object_count": object_count,
            "total_size_bytes": total_size_bytes,
            "versioning_enabled": version_enabled,
            "public_access_blocked": public_access_blocked
        }
    except ClientError as e:
        return None
    except Exception as e:
        return None


@app.get('/api/v1/s3/buckets')
def get_buckets():
    
    credentials_check = check_credentials()
    if not isinstance(credentials_check, bool):
        return credentials_check  

    session_token = session.get("aws_session_token")
    region = session.get("region")

    s3_client = get_aws_client("s3", session_token, region)  

    try:
        response = s3_client.list_buckets()
        buckets_data = []
        for bucket in response.get('Buckets', []):
            bucket_name = bucket['Name']
            bucket_details = get_bucket_details_logic(bucket_name, s3_client)
            if bucket_details:
                buckets_data.append(bucket_details)

        if not buckets_data:
            return jsonify({"error": "No buckets found", "buckets": []}), 404

        return jsonify({"buckets": buckets_data})

    except Exception as e:
        return jsonify({"error": f"Failed to fetch bucket information: {str(e)}"}), 500


@app.get('/api/v1/s3/buckets/<bucket_name>/details')
def get_bucket_details(bucket_name):
    
    credentials_check = check_credentials()
    if not isinstance(credentials_check, bool):
        return credentials_check  

    session_token = session.get("aws_session_token")
    region = session.get("region")

    s3_client = get_aws_client("s3", session_token, region)  

    try:
        bucket_details = get_bucket_details_logic(bucket_name, s3_client)
        if bucket_details:
            return jsonify(bucket_details)
        else:
            return jsonify({"message": f"Bucket '{bucket_name}' not found or there is no detailed information."}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to fetch bucket details: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5010)
