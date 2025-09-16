# Realtime Socket Chat App 🚀

A Django + Django Channels based **real-time chat application** with WebSocket support, JWT authentication, and notifications.

## 🔧 Features
- **JWT Authentication** over WebSockets using custom middleware
- **Real-time Chat** with multiple rooms
- **User Online/Offline Status**
- **Notifications** using WebSocket groups
- **Typing Indicators**
- **Test Client** (`test.py`) to simulate socket connections

## 📂 Project Structure
```
core/
 ├── asgi.py          # ASGI entrypoint
 ├── routing.py       # WebSocket URL routing
chat/
 ├── consumers.py     # WebSocket consumers (Chat, Echo, Notification)
 ├── middleware.py    # JWT WebSocket authentication middleware
 ├── tests/           # Future tests
test.py               # Example socket test client
```

## ⚡ Setup & Run
### 1️⃣ Clone the repo
```bash
git clone https://github.com/<your-username>/Realtime-socket-chat-app.git
cd Realtime-socket-chat-app
```

### 2️⃣ Create virtual environment
```bash
python -m venv env
source env/bin/activate   # Linux/Mac
env\Scripts\activate    # Windows
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Run migrations
```bash
python manage.py migrate
```

### 5️⃣ Start server
```bash
daphne core.asgi:application -p 8001
```

### 6️⃣ Run WebSocket test client
```bash
python test.py
```

## 🛠 Tech Stack
- **Django** (Backend framework)
- **Django Channels** (WebSockets)
- **Redis** (Channel layer backend)
- **JWT Authentication** (via `djangorestframework-simplejwt`)
- **Daphne** (ASGI server)

## 🧑‍💻 Development Notes
- Use `.env` file for secrets (don’t commit it!)
- JWT tokens must be passed in the WebSocket query string (`?token=<jwt>`)
- Run `test.py` to verify Echo, Chat, and Notifications work.

## 📜 License
MIT License. Feel free to use and modify.
