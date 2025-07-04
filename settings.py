import os

import yaml

from pydantic import BaseModel, Field

class _DatabaseSettingsModel(BaseModel):
    url: str = 'sqlite:///database.db'

class _FunctionalitySettingsModel(BaseModel):
    message_refresh_interval: float = Field(default=1.0, ge=0.001)
    scroll_speed: int = Field(default=5, ge=1)

class _DialogGraphicsSettingsModel(BaseModel):
    description_wrap_length: int = Field(default=480, ge=1)
    field_gap: int = 4

class _GraphicsSettingsModel(BaseModel):
    dialogs: _DialogGraphicsSettingsModel = _DialogGraphicsSettingsModel()
    font_family: str = 'Segue UI'
    font_size: int = Field(default=9, ge=1)
    horizontal_padding: int = Field(default=10, ge=1)
    vertical_padding: int = Field(default=10, ge=1)

class _ServerSettingsModel(BaseModel):
    post_message_url: str = 'http://127.0.0.1:8000/data/post/message'
    post_exchange_key_url: str = 'http://127.0.0.1:8000/data/post/exchange-key'
    fetch_data_url: str = 'http://127.0.0.1:8000/data/fetch'
    ping_url: str = 'http://127.0.0.1:8000/ping'
    ping_timeout: float = Field(default=1.0, gt=0.0)
    request_timeout: float = Field(default=5.0, gt=0.0)
    operations_sleep: float = Field(default=5.0, ge=0.001)

class _SettingsModel(BaseModel):
    local_database: _DatabaseSettingsModel = _DatabaseSettingsModel()
    functionality: _FunctionalitySettingsModel = _FunctionalitySettingsModel()
    graphics: _GraphicsSettingsModel = _GraphicsSettingsModel()
    server: _ServerSettingsModel = _ServerSettingsModel()
    window_name: str = 'Cryptcord'
    def get_font(self):
        return (self.graphics.font_family, self.graphics.font_size)
    def get_font_bold(self):
        return self.get_font() + ('bold',)
    class Config:
        validate_default = True           

def _load_settings():
    # Create the settings file if necessary.
    if not os.path.exists('settings.yaml'):
        with open('settings.yaml', 'w') as _:
            pass

    # Load settings from the file.
    with open('settings.yaml', 'r') as file:
        data = yaml.safe_load(file)
        if isinstance(data, dict):
            settings = _SettingsModel.model_validate(data)
        else:
            settings = _SettingsModel.model_validate({})

    # Add default values to the file.
    with open('settings.yaml', 'w') as file:
        yaml.safe_dump(settings.model_dump(), file)

    # Return the settings object.
    return settings

settings = _load_settings()