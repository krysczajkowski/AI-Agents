import logging

# Konfiguracja loggera do zapisu do pliku
logging.basicConfig(
    filename='agent.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Logujemy informacje dotyczące działania agenta
logging.info("Agent started working")

# Finalna odpowiedź dla użytkownika, wyświetlana w głównym terminalu
final_answer = "Hello, this is your answer!"
print(final_answer)
