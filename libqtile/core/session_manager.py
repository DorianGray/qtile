import asyncio
import os
from typing import Optional

from libqtile import ipc
from libqtile.core.loop import QtileLoop
from libqtile.core.manager import Qtile


class SessionManager:
    def __init__(self, qtile: Qtile, *, socket_path: str = None) -> None:
        """Manages a qtile session

        :param qtile:
            The Qtile instance to manage
        :param socket_path:
            The file name to use as the qtile socket file.
        """
        self.qtile = qtile
        self.server = ipc.Server(
            self._prepare_socket_path(socket_path),
            self.qtile.server.call,
        )

    def _prepare_socket_path(self, socket_path: Optional[str] = None) -> str:
        if socket_path is None:
            # Dots might appear in the host part of the display name
            # during remote X sessions. Let's strip the host part first
            display_name = self.qtile.core.display_name
            display_number = display_name.partition(":")[2]
            if "." not in display_number:
                display_name += ".0"
            socket_path = ipc.find_sockfile(display_name)

        if os.path.exists(socket_path):
            os.unlink(socket_path)

        return socket_path

    def loop(self) -> None:
        asyncio.run(self.async_loop())

    async def async_loop(self) -> None:
        async with QtileLoop(self.qtile), self.server:
            await self.qtile.async_loop()
