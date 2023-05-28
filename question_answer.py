import load

history = [] 

def add_to_history(new_input):
    history.append(new_input)

def get_qa_result(question: str) -> str:
    answer=load.returnAnswer(question, history)
    add_to_history(f"Usuario: {question}")
    add_to_history(f"Bot: {answer}")
    return answer
