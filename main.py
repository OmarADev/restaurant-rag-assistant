# Import the Ollama LLM wrapper from LangChain
# This allows us to use a locally hosted LLM via Ollama
from langchain_ollama.llms import OllamaLLM

# Import ChatPromptTemplate to create structured prompts
# This lets us safely insert variables like documents and questions
from langchain_core.prompts import ChatPromptTemplate

# Import the retriever object created in vector.py
# The retriever performs similarity search over the vector database
from vector import retriever


# Initialize the language model
# llama3.2 will be used to generate answers
model = OllamaLLM(model="llama3.2")


# Define the RAG prompt template as a multi-line string
# This prompt strictly constrains the model to only use retrieved documents
template = """
You are a helpful assistant answering questions about a pizza restaurant
based ONLY on the provided restaurant documents.

The documents may include:
- Customer reviews
- The restaurant menu (PDF)
- Student discount or other promotional images (converted to text)

Here are the relevant documents: {documents}

User question: {question}

RULES:
1. ONLY answer based on information in the documents above.
2. If the documents do not contain relevant information to answer the question,
   respond EXACTLY with: "I don't know"
3. Do NOT make up information.
4. Do NOT provide general knowledge or assumptions.
5. Do NOT answer questions about topics not covered in the documents.

Answer:
"""


# Convert the raw prompt string into a ChatPromptTemplate
# This allows us to dynamically insert documents and questions
prompt = ChatPromptTemplate.from_template(template)


# Create a simple RAG chain
# The pipe operator (|) sends the filled prompt into the LLM
rag_chain = prompt | model


# Define a baseline function that answers WITHOUT retrieval
# This is used to demonstrate failure cases and hallucination risk
def answer_without_retrieval(question: str) -> str:
    """Baseline model answer with no retrieval."""

    # Create a simple prompt without any documents
    base_prompt = f"""You are a helpful assistant.

Answer the following question as best as you can:

Question: {question}

Answer:"""

    # Send the prompt directly to the LLM
    return model.invoke(base_prompt)


# Start an infinite loop to allow repeated user questions
while True:
    # Print a visual separator for readability
    print("\n\n-------------------------------")

    # Ask the user to input a question
    question = input("Ask your question (q to quit): ")

    # Exit the program if the user types 'q'
    if question.lower() == "q":
        break

    # Ask the user which mode to run
    # 1 = RAG only
    # 2 = No retrieval only
    # 3 = Compare both
    mode = input("Mode (1 = RAG, 2 = no retrieval, 3 = compare): ")


    # Mode 2: Answer WITHOUT retrieval
    if mode == "2":
        print("\n--- Answer WITHOUT retrieval ---\n")
        print(answer_without_retrieval(question))


    # Mode 3: Compare no retrieval vs RAG
    elif mode == "3":
        # First show the answer without retrieval
        print("\n--- Answer WITHOUT retrieval ---\n")
        print(answer_without_retrieval(question))

        # Then show the answer with retrieval
        print("\n--- Answer WITH RAG ---\n")

        # Retrieve the top-k most relevant documents
        docs = retriever.invoke(question)

        # Generate the RAG answer using retrieved documents
        print(rag_chain.invoke({"documents": docs, "question": question}))


    # Default mode: Answer WITH RAG only
    else:
        print("\n--- Answer WITH RAG ---\n")

        # RETRIEVAL STEP
        # Performs semantic similarity search over the vector database
        # Returns the top-k most relevant document chunks
        docs = retriever.invoke(question)

        # Generate the answer using retrieval-augmented generation
        print(rag_chain.invoke({"documents": docs, "question": question}))
