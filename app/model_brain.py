# # model_brain.py
# import ollama


# def query_model(prompt: str) -> str:
#     """Send prompt to Ollama model and return the response."""
#     response = ollama.chat(
#         model="tinyllama:latest",  # replace with your downloaded model
#         messages=[{"role": "user", "content": prompt}]
#     )
#     print(response["message"])
#     return response['message']['content']


import ollama

def query_model(prompt: str):
    system_prompt = """
    You are a SQL generator.

    Return ONLY valid SQL.
    Do not explain.
    Do not add extra text.
    Do not wrap in quotes.
    Return only the query.
    Never reply with text message unless asked to.
    """
    user_prompt = prompt
    print("Query has been passed to the model.")
    # Pseudocode depending on your LLM library
    response = ollama.chat(
        model="phi3:mini",  # replace with your downloaded model
        messages=[{"role": "user", "content": prompt}]
    )
    print("Now the model has replied")
    return response['message']['content']
