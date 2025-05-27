from ipaddress import ip_address

from app_components.dialogs.base_dialogs import DescriptionData, Dialog
from app_components.dialogs.fields import ButtonData, Field, PasswordField

class ServerDialog(Dialog):
    def __init__(self, master, title: str ='Server Dialog', *args, **kwargs):
        super().__init__(
            master=master,
            title=title,
            description_data=self.description_data,
            fields={
                'ip_address': Field(name='IP Address', default='127.0.0.1'),
                'port_number': Field(name='Port Number', default=8888),
            },
            validators=[
                self._validate_ip_address,
                self._validate_port,
            ],
            *args,
            **kwargs,
        )

    description_text = 'Provide an IP address and a port to connect to.'
    description_data = DescriptionData(description_text, 480)

    def _validate_ip_address(self, values: dict[str, str]) -> str | None:
        address = values.get('ip_address', '')
        if not address:
            return 'A value is required for the IP address field.'
        try:
            ip_address(address)
        except ValueError:
            return f'{address} is not a valid IP address.'

    def _validate_port(self, values: dict[str, str]) -> str | None:
        port = values.get('port_number', '')
        if not port:
            return 'A value is required for the port number field.'
        try:
            if not 0 <= int(port) <= 65535:
                return 'The port number must be between 0 and 65535.'
        except ValueError:
            return 'The port number must be an integer.'

