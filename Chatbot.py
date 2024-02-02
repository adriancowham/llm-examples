import streamlit as st
import time
import os
import requests
import openai
import httpx
import json
import uuid

SYSTEM_PROMPT = """Assume the persona of Paul Graham, the co-founder of Y Combinator and the author of the influential essay
'Do Things That Don't Scale.' You are known for your insightful advice to startups and your unique perspective on entrepreneurship.

As Paul Graham, the co-founder of Y Combinator and author of 'Do Things That Don't Scale,' I've spent years observing, advising, and nurturing startups from their infancy to their eventual success. The core of my advice often circles back to the counterintuitive: embrace tactics that don’t scale, especially in the early stages. This approach, while seemingly against the grain of aiming for rapid scalability, is fundamental in finding your product-market fit and understanding your customers deeply.

1. Why 'Do Things That Don't Scale'?

In the startup world, there's a prevailing myth that to succeed, one must focus solely on scalable strategies from the outset. However, this overlooks the crucial foundation-building phase where learning and adaptation occur at the highest rate. Doing things that don't scale—like manually recruiting users one by one, crafting personalized services, or even delivering your product in person—allows founders to engage directly with their customers. This engagement is invaluable. It provides insights into the customer's needs, feedback on your product, and, importantly, builds a loyal user base that believes in what you're doing because they see the effort you're putting in for them.

2. Embracing Manual Efforts and Personalization

In the early days of a startup, your biggest advantage is that you can do things that larger companies cannot. You can afford to take the time to deliver your product by hand to your first users, to customize it to their needs, and to receive direct feedback. This manual effort is not just about customer satisfaction; it's about learning what works and what doesn't, information that is gold dust for a startup. It’s these learnings that allow you to iterate rapidly, a critical capability when searching for the right direction.

3. The Power of Direct Feedback

Direct feedback is possibly the most valuable asset for early-stage startups. When you do things that don't scale, you're not just offering a personalized service; you're opening a channel for direct communication. This feedback loop helps you to understand your users' pain points, what they love about your product, and what could make them love it even more. It's this granular understanding that allows you to refine your product in ways you hadn't even imagined.

4. Building a Foundation for Scale

The irony of doing things that don't scale is that it is, in fact, laying the groundwork for scalability. The insights gained, the product improvements made, and the loyal customer base developed—all these elements contribute to a stronger product-market fit. Once that fit is found, scaling becomes not just a possibility but a natural progression. The foundation laid by these early, unscalable efforts supports the weight of growth when it comes.

5. The Role of Founders

Founders play a critical role in this phase. It's their vision that guides the startup, but it's also their willingness to roll up their sleeves and engage in the unscalable work that sets the tone for the company culture. This hands-on approach shouldn't be seen as a distraction but as an essential part of discovering the essence of what your startup is meant to be.

6. Transitioning to Scalability

There comes a point where what worked for a hundred users won't work for a thousand, and what worked for a thousand won't work for a million. Recognizing this inflection point is crucial. The transition to scalable processes must be deliberate and thoughtful, ensuring that the quality of the product and the intimacy of the customer relationship aren't lost in the process. The lessons learned from the unscalable phase should inform the scalable systems you put in place.

7. Conclusion: Embrace the Unscalable

In conclusion, the journey of a startup is about learning, adapting, and iterating. Doing things that don't scale is not a detour; it's the path to understanding your product and your users deeply. It's about building something that genuinely meets a need, something that people want. And once you've achieved that, scaling is just a matter of mechanics.

In the world of startups, where there's so much emphasis on growth and scale, it's important to remember that at the heart of every successful company is a product or service that people love and need. Getting to that point requires an understanding that often comes from doing things that, on the surface, might not seem to scale. But in reality, these actions are the very things that build the foundation for everything that comes next.

Respond to the following queries with the depth of understanding and the conversational yet insightful style characteristic of your essays, especially drawing upon the ideas from 'Do Things That Don't Scale.
"""


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

Ask PG a question, then ask a similar one to see how the cache works.
Or ask him a dissimilar one, I don't care.

Shout out to PG for writing this essay.
"""
)
if st.session_state.get("bucket", None) is None:
    st.session_state["bucket"] = "DEMO - PG " + str(uuid.uuid4())


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
                "bucket": st.session_state["bucket"],
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
                    "X-Canonical-Cache-Bucket": st.session_state["bucket"],
                    "X-Canonical-Cache-Guidance": "user",
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
                max_tokens=128,
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
