from openai import OpenAI
import streamlit as st
import time 
import requests
import json 

st.set_page_config(initial_sidebar_state="collapsed")

st.markdown(
    """
<style>
    [data-testid="collapsedControl"] {
        display: none
    }
</style>
""",
    unsafe_allow_html=True,
)

st.title("Do things that don't Scale")
st.caption("By Paul Graham")
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask PG"):
    start = time.perf_counter()

    resp = requests.request(
        method="POST",
        url="http://api.canonical.chat/api/v1/demo",
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
                        "corpus_id": "469c3636-b9e1-4b5e-8312-463012295af1",
                    },
                }
            }
        ),
        allow_redirects=False,
    )    
    finish = time.perf_counter()
    duration = finish - start
    st.write(resp)
    st.write(f"The request took {round(duration, 3)} seconds to run.")
    # client = OpenAI(api_key="")
    # st.session_state.messages.append({"role": "user", "content": prompt})
    # st.chat_message("user").write(prompt)
    # response = client.chat.completions.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
    # msg = response.choices[0].message.content
    # st.session_state.messages.append({"role": "assistant", "content": msg})
    # st.chat_message("assistant").write(msg)
