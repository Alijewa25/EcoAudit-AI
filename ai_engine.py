import json
import os
from openai import OpenAI  # Modern OpenAI SDK
from dotenv import load_dotenv

load_dotenv()

# DeepSeek Configuration
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# Use 'deepseek-chat' for normal analysis or 'deepseek-reasoner' (R1) for deep logic
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

class ESGAIAgent:
    """Generates ESG audit summaries using DeepSeek or OpenAI API."""

    def __init__(self):
        if DEEPSEEK_API_KEY:
            self.client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com"
            )
            self.model = DEEPSEEK_MODEL
        elif OPENAI_API_KEY:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            self.model = OPENAI_MODEL
        else:
            raise RuntimeError(
                'No DeepSeek or OpenAI API key configured. Add DEEPSEEK_API_KEY or OPENAI_API_KEY to .env.'
            )

        self.knowledge_base = {
            'CBAM_FACTORS': {
                'Steel': '1.9 tCO2 per ton',
                'Cement': '0.8 tCO2 per ton',
                'Aluminum': '4.5 tCO2 per ton'
            },
            'EMISSION_FACTORS': {
                'Electricity_AZ': 0.411,
                'Natural_Gas': 2.02,
                'Diesel': 2.68
            }
        }

    def build_prompt(self, document_text: str) -> str:
        return (
            'You are an ESG Specialist and Senior Auditor (Environmental Truth-Machine).\n'
            'Use the following emission factors and regulatory logic to review the document text:\n'
            '- Electricity (Azerbaijan): 0.411 kgCO2/kWh\n'
            '- Natural Gas: 2.02 kgCO2/m3\n'
            '- Diesel: 2.68 kgCO2/L\n'
            '- CBAM Steel Factor: 1.9 tCO2/t\n\n'
            'Embedded knowledge for calculations:\n'
            f'{json.dumps(self.knowledge_base, indent=2)}\n\n'
            'Your Task:\n'
            '1. Extract quantities. 2. Compute emissions. 3. Categorize as Scope 1, 2, or 3.\n'
            '4. Check for "Greenwashing" (mismatch between claims and data).\n'
            '5. Provide a summary for EU export markets (CBAM/CSRD).\n\n'
            'Return a polished report in Markdown format. If you find data inconsistencies, highlight them as "🚨 GREENWASHING ALERT".\n\n'
            'Document Text:\n'
            f'{document_text}'
        )

    def analyze_document_text(self, document_text: str) -> str:
        if not document_text or not document_text.strip():
            raise ValueError('Document text is empty or invalid.')

        prompt = self.build_prompt(document_text)

        try:
            # Calling DeepSeek through the OpenAI SDK
            response = self.client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional ESG Auditor specialized in EU regulations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2, # Low temperature for accurate auditing
                max_tokens=2000
            )

            # The SDK shape can vary between versions; normalize safely
            choices = getattr(response, 'choices', None) or response.get('choices') if isinstance(response, dict) else None
            if not choices:
                raise RuntimeError('DeepSeek returned no content.')

            first = choices[0]
            content = None

            # Try common shapes: object with .message.content, dict with ['message']['content'], or .text
            if hasattr(first, 'message'):
                msg = first.message
                if isinstance(msg, dict):
                    content = msg.get('content')
                else:
                    content = getattr(msg, 'content', None)
            elif isinstance(first, dict):
                # e.g. {'message': {'content': '...'}} or {'text': '...'}
                msg = first.get('message')
                if isinstance(msg, dict):
                    content = msg.get('content')
                else:
                    content = first.get('text')
            else:
                content = getattr(first, 'text', None)

            if not content:
                raise RuntimeError('DeepSeek returned no content.')

            return content.strip()

        except Exception as exc:
            return f"DeepSeek Analysis Error: {str(exc)}"