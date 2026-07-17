# ----------------------------------------------------------
# LEGACY: Gemini integration helper
#
# This module is retained for reference only. The current
# project uses OpenAI via the OpenAI Python SDK instead of
# the deprecated Gemini integration.
# ----------------------------------------------------------

from google import genai

def ask_gemini(api_key, context, question):

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an HR Assistant.

Answer ONLY from the HR policy below.

If the answer is not found, say:

'I could not find this information in the HR policies.'

HR Policies:

{context}

Question:
{question}
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:

        print("========== GEMINI ERROR ==========")
        print(e)
        print("==================================")

        error = str(e)

        if "429" in error:
            return "⚠️ The AI request limit has been reached. Please try again later or contact the administrator."

        elif "503" in error:
            return "⚠️ The AI service is temporarily busy. Please wait a few seconds and try again."

        else:
            return "⚠️ An unexpected error occurred. Please contact the administrator."


# ----------------------------------------------------------
# Function Name : check_gemini_status()
#
# Purpose:
# Check whether the Gemini API service is currently available.
#
# Returns:
# 🟢 Online - If the API responds successfully.
# 🔴 Busy   - If the API is unavailable or overloaded.
# ----------------------------------------------------------

def check_gemini_status(api_key):

    try:

        client = genai.Client(api_key=api_key)

        client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Hello"
        )

        return "🟢 Online"

    except:

        return "🔴 Busy"
