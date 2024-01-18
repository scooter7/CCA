import streamlit as st
import boto3
import pandas as pd
import io
from datetime import datetime

# Initialize boto3 client with credentials from Streamlit Secrets
def init_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
    )

def download_from_s3(s3_client, bucket_name, file_name):
    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key=file_name)
        return pd.read_csv(io.BytesIO(obj['Body'].read()))
    except s3_client.exceptions.NoSuchKey:
        return None

def upload_to_s3(s3_client, data, bucket_name, file_name):
    csv_buffer = io.StringIO()
    data.to_csv(csv_buffer, index=False)
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer.getvalue())

def main():
    st.title("Institutional Analysis Tool")
    s3_client = init_s3_client()

    with st.form("institution_info"):
        full_name = st.text_input("Institution’s Full Name")
        abbreviation = st.text_input("Institution’s Abbreviation")
        institution_type = st.selectbox("Type of Institution", ["Community College", "Private", "Public", "School", "Other"])
        analysis_date = st.date_input("Month/Year of Analysis", datetime.now())
        client_institution = st.text_input("Client Institution")
        website_url = st.text_input("Main Website URL")
        narrative_archetypes = {color: st.slider(f"{color} Archetype Percentage", 0, 100, 10, 10, key=color) for color in ["Purple", "Green", "Blue", "Maroon", "Yellow", "Orange", "Pink", "Red", "Silver", "Beige"]}
        submit_button = st.form_submit_button("Submit")

        if submit_button:
            new_data = pd.DataFrame([{
                "Full Name": full_name,
                "Abbreviation": abbreviation,
                "Type": institution_type,
                "Analysis Date": analysis_date.strftime("%Y-%m"),
                "Client Institution": client_institution,
                "Website URL": website_url,
                **narrative_archetypes
            }])
            existing_data = download_from_s3(s3_client, 'Scooter', 'competitiveanalyses.csv')
            consolidated_data = pd.concat([existing_data, new_data], ignore_index=True) if existing_data is not None else new_data
            upload_to_s3(s3_client, consolidated_data, 'Scooter', 'competitiveanalyses.csv')
            st.success("Data Saved Successfully!")

if __name__ == "__main__":
    main()
