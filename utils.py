def is_greeting(message: str) -> bool:
    greetings = [
        "selam", "selamlar", "merhaba", "hi", "hey", "günaydın",
        "iyi akşamlar", "iyi geceler", "sa", "slm", "nasılsın"
    ]
    message = message.lower()
    return any(greet in message for greet in greetings)