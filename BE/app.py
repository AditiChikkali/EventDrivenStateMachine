# Import required libraries
from flask import Flask, render_template, request, jsonify
from transitions import Machine
import threading
import subprocess
import os
import socket
import time

# Initialize Flask app
app = Flask(__name__, template_folder="../FE")

# ================================
# 1. Define Error Check Functions
# ================================


def is_log_file_missing():
    log_file_path = os.path.join(os.path.dirname(__file__), "sample.log")
    return not os.path.exists(log_file_path)


def is_log_file_empty():
    log_file_path = "sample.log"
    return os.path.exists(log_file_path) and os.path.getsize(log_file_path) == 0


def is_log_file_too_large():
    log_file_path = "sample.log"
    max_size = 10 * 1024 * 1024  # 10 MB
    return os.path.exists(log_file_path) and os.path.getsize(log_file_path) > max_size


def is_network_unavailable():
    try:
        socket.create_connection(("www.google.com", 80))
        return False
    except OSError:
        return True


# Command execution error check
def execute_command():
    try:
        subprocess.run(["tail", "-f", "sample.log"], check=True)
    except subprocess.CalledProcessError:
        print("[ERROR] Command execution error.")
        fsm.error()


# ================================
# 2. Define FSM and States
# ================================

states = ["idle", "starting", "running", "error", "stopping"]


class ServiceFSM:
    def __init__(self):
        self.machine = Machine(model=self, states=states, initial="idle")
        self.machine.add_transition("start", "idle", "starting", after="on_starting")
        self.machine.add_transition("run", "starting", "running", after="on_running")
        self.machine.add_transition("stop", "running", "stopping", after="on_stopping")
        self.machine.add_transition("reset", "*", "idle")
        self.machine.add_transition("error", "*", "error")

        # Log state transitions
        for state in states:

            self.machine.add_transition(
                trigger=f"on_enter_{state}",
                source="*",
                dest=state,
                after="after_state_change",
            )

    def after_state_change(self):
        print(f"[INFO] Transitioned to {self.state} state.")

    def on_starting(self):
        print("[INFO] Transitioning to starting...")
        if is_log_file_missing():
            print("[ERROR] Log file not found.")
            self.error()
            return
        if is_network_unavailable():
            print("[ERROR] Network connectivity error.")
            self.error()
            return
        threading.Timer(2.0, self.run).start()

    def on_running(self):
        print("[INFO] Service is running...")
        threading.Thread(target=self.tail_log).start()

    def on_stopping(self):
        print("[INFO] Entered on_stopping function.")
        try:
            print("[INFO] Stopping service...")
            threading.Timer(2.0, self.reset).start()
            print("[INFO] Reset timer started.")
        except Exception as e:
            print(f"[ERROR] Exception in on_stopping: {e}")
            self.error()

    # ================================
    # 3. Define Log Tailing with Error Handling
    # ================================
    def tail_log(self):
        log_file_path = os.path.join(os.path.dirname(__file__), "sample.log")

        # Error checks before tailing the log
        if is_log_file_missing():
            print("[ERROR] Log file not found.")
            self.error()
            return
        if is_log_file_empty():
            print("[ERROR] Log file is empty.")
            self.error()
            return
        if is_log_file_too_large():
            print("[ERROR] Log file size exceeded.")
            self.error()
            return
        if is_network_unavailable():
            print("[ERROR] Network connectivity error.")
            self.error()
            return

        # Proceed with tailing if no errors
        try:
            with open(log_file_path, "r") as file:
                file.seek(0, 2)
                while self.state == "running":
                    line = file.readline()
                    if line:
                        print(line.strip())
                    else:
                        time.sleep(1)
        except FileNotFoundError:
            print("[ERROR] Log file not found.")
            self.error()
        except PermissionError:
            print("[ERROR] Permission denied for log file.")
            self.error()
        except Exception as e:
            print(f"[ERROR] Unexpected exception in tail service: {e}")
            self.error()

    def on_error(self):
        print("[INFO] System has encountered an error. Waiting for reset.")


fsm = ServiceFSM()


# ================================
# 4. Flask Routes
# ================================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/state", methods=["GET"])
def get_state():
    print(f"[DEBUG] Current state: {fsm.state}")
    return jsonify({"state": fsm.state})


@app.route("/transition", methods=["POST"])
def transition():
    action = request.json.get("action")
    print(f"[DEBUG] Received action: {action}")  # Log received action
    if action in ["start", "stop", "reset"]:
        try:
            print(f"[DEBUG] Executing action: {action}")  # Log action execution
            getattr(fsm, action)()
        except Exception as e:
            print(f"[ERROR] Exception: {e}")  # Log exceptions
            fsm.error()
            return jsonify({"state": fsm.state, "error": str(e)}), 500
    else:
        print("[ERROR] Invalid action received.")
    return jsonify({"state": fsm.state})


if __name__ == "__main__":
    app.run(debug=True)
