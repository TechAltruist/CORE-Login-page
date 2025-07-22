# Here are your Instructions
# Local development setup
# Backend Setup
cd backend
pip install -r requirements.txt
#Update .env with your Supabase credentials
uvicorn server:app --reload --port 8001
# Frontend setup
cd frontend
npm install
#Update .env with your Supabase credentials
npm start
