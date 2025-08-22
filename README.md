## Run local

pip install -r requirements.txt
uvicorn app.main:app --reload

## Health

curl http://localhost:8000/health

## Docker

docker build -t vitai-backend .
docker run -p 8000:8000 vitai-backend
