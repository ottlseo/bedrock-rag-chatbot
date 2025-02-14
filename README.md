# Amazon Bedrock으로 멀티모달 RAG 챗봇 손쉽게 구축하기 실전 가이드

#### 목차
- Step 1. [Knowledge base와 연동할 S3 소스 버킷 생성](#step-1-knowledge-base와-연동할-s3-소스-버킷-생성)
- Step 2. [Bedrock knowledge base 생성하기](#step-2-bedrock-knowledge-base-생성하기)
  - (선택사항) [검색 성능을 높이기 위해 Chunking and parsing configurations 설정하기](#선택사항-검색-성능을-높이기-위해-chunking-and-parsing-configurations-설정하기)
- Step 3. [EC2에 챗봇 애플리케이션 배포하기](#step-3-ec2에-챗봇-애플리케이션-배포하기)
- Step 4. [배포한 애플리케이션 테스트해보기](#step-4-배포한-애플리케이션-테스트해보기)

- - - 

생성형 AI의 중요성이 대두되면서, 기존에 모델 학습부터 시작하는 MLOps보다 더 저렴한 비용으로도 원하는 문서의 내용을 기반으로 AI 결과를 생성하는 RAG (Retrieval-Augmented Generation, 검색 증강 생성) 기법이 함께 주목받고 있습니다. RAG는 맞춤형 데이터를 활용하여, 대규모 언어 모델이 응답을 생성하기 전에 학습 데이터 소스 외부의 맞춤형 지식 베이스를 참조하도록 하는 프로세스를 말합니다. RAG를 활용한 생성형 AI는 대규모 데이터베이스에서 관련 정보를 검색하고 이를 바탕으로 응답을 생성하기 때문에, 모델을 다시 학습 시킬 필요 없이 특정 도메인이나 조직의 내부 지식을 기반으로 LLM 기능을 확장할 수 있는 비용 효율적인 접근 방식입니다. 

![image](https://github.com/user-attachments/assets/08d4a781-7a30-4fb3-ac34-d1a4203898d4)

Amazon Bedrock 역시 RAG 구축을 위한 손쉬운 방법으로 Knowledge base 기능을 지원하고 있습니다. Amazon Bedrock Knowledge base를 이용하면 클릭 몇 번으로 FM을 OpenSearch와 같은 RAG용 데이터 소스에 연결해 테스트할 수 있습니다. 본 포스팅에서는 Amazon Bedrock Knowledge base를 활용해 고성능 RAG를 손쉽게 구축하는 방법에 대해 알아보고, 이렇게 구축한 RAG를 아래와 같은 챗봇 애플리케이션 형태로 EC2에 배포하는 방법을 코드와 함께 단계별로 소개합니다. 

## Architecture & Demo
![image](https://github.com/user-attachments/assets/3211645d-c4c5-4507-ac6e-19b19cb3d495)

![image](https://github.com/user-attachments/assets/e67285aa-77a9-46e7-ad48-9e283b398eef)

## Step 1. Knowledge base와 연동할 S3 소스 버킷 생성

먼저 Bedrock Knowledge base와 연동할 S3 버킷을 생성해야 합니다. 해당 링크를 클릭해 us-west-2 (오레곤) 리전에서 AWS S3 Console에 접속해 새로운 버킷을 생성할 수 있습니다. 이후 단계에서 Bedrock Knowledge base를 생성할 때 해당 버킷 이름을 활용해야 하므로 고유하면서 기억하기 쉬운 이름을 입력하고, 그 외 설정은 기본값으로 두고 버킷을 생성합니다. 

![image](https://github.com/user-attachments/assets/da5820a9-c84c-4a7d-a736-cbf361d1dc32)

버킷 생성이 완료되면, RAG를 통해 검색하고자 하는 문서를 해당 버킷에 미리 업로드해두겠습니다. 
(본 실습에서는 50장 분량의 EC2 사용자 가이드 PDF를 업로드했습니다: [ec2_userguide_1-50.pdf](./sampledata/ec2_userguide_1-50.pdf) )


## Step 2. Bedrock knowledge base 생성하기

### Bedrock model access 요청하기
Bedrock Console에 접근해, 가장 먼저 Bedrock 서비스를 통해 사용하고자 하는 파운데이션 모델 (FM)에 대해 액세스를 요청해야 합니다. 아래 스크린샷과 같이 왼쪽 사이드바에서 Model access를 클릭해 액세스 요청 페이지에 접속합니다. 

![image](https://github.com/user-attachments/assets/58b97443-b281-48af-8b33-f01f84ff7cf1)

아래와 같이 Model access 페이지에서 ‘Enable specific models’를 클릭합니다.

![image](https://github.com/user-attachments/assets/0c54aa49-15da-4301-839e-57c85a854d0d)

본 실습에서 사용할 모델은 아래와 같습니다. 해당 모델을 선택한 후 Next (다음)을 클릭합니다.

* Claude 3 Sonnet
* Titan Embeddings G1 - Text
* Titan Text Embeddings V2

![image](https://github.com/user-attachments/assets/acbd9184-4b09-4bf3-9d75-b74927f6b902)

Access 신청을 원하는 모델이 잘 선택되었는지 확인 후 Submit (제출)을 클릭해 신청을 완료합니다. 일부 모델은 Access를 부여받기까지 시간이 소요될 수 있습니다. Access 신청이 완료되면 아래와 같이 Access Status 가 Access granted 로 변경됩니다.

![image](https://github.com/user-attachments/assets/bdce9377-b828-4d3b-8f69-98d7afdddb9d)

### Bedrock knowledge base 생성 및 S3 데이터 소스 연결하기

이제 Bedrock Knowledge base를 생성할 준비가 되었습니다. Bedrock Console의 좌측 사이드바에서 Knowledge bases (지식 기반)을 클릭해 생성 화면에 접속하고, ‘Create knowledge base’ 버튼을 클릭합니다. 

![image](https://github.com/user-attachments/assets/e5a89406-9361-41d9-b483-5c6cb0fc7e49)

아래와 같이 설정하고, ‘Next (다음)’ 버튼을 눌러 다음 설정으로 이동합니다. 

![image](https://github.com/user-attachments/assets/c17dc933-8d6d-403e-86e1-8ebcf4f8bda4)

다음은 Knowledge base의 Data source를 설정하는 단계입니다. ‘Browse S3’ 버튼을 클릭하고, 앞서 [Step 1]에서 생성했던 버킷을 선택해줍니다.

![image](https://github.com/user-attachments/assets/b45ce095-8c94-43f7-a278-9c36420ba31a)
![image](https://github.com/user-attachments/assets/15725123-3d54-4fdf-8ef0-cc449c661968)

### (선택사항) 검색 성능을 높이기 위해 Chunking and parsing configurations 설정하기

RAG의 검색 성능을 높이고 싶다면 (특히 이미지나 표가 포함되어 있는 복잡한 문서에서 정보를 검색하고자 하는 경우), 해당 섹션을 고려해야 합니다. RAG 시스템이 복잡한 실제 애플리케이션에 적용되기 위해서는 이미지나 표에 있는 데이터도 잘 검색할 수 있는 멀티모달 처리 능력이 필요합니다. 지난 2024.07.10에 Bedrock에 새로 추가된 ‘Chunking and parsing configurations’ 설정을 통해 이러한 성능을 개선하고 멀티모달 RAG를 구현할 수 있습니다. 

LLM을 활용한 파싱 기능은 PDF와 같이 구조화되지 않은 문서에서 정보를 구조화하고, 이미지 및 테이블이 포함하고 있는 정보도 검색 가능한 형태로 인덱싱하는 데 도움이 됩니다. 아래와 같이 ‘Chunking and parsing configurations’를 ‘Custom’으로 선택하고, Parsing strategy에서 ‘Use foundation model for parsing’ 체크박스를 선택한 뒤, 파싱에 사용할 모델을 ‘Claude 3 Sonnet v1’과 ‘Claude 3 Haiku v1’ 중 하나로 선택합니다. (해당 실습에서는 Sonnet v1 모델을 사용합니다) 

![image](https://github.com/user-attachments/assets/47a603ed-e8f6-44b0-88d4-1c9ed7491585)

위 스크린샷에서 빨간 사각형으로 표시한 부분이 파싱을 위해 LLM에 전달하는 프롬프트입니다. 해당 프롬프트는 원하는 대로 수정할 수 있지만, 해당 실습에서는 기본으로 주어지는 프롬프트를 그대로 사용했습니다. 기본 프롬프트의 내용을 요약하면 아래와 같습니다. 

```
1. 각 페이지를 주의 깊게 살피고, 헤더, 본문 텍스트, 각주, 표, 이미지 및 페이지 번호 등 페이지에 있는 모든 요소를 식별해 마크다운 형식으로 변환합니다. 
    * 메인 제목에는 #, 섹션에는 ##, 하위 섹션에는 ### 등을 사용 (기타 가이드 생략)
2. Visualization (이미지 등) 요소를 발견한 경우, 이에 대한 자세한 설명을 작성합니다.
3. Table (표) 요소를 발견할 경우, 마크다운 테이블로 변환합니다. 
```

이와 같이 LLM 파싱 기능은 문서를 검색 가능한 형태로 임베딩하기에 앞서 위와 같은 프롬프트를 활용해 LLM이 구조를 재정의하게 함으로써 텍스트는 물론 이미지 및 표에 대한 검색 성능을 높일 수 있습니다. LLM을 사용하는 것이므로 대용량 문서에 활용할 때에는 비용을 고려하는 것이 좋습니다. 

이후 Chunking strategy 역시 설정할 수 있습니다. 기본으로 주어지는 Default chunking 외에 다른 옵션을 선택할 수 있으며, 앞서 LLM 파싱을 통해 문서를 마크다운 형태로 파싱했으므로 해당 가이드에서는 Hierachical chunking을 선택했습니다. Token size도 사용 사례에 적합한 크기로 맞춰 설정한 후, ‘Next (다음)’를 눌러 다음 단계로 넘어갑니다.

![image](https://github.com/user-attachments/assets/532db6e6-2002-4f2d-94b6-9d174bf19e1c)

해당 LLM parsing 기능을 활용한 결과로, 아래와 같이 복잡한 표/이미지에 있는 그림도 높은 성능으로 retrieve 해올 수 있는 것을 확인하실 수 있습니다. 

<img width="565" alt="image" src="https://github.com/user-attachments/assets/a03b5353-2970-4b91-8bb2-aa4d16b10f09">

> 다양한 Chunking 전략 및 메타데이터 프로세싱 설정과 관련해서는 다음 블로그 게시물을 참고하시면 좋습니다. 대상 문서의 크기, 종류 및 기타 특성을 고려해 상황에 맞는 Chunking 옵션을 선택하는 것이 RAG의 성능을 높이는 데 도움이 됩니다: https://aws.amazon.com/ko/blogs/machine-learning/amazon-bedrock-knowledge-bases-now-supports-advanced-parsing-chunking-and-query-reformulation-giving-greater-control-of-accuracy-in-rag-based-applications/

### 임베딩 모델 선택 및 벡터 DB로서의 OpenSearch serverless 생성하기
사용할 Embedding 모델을 선택할 수 있으며, 해당 실습에서는 Titan text Embeddings v2 모델을 선택합니다. Vector dimensions 역시 RAG의 정확도 및 속도를 결정하는 요인이므로, 기본 제공되는 값 외에 원하는 값으로 설정이 가능합니다. 
Vector database로는 ‘Quick create a new vector store’ 옵션을 선택해 OpenSearch Serverless를 새로 생성해줍니다. 이후 ‘Next (다음)’ 버튼을 눌러 검토 단계로 이동하고, 검토 후 ‘Create knowledge base’ 버튼을 클릭해 Knowledge base를 생성합니다. 설정한 내용대로 Knowledge base를 구성하고 OpenSearch Serverless를 생성하는 데에 수 분이 소요됩니다.

![image](https://github.com/user-attachments/assets/fa4f8f51-9f2e-4d30-8ee4-7aec1000ab8c)
![image](https://github.com/user-attachments/assets/4fa02e60-279f-40e2-a076-5ea65515ef75)

### 생성한 Knowledge Base 콘솔에서 테스트해보기
Knowledge base가 성공적으로 생성되었습니다. Data source에 앞서 [Step 1]에서 만들었던 S3 bucket이 연결되어 있는 것을 확인할 수 있습니다. 해당 Data source를 선택한 뒤, ‘Sync’ 버튼을 클릭해 버킷 내의 데이터를 Knowledge base로 연동해주겠습니다. 데이터의 크기에 따라 수 분에서 수 시간이 소요될 수 있습니다.

![image](https://github.com/user-attachments/assets/0a243c29-39ad-4e82-a49b-07b706473e6e)
![image](https://github.com/user-attachments/assets/fec762b2-a629-4803-89aa-f328aa9649a3)
![image](https://github.com/user-attachments/assets/1af4bda3-2faf-4632-ba30-0592011b2d90)

## Step 3. EC2에 챗봇 애플리케이션 배포하기

### EC2 생성
* ‘Ubuntu’ 서버로 생성합니다. (실습에서는 Ubuntu Server 24.04 LTS, SSD Volume Type 을 사용합니다.)
* 보안그룹에 SSH(22 port) , HTTP (80) 에 대해 inbound rule을 추가해줍니다. 
* 본 실습에서는 인스턴스 m5.large 유형을 사용합니다.

![image](https://github.com/user-attachments/assets/dead46f2-f6de-4b2e-b0c7-4d337ef082e0)
![image](https://github.com/user-attachments/assets/d932d83a-fec3-4efd-9933-009713ed02f2)

### 소스코드 다운로드 및 필요 패키지 설치
EC2가 만들어지면, EC2에 접근해 root 디렉토리에서 아래 명령어를 입력합니다. 
```
sudo apt update 
sudo apt-get install -y ec2-instance-connect
sudo apt-get install -y git
sudo apt-get install -y python3-pip
sudo apt-get install -y python3.12-venv

git clone https://github.com/ottlseo/bedrock-rag-chatbot.git
sudo git checkout ec2-manual-deployment

sudo python3 -m venv --copies /home/ubuntu/my_env
sudo chown -R ubuntu:ubuntu /home/ubuntu/my_env
source /home/ubuntu/my_env/bin/activate

cd bedrock-rag-chatbot/application

pip3 install -r requirements.txt
```

### 생성한 Bedrock Knowledge base ID를 소스코드 내 variables.py 에 입력

- [Step 2]에서 생성한 Bedrock KB console에서 ID를 복사한 뒤,
  - ![image](https://github.com/user-attachments/assets/d473a37b-8af0-4382-9c3e-eb1191e7b680)
- Clone 받아온 코드 variables.py 파일을 열고 KNOWLEDGE_BASE_ID 변수에 복사한 ID를 할당해줍니다.
  - ![image](https://github.com/user-attachments/assets/525a7b8b-f77a-48f0-a7fb-1fe2fb95345d)

### EC2 배포하기
EC2에서 아래 명령어를 입력해 에디터를 엽니다. 
```
sudo vi /etc/systemd/system/streamlit.service
```
이후 열린 에디터에 아래 내용을 붙여넣습니다. 
```
[Unit]
Description=Streamlit App
After=network.target

[Service]
User=ubuntu
Environment='AWS_DEFAULT_REGION=us-west-2'
WorkingDirectory=/home/ubuntu/bedrock-rag-chatbot/application
ExecStartPre=/bin/bash -c 'sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8501'
ExecStart=/bin/bash -c 'source /home/ubuntu/my_env/bin/activate && streamlit run streamlit.py --server.port 8501'
Restart=always

[Install]
WantedBy=multi-user.target
```

입력 후에는 `:wq` 를 입력해 에디터를 종료한 뒤, 아래 명령어로 Streamlit 애플리케이션을 시작해줍니다. 
```
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit

```

→ 이제 EC2의 public ip로 Streamlit 애플리케이션에 접근할 수 있습니다. 

- - -

# Step 4. 배포한 애플리케이션 테스트해보기
- Sample demo: http://35.87.31.249/

#### 샘플 질문: 
- `EC2란 무엇인가요?`
  - 예상 답변: Amazon Elastic Compute Cloud (Amazon EC2)는 Amazon Web Services (AWS) 클라우드에서 제공하는 온디맨드 확장 가능한 컴퓨팅 용량 서비스입니다. Amazon EC2를 사용하면 하드웨어 비용을 절감하고 애플리케이션을 더 빠르게 개발 및 배포할 수 있습니다. 필요한 만큼의 가상 서버를 시작하고, 보안 및 네트워킹을 구성하고, 스토리지를 관리할 수 있습니다. EC2 인스턴스는 AWS 클라우드에서 실행되는 가상 서버입니다. EC2 인스턴스를 시작할 때 지정한 인스턴스 유형에 따라 인스턴스에 할당되는 하드웨어 리소스가 결정됩니다. 각 인스턴스 유형은 CPU, 메모리, 네트워크, 스토리지 및 그래픽 하드웨어 리소스의 다양한 조합을 제공합니다.
- `Amazon Bedrock 이란 무엇인가요?`
  - 예상 답변: 제공된 검색 결과에는 "Amazon Bedrock"에 대한 정보가 없기 때문에 이에 대해 정확한 답변을 드릴 수 없습니다.
- `Powershell을 위한 AWS tool에 대해 설명해주세요.`
  - 예상 답변: AWS는 PowerShell을 위한 AWS Tools for Windows PowerShell 모듈을 제공합니다. 이 모듈은 AWS SDK for .NET의 기능을 기반으로 하며, PowerShell 명령줄에서 AWS 리소스에 대한 작업을 스크립팅할 수 있게 해줍니다. AWS Tools for Windows PowerShell을 사용하면 Amazon EC2와 같은 AWS 서비스에 대한 cmdlet을 사용할 수 있습니다. AWS Tools for Windows PowerShell 사용을 시작하려면 AWS Tools for Windows PowerShell 사용 설명서를 참조하세요. Amazon EC2에 대한 cmdlet은 AWS Tools for PowerShell Cmdlet Reference에서 확인할 수 있습니다.
