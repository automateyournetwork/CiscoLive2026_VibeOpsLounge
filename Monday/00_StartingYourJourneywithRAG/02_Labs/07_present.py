import streamlit as st
from genie.testbed import load
from langchain_community.document_loaders import JSONLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
import tempfile, os, json, uuid
from lab_utils import discover_device

# --- UI Setup ---
st.set_page_config(page_title="Chat with Interface Table", page_icon="🛣️")
st.title("🛣️ Chat with Your Interface Table")
st.markdown("Ask anything about the live Interface table retrieved from your discovered device using pyATS!")

# --- Cached RAG Pipeline Setup ---
def setup_routing_chain():
    # Step 1: Select first device, connect (learn hostname), and get routing table
    testbed = load("testbed.yaml")
    # choose first device entry and let pyATS learn hostname if available
    device = next(iter(testbed.devices.values()))
    print("🔌 Connecting to device (will attempt hostname discovery)...")
    device.connect(log_stdout=True, learn_hostname=True)
    device_name = getattr(device, "name", None) or next(iter(testbed.devices))
    parsed_output = device.parse("show ip interface brief")

    # Step 2: Write JSON to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as tmp:
        json.dump(parsed_output, tmp, indent=2)
        tmp_path = tmp.name

    # Step 3: Load into LangChain Documents
    loader = JSONLoader(
        file_path=tmp_path,
        jq_schema='.',  # 1 route per document
        text_content=False
    )
    documents = loader.load()
    os.remove(tmp_path)

    # Step 4: Embed & Split
    embedding = OpenAIEmbeddings(model="text-embedding-3-small")
    splitter = SemanticChunker(embedding)
    chunks = splitter.split_documents(documents)

    # Step 5: Build Chroma vector store
    vector_store = Chroma.from_documents(chunks, embedding)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    # Step 6: Set up RAG chain
    llm = ChatOpenAI(model="gpt-5.5", temperature=0)
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )
    return qa_chain, device_name


# --- Lazy Streamlit app wiring ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None

if "device_name" not in st.session_state:
    st.session_state.device_name = None

# Show connected device if already initialized
if st.session_state.device_name:
    st.subheader(f"Connected device: {st.session_state.device_name}")

# --- Chat Interaction ---
question = st.text_input("💬 Ask a question about your Interface table:")

if question:
    if st.session_state.qa_chain is None:
        with st.spinner("Initializing connection and building RAG pipeline..."):
            qa_chain, device_name = setup_routing_chain()
            st.session_state.qa_chain = qa_chain
            st.session_state.device_name = device_name

    with st.spinner("Thinking..."):
        response = st.session_state.qa_chain.invoke({
            "question": question,
            "chat_history": st.session_state.chat_history
        })
        st.session_state.chat_history.append((question, response["answer"]))

# --- Display Chat History ---
for user_q, answer in reversed(st.session_state.chat_history):
    st.markdown(f"**🧑‍💻 You:** {user_q}")
    bot_name = st.session_state.device_name or "Device"
    st.markdown(f"**🤖 {bot_name} Interface Bot:** {answer}")
    st.markdown("---")
