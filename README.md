
# 메이플키우기 종결 계산기 (고대책 반영)

## 로컬 실행 (PC)
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 배포 1) Streamlit Community Cloud (가장 쉬움)
1. 이 폴더를 GitHub 레포로 올리기
2. Streamlit Community Cloud에서 `app.py` 선택해서 Deploy

## 배포 2) Docker (어디든 배포 가능)
```bash
docker build -t maple-endgame .
docker run -p 8501:8501 maple-endgame
```
브라우저에서 http://localhost:8501 접속
