import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
import os
import datetime
from deep_translator import GoogleTranslator  # Import Google Translate
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains import ConversationalRetrievalChain

chat_history = []  # To store chat history

# Define your custom prompt
custom_prompt_template = """
You are the official FoodChow Assistant — a warm, respectful, and helpful virtual assistant for FoodChow, a trusted platform for food ordering and restaurant management.

Your job is to assist users with anything related to FoodChow, such as:

- Finding restaurants  
- Food and menu-related queries  
- Help with placing or tracking orders  
- Support for restaurant owners and partners  
- Account access, login issues, payment, or delivery assistance  
- How-to guides and feature explanations  

Response Guidelines (follow strictly):

- Always reply as the FoodChow Assistant. Do not mention AI or that you are a model.
- bold the importanat keyword underline and like use all formating to make resposne appropriate and interactive breack line 
- Use plain text with limited formatting: use `<br>` for new lines, and `-` or `*` to create bullet points. Do NOT use markdown or HTML except `<br>`.
- Be calm, emotionally supportive, and encouraging. Appreciate any detailed or thoughtful questions. Be polite and make users feel valued.
- Keep responses short, clear, and easy to understand (under 90 words unless essential).
- Never assume or make up answers. 
- If the information or link is not present, respond clearly that it’s unavailable and politely guide the user to contact support only when necessary:
    📞 Phone: 9979619136
    📧 Email: support@foodchow.com
 Do not include support details every time — only when the information is clearly unavailable or incomplete.
  Use this only when information is missing or cannot be found.

- Always include a link if it is helpful or necessary for the user’s request.
- If there is a new line in your response, use the <br> tag to separate lines.
- Never provide incorrect or assumed URLs. Only use known and correct ones.
- Be emotionally intelligent — thank users when they provide helpful detail, offer appreciation, and always show willingness to help.
- Not always you need to give support phone number and email only share when you find it difficult to answer or loike you dont have comple or unsure answer than only you need to give when it required to give.
- try to give to the point answers
-currently do not suggest any video link 
- instend of using star use • bullet points make approrpiate look and feel

Keep in Mind : If the user asks something like “Can I do this?” or just wants to know availability, simply confirm if it’s possible — no need to give steps or video. But if the question needs a process or explanation, first describe what to do in short, then ask but only when you find videolink : “Would you like to watch a video for this?” Only provide the video link if they say yes.
- try to add relevat emojies with text for user experiance
- try to bold important word where u can use html elements like<b></b>
- Never provide incorrect or assumed URLs. Only use known and correct ones.
-  If any link is shown, it must always use HTML `<a>` tags. Do NOT paste raw URLs. for example <a href="https://example.com">How to Connect Printer in POS</a>
- please do not use hello or hi greeting message in every time 
- if user ask for demo related things than only you need to ask their contact details like email Id, name and contact number one by one other wise no need
❌ Never create or make up links. Only use links if they are explicitly found in the context.
✅ If a valid link is found, always present it using an HTML <a> tag. Do NOT paste raw URLs or guess URLs.

Context:  
{context}

User Question:  
{question} 

Helpful Answer:

"""

# Design Prompt
prompt = PromptTemplate(
    template=custom_prompt_template,
    input_variables=["context", "question"]
)

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="answer"
)

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)  # Enable CORS for frontend communication

# Set up API Key
# os.environ["GOOGLE_API_KEY"] = "AIzaSyDVt8UMG76EUfZeKe8mSyZ2e0EmjSUSw3I"
# os.environ["GOOGLE_API_KEY"] = "AIzaSyDVt8UMG76EUfZeKe8mSyZ2e0EmjSUSw3I"
# os.environ["GOOGLE_API_KEY"] = "AIzaSyCVSTqWByxTjrLJoIpFH0iWGVFmp1nUrUk"
os.environ["GOOGLE_API_KEY"] = "AIzaSyA7KB499x6EdPv_CTSrF58b9j73qDdDbPQ"

# Initialize LLM
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# Load Embeddings & Vector DB
model_name = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(model_name=model_name)
vectorDB_FilePath = "Faiss_index"

translator = GoogleTranslator()  # Initialize Google Translate

# Extract Data from PDF files


def extract_text_from_pdfs(folder_path):
    doc = ""

    # Loop through all the files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(folder_path, filename)

            # Open each PDF file and extract its content
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    doc += page.extract_text()  # Append text from the page to doc

    return doc


def get_text_chunks(input_data):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=500
    )

    if isinstance(input_data, str):
        # Raw text (e.g., from a PDF)
        chunks = text_splitter.split_text(input_data)
        # Convert each chunk to Document object
        return [Document(page_content=chunk) for chunk in chunks]

    elif isinstance(input_data, list) and all(isinstance(doc, Document) for doc in input_data):
        # List of Document objects (e.g., from JSON)
        return text_splitter.split_documents(input_data)

    else:
        raise ValueError(
            "Unsupported input type: must be string or list of Document objects")


# load data from json files


def load_faq_json_to_docs(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        faq_data = json.load(f)

    docs = []
    for item in faq_data:
        question = item.get("question", "").strip()
        answer = item.get("response", "").strip()

        content = f"Q: {question}\nA: {answer}"

        doc = Document(
            page_content=content,
            metadata={
                "source": "faq",
                "question": question
            }
        )
        docs.append(doc)

    return docs

# Load Video Data
# Load Video Data and return as a list of Document objects


def load_video_json_to_docs(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        video_data = json.load(f)

    docs = []
    for item in video_data:
        title = item.get("title", "").strip()
        url = item.get("URL", "").strip()
        transcript = item.get("transcript", "").strip()

        # Structure the document content
        content = f'''Title: {title}\nVideo URL: {
            url}\nTranscript:\n{transcript}'''

        doc = Document(
            page_content=content,
            metadata={
                "source": "video",
                "title": title,
                "url": url
            }
        )
        docs.append(doc)

    return docs


def create_vector_db():
    raw_text = extract_text_from_pdfs("data/Documentation")
    text_chunks = get_text_chunks(raw_text)
    pos_faq_docs = load_faq_json_to_docs("data/FAQs/FAQs_POS.json")
    pos_chunks = get_text_chunks(pos_faq_docs)
    # general_faq_docs = load_faq_json_to_docs("data/FAQs/FAQs_General.json")
    # general_chunks = get_text_chunks(general_faq_docs)
    video_link_data = load_video_json_to_docs(
        "data/VideoLinkData/videoLinkData.json")
    videodata_chunks = get_text_chunks(video_link_data)
    faq_docs = load_faq_json_to_docs("data/FAQs/FAQ.json")
    chunks = get_text_chunks(faq_docs)

    all_docs = text_chunks + pos_chunks + videodata_chunks + chunks
    # loader = CSVLoader(file_path='possystemQA.csv', source_column='prompt')
    # docs = loader.load()
    vectorDB = FAISS.from_documents(documents=all_docs, embedding=embeddings)
    vectorDB.save_local(vectorDB_FilePath)


if not os.path.exists(vectorDB_FilePath):
    print("Creating FAISS index...")
    create_vector_db()
    print("FAISS index created successfully!")
else:
    print("FAISS index already exists.")


def get_qa_chain():
    vectorDB = FAISS.load_local(
        vectorDB_FilePath, embeddings, allow_dangerous_deserialization=True)
    retriever = vectorDB.as_retriever(score_threshold=0.7)

    chain = ConversationalRetrievalChain.from_llm(
        llm=model,
        retriever=retriever,
        return_source_documents=True,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt}
    )

    return chain


qa_chain = get_qa_chain()


@app.route("/")
def index():
    return render_template("test.html")

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "✅ FoodChow Chatbot API is running"}), 200


@app.route("/api/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    question = data.get("question", "").strip()
    language = data.get("language", "en")
    print(question)
    if not question:
        return jsonify({"error": "❌ Please provide a question."}), 400

    try:
        # Translate input to English if needed
        if language != "en":
            question_translated = GoogleTranslator(source=language, target="en").translate(question)
        else:
            question_translated = question

        # Get AI response
        answer_en = qa_chain.invoke({"question": question_translated})
        print(answer_en)

        # Extract the answer string from the response
        answer_text = answer_en['answer'] if isinstance(answer_en, dict) and 'answer' in answer_en else str(answer_en)

        # Translate back if needed
        if language != "en":
            answer_translated = GoogleTranslator(source="en", target=language).translate(answer_text)
        else:
            answer_translated = answer_text

        return jsonify({
            "question": question,
            "language": language,
            "answer": answer_translated
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_query = data.get("message", "")
    user_lang = data.get("language", "en")  # Default language is English

    if not user_query:
        return jsonify({"response": "Please enter a valid query."})

    # Translate user's message to English
    translated_query = GoogleTranslator(
        source=user_lang, target="en").translate(user_query)

    # Get AI response
    ai_response = qa_chain.invoke({"question": translated_query})
    print(ai_response)
    # Translate response back to user's language
    translated_response = GoogleTranslator(
        source="en", target=user_lang).translate(ai_response['answer'])
    print('\n\n', translated_response)

    save_chat_to_file(user_query, translated_response, user_lang)
    return jsonify({"response": translated_response})


def save_chat_to_file(user_question, bot_answer, lang="en", file_path="chat_history.json"):
    chat_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "question": user_question,
        "answer": bot_answer,
        "language": lang
    }

    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                chat_data = json.load(f)
        else:
            chat_data = []

        chat_data.append(chat_entry)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print("Error saving chat:", e)

if __name__ == "__main__":

    app.run(host="195.201.175.72", port=5002, debug=True)  # airtal
    # app.run(host="192.168.1.7", port=5000, debug=True) #shri_5G
    # app.run(host="192.168.84.195", port=5000, debug=True) #dixita
    # app.run(host="172.16.3.193", port=5000, debug=True) #ppsu_student
    # app.run(host="192.168.29.85", port=5000, debug=True)#tanacious_jio_5g
