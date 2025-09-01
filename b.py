import os
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from dotenv import load_dotenv
import time

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from openai import OpenAI

# ---------------- INIT ----------------
load_dotenv("config.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o-mini", temperature=0.7)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------- SESSION STATE ----------------
session_state = {
    "products": [],
    "campaign_info_complete": False,
    "campaign_json": None
}

# ---------------- PRODUCT METADATA ----------------
def extract_metadata(url):
    try:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")

        title = soup.find("meta", property="og:title")
        image = soup.find("meta", property="og:image")
        title = title["content"] if title else (soup.title.string if soup.title else "Unknown Product")
        image = image["content"] if image else "https://via.placeholder.com/300x200?text=No+Image"

        text = soup.get_text()
        match = re.search(r"\$[\d,]+(\.\d{1,2})?", text)
        price = match.group() if match else None

        return {"url": url, "title": title.strip(), "image": image, "price": price}
    except Exception as e:
        return {
            "url": url,
            "title": f"Product from {urlparse(url).netloc}",
            "image": "https://via.placeholder.com/300x200?text=No+Image",
            "price": None,
            "error": str(e)
        }

# ---------------- STAGE 1: LLM-assisted info collection ----------------
SYSTEM_PROMPT_STAGE1 = """
You are a friendly email marketing assistant. Your goal is:
1. Collect 1-10 product URLs from the user.
2. Collect campaign info step-by-step: campaign name, audience, tone, call-to-action. Give examples to help user decide.
3. Only confirm completion when all fields are collected.
4. Ask for missing info in a friendly manner, one question at a time.
5. Once you feel like you have all the information required, reply with "all information collected" ONLY.
"""

def stage1_collect_info(user_message):
    
    url_pattern = re.compile(r"https?://\S+")
    links = url_pattern.findall(user_message)
    for link in links:
        if len(session_state["products"]) < 10:
            metadata = extract_metadata(link.strip())
            session_state["products"].append(metadata)

    
    llm_messages = [SystemMessage(content=SYSTEM_PROMPT_STAGE1)]
    for msg in memory.chat_memory.messages:
        if hasattr(msg, 'type') and msg.type == "human":
            llm_messages.append(HumanMessage(content=msg.content))
        else:
            llm_messages.append(AIMessage(content=msg.content))

    user_msg_content = f"""
Products collected so far: {json.dumps(session_state['products'], indent=2)}
User says: {user_message}
"""
    llm_messages.append(HumanMessage(content=user_msg_content))
    response = llm.invoke(llm_messages)
    reply_content = response.content
    memory.chat_memory.add_user_message(user_message)
    memory.chat_memory.add_ai_message(reply_content)

   
    if "all information collected" in reply_content.lower():
        session_state["campaign_info_complete"] = True

    return reply_content

# ---------------- STAGE 2: Generate JSON via LLM ----------------
def generate_json_via_llm(summary, products):
    """
    Call the LLM to generate structured JSON from conversation summary + products.
    """
    prompt = f"""
You are an expert assistant that converts a summary of an email campaign into structured JSON.
The summary of the conversation is:

{summary}

Products collected:

{json.dumps(products, indent=2)}

Requirements:
1. Output a valid JSON object with these fields:
   - campaign_name
   - audience
   - tone
   - call_to_action
   - products (each with title, url, image, price)
2. Return ONLY JSON, no explanations or extra text.
"""
    response = llm.invoke([
        SystemMessage(content="You are a JSON generator."),
        HumanMessage(content=prompt)
    ])

   
    content = response.content.strip()
    if content.startswith("```"):
        # Remove ```json or ```
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    try:
        campaign_json = json.loads(content)
        session_state["campaign_json"] = campaign_json
        return campaign_json
    except json.JSONDecodeError:
        print("❌ Failed to parse JSON from LLM output:")
        print(content)
        return None

# ---------------- STAGE 3: Generate HTML ----------------
def generate_html_from_json(campaign_json):
    html_prompt = f"""
Create a complete HTML email campaign based on this JSON:

{json.dumps(campaign_json, indent=2)}

Requirements:
1. Complete HTML (DOCTYPE, head, body)
2. Inline CSS, responsive design
3. Include products with title, image, price
4. Include call-to-action and visually appealing layout

Return ONLY HTML code without explanations or any text. Strictly PURE Html.
"""
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert email designer. Return ONLY HTML."},
            {"role": "user", "content": html_prompt}
        ],
        temperature=0.7,
        max_tokens=4000,
        stream=True,
    )

    html_email = ""
    for event in stream:
        if hasattr(event, "choices") and event.choices:
            delta = event.choices[0].delta
            if delta and getattr(delta, "content", None):
                chunk = delta.content
                html_email += chunk
                print(chunk, end="", flush=True)
                time.sleep(0.01)
    return html_email

# ---------------- MAIN ----------------
if __name__ == "__main__":
    print("🤖 Email Campaign Bot Started!\n")
    print("Bot: Hi! Let's start your email campaign. Please provide 1 to 10 product URLs.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # Stage 1: LLM-assisted info collection
        bot_reply = stage1_collect_info(user_input)
        print(f"Bot: {bot_reply}\n")

        if session_state["campaign_info_complete"]:
            # Stage 2: Generate JSON via LLM
            summary = "\n".join([msg.content for msg in memory.chat_memory.messages])
            campaign_json = generate_json_via_llm(summary, session_state["products"])

            if campaign_json:
                print("Bot: ✅ JSON generated via LLM!\n")
                print(json.dumps(campaign_json, indent=2))

                # Stage 3: Generate HTML
                print("\nBot: Generating HTML...\n")
                generate_html_from_json(campaign_json)
                print("\n✅ HTML generation complete!")
            else:
                print("Bot: ❌ Failed to generate JSON via LLM.")
            break
