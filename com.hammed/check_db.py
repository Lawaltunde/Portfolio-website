from app import app, db, Message

with app.app_context():
    messages = Message.query.order_by(Message.timestamp.desc()).all()
    if messages:
        print("Messages found in the database:")
        for message in messages:
            print(f"  ID: {message.id}")
            print(f"  Name: {message.user_name}")
            print(f"  Email: {message.email}")
            print(f"  Subject: {message.subject}")
            print(f"  Message: {message.message}")
            print(f"  Timestamp: {message.timestamp}")
            print("-" * 20)
    else:
        print("No messages found in the database.")