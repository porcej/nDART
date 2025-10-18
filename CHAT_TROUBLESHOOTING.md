# Chat Real-Time Messaging Troubleshooting

This guide helps troubleshoot issues with real-time chat messaging in the nDART application.

## 🔧 **Issue: Messages Don't Show Up Until Page Refresh**

### Root Cause Analysis

The issue was caused by **conflicting SocketIO event handlers** in the codebase:

1. **Old implementation** in `app.py` (lines 161-184) using `'joined'`, `'text'`, `'left'` events
2. **New implementation** in `blueprints/chat/routes.py` using `'join'`, `'send_message'` events
3. **Frontend JavaScript** using the new implementation but conflicting with old handlers

### ✅ **Fixes Applied**

#### 1. Removed Conflicting Event Handlers
```python
# REMOVED from app.py - these were conflicting:
@socketio.on('joined', namespace='/chat')
@socketio.on('text', namespace='/chat') 
@socketio.on('left', namespace='/chat')
```

#### 2. Added Missing Event Handlers
```python
# ADDED to blueprints/chat/routes.py:
@socketio.on('leave', namespace='/chat')
@socketio.on('typing', namespace='/chat')
@socketio.on('stop_typing', namespace='/chat')
```

#### 3. Fixed Room Broadcasting
```python
# CHANGED from room_id=room_id to room=room_id
emit('receive_message', message_dict, room=room_id)
```

#### 4. Added Debug Logging
```javascript
// Frontend debugging
console.log('Socket connected:', socket.id);
console.log('Sending message:', { message, room_id: currentRoomId });
console.log('Received message:', data);
```

```python
# Backend debugging
logger.info(f"Received send_message: {data}")
logger.info(f"Emitting receive_message to room {room_id}: {message_dict}")
```

## 🔧 **Troubleshooting Steps**

### Step 1: Check Browser Console
1. Open browser Developer Tools (F12)
2. Go to Console tab
3. Look for SocketIO connection messages:
   - `Socket connected: [socket-id]`
   - `Sending message: {message: "...", room_id: "..."}`
   - `Received message: {...}`

### Step 2: Check Server Logs
```bash
# View application logs
docker-compose logs -f ndart

# Look for these log messages:
# "Received send_message: {...}"
# "Emitting receive_message to room ..."
```

### Step 3: Test SocketIO Connection
```javascript
// In browser console, test connection:
const socket = io.connect('//' + document.domain + ':' + location.port + '/chat');
socket.on('connect', () => console.log('Connected:', socket.id));
socket.emit('send_message', {message: 'test', room_id: '1'});
```

### Step 4: Verify Event Handlers
Check that these event handlers exist in `blueprints/chat/routes.py`:
- `@socketio.on('join', namespace='/chat')`
- `@socketio.on('send_message', namespace='/chat')`
- `@socketio.on('leave', namespace='/chat')`
- `@socketio.on('typing', namespace='/chat')`
- `@socketio.on('stop_typing', namespace='/chat')`

## 🔧 **Common Issues and Solutions**

### Issue 1: SocketIO Connection Fails
**Symptoms:** Console shows "Socket connection error"
**Solution:**
```bash
# Check if SocketIO is properly configured
docker-compose exec ndart python -c "
from extensions import socketio
print('SocketIO configured:', socketio is not None)
"
```

### Issue 2: Messages Not Broadcasting
**Symptoms:** Messages save to database but don't appear for other users
**Solution:**
```python
# Ensure proper room broadcasting
emit('receive_message', message_dict, room=room_id)  # Correct
# NOT: emit('receive_message', message_dict, room_id=room_id)  # Wrong
```

### Issue 3: Duplicate Event Handlers
**Symptoms:** Messages appear multiple times or don't work at all
**Solution:**
```bash
# Search for duplicate handlers
grep -r "@socketio.on" app.py blueprints/
# Should only find handlers in blueprints/chat/routes.py
```

### Issue 4: Namespace Mismatch
**Symptoms:** Events not reaching handlers
**Solution:**
```javascript
// Frontend must use correct namespace
const socket = io.connect('//' + document.domain + ':' + location.port + '/chat');
// NOT: const socket = io.connect('//' + document.domain + ':' + location.port);
```

## 🔧 **Testing Real-Time Messaging**

### Test 1: Basic Connection
1. Open two browser tabs/windows
2. Login as different users
3. Go to chat page
4. Check console for "Socket connected" messages

### Test 2: Message Broadcasting
1. User A sends a message
2. User B should see the message immediately
3. Check console for "Received message" logs

### Test 3: Room Switching
1. Switch rooms in one browser
2. Send message in new room
3. Other users in same room should see message

## 🔧 **Debug Commands**

### Check SocketIO Status
```bash
# Test SocketIO endpoint
curl -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:9091/socket.io/
```

### Check Database Messages
```bash
# View recent messages
docker-compose exec ndart python -c "
from app import create_app
from models import ChatMessage
app = create_app()
with app.app_context():
    messages = ChatMessage.query.order_by(ChatMessage.created_at.desc()).limit(5).all()
    for msg in messages:
        print(f'{msg.created_at}: {msg.sender}: {msg.content}')
"
```

### Check Event Handlers
```bash
# List all SocketIO event handlers
docker-compose exec ndart python -c "
from app import create_app
from extensions import socketio
app = create_app()
print('SocketIO event handlers:')
for handler in socketio.handlers:
    print(f'  {handler}')
"
```

## 🔧 **Performance Optimization**

### 1. Connection Pooling
```python
# In gunicorn.conf.py
worker_connections = 1000
timeout = 120
```

### 2. Message Rate Limiting
```python
# In blueprints/chat/routes.py
@rate_limit_messages()
def handle_send_message(data):
    # Rate limiting implementation
```

### 3. Database Optimization
```python
# Use database indexes
class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    __table_args__ = (
        db.Index('idx_room_created', 'room_id', 'created_at'),
    )
```

## 🔧 **Monitoring and Alerts**

### Health Check Endpoint
```bash
# Check chat functionality
curl http://localhost:9091/health
```

### Log Monitoring
```bash
# Monitor chat logs
docker-compose logs -f ndart | grep -E "(send_message|receive_message|SocketIO)"
```

### Error Tracking
```python
# Add error handling
@socketio.on_error_default
def default_error_handler(e):
    logger.error(f"SocketIO error: {e}")
    emit('error', {'message': 'An error occurred'})
```

## 🔧 **Production Considerations**

### 1. Use Production WSGI Server
```bash
# Use Gunicorn with eventlet for production
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:9091 wsgi:app
```

### 2. Configure Reverse Proxy
```nginx
# Nginx configuration for WebSocket support
location /socket.io/ {
    proxy_pass http://ndart-app:9091;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### 3. Database Connection Pooling
```python
# Configure SQLAlchemy for production
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

## 🔧 **Quick Fixes**

### If Messages Still Don't Appear:
1. **Clear browser cache** and reload
2. **Check browser console** for JavaScript errors
3. **Verify SocketIO connection** in Network tab
4. **Test with different browsers** to isolate issues
5. **Check server logs** for error messages

### If Connection Fails:
1. **Restart container**: `docker-compose restart`
2. **Check port binding**: Ensure port 9091 is accessible
3. **Verify SocketIO version**: Check static/js/socket.io version
4. **Test with curl**: `curl -H "Connection: Upgrade" http://localhost:9091/socket.io/`

The chat real-time messaging should now work properly with messages appearing immediately for all users in the same room! 🎉
