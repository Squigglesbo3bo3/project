import ollama

# =============================
# Memory
# =============================
messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful medical assistant specialized in pneumonia.\n"
            "- You understand different spellings, typos, and variations of pneumonia-related terms.\n"
            "- Answer any question that is related in meaning to pneumonia, even if the spelling is incorrect.\n"
            "- If a question is completely unrelated to pneumonia, politely say:\n"
            "'Sorry, I only answer pneumonia-related questions.'\n"
            "- Otherwise, answer naturally like ChatGPT.\n"
            "- Be helpful, clear, and conversational.\n"
            "- Do not be overly rigid or scripted.\n"
            "- Always end with: 'This is not medical advice.'"
        )
    }
]

# =============================
# Chat function
# =============================
def ask_chatbot(question):

    messages.append({
        "role": "user",
        "content": question
    })

    response = ollama.chat(
        model="llama3",
        messages=messages
    )

    reply = response['message']['content']

    messages.append({
        "role": "assistant",
        "content": reply
    })

    return reply


# =============================
# Main loop
# =============================
if __name__ == "__main__":
    print("💬 Pneumonia Chatbot (type 'exit' to quit)\n")

    while True:
        question = input("You: ")

        if question.lower() == "exit":
            print("👋 Goodbye!")
            break

        answer = ask_chatbot(question)
        print("\nBot:\n", answer, "\n")