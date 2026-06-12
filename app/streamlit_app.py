import streamlit as st


st.set_page_config(page_title="RAG Learning Chatbot", layout="wide")

st.title("RAG Learning Chatbot")
st.caption("Demo hỏi đáp tài liệu học tập sử dụng Retrieval-Augmented Generation")

with st.sidebar:
    st.header("Sinh viên")
    st.selectbox("Tài khoản", ["student_demo"])
    st.selectbox("Trình độ", ["Cơ bản", "Trung bình", "Nâng cao"])

uploaded_files = st.file_uploader(
    "Upload tài liệu học tập",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True,
)

question = st.chat_input("Đặt câu hỏi về tài liệu đã upload")

if uploaded_files:
    st.success(f"Đã chọn {len(uploaded_files)} tài liệu. Pipeline xử lý sẽ được cài ở các tuần tiếp theo.")

if question:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        st.write("Chức năng RAG sẽ được kết nối sau khi hoàn thành document loader, embedding và vector store.")
        st.caption("Nguồn: chưa có vì pipeline retrieval chưa được cài đặt.")

