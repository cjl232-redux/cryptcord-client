class User:
    def __init__(self, verification_key : bytes):
        """
        Constructs a user object.

        Parameters
        ----------
        verification_key : bytes
            A public key used to verify all messages received from the user.
        """
        self.verification_key = verification_key
        pass
    pass