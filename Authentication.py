from flask import session, jsonify, request
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
import pytz

def login():
    data = request.json
    access_key = data.get("aws_access_key_id")
    secret_key = data.get("aws_secret_access_key")
    region = data.get("aws_region")  

    if not access_key or not secret_key:
        return jsonify({"error": "Credentials are missing"}), 400

    try:
        session_client = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        sts_client = session_client.client("sts")

        sts_client.get_caller_identity()

        temp_credentials = sts_client.get_session_token(DurationSeconds=3600)

        session["aws_session_token"] = temp_credentials["Credentials"]["SessionToken"]
        session["region"] = region
        session["expires_at"] = temp_credentials["Credentials"]["Expiration"].isoformat()

        return jsonify({"message": "Login successful", "expires_at": session["expires_at"]}), 200

    except ClientError:
        return jsonify({"error": "Invalid AWS credentials"}), 401
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


def check_credentials():
    if "aws_session_token" not in session:
        return jsonify({"error": "Please login before making API requests."}), 401
    
    expiration_time_str = session.get("expires_at")

    if expiration_time_str:
        try:
            expiration_time = datetime.fromisoformat(expiration_time_str)

            utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)

            if utc_now > expiration_time:
                return jsonify({"error": "Session has expired. Please log in again."}), 400
    return True
