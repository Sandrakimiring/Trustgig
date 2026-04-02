import httpx
import json

#takes a freelancers data and returns a writetn trust report
def generate_trust_report(freelancer:dict)-> str:
    applied = freelancer.get("jobs_applied", 0) or 1 #if jobs_applied is 0 (falsy), use 1 instead.
    completed = freelancer.get("jobs_completed", 0)
    completion_rate = round((completed / applied) * 100)

    prompt = f"""

You are an AI assistant for trustgig, a freelance market place for kenyan workers.

Here is teh freelancer data:

*Name: {freelancer.get('name', 'Unknown')}
*Skills: {freelancer.get('skills', 'Not Listed')}
*Location: {freelancer.get('Loaction', 'kenya')}
*Experience Level: {freelancer.get('experience','Unknown')}
*Job applied: {applied}
*Jobs completed: {completed}
*Completion_rate: {completion_rate}%

Write a SHORT trust report (3–4 sentences) that a client would read before hiring.
- Highlight strengths and any concerns honestly.
- Use plain, professional English.
- End with a recommendation: "Recommended", "Use with caution", or "Not recommended".
- Do NOT use bullet points. Write in flowing paragraphs.
""" 
    response = httpx.post(
        headers = {'Content-Type': 'application/json'},
        json = {
            'model': 'GPT-5.4-mini',
            'max_tokens': 1000,
            'messages': 
            ['role': 'user', 'content': prompt]
        },
        timeout = 30.0
    )

    data = response.json()
    return data['content'][0]['text'] #basically digs into the nested data

def get_trust_score_label(completion_rate: float) -> str:
    if completion_rate >= 90:
        return "hightly trusted"
    elif completion_rate >= 70:
        return "Trusted"
    elif completion_rate >= 50:
        return "Use freelancer with caution"
    else:
        return "not recommended"

if __name__("__main__"):
    sample_freelancer = {
        "name": "Mercy Wanjiru",
        "skills": "python, pandas, data analysis",
        "location": "Nairobi",
        "experience": "intermediate",
        "jobs_applied": 10,
        "jobs_completed": 8,
    }
 
    print("Generating trust report for:", sample_freelancer["name"])
    print("─" * 50)
 
    report = generate_trust_report(sample_freelancer)
    print(report)
 
    rate = (sample_freelancer["jobs_completed"] / sample_freelancer["jobs_applied"]) * 100
    print("\nScore Label:", get_trust_score_label(rate))
