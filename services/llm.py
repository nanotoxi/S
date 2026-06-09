import logging
import json
from groq import AsyncGroq
from bot.config import GROQ_API_KEY, GROQ_MODEL_70B, GROQ_MODEL_8B

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = AsyncGroq(api_key=GROQ_API_KEY)
        self.default_model = GROQ_MODEL_70B
        self.fast_model = GROQ_MODEL_8B

    async def get_chat_completion(self, messages, model=None, temperature=0.7, max_tokens=1024, response_format=None):
        target_model = model or self.default_model
        try:
            kwargs = {
                "messages": messages,
                "model": target_model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format:
                kwargs["response_format"] = response_format

            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error with model {target_model}: {e}")
            return None

    async def parse_resume(self, resume_text):
        system_prompt = (
            "You are an expert resume parser. Extract information into STRICT JSON. "
            "Be concise: for responsibilities and achievements, summarize into 3-4 key bullet points max. "
            "Do not include any conversational text. Use the provided schema.\n\n"
            "Schema:\n"
            "{\n"
            "  \"personal\": { \"name\": \"\", \"email\": \"\", \"phone\": \"\", \"location\": \"\" },\n"
            "  \"summary\": \"\",\n"
            "  \"experience\": [ { \"title\": \"\", \"company\": \"\", \"duration\": \"\", \"responsibilities\": [], \"achievements\": [] } ],\n"
            "  \"education\": [ { \"degree\": \"\", \"institution\": \"\", \"year\": \"\", \"grade\": \"\" } ],\n"
            "  \"skills\": { \"technical\": [], \"soft\": [] },\n"
            "  \"certifications\": [],\n"
            "  \"projects\": [ { \"name\": \"\", \"description\": \"\", \"tech_stack\": [], \"link\": \"\" } ],\n"
            "  \"languages\": [],\n"
            "  \"social\": { \"linkedin\": \"\", \"github\": \"\", \"portfolio\": \"\", \"instagram\": \"\" }\n"
            "}"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Resume Text:\n{resume_text}"}
        ]
        
        return await self.get_chat_completion(
            messages, 
            model=self.default_model, 
            temperature=0.1, 
            max_tokens=8000,
            response_format={"type": "json_object"}
        )

    async def generate_jd(self, jd_data):
        system_prompt = (
            "You are a professional HR and recruitment specialist. Create a compelling, well-structured "
            "job description based on the details provided by the employer. Use professional language, "
            "clear headings, and bullet points. Ensure it sounds attractive to high-quality candidates."
        )
        
        user_prompt = f"Please generate a JD from these details:\n{json.dumps(jd_data, indent=2)}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self.get_chat_completion(messages, model=self.default_model, temperature=0.7, max_tokens=2000)

    async def identify_resume_gaps(self, structured_data):
        system_prompt = (
            "You are a recruitment assistant. Analyze the provided structured resume JSON and identify "
            "missing or weak information. PRIORITIZE: Missing LinkedIn URL is a critical gap. "
            "Also look for: missing summary, missing skills, lack of quantified achievements. "
            "Return a JSON object with a list of 'gaps', where each gap has a 'field' name and a 'question' "
            "to ask the user. IMPORTANT: Mention in the question that they can reply with 'None' or 'No' "
            "if they don't have it.\n"
            "Schema: { \"gaps\": [ {\"field\": \"\", \"question\": \"\"} ] }"
        )
        
        user_prompt = f"Structured Data:\n{json.dumps(structured_data, indent=2)}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.get_chat_completion(
            messages, 
            model=self.default_model, 
            temperature=0.3, 
            response_format={"type": "json_object"}
        )
        return response

    async def suggest_jd_fields(self, jd_data: dict, field: str) -> list:
        system_prompt = (
            f"You are an HR specialist. Based on the job details, suggest exactly 8 relevant {field} "
            f"for this role. Be specific to the title, employment type, and experience level. "
            f"Return ONLY a JSON object with key 'items' containing an array of strings. "
            f"Each item must be concise (under 10 words)."
        )
        user_prompt = f"Job details:\n{json.dumps(jd_data, indent=2)}\n\nReturn {{\"items\": [...]}} with 8 {field}."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw = await self.get_chat_completion(
            messages, model=self.default_model, temperature=0.7, max_tokens=400,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(raw).get("items", [])
        except Exception:
            return []

llm_service = LLMService()
