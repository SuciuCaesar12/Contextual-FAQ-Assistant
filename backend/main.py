from langchain_community.docstore.document import Document
from langchain_core.runnables import RunnableLambda
from langchain_community.embeddings import OllamaEmbeddings
from typing import List, Union
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from data import DatabaseComponent
from pydantic import BaseModel
import utils
import os

class ChatRequest(BaseModel):
    user_question: str

class ChatResponse(BaseModel):
    source: str
    matched_question: str
    answer: str

class QA(BaseModel):
    question: str
    answer: str

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')
OLLAMA_SERVICE_URL = os.environ.get('OLLAMA_SERVICE_URL')

# Initialize the FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Initialize the database component
db = DatabaseComponent(
    connection_url=DATABASE_URL,
    embeddings=OllamaEmbeddings(model='llama3', base_url=OLLAMA_SERVICE_URL)
)
# Initialize the OpenAI API client
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def get_openai_answer(question: str) -> str:
    print("[INFO]: Forwarding the question to OpenAI API...")
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system", 
                "content": 
                    '''You are here to answer any questions you are asked. Be concise and informative. 
                    Do not provide more information than necessary.'''
            },
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content


def find_local_match(user_question: str) -> Union[Document, None]:
    result = db.similarity_search_with_score(user_question, k=1)
    if len(result) == 1 and result[0][1] < 0.1:
        print(f'''
                    [INFO]: Matched question: {result[0][0].page_content} \n
                            Score: {result[0][1]} \n
                            Answer: {result[0][0].metadata['answer']}
               ''')
        return result[0][0]
    
    return None


def send_response(info) -> ChatResponse:
    if 'it' in info['topic'].lower():
        # Check if there's a local match for the user question
        matched_doc = find_local_match(info['user_question'])
        
        if matched_doc:
            return ChatResponse(
                source="local",
                matched_question=matched_doc.page_content,
                answer=matched_doc.metadata['answer']
            )
        else:
            # Forward the question to OpenAI API and get the answer
            answer = get_openai_answer(info['user_question'])
            # Cache the answer in the local database
            db.add_documents([
                Document(
                    page_content=info['user_question'], 
                    metadata={'answer': answer}
                )
            ])
            print(f"[INFO]: Document added to the database")

            return ChatResponse(
                source="openai",
                matched_question="N/A",
                answer=answer
            )
  
    elif 'other' in info['topic'].lower():
        print("[INFO]: This is not really what I was trained for, therefore I cannot answer. Try again.")
        return ChatResponse(
            source='local',
            matched_question='N/A',
            answer='This is not really what I was trained for, therefore I cannot answer. Try again.'
        )


def create_chain():
    return {
        "topic": utils.create_topic_classifier(base_url=OLLAMA_SERVICE_URL), 
        "user_question": lambda x: x['user_question']
        } | RunnableLambda(send_response)


full_chain = create_chain()


@app.post("/ask-question")
async def ask_question(question: ChatRequest) -> ChatResponse:
    return full_chain.invoke({'user_question': question.user_question})


@app.post("/add-qas")
async def add_qas(qas: List[QA]) -> List[str]:
    docs = [Document(page_content=qa.question, metadata={'answer': qa.answer}) for qa in qas]
    return db.add_documents(docs)
