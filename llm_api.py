import os
import json
import re
from typing import List
import torch
from langchain_openai import ChatOpenAI
from langchain_core.messages import trim_messages, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers.string import StrOutputParser

from vector_store import init_ensemble_retriever

class LLMService:
    def __init__(
            self, 
            model: str = "gpt-4.1-mini", 
            ai_rag_file_path: str = "./curriculum_courses_pdf_curriculum_ai.csv",
            product_ai_rag_file_path: str = './curriculum_courses_pdf_curriculum_ai_product.csv',
            system_prompt_template_path: str = "./system_prompt.txt"
    ):
        self.model = ChatOpenAI(
            base_url=os.getenv("BASE_URL"),
            model=model,
            api_key=os.getenv("LLM_KEY")
        )

        self.retriever_ai = init_ensemble_retriever(
            file_path=ai_rag_file_path,
            device="cuda:0" if torch.cuda.is_available() else "cpu",
            k=5
        )

        self.retriever_ai_product = init_ensemble_retriever(
            file_path=product_ai_rag_file_path,
            device="cuda:0" if torch.cuda.is_available() else "cpu",
            k=5
        )

        with open(system_prompt_template_path, encoding="utf-8") as f:
            template = f.read()
        self.prompt_template = PromptTemplate.from_template(template)


        self.llm_chain = self.model | StrOutputParser()

    def generate(self, user_query: str) -> str:
        recommendations_ai = self.retriever_ai.invoke(user_query)
        recommendations_ai_product = self.retriever_ai_product.invoke(user_query)
        prompt = self.prompt_template.format(ai_examples=recommendations_ai, product_au_examples=recommendations_ai_product, user_query=user_query)
        print(prompt)
        llm_output = self.llm_chain.invoke(prompt)
        return llm_output