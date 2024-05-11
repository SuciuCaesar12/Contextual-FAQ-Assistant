from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.llms.ollama import Ollama


def create_topic_classifier(topic: str = 'IT', base_url: str = 'http://localhost:11434'):
    return (
        PromptTemplate.from_template(
            """Given the user question below, is the question IT related?. Classify the question as 'IT' or 'Other'.

            Do not respond with more than one word.

            <question>
            {user_question}
            </question>

            Classification:"""
            )
            | Ollama(model='llama3', base_url=base_url)
            | StrOutputParser()
    ) 
