from pydantic import BaseModel

class _ServerSettingsSchema(BaseModel):
    server_url: str = 'http://127.0.0.1:8000'
    post_message_path: str = '/messages/send'

class _GraphicsSettingsSchema(BaseModel):
    pass

class SettingsSchema(BaseModel):
    graphics: _GraphicsSettingsSchema
    server: _ServerSettingsSchema