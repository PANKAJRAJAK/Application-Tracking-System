import streamlit as st  # pyright: ignore[reportMissingImports]
import pdf2image  # pyright: ignore[reportMissingImports]
import io
import json
import base64
import time
import google.generativeai as genai  # pyright: ignore[reportMissingImports]
from google.api_core.exceptions import ResourceExhausted # type: ignore

# -------------------- Gemini Setup --------------------
genai.configure(api_key=st.secrets.GOOGLE_API_KEY)

# Free-tier friendly model
model = genai.GenerativeModel("models/gemini-flash-latest")

# -------------------- Helper Functions --------------------

def get_gemini_response(prompt, pdf_content, job_description):
    try:
        response = model.generate_content(
            [prompt, pdf_content[0], job_description],
            generation_config={"temperature": 0.2}
        )
        return response.text
    except ResourceExhausted:
        time.sleep(10)
        return "⚠️ Gemini API quota exceeded. Please wait a few seconds and try again."

def get_gemini_response_keywords(prompt, pdf_content, job_description):
    try:
        response = model.generate_content(
            [prompt, pdf_content[0], job_description],
            generation_config={"temperature": 0.2}
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text[7:-3]
        return json.loads(text)
    except (ResourceExhausted, json.JSONDecodeError):
        return None

@st.cache_data(show_spinner=False)
def input_pdf_setup(uploaded_file):
    if uploaded_file is None:
        raise FileNotFoundError("No file uploaded")

    images = pdf2image.convert_from_bytes(uploaded_file.read())
    first_page = images[0]

    img_byte_arr = io.BytesIO()
    first_page.save(img_byte_arr, format="JPEG")

    return [{
        "mime_type": "image/jpeg",
        "data": base64.b64encode(img_byte_arr.getvalue()).decode()
    }]

# -------------------- Streamlit UI --------------------

st.set_page_config(page_title="ATS Resume Scanner")
st.header("Application Tracking System")

input_text = st.text_area("Job Description:")
uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

if "resume" not in st.session_state:
    st.session_state.resume = None

if uploaded_file:
    st.success("PDF uploaded successfully")
    st.session_state.resume = uploaded_file

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    submit1 = st.button("Tell Me About the Resume")

with col2:
    submit2 = st.button("Get Keywords")

with col3:
    submit3 = st.button("Percentage Match")

# -------------------- Prompts --------------------

input_prompt1 = """
You are an experienced Technical Human Resource Manager.
Review the resume against the job description and provide strengths and weaknesses.
"""

input_prompt2 = """
As an expert ATS scanner, identify skills required from the job description.
Return JSON only in this format:
{ "Technical Skills": [], "Analytical Skills": [], "Soft Skills": [] }
"""

input_prompt3 = """
Evaluate the resume against the job description.
Return:
1) Percentage match
2) Missing keywords
3) Final thoughts
"""

# -------------------- Validation --------------------

def validate_inputs():
    if not input_text.strip():
        st.warning("Please enter a job description.")
        return False
    if st.session_state.resume is None:
        st.warning("Please upload a resume.")
        return False
    return True

# -------------------- Button Actions --------------------

if submit1 and validate_inputs():
    with st.spinner("Analyzing resume..."):
        pdf_content = input_pdf_setup(st.session_state.resume)
        response = get_gemini_response(input_prompt1, pdf_content, input_text)
        st.subheader("Resume Evaluation")
        st.write(response)

elif submit2 and validate_inputs():
    with st.spinner("Extracting keywords..."):
        pdf_content = input_pdf_setup(st.session_state.resume)
        response = get_gemini_response_keywords(input_prompt2, pdf_content, input_text)

        if response:
            st.subheader("Extracted Skills")
            st.write(f"**Technical Skills:** {', '.join(response.get('Technical Skills', []))}")
            st.write(f"**Analytical Skills:** {', '.join(response.get('Analytical Skills', []))}")
            st.write(f"**Soft Skills:** {', '.join(response.get('Soft Skills', []))}")
        else:
            st.error("Could not extract skills. Please try again.")

elif submit3 and validate_inputs():
    with st.spinner("Calculating match percentage..."):
        pdf_content = input_pdf_setup(st.session_state.resume)
        response = get_gemini_response(input_prompt3, pdf_content, input_text)
        st.subheader("ATS Match Result")
        st.write(response)