import os
import shutil
import requests
from typing import List, Dict, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

load_dotenv()


class PDFRAGPipeline:
    """
    Retrieval-Augmented Generation (RAG) pipeline for PDF documents from URLs.
    Each PDF is treated as a full document (no chunking).
    Embeddings are stored and retrieved using FAISS.
    """

    def __init__(
        self,
        db_path: str = "faiss_resume_full_db",
        download_dir: str = "resumes",
        model_name: str = "gpt-4-turbo"
    ):
        self.db_path = db_path
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)

        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(model_name=model_name)
        self.vectorstore: Optional[FAISS] = None

    # ------------------------
    # STEP 1: Download PDFs
    # ------------------------
    def download_pdfs(self, resume_list: List[Dict[str, str]]) -> List[str]:
        pdf_files = []
        for item in resume_list:
            pdf_url = item.get("resume_url")
            if not pdf_url:
                continue

            file_name = os.path.join(self.download_dir, pdf_url.split("/")[-1])
            print(f"⬇️ Downloading {file_name} ...")

            response = requests.get(pdf_url)
            if response.status_code == 200:
                with open(file_name, "wb") as f:
                    f.write(response.content)
                pdf_files.append(file_name)
            else:
                print(f"⚠️ Failed to download {pdf_url}")

        print(f"✅ Downloaded {len(pdf_files)} PDFs successfully")
        return pdf_files

    # ------------------------
    # STEP 2: Load PDFs as Documents
    # ------------------------
    def load_documents(self, pdf_files: List[str]) -> List[Document]:
        all_docs = []
        for file_path in pdf_files:
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            full_text = "\n".join([p.page_content for p in pages])

            doc = Document(
                page_content=full_text,
                metadata={
                    "filename": os.path.basename(file_path),
                    "source": file_path,
                },
            )
            all_docs.append(doc)

        print(f"✅ Loaded {len(all_docs)} full documents")
        return all_docs

    # ------------------------
    # STEP 3: Embed and Store in FAISS
    # ------------------------
    def build_faiss_index(self, documents: List[Document]):
        print("🔄 Building FAISS vector store ...")
        self.vectorstore = FAISS.from_documents(documents, self.embeddings)
        self.vectorstore.save_local(self.db_path)
        print(f"✅ FAISS vector store saved at '{self.db_path}'")

        if os.path.exists(self.download_dir):
            shutil.rmtree(self.download_dir)
            print(f"🧹 Cleaned up download directory: {self.download_dir}")

    # ------------------------
    # STEP 4: Load Existing FAISS DB
    # ------------------------
    def load_faiss_index(self):
        print(f"📂 Loading FAISS DB from '{self.db_path}' ...")
        self.vectorstore = FAISS.load_local(
            self.db_path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        print("✅ FAISS database loaded successfully")

    # ------------------------
    # STEP 5: Query the System
    # ------------------------
    def query(self, query_text: str, top_k: int = 1) -> str:
        if not self.vectorstore:
            raise ValueError("❌ FAISS index not loaded. Run build_faiss_index() or load_faiss_index().")

        retriever = self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": top_k})
        qa_chain = RetrievalQA.from_chain_type(llm=self.llm, retriever=retriever, chain_type="stuff")

        print(f"🔍 Querying: {query_text}")
        result = qa_chain.run(query_text)
        return result


# ==============================================
# 🧠 Example Usage
# ==============================================
if __name__ == "__main__":
    Resume = [{'resume_url': 'https://jntavmoxtjnflnrsbulo.supabase.co/storage/v1/object/public/resumes/28/aroravaibhav102@gmail.com-1759582496999-Vaibhav%20Arora%20Amazon.pdf'}, {'resume_url': 'https://jntavmoxtjnflnrsbulo.supabase.co/storage/v1/object/public/resumes/28/aroravaibhav661@gmail.com-1759582514316-NISHTHA%20ARORA%20Resume.pdf'}]

    # Initialize pipeline
    rag = PDFRAGPipeline()

    # 1️⃣ Download PDFs
    pdf_files = rag.download_pdfs(Resume)

    # 2️⃣ Load into documents
    docs = rag.load_documents(pdf_files)

    # 3️⃣ Build FAISS DB
    rag.build_faiss_index(docs)

    # 4️⃣ Query the RAG system
    query = "Give Person with perfect match for Banking role"
    answer = rag.query(query)
    print("\n💡 Answer:", answer)


