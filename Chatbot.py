import streamlit as st
import time
import requests
import json
import os
import logging

_FIELD_SEPARATOR = ":"


class SSEClient(object):
    """Implementation of a SSE client.
    See http://www.w3.org/TR/2009/WD-eventsource-20091029/ for the
    specification.
    """

    def __init__(self, event_source, char_enc="utf-8"):
        """Initialize the SSE client over an existing, ready to consume
        event source.
        The event source is expected to be a binary stream and have a close()
        method. That would usually be something that implements
        io.BinaryIOBase, like an httplib or urllib3 HTTPResponse object.
        """
        self._logger = logging.getLogger(self.__class__.__module__)
        self._logger.debug("Initialized SSE client from event source %s", event_source)
        self._event_source = event_source
        self._char_enc = char_enc

    def _read(self):
        """Read the incoming event source stream and yield event chunks.
        Unfortunately it is possible for some servers to decide to break an
        event into multiple HTTP chunks in the response. It is thus necessary
        to correctly stitch together consecutive response chunks and find the
        SSE delimiter (empty new line) to yield full, correct event chunks."""
        data = b""
        for chunk in self._event_source:
            for line in chunk.splitlines(True):
                data += line
                if data.endswith((b"\r\r", b"\n\n", b"\r\n\r\n")):
                    yield data
                    data = b""
        if data:
            yield data

    def events(self):
        for chunk in self._read():
            event = Event()
            # Split before decoding so splitlines() only uses \r and \n
            for line in chunk.splitlines():
                # Decode the line.
                line = line.decode(self._char_enc)

                # Lines starting with a separator are comments and are to be
                # ignored.
                if not line.strip() or line.startswith(_FIELD_SEPARATOR):
                    continue

                data = line.split(_FIELD_SEPARATOR, 1)
                field = data[0]

                # Ignore unknown fields.
                if field not in event.__dict__:
                    self._logger.debug(
                        "Saw invalid field %s while parsing " "Server Side Event", field
                    )
                    continue

                if len(data) > 1:
                    # From the spec:
                    # "If value starts with a single U+0020 SPACE character,
                    # remove it from value."
                    if data[1].startswith(" "):
                        value = data[1][1:]
                    else:
                        value = data[1]
                else:
                    # If no value is present after the separator,
                    # assume an empty value.
                    value = ""

                # The data field may come over multiple lines and their values
                # are concatenated with each other.
                if field == "data":
                    event.__dict__[field] += value + "\n"
                else:
                    event.__dict__[field] = value

            # Events with no data are not dispatched.
            if not event.data:
                continue

            # If the data field ends with a newline, remove it.
            if event.data.endswith("\n"):
                event.data = event.data[0:-1]

            # Empty event names default to 'message'
            event.event = event.event or "message"

            yield event

    def close(self):
        """Manually close the event source stream."""
        self._event_source.close()


class Event(object):
    """Representation of an event from the event stream."""

    def __init__(self, id=None, event="message", data="", retry=None):
        self.id = id
        self.event = event
        self.data = data
        self.retry = retry

    def __str__(self):
        s = "{0} event".format(self.event)
        if self.id:
            s += " #{0}".format(self.id)
        if self.data:
            s += ", {0} byte{1}".format(len(self.data), "s" if len(self.data) else "")
        else:
            s += ", no data"
        if self.retry:
            s += ", retry in {0}ms".format(self.retry)
        return s


host = os.environ.get("CANONICAL_HOST", "http://localhost:8000/")
api_url = host + "api/v1/demo"

with st.sidebar:
    st.markdown(
        """
# Canonical Semantic Cache
## How to integrate with your app
- Set the OpenAI base URL.
- Set Canonical API key.
- Choose your bucket.

Here's an example.

```python
import httpx
import openai
import os

    client = openai.OpenAI(
    base_url=os.environ.get("CANONICAL_CACHE_HOST", None),
    api_key=os.environ.get("OPENAI_API_KEY", None),
    http_client=httpx.Client(
        headers={
            "X-Canonical-Api-Key": os.environ.get("CANONICAL_CACHE_API_KEY", None),

            # Required - The name of the bucket you want to use. Think of a bucket as a namespace.
            # You can have one per app, or one per user, or one per whatever you want. It's
            # logical scoping of LLM request, use it however makes sense for your app.
            "X-Canonical-Bucket": os.environ.get("CANONICAL_CACHE_BUCKET", None),

            # Optional - Default is false. If true the request will will bypass the cache and go straight to the LLM.
            "X-Canonical-Skip-Cache": "False",

            # Optional - Default is None. The maximum age of the cache entry in seconds.
            # If the cache entry is older than this value, the cache will be bypassed and the request will go
            # straight to the LLM. Subsequently, the matching entry (if one exists) will be refreshed.
            "X-Canonical-Age": None,

            # Optional - Default is "False". If true, on a cache hit, the response will be rephrased using our local LLM.
            # This is useful if you want to avoid sending the same response to the user.
            "X-Canonical-Rephrase": "False",
        },
    ),
)
```
Then use the OpenAI client as you normally would.
```python
client.chat.completions.create(...)
```
We pass back a fiew pieces of information in the response headers. They are:
- `X-Canonical-Cache-Hit`: True or False
- `X-Canonical-Cache-Score`: The similarity score (0 - 1.0) of the closest match
- More to be add soon

Interested in trying it out or want to learn more about how it works?
Contact us at

[adrian@canonical.chat](mailto:adrian@canonical.chat)

[tom@canonical.chat](mailto:tom@canonical.chat)

Or book a meeting with us [here](https://calendly.com/tom-tule/30min).

For a more prompt response, text us at [(707) 344 - 0840](tel:7073440840).
"""
    )

st.markdown(
    """
# Canonical Semantic Cache Demo
## Do Things That Don't Scale
By Paul Graham

Ask PG a question, then asking a similar one to see how the cache works.
Or ask him a dissimilar one, I don't care.

Shot out to PG for writing this essay. It's a classic. Thank you. :hearts:
"""
)
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask PG"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    start = time.perf_counter()

    with st.chat_message("assistant"):
        full_response = ""
        message_placeholder = st.empty()

        resp = requests.request(
            method="POST",
            url=api_url,
            stream=True,
            headers={
                "Content-Type": "application/vnd.api+json",
            },
            data=json.dumps(
                {
                    "data": {
                        "type": "DemoAPIView",
                        "attributes": {
                            "query": prompt,
                            "corpus_id": os.environ.get(
                                "CORPUS_ID", "469c3636-b9e1-4b5e-8312-463012295af1"
                            ),
                        },
                    }
                }
            ),
            allow_redirects=False,
        )
        finish = time.perf_counter()
        duration = finish - start
        sseclient = SSEClient(resp)
        for event in sseclient.events():
            full_response += event.data
            message_placeholder.markdown(full_response)
        full_response += "\n\nCache hit: " + resp.headers.get(
            "X-Canonical-Cache-Hit", "False"
        )
        full_response += f"\n\nThe request took {round(duration, 3)} seconds."
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
