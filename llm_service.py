import dashscope
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, CSVLoader, UnstructuredMarkdownLoader, TextLoader, PyPDFLoader, UnstructuredHTMLLoader
from langchain_community.vectorstores import AnalyticDB
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_community.llms import Tongyi
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.prompts import PromptTemplate
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class LLMService:
    def __init__(self) -> None:
        self.vector_db = self.connect_adb()
        self.llm = self.activate_llm()

    def activate_llm(self):
        dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

        tongyi_chat = ChatTongyi(streaming=False)
        return tongyi_chat

    def connect_adb(self):
        connection_string = AnalyticDB.connection_string_from_db_params(
            host=os.getenv('PG_HOST'),
            database=os.getenv('PG_DATABASE'),
            user=os.getenv('PG_USER'),
            password=os.getenv('PG_PASSWORD'),
            driver='psycopg2cffi',
            port=5432
        )

        embedding = DashScopeEmbeddings(
            model=os.getenv('EMBEDDING_MODEL'),
        )

        vector_db = AnalyticDB(
            embedding_function=embedding,
            embedding_dimension=int(os.getenv('EMBEDDING_DIMENSION')),
            connection_string=connection_string
        )
        return vector_db

    def upload_file_knowledge(self, file):
        # Load file based on extension
        if file.lower().endswith('.csv'):
            documents = CSVLoader(file).load()
        elif file.lower().endswith('.md'):
            documents = UnstructuredMarkdownLoader(file).load()
        elif file.lower().endswith('.txt'):
            documents = TextLoader(file).load()
        elif file.lower().endswith('.pdf'):
            documents = PyPDFLoader(file).load()
        elif file.lower().endswith('.html'):
            documents = UnstructuredHTMLLoader(file).load()
        else:
            raise ValueError(f"Unsupported file extension: {file.lower()}")
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        docs = text_splitter.split_documents(documents)
        start_time = time.time()
        self.vector_db.add_documents(docs)
        end_time = time.time()
        print(f"Insert into AnalyticDB Success. Cost time: {end_time - start_time} s")
    
    def upload_directory(self, dir_path):
        docs = DirectoryLoader(dir_path, glob=os.getenv('GLOB_PATTERN', '*'), show_progress=True).load()
        text_splitter = CharacterTextSplitter(chunk_size=int(os.getenv('CHUNK_SIZE', 1000)), chunk_overlap=int(os.getenv('CHUNK_OVERLAP', 0)))
        docs = text_splitter.split_documents(docs)
        start_time = time.time()
        self.vector_db.add_documents(docs)
        end_time = time.time()
        print(f"Insert into AnalyticDB Success. Cost time: {end_time - start_time} s")
    
    def content_query(self, question, history):

        # Prepare history messages
        history_messages = []
        for msg in history:
            if msg[0] is not None:  # This checks the first item in the tuple
                history_messages.append(HumanMessage(content=msg[0]))  # Assuming the first item of tuple is where you want the content
            if msg[1] is not None:  # This checks the second item in the tuple
                history_messages.append(AIMessage(content=msg[1]))  # Directly using the strings
        history_messages.append(HumanMessage(content=question))
                
        # Get context from vector db
        docs = self.vector_db.similarity_search(question, k=3)
        context_docs = ""
        for idx, doc in enumerate(docs):
            context_docs += f"-----\n\n{idx+1}.\n{doc.page_content}"
        context_docs += "\n\n-----\n\n"

        # Define the prompt template
        template = """
You are a QA assistant.
The original query is as follows: {question}
Given the context information and not prior knowledge, answer the query
------------
{context}
------------

Given the context information and is prior knowledge, answer the query. 
 Answer: 
"""
        os.getenv('PROMPT_TEMPLATE', "Given below context and question; Please answer the question:\n\nContext: {context}\n\nQuestion: {question}\n\nAnswer:")
        prompt = PromptTemplate(template=template, input_variables=["context", "question"])
        
        # Add system message at the beginning
        system_message = SystemMessage(content=f"Context: {context_docs}\n\nQuestion: {question}")
        history_messages.insert(0, system_message)
        
        # Invoke the LLM with chat history and the new question
        response = self.llm.invoke(history_messages)
        
        return response.content
    
if __name__ == "__main__":
    is_upload_file = False
    is_upload_dir = False
    is_question = True
    solver = LLMService()
    if is_upload_file:
        print('Uploading file to ADB.')
        upload_file = './docs/pai.txt'
        solver.upload_file_knowledge(upload_file)
    if is_upload_dir:
        print('Uploading directory to ADB.')
        upload_dir = "./docs"
        solver.upload_directory(upload_dir)
    if is_question:  # Changed from args.query to args.question
        question = "Tell me about Alibaba Cloud PAI"
        answer = solver.content_query(question, [])  # Changed from args.query to args.question
        print("The answer is: ", answer)

        
# python llm_service.py --question "Tell me about Machine Learning PAI"

# python llm_service.py --config config.json --question "Tell me about Machine Learning PAI"


# psql -h gp-gs5iz2qi7885imf49-master.gpdbmaster.singapore.rds.aliyuncs.com -p 5432 -U genai_db -d genai_db

# SELECT COUNT(*) FROM document_chunks;
# SELECT content FROM document_chunks;
# TRUNCATE TABLE document_chunks;