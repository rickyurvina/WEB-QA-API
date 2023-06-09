
import pandas as pd
import tiktoken
import openai
import numpy as np
from openai.embeddings_utils import distances_from_embeddings, cosine_similarity
import os
from config import OPENAI_API_KEY
from config import OPENAI_ORGANIZATION
from config import MAX_TOKENS
from config import MODEL_EMBEDDINGS
from config import MAX_TOKENS
from config import MAX_LEN
from config import MAX_TOKENS_ANSWER
from config import MODEL_OPENAI
from config import TEMPERATURE
openai.organization = OPENAI_ORGANIZATION
openai.api_key = OPENAI_API_KEY
openai.Model.list()

def remove_newlines(serie):
    serie = serie.str.replace('\n', ' ')
    serie = serie.str.replace('\\n', ' ')
    serie = serie.str.replace('  ', ' ')
    serie = serie.str.replace('  ', ' ')
    return serie

# Create a list to store the text files
texts = []


tokenizer = tiktoken.get_encoding("cl100k_base")

df = pd.read_csv('processed/scraped.csv', index_col=0)
df.columns = ['title', 'text']

df['n_tokens'] = df.text.apply(lambda x: len(tokenizer.encode(x)))

df.n_tokens.hist()

max_tokens = MAX_TOKENS

# Function to split the text into chunks of a maximum number of tokens
def split_into_many(text, max_tokens=max_tokens):
    # Split the text into sentences
    sentences = text.split('. ')

    # Get the number of tokens for each sentence
    n_tokens = [len(tokenizer.encode(" " + sentence)) for sentence in sentences]

    chunks = []
    tokens_so_far = 0
    chunk = []

    # Loop through the sentences and tokens joined together in a tuple
    for sentence, token in zip(sentences, n_tokens):

        # If the number of tokens so far plus the number of tokens in the current sentence is greater
        # than the max number of tokens, then add the chunk to the list of chunks and reset
        # the chunk and tokens so far
        if tokens_so_far + token > max_tokens:
            chunks.append(". ".join(chunk) + ".")
            chunk = []
            tokens_so_far = 0

        # If the number of tokens in the current sentence is greater than the max number of
        # tokens, go to the next sentence
        if token > max_tokens:
            continue

        # Otherwise, add the sentence to the chunk and add the number of tokens to the total
        chunk.append(sentence)
        tokens_so_far += token + 1

    # Add the last chunk to the list of chunks
    if chunk:
        chunks.append(". ".join(chunk) + ".")

    return chunks

shortened = []

# Loop through the dataframe
for row in df.iterrows():

    # If the text is None, go to the next row
    if row[1]['text'] is None:
        continue

    # If the number of tokens is greater than the max number of tokens, split the text into chunks
    if row[1]['n_tokens'] > max_tokens:
        shortened += split_into_many(row[1]['text'])

    # Otherwise, add the text to the list of shortened texts
    else:
        shortened.append(row[1]['text'])


df = pd.DataFrame(shortened, columns=['text'])
df['n_tokens'] = df.text.apply(lambda x: len(tokenizer.encode(x)))
df.n_tokens.hist()

df['embeddings'] = df.text.apply(
    lambda x: openai.Embedding.create(input=x, engine=MODEL_EMBEDDINGS)['data'][0]['embedding'])
df.to_csv('processed/embeddings.csv')
df.head()

df = pd.read_csv('processed/embeddings.csv', index_col=0)
df['embeddings'] = df['embeddings'].apply(eval).apply(np.array)

df.head()

def create_context(
        question,history, df, max_len=1800, size="ada"
):
    combined_text = "\n\n".join(history) + "\n\n" + question
    print(combined_text)
    # Get the embeddings for the question
    q_embeddings = openai.Embedding.create(input=combined_text, engine=MODEL_EMBEDDINGS)['data'][0]['embedding']

    # Get the distances from the embeddings
    df['distances'] = distances_from_embeddings(q_embeddings, df['embeddings'].values, distance_metric='cosine')

    returns = []
    cur_len = 0

    # Sort by distance and add the text to the context until the context is too long
    for i, row in df.sort_values('distances', ascending=True).iterrows():

        # Add the length of the text to the current length
        cur_len += row['n_tokens'] + 4

        # If the context is too long, break
        if cur_len > max_len:
            break

        # Else add it to the text that is being returned
        returns.append(row["text"])

    # Return the context
    return "\n\n###\n\n".join(returns)


def answer_question(
        df,
        history,
        model=MODEL_OPENAI,
        question="Que es Laverix?",
        max_len=MAX_LEN,
        size="ada",
        debug=False,
        max_tokens=MAX_TOKENS_ANSWER,
        stop_sequence=None,
):
   
    context = create_context(
        question,
        history,
        df,
        max_len=max_len,
        size=size,
    )


    try:
        # Create a completions using the questin and context
        response = openai.Completion.create(
            prompt=f"Usted es un bot de ventas que explicará cualquier inquietud de un usuario.  Ten en cuenta que en el contexto esta el historial del chat. Responda la pregunta según el contexto a continuación, siempre en español, y si la pregunta no se puede responder según el contexto, diga \"No se a que se refieres, puedes explicarlo de diferente manera?\"\n\Contexto: {context}\n\n---\n\Pregunta: {question}\Respuesta:",
            temperature=TEMPERATURE,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop_sequence,
            model=model,
        )
        return response["choices"][0]["text"].strip()
    except Exception as e:
        print(e)
        return ""

def returnAnswer(question, history):
    return answer_question(df,history, question=question, debug=False)
    

