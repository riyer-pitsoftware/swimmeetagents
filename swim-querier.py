from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

FILE_PATH = 's5-sat-am-1-1-_090837.pdf'

def query_file():
    # Load PDF
    loader = PyPDFLoader(FILE_PATH)
    documents = loader.load()

    # Split text into manageable chunks
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = text_splitter.split_documents(documents)

    # Generate embeddings
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = FAISS.from_documents(docs, embedding_model)

    # Query
    query = "what is Parth doing?"
    results = db.similarity_search(query)
    for result in results:
        print(result.page_content)

import pdfplumber

def examine_page_extraction():
    with pdfplumber.open(FILE_PATH) as pdf:
        for page in pdf.pages:
            #print(page.extract_text())
            tables = page.extract_tables()
            for table in tables:
                print(table)
from PyPDF2 import PdfReader

def more_complex_extraction():
    
    pdf_path = FILE_PATH
    reader = PdfReader(pdf_path)

    text_data = []
    for page in reader.pages:
        text_data.append(page.extract_text())

    # Combine all pages into a single string for processing
    full_text = "\n".join(text_data)

    import re

    # Split text based on "Heat N of M" pattern
    heat_pattern = r"(Heat\s+\d+\s+of\s+\d+)"
    segments = re.split(heat_pattern, full_text)

    # Recombine the heat identifier with its respective table data
    tables = []
    for i in range(1, len(segments), 2):  # Process in pairs (heat header + table data)
        heat_id = segments[i].strip()  # e.g., "Heat 1 of 3"
        table_data = segments[i + 1].strip()
        tables.append((heat_id, table_data))

    # Check extracted tables
    #for heat_id, table_data in tables:
        #print(f"{heat_id}:\n{table_data}\n{'-'*40}")

    parsed_tables = []

    for heat_id, table_data in tables:
        rows = []
        for line in table_data.split("\n"):
            # Split by multiple spaces
            row = re.split(r'\s{2,}', line.strip())  # At least 2 spaces
            if row:  # Ignore empty lines
                rows.append(row)
        parsed_tables.append((heat_id, rows))

    from sentence_transformers import SentenceTransformer

    # Load embedding model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Combine heat ID with rows for meaningful embeddings
    texts = []
    metadata = []
    for heat_id, rows in parsed_tables:
        for row in rows:
            texts.append(f"{heat_id}: {' '.join(row)}")
            metadata.append({"heat_id": heat_id, "row_data": row})

    # Generate embeddings
    embeddings = model.encode(texts)

    import faiss
    import numpy as np

    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))

    # Save the index for reuse
    faiss.write_index(index, "heat_index")

    # Load the FAISS index
    index = faiss.read_index("heat_index")

    # Query the database
    query = "Parth"
    query_embedding = model.encode([query])
    D, I = index.search(np.array(query_embedding), k=3)  # Top 3 results

    # Print closest matches
    for idx in I[0]:
        print(f"Closest match: {texts[idx]}")
        print(f"Row: {' '.join(metadata[idx]['row_data'])}")



more_complex_extraction()