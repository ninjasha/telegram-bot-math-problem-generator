from openai import AsyncOpenAI
from config import AI_TOKEN
import logging

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=AI_TOKEN,
)

### Function to work with AI-model ###
async def ai_generate(text: str):
    try:
        completion = await client.chat.completions.create(                 # Creating a requst to AI-model
            model="deepseek/deepseek-chat",                                # The name of AI-model
            messages=[{"role": "user", "content": text}],
            max_tokens=1300
        )
        
        if completion.choices and completion.choices[0].message.content:   # Receiving an answer
            return completion.choices[0].message.content
        else:
            logging.error("Empty response from API")
            return None
            
    except Exception as e:
        logging.error(f"Error in ai_generate: {str(e)}")
        return None