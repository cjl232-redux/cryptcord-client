import binascii

from base64 import urlsafe_b64decode, urlsafe_b64encode


def _validate_key(value: str) -> str:
    try:
        raw_bytes = urlsafe_b64decode(value)
        if len(raw_bytes) != 32:
            raise ValueError('Value must have an unencoded length of 32 bytes')
        return urlsafe_b64encode(raw_bytes).decode()
    except binascii.Error:
        raise ValueError('Value is not valid Base64')

def _toggle_password_visibility(entry: tk.Entry, _):
    entry.config(show='●' if entry.cget('show') == '' else '')
    entry.focus()

class _PrivateKeyPasswordModel(BaseModel):
    password: Annotated[
        str,
        Field(title='Password'),
        FieldButtonData('Show/Hide', _toggle_password_visibility),
        FieldPropertiesData(hidden=True),
    ]