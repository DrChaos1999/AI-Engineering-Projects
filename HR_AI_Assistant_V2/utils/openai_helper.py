from openai import OpenAI, OpenAIError


def ask_openai(api_key: str, context: str, question: str, model: str = "gpt-4o-mini") -> str:
    """Generate an HR answer from OpenAI using the policy text context."""
    client = OpenAI(api_key=api_key)

    system_prompt = (
        "You are an HR assistant for Trimco Bangladesh. "
        "Answer using only the provided HR policy content. "
        "If the answer cannot be found in the policies, say: "
        "I could not find this information in the HR policies."
    )

    user_prompt = f"""
HR Policies:
{context}

Question:
{question}
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=600,
            temperature=0.2,
        )

        if response.choices and response.choices[0].message:
            message = response.choices[0].message
            if isinstance(message, dict):
                content = message.get("content", "")
            else:
                content = getattr(message, "content", None)
                if content is None:
                    content = getattr(message, "text", "")
            if content:
                return content.strip()

        return "⚠️ The AI service did not return a valid answer."

    except OpenAIError as exc:
        error_text = str(exc)
        if "429" in error_text:
            return "⚠️ The OpenAI request limit has been reached. Please try again later."
        if "503" in error_text:
            return "⚠️ The OpenAI service is temporarily busy. Please try again later."
        return f"⚠️ An unexpected OpenAI error occurred: {error_text}"
    except Exception as exc:
        return f"⚠️ An unexpected error occurred while communicating with OpenAI: {exc}"
