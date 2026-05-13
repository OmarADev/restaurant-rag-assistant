# app.py
# Streamlit UI for the Restaurant RAG Assistant.
# Users select a restaurant from the sidebar, then ask questions.
# Answers are grounded in that restaurant's documents only.
# Source indicators show which document type each answer came from.

import os
import streamlit as st
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import get_available_restaurants, build_vector_store

# ---- Page config ----
st.set_page_config(
    page_title="Restaurant RAG Assistant",
    page_icon="🍽️",
    layout="centered"
)

# ---- LLM setup ----
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
model = OllamaLLM(model="llama3.2", base_url=OLLAMA_HOST)

PROMPT_TEMPLATE = """
You are a helpful assistant answering questions about a restaurant.
Answer ONLY based on the documents provided below.

Documents:
{documents}

User question: {question}

Rules:
1. Only use information from the documents above.
2. If the answer is not in the documents, say exactly: "I don't have that information."
3. Do not make up details or use general knowledge.
4. Be concise and direct.

Answer:
"""

prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
chain = prompt | model


# ---- Sidebar: restaurant selector ----
st.sidebar.title("🍽️ Select a Restaurant")

restaurants = get_available_restaurants()

if not restaurants:
    st.sidebar.warning(
        "No restaurants found.\n\n"
        "Run `python fetch_restaurant.py` to fetch local restaurants first."
    )
    st.title("Restaurant RAG Assistant")
    st.info(
        "👋 To get started:\n\n"
        "1. Open a terminal in this folder\n"
        "2. Run: `python fetch_restaurant.py`\n"
        "3. Enter your city when prompted\n"
        "4. Restart this app"
    )
    st.stop()

selected_label = st.sidebar.selectbox(
    "Choose a restaurant:",
    options=list(restaurants.keys())
)

selected_folder = restaurants[selected_label]
restaurant_name = selected_label.split("›")[-1].strip()

# ---- Load vector store for selected restaurant ----
# Cache per restaurant folder so switching is fast
@st.cache_resource(show_spinner="Loading restaurant data...")
def load_retriever(folder):
    return build_vector_store(folder)

retriever = load_retriever(selected_folder)

# ---- Main UI ----
st.title(f"🍽️ {restaurant_name}")
st.caption("Ask anything about this restaurant. Answers are based on its actual data only.")

# Reset chat history when restaurant changes
if "last_restaurant" not in st.session_state or st.session_state.last_restaurant != selected_label:
    st.session_state.history = []
    st.session_state.last_restaurant = selected_label

# Display chat history
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Show source badge if available
        if msg["role"] == "assistant" and "sources" in msg:
            source_text = " · ".join(sorted(set(msg["sources"])))
            st.caption(f"📄 Sources: {source_text}")

# Chat input
user_input = st.chat_input(f"Ask about {restaurant_name}...")

if user_input:
    # Show user message
    st.session_state.history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Retrieve and generate
    with st.chat_message("assistant"):
        with st.spinner("Looking that up..."):
            # Retrieve relevant documents
            docs = retriever.invoke(user_input)

            # Extract source labels for display
            sources = [doc.metadata.get("source", "Unknown") for doc in docs]

            # Format documents for the prompt
            formatted_docs = "\n\n".join(
                f"[{doc.metadata.get('source', 'Document')}]\n{doc.page_content}"
                for doc in docs
            )

            # Generate answer
            answer = chain.invoke({
                "documents": formatted_docs,
                "question": user_input
            })

            st.markdown(answer)
            source_text = " · ".join(sorted(set(sources)))
            st.caption(f"📄 Sources: {source_text}")

    st.session_state.history.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })
