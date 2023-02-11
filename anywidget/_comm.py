from __future__ import annotations
from typing import TYPE_CHECKING, Any, cast

import comm.base_comm
from ipykernel.jsonutil import json_clean
from ipykernel.kernelbase import Kernel
import json


if TYPE_CHECKING:
    from jupyter_client.session import Session

# mostly copied from ipykernel.comm... but
# 1. we don't inherit from LoggingConfigurable
# 2. we add typing
# 3. we add a hook for customizing serialization


class Comm(comm.base_comm.BaseComm):
    """The base class for comms."""

    kernel: Kernel | None = None

    def send(self, data=None, metadata=None, buffers=None):
        """Send a message to the frontend-side version of this comm"""
        self.publish_msg(
            "comm_msg",
            data=data,
            metadata=metadata,
            buffers=buffers,
        )

    def publish_msg(
        self,
        msg_type: str,
        data: Any = None,
        metadata: Any = None,
        buffers: Any = None,
        **keys: Any,
    ) -> None:
        """Helper for sending a comm message on IOPub"""
        if not Kernel.initialized():
            return

        data = {} if data is None else data
        metadata = {} if metadata is None else metadata

        # json_clean is a no-op for jupyter-client>=7.
        content = json_clean(dict(data=data, comm_id=self.comm_id, **keys))

        if self.kernel is None:
            self.kernel = Kernel.instance()

        # in the sending process below, content is first turned into a message
        # (just a dict) by the `Session.send` method here:
        # https://github.com/jupyter/jupyter_client/blob/557530b9f9ade569a22f651e36ac54b939b96ec3/jupyter_client/session.py#L821-L826

        # the msg dict is then serialized by `Session.serialize`` here:
        # https://github.com/jupyter/jupyter_client/blob/557530b9f9ade569a22f651e36ac54b939b96ec3/jupyter_client/session.py#L850

        # `serialize` has a clause that passes `content` through if it's already bytes:
        #   elif isinstance(content, bytes):
        #       # content is already packed, as in a relayed message
        #       pass

        # this means that we can customize the serialization of the content by
        # making `content` bytes rather than a dict here

        session = cast("Session", self.kernel.session)
        session.send(
            self.kernel.iopub_socket,
            msg_type,
            content,
            metadata=json_clean(metadata),
            parent=self.kernel.get_parent("shell"),
            ident=self.topic,
            buffers=buffers,
        )
