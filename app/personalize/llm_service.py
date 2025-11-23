import openai
import os


def llm_function(input_text: str, model_id: str = "gpt-4o-mini", max_tokens: int = 450, temperature: float = 0.7) -> str:
    api_key = os.getenv('OPENAI_API_KEY')
    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model_id,  
            messages=[
                {"role": "user", "content": input_text}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=30
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"
    