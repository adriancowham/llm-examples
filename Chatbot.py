import streamlit as st
import time
import os
import requests
import openai
import httpx
import json

SYSTEM_PROMPT = """Assume the persona of Paul Graham, the co-founder of Y Combinator and the author of the influential essay
'Do Things That Don't Scale.' You are known for your insightful advice to startups and your unique
perspective on entrepreneurship. Respond to the following queries with the depth of understanding
and the conversational yet insightful style characteristic of your essays, especially drawing upon
the ideas from 'Do Things That Don't Scale."""


with st.sidebar:
    st.markdown(
        """
# Canonical Semantic Cache
Interested in trying it out or want to learn more about how it works?
Contact us at

[founders@canonical.chat](mailto:founders@canonical.chat)

Or book a meeting with us [here](https://calendly.com/tom-tule/30min).

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
    base_url="https://cache.canonical.chat/",
    http_client=httpx.Client(
        headers={
            "X-Canonical-Api-Key": os.environ.get("CANONICAL_CACHE_API_KEY", None),

            # Required - The name of the bucket you want to use. Think of a bucket as a namespace.
            # You can have one per app, or one per user, or one per whatever you want. It's
            # logical scoping of LLM request, use it however makes sense for your app.
            "X-Canonical-Cache-Bucket": os.environ.get("CANONICAL_CACHE_BUCKET", None),
        },
    ),
)
```
Then use the OpenAI client as you normally would. But please note, we currently return a 404 if a match
isn't found.
```python
try:
    completion = client.chat.completions.create(...)
except openai.NotFoundError as e:
    # do something
```
Here's how to update the Cache:
```python
requests.request(
    method="POST",
    url="https://cache.canonical.chat/api/v1/cache",
    headers={
        "Content-Type": "application/json",
        "X-Canonical-Api-Key": os.environ.get("CANONICAL_CACHE_API_KEY", None),
    },
    data=json.dumps({
        "bucket": <bucket_name>,
        "messages": msglist,
    })
)
```
Take note of the path in the URL, `api/v1/cache`. The body is a JSON object with two keys:
- `bucket`: The name of the bucket you want to update.
- `messages`: A list of messages. Each message is a JSON object with two keys:
    - `role`: The role of the message. Either `system`, `user`, `assistant`, `function`, `function_result`, etc....
    - `content`: The content of the message.
Here is an example of a valid request body:
```json
{
    "bucket": "my_bucket",
    "messages": [
        {
            "role": "user",
            "content": "Hello, how are you?"
        },
        {
            "role": "assistant",
            "content": "I'm doing well, how are you?"
        },
    ]
}
```
We pass back a fiew pieces of information in the response headers. They are:
- `X-Canonical-Cache-Hit`: True or False
- `X-Canonical-Cache-Score`: The similarity score (0 - 1.0) of the closest match
- More to be added soon
"""
    )

st.markdown(
    """
# Canonical Semantic Cache Demo
## Do Things That Don't Scale
By Paul Graham

Ask PG a question, then asking a similar one to see how the cache works.
Or ask him a dissimilar one, I don't care.

Shout out to PG for writing this essay.
"""
)


def update_cache(messages):
    return requests.request(
        method="POST",
        url=f"{os.environ.get('CANONICAL_CACHE_HOST', 'http://localhost:8001/')}api/v1/cache",
        headers={
            "Content-Type": "application/json",
            "X-Canonical-Api-Key": os.environ.get("CANONICAL_CACHE_API_KEY", None),
        },
        data=json.dumps(
            {
                "bucket": "DEMO - PG",
                "messages": messages,
            }
        ),
    )


if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

for msg in st.session_state.messages:
    if msg["role"] != "system":
        st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask PG"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    start = time.perf_counter()

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        client = openai.OpenAI(
            base_url=os.environ.get("CANONICAL_CACHE_HOST", None),
            api_key=os.environ.get("CANONICAL_CACHE_API_KEY", None),
            http_client=httpx.Client(
                headers={
                    "X-Canonical-Api-Key": os.environ.get(
                        "CANONICAL_CACHE_API_KEY", None
                    ),
                    "X-Canonical-Cache-Bucket": "DEMO - PG",
                }
            ),
        )
        cache_hit = False
        start = time.perf_counter()
        try:
            completion = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                stream=True,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )
            cache_hit = True
        except openai.NotFoundError as e:
            client = openai.OpenAI(
                api_key=os.environ.get("OPENAI_API_KEY", None),
            )
            completion = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                stream=True,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )
        finish = time.perf_counter()
        duration = finish - start
        metrics = ""
        metrics += f"\n\nCache hit: {str(cache_hit)}"
        metrics += f"\n\nTime to first token: {round(duration, 3)} seconds.\n\n"

        full_response = ""
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
                message_placeholder.markdown(metrics + full_response)

        if not cache_hit:
            update_cache(
                [
                    {
                        "role": "user",
                        "content": prompt,
                    },
                    {
                        "role": "assistant",
                        "content": full_response,
                    },
                ]
            )
    st.session_state.messages.append(
        {"role": "assistant", "content": metrics + full_response}
    )
