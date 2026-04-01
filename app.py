import streamlit as st
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever, RESTAURANT_NAME

# LLM
model = OllamaLLM(model="llama3.2")

# Prompt template
template = """
You are a helpful assistant answering questions about {restaurant_name}
based ONLY on the provided restaurant documents.

The documents may include:
- Customer reviews
- The restaurant menu (PDF)
- Student discount or other promotional information

Here are the relevant documents: {{documents}}

User question: {{question}}

RULES:
1. ONLY answer based on information in the documents above.
2. If the documents do not contain relevant information, respond EXACTLY with: "I don't know"
3. Do NOT make up information.
4. Do NOT provide general knowledge or assumptions.
5. Do NOT answer questions about topics not covered in the documents.

Answer:
""".format(restaurant_name=RESTAURANT_NAME)

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model


# ----- Streamlit UI -----

st.set_page_config(
    page_title=f"{RESTAURANT_NAME} Assistant",
    page_icon="🍕",
    layout="centered",
)

st.title(f"🍕 {RESTAURANT_NAME} — RAG Assistant")
st.caption("Ask questions about the menu, reviews, or student discount.")

if "history" not in st.session_state:
    st.session_state.history = []

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask something about the restaurant...")
if user_input:
    st.session_state.history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            documents = retriever.invoke(user_input)
            answer = chain.invoke({"documents": documents, "question": user_input})
            st.markdown(answer)

    st.session_state.history.append({"role": "assistant", "content": answer})
