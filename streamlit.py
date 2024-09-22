import streamlit as st 
import bedrock

st.set_page_config(layout="wide")
st.title("Welcome to AWS RAG Demo!") 

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    btn1 = st.button("💬 **이 RAG의 아키텍처를 보여주세요.**")
with col2:
    btn2 = st.button("💬 **이 애플리케이션의 UI는 어떻게 만들어졌나요?**")

# st.markdown('''- 이 데모는 검색 증강 생성 (RAG)을 활용한 생성형 AI 애플리케이션을 빠르게 구성하고 테스트해보기 위한 챗봇 애플리케이션입니다.''')
st.markdown('''- 이 데모는 Amazon Bedrock Knowledge base를 활용해 복잡하게 느껴질 수 있는 RAG 구성, 예를 들면 VectorStore Embedding 작업부터 Amazon OpenSearch serverless 생성 및 문서 인덱싱과 같은 작업들을 손쉽게 해결하고, Bedrock agent의 [RetrieveAndGenerate](https://docs.aws.amazon.com/ko_kr/bedrock/latest/APIReference/API_agent-runtime_RetrieveAndGenerate.html) API를 활용해 곧바로 Knowledge base에 질문할 수 있도록 Streamlit 애플리케이션과 연동해 챗봇을 구현한 데모입니다. ''')
st.markdown('''- [Github](https://github.com/ottlseo/bedrock-rag-chatbot)에서 코드를 확인하실 수 있습니다.''')
st.markdown('''- **시작하기 전에**, Bedrock Knowledge base와 연결된 **S3 소스 버킷에** :green[**질문하고자 하는 문서를 업로드**]해주세요.''')

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "안녕하세요, 무엇이 궁금하세요?"}
    ]
# 지난 답변 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if btn1:
    query = "이 RAG의 아키텍처를 보여주세요."
    st.chat_message("user").write(query)
    st.chat_message("assistant").image('architecture.png')

    st.session_state.messages.append({"role": "user", "content": query}) 
    st.session_state.messages.append({"role": "assistant", "content": "아키텍처 이미지를 다시 확인하려면 위 버튼을 다시 눌러주세요."})

if btn2:
    query = "이 애플리케이션의 UI는 어떻게 만들어졌나요?"
    answer = '''이 챗봇은 [Streamlit](https://docs.streamlit.io/)을 이용해 만들어졌어요.   
                Streamlit은 간단한 Python 기반 코드로 대화형 웹앱을 구축 가능한 오픈소스 라이브러리입니다.    
                아래 app.py 코드를 통해 Streamlit을 통해 간단히 챗봇 데모를 만드는 방법에 대해 알아보세요:
                💁‍♀️ [app.py 코드 확인하기](https://github.com/ottlseo/rag-chatbot-cdk/blob/main/frontend/app.py)
            '''
    st.chat_message("user").write(query)
    st.chat_message("assistant").write(answer)
    
    st.session_state.messages.append({"role": "user", "content": query}) 
    st.session_state.messages.append({"role": "assistant", "content": answer})

# 유저가 쓴 chat을 query라는 변수에 담음
query = st.chat_input("Search documentation")
if query:
    # Session에 메세지 저장
    st.session_state.messages.append({"role": "user", "content": query})
    
    # UI에 출력
    st.chat_message("user").write(query)

    # UI 출력
    answer = bedrock.query(query)
    st.chat_message("assistant").write(answer)

    # Session 메세지 저장
    st.session_state.messages.append({"role": "assistant", "content": answer})
        
