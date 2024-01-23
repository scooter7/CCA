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
    filtered_data = data[data[filter_column].astype(str).str.contains(filter_value, na=False)] if filter_value else data
    st.dataframe(filtered_data)

def generate_unique_record_id(existing_data):
    if existing_data.empty or 'Record ID' not in existing_data.columns:
        return 1
    else:
        return existing_data['Record ID'].max() + 1

def main():
    st.title("Institutional Analysis Tool")
    s3_client = init_s3_client()
    existing_data = download_from_s3(s3_client, 'Scooter', 'competitiveanalyses.csv')
    
    # Check if the 'Reload Data from S3' button is clicked
    if 'data' not in st.session_state or st.button("Reload Data from S3"):
        st.session_state.data = existing_data
    
    # Display the data from S3 if it exists
    if 'data' in st.session_state and st.session_state.data is not None:
        st.write("Data from S3:")
        st.dataframe(st.session_state.data)

    with st.form("institution_info"):
        record_id = st.number_input("Enter Record ID for Update (0 for new record)", min_value=0, step=1)
        full_name = st.text_input("Institution’s Full Name")
        abbreviation = st.text_input("Institution’s Abbreviation")
        institution_type = st.selectbox("Type of Institution", ["Community College", "Private", "Public", "School", "Other"])
        analysis_date = st.date_input("Month/Year of Analysis", datetime.now())
        client_institution = st.text_input("Client Institution")
        website_url = st.text_input("Main Website URL")
        purple = st.slider("Purple Archetype Percentage", 0, 100, 10)
        green = st.slider("Green Archetype Percentage", 0, 100, 10)
        blue = st.slider("Blue Archetype Percentage", 0, 100, 10)
        maroon = st.slider("Maroon Archetype Percentage", 0, 100, 10)
        yellow = st.slider("Yellow Archetype Percentage", 0, 100, 10)
        orange = st.slider("Orange Archetype Percentage", 0, 100, 10)
        pink = st.slider("Pink Archetype Percentage", 0, 100, 10)
        red = st.slider("Red Archetype Percentage", 0, 100, 10)
        silver = st.slider("Silver Archetype Percentage", 0, 100, 10)
        beige = st.slider("Beige Archetype Percentage", 0, 100, 10)
        submit_info_button = st.form_submit_button("Submit Institution Info")

        if submit_info_button:
            total_percentage = purple + green + blue + maroon + yellow + orange + pink + red + silver + beige
            if total_percentage != 100:
                st.error("Total percentage must add up to 100%. Currently, it adds up to " + str(total_percentage) + "%.")
            else:
                new_record_id = generate_unique_record_id(existing_data) if record_id == 0 else record_id
                inst_info_data = {
                    "Record ID": new_record_id,
                    "Full Name": full_name,
                    "Abbreviation": abbreviation,
                    "Type": institution_type,
                    "Analysis Date": analysis_date.strftime("%Y-%m"),
                    "Client Institution": client_institution,
                    "Website URL": website_url,
                    "Purple": purple,
                    "Green": green,
                    "Blue": blue,
                    "Maroon": maroon,
                    "Yellow": yellow,
                    "Orange": orange,
                    "Pink": pink,
                    "Red": red,
                    "Silver": silver,
                    "Beige": beige
                }
                if record_id == 0:
                    new_data = pd.DataFrame([inst_info_data])
                    existing_data = pd.concat([existing_data, new_data], ignore_index=True)
                else:
                    for key, value in inst_info_data.items():
                        existing_data.loc[existing_data['Record ID'] == record_id, key] = value
                upload_to_s3(s3_client, existing_data, 'Scooter', 'competitiveanalyses.csv')
                st.success("Institution Info Saved Successfully!")

    with st.form("narrative_notetaking"):
        narrative_record_id = st.number_input("Enter Record ID to Update", min_value=1, step=1)
        dimensions = st.text_area("What dimensions do you see in the archetypes?")
        compelling_evidence = st.selectbox("Does the narrative provide compelling evidence with emotive copy?", ["Yes", "No"])
        storytelling_structure = st.selectbox("Does the copy provide an emotive storytelling structure, or is it more informative?", ["Emotive Storytelling", "More Informative"])
        copy_content = st.selectbox("Is the copy 'content-heavy,' or is an appropriate amount of space used within the media?", ["Content-Heavy", "Appropriate Amount of Space"])
        authenticity = st.selectbox("How authentic do particular archetype expressions feel?", range(1, 6))
        off_archetypes = st.selectbox("Do any archetypes feel 'off'?", ["Yes", "No"])
        story_emergence = st.selectbox("Does a story emerge from the archetypal expressions?", ["Yes", "No"])
        archetype_expression = st.selectbox("How well are the archetypes expressed---do they feel emotive and make sense?", ["Yes", "No"])
        tagline_use = st.selectbox("Does the institution use a tagline or taglines?", ["Yes", "No"])
        description_students = st.text_area("How does it describe the students and/or institution?")
        beige_appearance = st.text_area("How and where does Beige appear--in other words, where is the most opportunity for improvement?")
        other_comments = st.text_area("Other Comments")
        submit_narrative_button = st.form_submit_button("Submit Narrative Analysis")

        if submit_narrative_button:
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
            if narrative_record_id in existing_data['Record ID'].values:
                for key, value in narrative_data.items():
                    existing_data.loc[existing_data['Record ID'] == narrative_record_id, key] = value
                upload_to_s3(s3_client, existing_data, 'Scooter', 'competitiveanalyses.csv')
                st.success("Narrative Analysis Updated Successfully!")
            else:
                st.error("Record ID does not exist. Please enter a valid ID.")

    with st.form("web_design_archetyping"):
        web_design_record_id = st.number_input("Enter Record ID to Update for Web Design Archetyping", min_value=1, step=1)
        web_design_purple = st.slider("Web Design - Purple Percentage", 0, 100, 10)
        web_design_green = st.slider("Web Design - Green Percentage", 0, 100, 10)
        web_design_blue = st.slider("Web Design - Blue Percentage", 0, 100, 10)
        web_design_maroon = st.slider("Web Design - Maroon Percentage", 0, 100, 10)
        web_design_yellow = st.slider("Web Design - Yellow Percentage", 0, 100, 10)
        web_design_orange = st.slider("Web Design - Orange Percentage", 0, 100, 10)
        web_design_pink = st.slider("Web Design - Pink Percentage", 0, 100, 10)
        web_design_red = st.slider("Web Design - Red Percentage", 0, 100, 10)
        web_design_silver = st.slider("Web Design - Silver Percentage", 0, 100, 10)
        web_design_beige = st.slider("Web Design - Beige Percentage", 0, 100, 10)
        wdn_dimensions = st.text_area("WDN - Dimensions")
        wdn_best_practices = st.selectbox("WDN - Best Practices", ["Yes", "No"])
        wdn_negative_space = st.selectbox("WDN - Negative Space", ["Yes", "No"])
        wdn_key_elements = st.selectbox("WDN - Key Elements", ["Yes", "No"])
        wdn_visual_hierarchy = st.selectbox("WDN - Visual Hierarchy", ["Yes", "No"])
        wdn_authenticity = st.selectbox("WDN - Authenticity", range(1, 6))
        wdn_off_archetypes = st.selectbox("WDN - Off Archetypes", ["Yes", "No"])
        wdn_beige_appearance = st.text_area("WDN - Beige Appearance")
        wdn_user_experience = st.text_area("WDN - User Experience")
        wdn_other_comments = st.text_area("WDN - Other Comments")
        submit_web_design_button = st.form_submit_button("Submit Web Design Archetyping")

        if submit_web_design_button:
            web_design_data = {
                "Web Design - Purple": web_design_purple,
                "Web Design - Green": web_design_green,
                "Web Design - Blue": web_design_blue,
                "Web Design - Maroon": web_design_maroon,
                "Web Design - Yellow": web_design_yellow,
                "Web Design - Orange": web_design_orange,
                "Web Design - Pink": web_design_pink,
                "Web Design - Red": web_design_red,
                "Web Design - Silver": web_design_silver,
                "Web Design - Beige": web_design_beige,
                "WDN - Dimensions": wdn_dimensions,
                "WDN - Best Practices": wdn_best_practices,
                "WDN - Negative Space": wdn_negative_space,
                "WDN - Key Elements": wdn_key_elements,
                "WDN - Visual Hierarchy": wdn_visual_hierarchy,
                "WDN - Authenticity": wdn_authenticity,
                "WDN - Off Archetypes": wdn_off_archetypes,
                "WDN - Beige Appearance": wdn_beige_appearance,
                "WDN - User Experience": wdn_user_experience,
                "WDN - Other Comments": wdn_other_comments
            }
            if web_design_record_id in existing_data['Record ID'].values:
                for key, value in web_design_data.items():
                    existing_data.loc[existing_data['Record ID'] == web_design_record_id, key] = value
                upload_to_s3(s3_client, existing_data, 'Scooter', 'competitiveanalyses.csv')
                st.success("Web Design Archetyping Data Updated Successfully!")
            else:
                st.error("Record ID does not exist. Please enter a valid ID.")

    with st.form("web_imagery_archetyping"):
        web_imagery_record_id = st.number_input("Enter Record ID to Update for Web Imagery Archetyping", min_value=1, step=1)
        web_imagery_purple = st.slider("Web Imagery - Purple Percentage", 0, 100, 10)
        web_imagery_green = st.slider("Web Imagery - Green Percentage", 0, 100, 10)
        web_imagery_blue = st.slider("Web Imagery - Blue Percentage", 0, 100, 10)
        web_imagery_maroon = st.slider("Web Imagery - Maroon Percentage", 0, 100, 10)
        web_imagery_yellow = st.slider("Web Imagery - Yellow Percentage", 0, 100, 10)
        web_imagery_orange = st.slider("Web Imagery - Orange Percentage", 0, 100, 10)
        web_imagery_pink = st.slider("Web Imagery - Pink Percentage", 0, 100, 10)
        web_imagery_red = st.slider("Web Imagery - Red Percentage", 0, 100, 10)
        web_imagery_silver = st.slider("Web Imagery - Silver Percentage", 0, 100, 10)
        web_imagery_beige = st.slider("Web Imagery - Beige Percentage", 0, 100, 10)
        submit_web_imagery_button = st.form_submit_button("Submit Web Imagery Archetyping")

    if submit_web_imagery_button:
        web_imagery_data = {
            "Web Imagery - Purple": web_imagery_purple,
            "Web Imagery - Green": web_imagery_green,
            "Web Imagery - Blue": web_imagery_blue,
            "Web Imagery - Maroon": web_imagery_maroon,
            "Web Imagery - Yellow": web_imagery_yellow,
            "Web Imagery - Orange": web_imagery_orange,
            "Web Imagery - Pink": web_imagery_pink,
            "Web Imagery - Red": web_imagery_red,
            "Web Imagery - Silver": web_imagery_silver,
            "Web Imagery - Beige": web_imagery_beige
        }
        if web_imagery_record_id in existing_data['Record ID'].values:
            for key, value in web_imagery_data.items():
                existing_data.loc[existing_data['Record ID'] == web_imagery_record_id, key] = value
            upload_to_s3(s3_client, existing_data, 'Scooter', 'competitiveanalyses.csv')
            st.success("Web Imagery Archetyping Data Updated Successfully!")

    with st.form("imagery_notetaking"):
        imagery_record_id = st.number_input("Enter Record ID to Update for Imagery Notetaking", min_value=1, step=1)
        imagery_dimensions = st.text_area("What dimensions do you see in the archetypes? (For ex. “Caring Purple” vs. “Supportive Purple” and why/how)")
        imagery_authenticity = st.selectbox("How authentic do particular archetype expressions feel?", range(1, 6))
        imagery_off_archetypes = st.selectbox("Do any archetypes feel 'off'?", ["Yes", "No"])
        imagery_quality = st.selectbox("What's the quality like?", range(1, 6))
        imagery_expression = st.selectbox("How well are the archetypes expressed---do they feel emotive and make sense within the bigger picture?", range(1, 6))
        imagery_diversity = st.selectbox("Does the imagery represent an adequate amount of diversity?", ["Yes", "No"])
        imagery_beige_appearance = st.text_area("How and where does Beige appear--in other words, where is the most opportunity for improvement?")
        imagery_other_comments = st.text_area("Other comments")
        submit_imagery_notetaking_button = st.form_submit_button("Submit Imagery Notetaking")

    if submit_imagery_notetaking_button:
        imagery_notetaking_data = {
            "Imagery Dimensions": imagery_dimensions,
            "Imagery Authenticity": imagery_authenticity,
            "Imagery Off Archetypes": imagery_off_archetypes,
            "Imagery Quality": imagery_quality,
            "Imagery Expression": imagery_expression,
            "Imagery Diversity": imagery_diversity,
            "Imagery Beige Appearance": imagery_beige_appearance,
            "Imagery Other Comments": imagery_other_comments
        }
        new_data = pd.DataFrame([imagery_notetaking_data])
        if imagery_record_id in existing_data['Record ID'].values:
            existing_data.update(new_data.set_index('Record ID'), overwrite=False)
            upload_to_s3(s3_client, existing_data, 'Scooter', 'competitiveanalyses.csv')
            st.success("Imagery Notetaking Data Updated Successfully!")
        else:
            st.error("Record ID does not exist. Please enter a valid ID.")

if __name__ == "__main__":
    main()
