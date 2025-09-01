Email Campaign Bot

add a config.env file with openai api key

A smart email campaign generator that helps you create fully-designed HTML email campaigns using AI. This bot guides you step-by-step, starting with your product URLs, to generate JSON-based campaign data and a live HTML email template.

Features

Product-first workflow: Start by providing 1–10 product URLs. The bot extracts metadata (title, image, price) to understand your products, enabling smarter, context-aware responses.

LLM-assisted conversation: The bot collects campaign information step-by-step (campaign name, audience, tone, call-to-action), offering suggestions and examples to ensure completeness.

JSON generation: Converts the conversation and product data into a structured JSON format.

HTML email generation: Produces a fully responsive, inline-styled HTML email with product listings, call-to-action buttons, and a visually appealing layout.

Live preview and copy: Frontend includes dual windows showing live HTML code streaming and rendered preview. Users can copy the generated HTML with one click.

Backend Workflow

Collect product URLs:
The bot first asks for product links to understand the items in your campaign. This allows it to give smarter responses tailored to your products.

Collect campaign information:
Using a step-by-step approach, the bot collects:

Campaign name

Target audience

Tone of the email

Call-to-action

It confirms completion only once all required fields are gathered.

Generate JSON representation:
Converts the collected information and product metadata into a structured JSON object. This serves as the blueprint for your email campaign.

Generate HTML email:
Calls the LLM to produce a complete HTML email based on the JSON. The HTML includes:

Inline CSS

Responsive layout

Product images, titles, and prices

Call-to-action buttons

Installation

Clone the repository:

git clone https://github.com/yourusername/email-campaign-bot.git
cd email-campaign-bot


Create a virtual environment:

python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows


Install dependencies:

pip install -r requirements.txt


Create a .env file (or config.env) with your OpenAI API key:

OPENAI_API_KEY=your_openai_api_key

Usage

Run the bot in terminal:

python app.py


Provide 1–10 product URLs when prompted.

Answer the bot’s questions about your campaign step-by-step.

Once all info is collected, the bot generates JSON and HTML for your email campaign.
