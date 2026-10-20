with open('bot/database/models.py', 'r', encoding='utf-8') as f:
    text = f.read()
    
new_model = '''class SupportMessage(Base):
    """Yordam so'rovlari jadvali."""
    __tablename__ = "support_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_type = Column(String(20), default="text") # text, photo, voice, video
    text_content = Column(Text, nullable=True)
    file_id = Column(String(255), nullable=True)
    status = Column(String(20), default="NEW") # NEW, READ
    created_at = Column(DateTime, default=func.now())
    
    user = relationship("User", lazy="joined")


class Payment(Base):'''

text = text.replace('class Payment(Base):', new_model)

with open('bot/database/models.py', 'w', encoding='utf-8') as f:
    f.write(text)
