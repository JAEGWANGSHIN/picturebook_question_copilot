# 📚 AI 그림책 질문수업 설계기

초등 교사가 학년·주제·그림책을 입력하면 질문 생성, 활동 설계, 지도안, 평가, PPT까지 자동으로 만들어주는 Streamlit 웹앱입니다.

## 주요 기능

| 기능 | 설명 |
|------|------|
| 🤖 AI 추천 | 우리 반 상황을 자유롭게 입력하면 맞는 그림책 4권 추천 |
| ❓ 질문 카드 생성 | 읽기 전·중·후 질문을 유형별 카드 UI로 표시 |
| 🎨 단계별 생성 | 질문·활동·지도안·평가+안내문을 각각 독립 생성 (비용 절약) |
| 🎞️ PPT 생성 | 9슬라이드 수업용 발표자료 (.pptx) 자동 생성 |
| 📚 그림책 DB | 35권 큐레이션 DB (주제·학년별 필터링) |

## 파일 구성

```
📁 레포지토리 루트
├── app.py            # Streamlit 메인 앱
├── make_pptx.js      # PPT 생성 Node.js 스크립트
├── requirements.txt  # Python 패키지
├── packages.txt      # 시스템 패키지 (Node.js)
└── README.md
```

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

환경변수로 API 키 설정:
```bash
export OPENAI_API_KEY="your_api_key"
```

## Streamlit Community Cloud 배포

1. 이 레포지토리를 GitHub에 push합니다.
2. [share.streamlit.io](https://share.streamlit.io)에서 레포지토리를 연결합니다.
3. **App settings → Secrets**에 아래 내용 입력:

```toml
OPENAI_API_KEY = "your_api_key"
```

> `packages.txt`에 `nodejs`가 있어서 Streamlit Cloud가 자동으로 Node.js를 설치합니다.  
> 앱 실행 시 pptxgenjs도 자동 설치되므로 별도 작업 불필요합니다.

## 기술 스택

- **Frontend**: Streamlit
- **AI**: OpenAI gpt-4o-mini
- **PPT 생성**: Node.js + pptxgenjs
- **문서 생성**: python-docx

---

만든이: 울산초 교사 신재광
