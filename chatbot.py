# chatbot.py

import google.generativeai as genai
from config import API_KEY
from utils import is_greeting

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")
chat = model.start_chat()

def get_bot_response(user_input, messages):
    if "teşekk" in user_input.lower() or "tşk" in user_input.lower():
        return "Rica ederim. Görüşme 5 saniye içinde kapanacak.", True

    if is_greeting(user_input):
        return "Selam! Ceza hukuku ile ilgili bir sorunuz varsa, dinliyorum. ", False

    try:
        previous_msgs = [f"{sender}: {msg}" for sender, msg in messages[-20:] if sender != "Siz"]
        joined_history = "\n".join(previous_msgs)

        response = chat.send_message(
            f"""
            Daha önceki konuşmalar:
            {joined_history}

            Şimdi kullanıcı şunu dedi:
            "{user_input}"

            Lütfen bu mesajı önceki bağlamla birlikte değerlendir. 
            Unutma bir avukat gibi soruları cevaplıyorsun. Meraklı ol.
            Konu ceza hukuku (TCK) kapsamında değerlendirilecekse devam et. önceki konuşmalar ve kullanıcının söylediği 
            herhangi bir şey sorduğun sorularda geçiyorsa devam et. 
            Eğer konu açık değilse, açıklayıcı bir soru sor. 
            Sorduğun sorulara numara koyma. 
            Kısa, net, halkın anlayacağı şekilde konuş.
            Saldırı ve benzeri sözcükleri TCK kapsamında değerlendir.
            """
        )
        return response.text.strip(), False
    except Exception as e:
        return f"Yanıt oluşturulurken hata: {str(e)}", False
