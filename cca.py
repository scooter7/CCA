import streamlit as st
import pandas as pd
from datetime import datetime
import boto3
from botocore.exceptions import NoCredentialsError

AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
bucket_name = "Scooter"
object_key = "competitiveanalyses.csv"

def init_s3_client():
    return boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

def download_from_s3(client, bucket, key):
    try:
        obj = client.get_object(Bucket=bucket, Key=key)
        return pd.read_csv(obj['Body'])
    except:
        return pd.DataFrame()

def upload_to_s3(client, df, bucket, key):
    try:
        csv_buffer = df.to_csv(index=False).encode()
        client.put_object(Bucket=bucket, Key=key, Body=csv_buffer)
        st.success("Data Uploaded Successfully to S3!")
    except NoCredentialsError:
        st.error("Credentials not available")

def display_data_table(data):
    st.write("## Current Data Table")
    st.write(data)

def main():
    st.title("Institutional Analysis Tool")
    s3_client = init_s3_client()

    existing_data = download_from_s3(s3_client, bucket_name, object_key)
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
                upload_to_s3(s3_client, consolidated_data, bucket_name, object_key)
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
                upload_to_s3(s3_client, existing_data, bucket_name, object_key)
                st.success("Narrative Analysis Updated Successfully!")
            else:
                st.error("Record ID does not exist. Please enter a valid ID.")

    with st.form("web_design_archetyping"):
        web_design_record_id = st.number_input("Enter Record ID to Update for Web Design Archetyping", min_value=1, step=1)
        web_design_archetypes = {color: st.slider(f"Web Design - {color} Percentage", 0, 100, 10, 10, key=f"web_{color}") for color in ["Purple", "Green", "Blue", "Maroon", "Yellow", "Orange", "Pink", "Red", "Silver", "Beige"]}
        submit_web_design_button = st.form_submit_button("Submit Web Design Archetyping")

        if submit_web_design_button:
            total_percentage = sum(web_design_archetypes.values())
            if total_percentage != 100:
                st.error("Total percentage must add up to 100%. Currently, it adds up to " + str(total_percentage) + "%.")
            else:
                web_design_data = {f"Web Design - {color} Percentage": percentage for color, percentage in web_design_archetypes.items()}
                for key, value in web_design_data.items():
                    existing_data.loc[existing_data['Record ID'] == web_design_record_id, key] = value
                upload_to_s3(s3_client, existing_data, bucket_name, object_key)
                st.success("Web Design Archetyping Data Updated Successfully!")

    with st.form("web_design_notetaking"):
        web_design_note_record_id = st.number_input("Enter Record ID to Update for Web Design Notetaking", min_value=1, step=1)
        dimensions = st.text_area("What dimensions do you see in the archetypes?")
        best_practices = st.selectbox("Are best practices used?", ["Yes", "No"], key="best_practices")
        negative_space = st.selectbox("Is negative space used strategically?", ["Yes", "No"], key="negative_space")
        key_elements = st.selectbox("Are key elements repeated to create unity and consistency to convey a clear visual brand identity?", ["Yes", "No"], key="key_elements")
        visual_hierarchy = st.selectbox("Is visual hierarchy used to allow readers to perceive what is important and make connections?", ["Yes", "No"], key="visual_hierarchy")
        authenticity_wdn = st.selectbox("How authentic do particular archetype expressions feel?", range(1, 6), key="authenticity_wdn")
        off_archetypes_wdn = st.selectbox("Do any archetypes feel 'off'?", ["Yes", "No"], key="off_archetypes_wdn")
        beige_appearance = st.text_area("How and where does Beige appear--in other words, where is the most opportunity for improvement?")
        user_experience = st.text_area("What is the user experience like?")
        other_comments = st.text_area("Other")

        submit_web_design_note_button = st.form_submit_button("Submit Web Design Notetaking")

        if submit_web_design_note_button:
            if web_design_note_record_id in existing_data['Record ID'].values:
                web_design_note_data = {
                    "WDN - Dimensions": dimensions,
                    "WDN - Best Practices": best_practices,
                    "WDN - Negative Space": negative_space,
                    "WDN - Key Elements": key_elements,
                    "WDN - Visual Hierarchy": visual_hierarchy,
                    "WDN - Authenticity": authenticity_wdn,
                    "WDN - Off Archetypes": off_archetypes_wdn,
                    "WDN - Beige Appearance": beige_appearance,
                    "WDN - User Experience": user_experience,
                    "WDN - Other Comments": other_comments
                }
                for key, value in web_design_note_data.items():
                    existing_data.loc[existing_data['Record ID'] == web_design_note_record_id, key] = value
                upload_to_s3(s3_client, existing_data, bucket_name, object_key)
                st.success("Web Design Notetaking Data Updated Successfully!")
            else:
                st.error("Record ID does not exist. Please enter a valid ID.")

    with st.form("web_imagery_archetyping"):
        web_imagery_record_id = st.number_input("Enter Record ID to Update for Web Imagery Archetyping", min_value=1, step=1)
        web_imagery_archetypes = {color: st.slider(f"Web Imagery - {color} Percentage", 0, 100, 10, 10, key=f"web_imagery_{color}") for color in ["Purple", "Green", "Blue", "Maroon", "Yellow", "Orange", "Pink", "Red", "Silver", "Beige"]}
        submit_web_imagery_button = st.form_submit_button("Submit Web Imagery Archetyping")

        if submit_web_imagery_button:
            total_percentage = sum(web_imagery_archetypes.values())
            if total_percentage != 100:
                st.error("Total percentage must add up to 100%. Currently, it adds up to " + str(total_percentage) + "%.")
            else:
                web_imagery_data = {f"Web Imagery - {color} Percentage": percentage for color, percentage in web_imagery_archetypes.items()}
                for key, value in web_imagery_data.items():
                    existing_data.loc[existing_data['Record ID'] == web_imagery_record_id, key] = value
                upload_to_s3(s3_client, existing_data, bucket_name, object_key)
                st.success("Web Imagery Archetyping Data Updated Successfully!")

    with st.form("web_imagery_notetaking"):
        web_imagery_note_record_id = st.number_input("Enter Record ID to Update for Web Imagery Notetaking", min_value=1, step=1)
        dimensions = st.text_area("What dimensions do you see in the archetypes?")
        best_practices = st.selectbox("Are best practices used?", ["Yes", "No"], key="best_practices_wi")
        negative_space = st.selectbox("Is negative space used strategically?", ["Yes", "No"], key="negative_space_wi")
        key_elements = st.selectbox("Are key elements repeated to create unity and consistency to convey a clear visual brand identity?", ["Yes", "No"], key="key_elements_wi")
        visual_hierarchy = st.selectbox("Is visual hierarchy used to allow readers to perceive what is important and make connections?", ["Yes", "No"], key="visual_hierarchy_wi")
        authenticity_wi = st.selectbox("How authentic do particular archetype expressions feel?", range(1, 6), key="authenticity_wi")
        off_archetypes_wi = st.selectbox("Do any archetypes feel 'off'?", ["Yes", "No"], key="off_archetypes_wi")
        beige_appearance = st.text_area("How and where does Beige appear--in other words, where is the most opportunity for improvement?")
        user_experience = st.text_area("What is the user experience like?")
        other_comments = st.text_area("Other")

        submit_web_imagery_note_button = st.form_submit_button("Submit Web Imagery Notetaking")

        if submit_web_imagery_note_button:
            if web_imagery_note_record_id in existing_data['Record ID'].values:
                web_imagery_note_data = {
                    "WI - Dimensions": dimensions,
                    "WI - Best Practices": best_practices,
                    "WI - Negative Space": negative_space,
                    "WI - Key Elements": key_elements,
                    "WI - Visual Hierarchy": visual_hierarchy,
                    "WI - Authenticity": authenticity_wi,
                    "WI - Off Archetypes": off_archetypes_wi,
                    "WI - Beige Appearance": beige_appearance,
                    "WI - User Experience": user_experience,
                    "WI - Other Comments": other_comments
                }
                for key, value in web_imagery_note_data.items():
                    existing_data.loc[existing_data['Record ID'] == web_imagery_note_record_id, key] = value
                upload_to_s3(s3_client, existing_data, bucket_name, object_key)
                st.success("Web Imagery Notetaking Data Updated Successfully!")
            else:
                st.error("Record ID does not exist. Please enter a valid ID.")

if __name__ == "__main__":
    main()
