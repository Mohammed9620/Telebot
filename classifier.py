import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.1-flash-lite"
_MODEL = MODEL

_PROMPT = (
    "You are filtering messages from Telegram job-posting groups.\n"
    "Your objective is to identify genuine tech/software job vacancies posted by employers or recruiters, "
    "and strictly reject non-tech roles, service offerings, and teaching positions.\n\n"
    "Step 1: Check message intent. Is this an actual hiring employer/recruiter advertising an open job vacancy?\n"
    "- REJECT if someone is offering their own services, looking for clients, advertising freelance availability, "
    "or posting a resume/portfolio (e.g., 'I am a developer available for hire', 'Hire me for your project', "
    "'DM me for web design', 'We provide software development services').\n"
    "Only accept messages where an employer or recruiter is seeking to HIRE someone for a specific vacancy.\n\n"
    "Step 2: Check job role.\n"
    "- REJECT ALL teaching, tutoring, mentoring, instructor, trainer, lecturer, and academic positions "
    "(e.g., 'Python Tutor', 'Computer Science Instructor', 'Coding Bootcamp Teacher', 'CS Lecturer'), "
    "even if the subject being taught is computer science, programming, or software engineering.\n"
    "- REJECT non-software/non-IT roles: mechanical, electrical, civil, or MEP engineering; construction management "
    "or BIM coordination (BIM is construction, not software); sales, customer service, call centers, marketing, "
    "accounting, finance, retail, hospitality, security guards, or administrative assistants.\n"
    "- ACCEPT ONLY roles where the practitioner's primary daily duty is hands-on work in computer science / software: "
    "software development (web, mobile, backend, frontend, full stack), data science, AI / machine learning, "
    "DevOps, cloud engineering, system administration, IT support, networking, database administration, QA/testing, "
    "or cybersecurity.\n\n"
    "Step 3: Extract exact job title(s) mentioned in the message.\n\n"
    "Step 4: Decide is_tech:\n"
    "is_tech MUST be true ONLY if the message is an actual job vacancy (NOT someone offering services) "
    "for a genuine hands-on software/IT practitioner role (NOT teaching/instructing). When in doubt, reject (set is_tech to false).\n\n"
    "Step 5: If is_tech is true, assign the best-matching category from:\n"
    "- Software Development\n"
    "- Data Science & AI\n"
    "- DevOps & Cloud\n"
    "- IT Support & SysAdmin\n"
    "- Cybersecurity\n"
    "- QA & Testing\n"
    "- Database Administration\n"
    "- Other Tech\n"
    "If is_tech is false, set category to 'Non-Tech'.\n\n"
    "Message:\n{text}"
)


_SCHEMA = {
    "type": "object",
    "properties": {
        "job_titles": {"type": "array", "items": {"type": "string"}},
        "is_tech": {"type": "boolean"},
        "category": {"type": "string"},
    },
    "required": ["job_titles", "is_tech", "category"],
}


def classify_job(text: str) -> dict:
    response = _client.models.generate_content(
        model=_MODEL,
        contents=_PROMPT.format(text=text),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_SCHEMA,
        ),
    )
    result = json.loads(response.text)
    is_tech = bool(result.get("is_tech", False))
    category = result.get("category", "Other Tech") if is_tech else "Non-Tech"
    return {
        "job_titles": result.get("job_titles", []),
        "is_tech": is_tech,
        "category": category,
    }


def is_tech_related(text: str) -> bool:
    return classify_job(text)["is_tech"]

