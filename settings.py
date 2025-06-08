import os

import yaml

from pydantic import BaseModel, ConfigDict

class _ServerSettingsModel(BaseModel):
    post_message_url: str = '127.0.0.1:8000/messages/post'
    post_exchange_key_url: str = '127.0.0.1:8000/exchange-keys/post'
    fetch_messages_url: str = '127.0.0.1:8000/messages/retrieve'
    fetch_exchange_keys_url: str = '127.0.0.1:8000/exchange-keys/retrieve'

class _SettingsModel(BaseModel):
    model_config = ConfigDict(validate_default=True)
    server: _ServerSettingsModel = _ServerSettingsModel()


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