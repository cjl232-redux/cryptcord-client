import aiosqlite
import asyncio

from typing import Awaitable, Callable

from json_types import JSONDict

_DATA_HANDLERS: dict[str, Callable[[int, JSONDict], Awaitable[JSONDict]]] = {

}

class MalformedDataError(Exception):
    pass

class UnrecognisedCommandError(Exception):
    pass

async def get_user_id(
        connection: aiosqlite.Connection,
        public_key: str,
    ) -> int:
    """
    Retrieves a unique user id for the supplied public key.

    If the public key is already stored in the database's user's table, this
    returns the associated id. Otherwise, it adds a new row and then returns
    that row's id.
    """
    RETRIEVAL_QUERY = 'SELECT id FROM users WHERE public_key = ?'
    INSERTION_QUERY = 'INSERT INTO users(public_key) VALUES(?) RETURNING id'
    #async with aiosqlite.connect(db_name) as conn:
    async with connection.execute(RETRIEVAL_QUERY, (public_key,)) as cursor:
        row = await cursor.fetchone()
    if row is not None:
        return row[0]
    else:
        async with connection.execute(INSERTION_QUERY, (public_key,)) as cursor:
            row = await cursor.fetchone()
        return row[0]


async def handle_data(
        connection: aiosqlite.Connection,
        data: JSONDict,
        public_key: str,
    ) -> JSONDict:
    id = await get_user_id(connection, public_key)
    if 'command' not in data:
        raise MalformedDataError()
    elif data['command'] not in _DATA_HANDLERS:
        raise UnrecognisedCommandError()
    if 'command' in data and data['command'] in _DATA_HANDLERS:
        return await _DATA_HANDLERS[data['command']]
    else:
        raise MalformedDataError()