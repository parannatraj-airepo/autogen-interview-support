import os
import streamlit as st
from pypdf import PdfReader
import autogen
from dotenv import load_dotenv

load_dotenv()

# --- 1. PAGE CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="AI Multi-Agent Interview Practice",
    page_icon="💼",
    layout="wide"
)

st.title("💼 AI Multi-Agent Interview Support System")
st.caption("Powered by AutoGen & Streamlit")

# --- 2. HELPER FUNCTIONS ---
def extract_text_from_pdf(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def get_llm_config():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OpenAI API Key not found. Please set OPENAI_API_KEY environment variable.")
        st.stop()
    return {
        "config_list": [{"model": "gpt-4o", "api_key": api_key}],
        "temperature": 0.3,
    }

# --- 3. SESSION STATE INITIALIZATION ---
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "resume_summary" not in st.session_state:
    st.session_state.resume_summary = ""
if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_q_idx" not in st.session_state:
    st.session_state.current_q_idx = 0
if "evaluations" not in st.session_state:
    st.session_state.evaluations = []
if "interview_completed" not in st.session_state:
    st.session_state.interview_completed = False

# --- 4. AUTOGEN AGENTS CREATION ---
def setup_agents(llm_config):
    # Agent 1: Resume Analyst
    resume_analyst = autogen.AssistantAgent(
        name="Resume_Analyst",
        llm_config=llm_config,
        system_message="""You are an expert HR Resume Analyst. 
        Analyze the provided resume and extract:
        1. Primary Technical & Soft Skills
        2. Overall Experience Level (Junior, Mid, Senior)
        3. 3-4 Key Focus Areas for Interviewing
        Be concise, objective, and structured."""
    )

    # Agent 2: Interviewer
    interviewer = autogen.AssistantAgent(
        name="Interviewer",
        llm_config=llm_config,
        system_message="""You are a Technical Interviewer. 
        Based on the candidate's resume analysis, generate 4 distinct, challenging interview questions:
        - Question 1: Core Technical Skill Verification
        - Question 2: System Design / Problem Solving
        - Question 3: Project-based Practical Experience
        - Question 4: Behavioral / Situational Strategy
        Return ONLY the 4 numbered questions separated by line breaks. Do not include extra conversational filler."""
    )

    # Agent 3: Evaluator
    evaluator = autogen.AssistantAgent(
        name="Evaluator",
        llm_config=llm_config,
        system_message="""You are a Senior Technical Hiring Manager and Evaluator.
        Given an interview question and the candidate's answer:
        1. Provide a score from 0 to 100 based on accuracy, clarity, and completeness.
        2. Highlight Key Strengths in the answer.
        3. Highlight Areas for Improvement.
        Format response strictly as:
        SCORE: <number>
        STRENGTHS: <text>
        IMPROVEMENTS: <text>"""
    )

    user_proxy = autogen.UserProxyAgent(
        name="User_Proxy",
        human_input_mode="NEVER",
        code_execution_config=False,
    )

    return user_proxy, resume_analyst, interviewer, evaluator

# --- 5. SIDEBAR: RESUME UPLOAD ---
with st.sidebar:
    st.header("📄 Resume Upload")
    uploaded_file = st.file_uploader("Upload candidate resume (PDF)", type=["pdf"])
    
    if uploaded_file and not st.session_state.interview_started:
        if st.button("Start Interview Process", type="primary"):
            llm_config = get_llm_config()
            user_proxy, resume_analyst, interviewer, evaluator = setup_agents(llm_config)

            with st.spinner("Agent 1: Analyzing Resume..."):
                resume_text = extract_text_from_pdf(uploaded_file)
                analysis_msg = user_proxy.initiate_chat(
                    resume_analyst,
                    message=f"Analyze this resume:\n{resume_text}",
                    max_turns=1,
                    summary_method="last_msg"
                )
                st.session_state.resume_summary = analysis_msg.summary

            with st.spinner("Agent 2: Generating Interview Questions..."):
                questions_msg = user_proxy.initiate_chat(
                    interviewer,
                    message=f"Generate 4 interview questions based on this profile:\n{st.session_state.resume_summary}",
                    max_turns=1,
                    summary_method="last_msg"
                )
                raw_qs = questions_msg.summary.strip().split("\n")
                st.session_state.questions = [q.strip() for q in raw_qs if q.strip()]

            st.session_state.interview_started = True
            st.rerun()

    if st.button("Reset Session"):
        st.session_state.clear()
        st.rerun()

# --- 6. MAIN WORKFLOW ---

# Case A: Initial State
if not st.session_state.interview_started:
    st.info("👈 Please upload a PDF resume in the sidebar to begin.")

# Case B: Ongoing Interview
elif st.session_state.interview_started and not st.session_state.interview_completed:
    st.subheader("📌 Profile Breakdown")
    st.markdown(st.session_state.resume_summary)
    st.divider()

    q_idx = st.session_state.current_q_idx
    total_q = len(st.session_state.questions)

    if q_idx < total_q:
        st.progress((q_idx) / total_q, text=f"Question {q_idx + 1} of {total_q}")
        
        current_q = st.session_state.questions[q_idx]
        st.markdown(f"### **Question {q_idx + 1}:**")
        st.warning(current_q)

        candidate_answer = st.text_area("Your Response:", height=150, key=f"answer_{q_idx}")

        if st.button("Submit Answer", type="primary"):
            if not candidate_answer.strip():
                st.error("Please provide an answer before submitting.")
            else:
                with st.spinner("Agent 3: Evaluating response..."):
                    llm_config = get_llm_config()
                    user_proxy, _, _, evaluator = setup_agents(llm_config)
                    
                    eval_prompt = f"Question: {current_q}\nCandidate Answer: {candidate_answer}"
                    eval_res = user_proxy.initiate_chat(
                        evaluator,
                        message=eval_prompt,
                        max_turns=1,
                        summary_method="last_msg"
                    )

                    st.session_state.evaluations.append({
                        "question": current_q,
                        "answer": candidate_answer,
                        "evaluation": eval_res.summary
                    })

                    if q_idx + 1 < total_q:
                        st.session_state.current_q_idx += 1
                    else:
                        st.session_state.interview_completed = True
                    st.rerun()

# Case C: Interview Completed (Final Report & Scores)
elif st.session_state.interview_completed:
    st.balloons()
    st.header("📊 Interview Performance & Score Card")
    st.divider()

    total_score = 0
    parsed_evals = []

    for item in st.session_state.evaluations:
        eval_text = item["evaluation"]
        score = 0
        strengths = ""
        improvements = ""

        # Parse evaluation response format
        for line in eval_text.split("\n"):
            if line.startswith("SCORE:"):
                try:
                    score = int(line.replace("SCORE:", "").strip())
                except ValueError:
                    score = 70
            elif line.startswith("STRENGTHS:"):
                strengths = line.replace("STRENGTHS:", "").strip()
            elif line.startswith("IMPROVEMENTS:"):
                improvements = line.replace("IMPROVEMENTS:", "").strip()

        total_score += score
        parsed_evals.append({
            "question": item["question"],
            "answer": item["answer"],
            "score": score,
            "strengths": strengths or eval_text,
            "improvements": improvements or "None noted."
        })

    avg_score = round(total_score / len(parsed_evals), 1)

    # Score Overview Cards
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Overall Performance Score", f"{avg_score} / 100")
    with col2:
        if avg_score >= 80:
            st.success("Verdict: Strong Candidate (Hire Recommendation)")
        elif avg_score >= 60:
            st.warning("Verdict: Moderate Performance (Needs Further Assessment)")
        else:
            st.error("Verdict: Needs Improvement")

    st.subheader("Detailed Breakdown by Question")

    for idx, eval_data in enumerate(parsed_evals, start=1):
        with st.expander(f"Question {idx}: Score {eval_data['score']}/100", expanded=True):
            st.write(f"**Question:** {eval_data['question']}")
            st.write(f"**Your Answer:** {eval_data['answer']}")
            st.markdown(f"**Score:** `{eval_data['score']}/100`")
            st.markdown(f"**Strengths:** {eval_data['strengths']}")
            st.markdown(f"**Areas for Improvement:** {eval_data['improvements']}")