import gradio as gr
import threading, queue, time
from helpers import ux
from essay_coach_poc_gui import EssayCoachFlow

flow = EssayCoachFlow()

# Run the flow in a background thread so the UI stays responsive
threading.Thread(target=flow.kickoff, daemon=True).start()

# Track whether the flow has finished
session_over = False

def drain_out(max_idle=10.15):
    """Pop all pending tutor messages.
       Stop when the queue stays empty for max_idle seconds."""
    msgs = []
    last_pop = time.time()
    while True:
        try:
            m = ux.out.get_nowait()            # non-blocking
            msgs.append(m)
            last_pop = time.time()
        except queue.Empty:
            if time.time() - last_pop >= max_idle:
                break                          # nothing new → flow is waiting
            time.sleep(0.02)                   # brief yield
    return msgs

def chat_v1(user_msg, history):
    global session_over
    if session_over:
        return gr.ChatMessage(role="assistant",
                              content="🔒 The session is over. Refresh to start again.")

    # 1️⃣ Pass the student's answer to the flow
    ux.in_.put(user_msg)

    # 2️⃣ Get the next prompt (or sentinel) from the flow
    next_msg = ux.out.get()

    # 3️⃣ Detect completion
    if next_msg == "<FLOW_DONE>":
        session_over = True
        return gr.ChatMessage(role="assistant", content="✅ Session complete!")

    # 4️⃣ Normal turn: just return the assistant message
    return gr.ChatMessage(role="assistant", content=next_msg)


def chat_v3(user_msg, history):
    ux.in_.put(user_msg)              # answer the flow
    msgs = drain_out()                # grab every new tutor line

    for m in msgs:
        if m == "<FLOW_DONE>":
            return gr.ChatMessage(role="assistant",
                                  content="✅ Session complete!")

        history.append(gr.ChatMessage(role="assistant", content=m))
    return gr.ChatMessage(role="assistant", content=history[-1].content)  # return the last message

def chat_v4(user_msg, history):
    global session_over
    if session_over:
        return {"role": "assistant",
                "content": "🔒 The session is over. Refresh to start again."}

    # ① Push the student's reply to the flow
    ux.in_.put(user_msg)

    # ② Drain everything the flow emitted (using the timeout-drain helper)
    msgs = drain_out()

    # ③ Handle completion sentinel
    if "<FLOW_DONE>" in msgs:
        session_over = True
        return {"role": "assistant", "content": "✅ Session complete!"}

    # ④ Forward the flow’s messages to the UI
    #    ─ ChatInterface will append this single dict to history for us
    tutor_reply = "\n\n".join(m for m in msgs) or "…"      # join if many lines
    return {"role": "assistant", "content": tutor_reply}


demo = gr.ChatInterface(
    fn=chat_v4,
    title="WritePal, K-12 Essay Coach",
    type="messages"        # future-proof: explicit modern format
)
demo.launch(share=False,ssl_verify=False,
                        debug=False,
                        server_name="0.0.0.0")
