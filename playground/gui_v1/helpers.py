# helpers.py
import queue, threading

class UXChannel:
    def __init__(self):
        self.out = queue.Queue()    # Flow → GUI
        self.in_ = queue.Queue()    # GUI  → Flow

    def ask(self, prompt: str):
        """Called by Flow; returns student's reply."""
        self.out.put(prompt)        # send question to GUI
        return self.in_.get()       # block until GUI answers

    def done(self):
        """Mark the Flow as complete."""
        self.out.put("<FLOW_DONE>") # special sentinel

ux = UXChannel()
