import streamlit as st
import boto3
import pandas as pd
import io
from datetime import datetime

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
        return pd.DataFrame(columns=['Record ID'])

def upload_to_s3(s3_client, data, bucket_name, file_name):
    csv_buffer = io.StringIO()
    data.to_csv(csv_buffer, index=False)
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer.getvalue())

def display_data_table(data):
    filter_column = st.sidebar.selectbox("Select column to filter by", data.columns)
    filter_value = st.sidebar.text_input("Enter value for filtering")

    if filter_value:
        filtered_data = data[data[filter_column].astype(str).str.contains(filter_value, na=False)]
    else:
        filtered_data = data

    st.dataframe(filtered_data)

def main():
    st.title("Institutional Analysis Tool")
    s3_client = init_s3_client()

    existing_data = download_from_s3(s3_client, 'Scooter', 'competitiveanalyses.csv')
    if 'data' not in st.session_state or st.button("Reload Data from S3"):
        st.session_state.data = existing_data
    if 'data' in st.session_state and st.session_state.data is not None:
        display_data_table(st.session_state.data)

    with st.form("institution_info"):
        record_id = st.number_input("Enter Record ID for Update (0 for new record)", min_value=0, step=1)
        full_name = st.text_input("Institution’s Full Name")
        abbreviation = st.text_input("Institution’s Abbreviation")
        institution_type = st.selectbox("Type of Institution", ["Community College", "Private", "Public", "School", "Other"])
        analysis_date = st.date_input("Month/Year of Analysis", datetime.now())
        client_institution = st.text_input("Client Institution")
        website_url = st.text_input("Main Website URL")
        narrative_archetypes = {color: st.slider(f"{color} Archetype Percentage", 0, 100, 10, 10, key=color) for color in ["Purple", "Green", "Blue", "Maroon", "Yellow", "Orange", "Pink", "Red", "Silver", "Beige"]}
        submit_info_button = st.form_submit_button("Submit Institution Info")

        if submit_info_button:
            total_percentage = sum(narrative_archetypes.values())
            if total_percentage != 100:
                st.error("Total percentage must add up to 100%. Currently, it adds up to " + str(total_percentage) + "%.")
            else:
                inst_info_data = {
                    "Record ID": record_id if record_id != 0 else (existing_data['Record ID'].max() + 1 if not existing_data.empty else 1),
                    "Full Name": full_name,
                    "Abbreviation": abbreviation,
                    "Type": institution_type,
                    "Analysis Date": analysis_date.strftime("%Y-%m"),
                    "Client Institution": client_institution,
                    "Website URL": website_url,
                    **narrative_archetypes
                }
                new_data = pd.DataFrame([inst_info_data])
                if record_id == 0:
                    consolidated_data = pd.concat([existing_data, new_data], ignore_index=True)
                else:
                    existing_data.update(new_data)
                    consolidated_data = existing_data
                upload_to_s3(s3_client, consolidated_data, 'Scooter', 'competitiveanalyses.csv')
                st.success("Institution Info Saved Successfully!")

    with st.form("narrative_notetaking"):
        narrative_record_id = st.number_input("Enter Record ID to Update", min_value=1, step=1)
        dimensions = st.text_area("What dimensions do you see in the archetypes?")
        compelling_evidence = st.selectbox("Does the narrative provide compelling evidence with emotive copy?", ["Yes", "No"], key="compelling_evidence_nn")
        storytelling_structure = st.selectbox("Does the copy provide an emotive storytelling structure, or is it more informative?", ["Emotive Storytelling", "More Informative"], key="storytelling_structure_nn")
        copy_content = st.selectbox("Is the copy 'content-heavy,' or is an appropriate amount of space used within the media?", ["Content-Heavy", "Appropriate Amount of Space"], key="copy_content_nn")
        authenticity = st.selectbox("How authentic do particular archetype expressions feel?", range(1, 6), key="authenticity_nn")
        off_archetypes = st.selectbox("Do any archetypes feel 'off'?", ["Yes", "No"], key="off_archetypes_nn")
        story_emergence = st.selectbox("Does a story emerge from the archetypal expressions?", ["Yes", "No"], key="story_emergence_nn")
        archetype_expression = st.selectbox("How well are the archetypes expressed---do they feel emotive and make sense?", ["Yes", "No"], key="archetype_expression_nn")
        tagline_use = st.selectbox("Does the institution use a tagline or taglines?", ["Yes", "No"], key="tagline_use_nn")
        description_students = st.text_area("How does it describe the students and/or institution?")
        beige_appearance = st.text_area("How and where does Beige appear--in other words, where is the most opportunity for improvement?")
        other_comments = st.text_area("Other comments")
        submit_narrative_button = st.form_submit_button("Submit Narrative Analysis")

        if submit_narrative_button:
            if narrative_record_id in existing_data['Record ID'].values:
                narrative_data = {
                    "Dimensions": dimensions,
                    "Compelling Evidence": compelling_evidence,
                    "Storytelling Structure": storytelling_structure,
                    "Copy Content": copy_content,
                    "Authenticity": authenticity,
                    "Off Archetypes": off_archetypes,
                    "Story Emergence": story_emergence,
                    "Archetype Expression": archetype_expression,
                    "Tagline Use": tagline_use,
                    "Description of Students": description_students,
                    "Beige Appearance": beige_appearance,
                    "Other Comments": other_comments
                }
                for key, value in narrative_data.items():
                    existing_data.loc[existing_data['Record ID'] == narrative_record_id, key] = value
                upload_to_s3(s3_client, existing_data, 'Scooter', 'competitiveanalyses.csv')
                st.success("Narrative Analysis Updated Successfully!")
            else:
                st.error("Record ID does not exist. Please enter a valid ID.")

    with st.form("web_design_archetyping"):
        web_design_record_id = st.number_input("Enter Record ID to Update for Web Design", min_value=1, step=1)
        web_design_archetypes = {color: st.slider(f"Web Design - {color} Percentage", 0, 100, 10, 10, key=f"web_{color}") for color in ["Purple", "Green", "Blue", "Maroon", "Yellow", "Orange", "Pink", "Red", "Silver", "Beige"]}
        submit_web_design_button = st.form_submit_button("Submit Web Design Archetyping")

        if submit_web_design_button:
            total_web_design_percentage = sum(web_design_archetypes.values())
            if total_web_design_percentage != 100:
                st.error("Total percentage for Web Design Archetyping must add up to 100%. Currently, it adds up to " + str(total_web_design_percentage) + "%.")
            else:
                if web_design_record_id in existing_data['Record ID'].values:
                    for key, value in web_design_archetypes.items():
                        existing_data.loc[existing_data['Record ID'] == web_design_record_id, f"Web Design - {key}"] = value
                    upload_to_s3(s3_client, existing_data, 'Scooter', 'competitiveanalyses.csv')
                    st.success("Web Design Archetyping Data Updated Successfully!")
                else:
                    st.error("Record ID does not exist. Please enter a valid ID.")

if __name__ == "__main__":
    main()
