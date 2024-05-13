from langchain_community.docstore.document import Document
from langchain_core.runnables import RunnableLambda
from langchain_community.embeddings import OllamaEmbeddings
from typing import List, Union, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from data import DatabaseComponent
from pydantic import BaseModel
import utils
import os

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    user_question: str

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    source: str
    matched_question: str
    answer: str

class QA(BaseModel):
    """Model for QA pair"""
    question: str
    answer: str
    
OPENAI_API_KEY = None
DATABASE_URL = 'postgresql+psycopg://postgres:psql@localhost:5432/context_qa_db'
OLLAMA_SERVICE_URL = 'http://localhost:11434'
    
# OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
# DATABASE_URL = os.environ.get('DATABASE_URL')
# OLLAMA_SERVICE_URL = os.environ.get('OLLAMA_SERVICE_URL')

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
database = DatabaseComponent(
    connection_url=DATABASE_URL,
    embeddings=OllamaEmbeddings(model='llama3', base_url=OLLAMA_SERVICE_URL)
)

# Initialize the OpenAI API client
if OPENAI_API_KEY is not None:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
    def get_openai_answer(question: str) -> str:
        """Get answer from OpenAI API"""
        try:
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
        except Exception as e:
            print(f"[ERROR]: An error occurred while calling the OpenAI API: {str(e)}")
            return None
    
    print("[INFO]: OpenAI API client initialized successfully.")
else:
    def get_openai_answer(question: str) -> str:
        return None
    print("[INFO]: OpenAI API client not initialized. Please provide an API key.")

# Ollama chain
ollama_chain = utils.create_ollama_chain(base_url=OLLAMA_SERVICE_URL)

def find_local_match(user_question: str) -> Union[Document, None]:
    """Find local match in the database"""
    result = database.similarity_search_with_score(user_question, k=1)
    if len(result) == 1 and result[0][1] < 0.1:
        print(f'''
                    [INFO]: Matched question: {result[0][0].page_content} \n
                            Score: {result[0][1]} \n
                            Answer: {result[0][0].metadata['answer']}
               ''')
        return result[0][0]

    return None


def send_response(info: Dict[str, Any]) -> ChatResponse:
    """Send response to the user"""
    if "it" in info["topic"].lower():
        # Check if there's a local match for the user question
        matched_doc = find_local_match(info["user_question"])

        if matched_doc:
            return ChatResponse(
                source="local",
                matched_question=matched_doc.page_content,
                answer=matched_doc.metadata["answer"]
            )
        else:
            # Forward the question to OpenAI API and get the answer
            answer = get_openai_answer(info["user_question"])

            if not answer:
                print("[INFO]: Forwarding the question to Ollama API...")
                answer = ollama_chain.invoke({"user_question": info["user_question"]})

                if not answer:
                    return ChatResponse(
                        source='local',
                        matched_question='N/A',
                        answer='I am sorry, I could not find an answer to your question. Try again.'
                    )
                else:
                    source, matched_question = "local", "N/A"
            else:
                source, matched_question = "openai", "N/A"

            # cache the question and answer in the database
            database.add_documents([Document(page_content=info["user_question"], metadata={"answer": answer})])
            return ChatResponse(
                source=source,
                matched_question=matched_question,
                answer=answer
            )
    
    elif "other" in info["topic"].lower():
        return ChatResponse(
            source='local',
            matched_question='N/A',
            answer='I am sorry, I could not find an answer to your question. Try again.'
        )


def create_chain() -> Dict[str, Any]:
    """Create the chat chain"""
    return {
        "topic": utils.create_topic_classifier(base_url=OLLAMA_SERVICE_URL), 
        "user_question": lambda x: x["user_question"]
        } | RunnableLambda(send_response)


chat_chain = create_chain()


@app.post("/ask-question")
async def ask_question(question: ChatRequest) -> ChatResponse:
    """Ask question to the chat model"""
    return chat_chain.invoke({"user_question": question.user_question})


@app.post("/add-qas")
async def add_qas(qas: List[QA]) -> List[str]:
    """Add QA pairs to the database"""
    docs = [Document(page_content=qa.question, metadata={"answer": qa.answer}) for qa in qas]
    return database.add_documents(docs)