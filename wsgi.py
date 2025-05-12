from app import create_app, init_socketio
   
app = create_app()
socketio_app = init_socketio(app)
   
# For WSGI servers
application = app