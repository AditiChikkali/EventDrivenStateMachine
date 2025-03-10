# Import required libraries
from flask import Flask, render_template, request, jsonify
from transitions import Machine
import threading
import subprocess
import os
import socket
import time
import platform  # For OS detection
import logging

# ================================
# 1. Configure Logging at the Top
# ================================

# Define the log file path
log_file_path = os.path.join(os.path.dirname(__file__), "sample.log")

# Create a custom logger
logger = logging.getLogger("FSMLogger")
logger.setLevel(logging.DEBUG)  # Log everything to console

# Create handlers
file_handler = logging.FileHandler(log_file_path, mode="a")
file_handler.setLevel(logging.WARNING)  # Log only WARNING and above to file

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Log everything to console

# Create formatters and add them to handlers
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Initialize Flask app
app = Flask(__name__, template_folder="../FE")

# ================================
# 2. Define Error Check Functions
# ================================


def is_log_file_missing():
    return not os.path.exists(log_file_path)


def is_log_file_empty():
    return os.path.exists(log_file_path) and os.path.getsize(log_file_path) == 0


def is_log_file_too_large():
    max_size = 10 * 1024 * 1024  # 10 MB
    return os.path.exists(log_file_path) and os.path.getsize(log_file_path) > max_size


def is_network_unavailable():
    try:
        socket.create_connection(("www.google.com", 80))
        return False
    except OSError:
        return True


# Command execution error check (Cross-platform Fix)
def execute_command():
    try:
        if platform.system() == "Windows":
            subprocess.run(
                ["powershell", "-Command", "Get-Content", log_file_path, "-Wait"],
                check=True,
            )
        else:
            subprocess.run(["tail", "-f", log_file_path], check=True)
    except subprocess.CalledProcessError:
        logger.error("Command execution error.")
        fsm.error()
    except FileNotFoundError:
        logger.error("Log file not found.")
        fsm.error()
    except PermissionError:
        logger.error("Permission denied for log file.")
        fsm.error()


# ================================
# 3. Define FSM and States
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
        logger.info(f"Transitioned to {self.state} state.")

    def on_starting(self):
        logger.info("Transitioning to starting...")
        if is_log_file_missing():
            logger.error("Log file not found.")
            self.error()
            return
        if is_network_unavailable():
            logger.error("Network connectivity error.")
            self.error()
            return
        threading.Timer(2.0, self.run).start()

    def on_running(self):
        logger.info("Service is running...")
        threading.Thread(target=self.tail_log).start()

    def on_stopping(self):
        logger.info("Entered on_stopping function.")
        try:
            logger.info("Stopping service...")
            threading.Timer(2.0, self.reset).start()
            logger.info("Reset timer started.")
        except Exception as e:
            logger.error(f"Exception in on_stopping: {e}")
            self.error()

    # ================================
    # 4. Define Log Tailing with Error Handling
    # ================================
    def tail_log(self):
        if is_log_file_missing():
            logger.error("Log file not found.")
            self.error()
            return
        if is_log_file_empty():
            logger.warning("Log file is empty.")
            self.error()
            return
        if is_log_file_too_large():
            logger.warning("Log file size exceeded.")
            self.error()
            return
        if is_network_unavailable():
            logger.error("Network connectivity error.")
            self.error()
            return

        try:
            with open(log_file_path, "r") as file:
                file.seek(0, 2)
                while self.state == "running":
                    line = file.readline()
                    if line:
                        logger.info(line.strip())  # Log lines from file
                    else:
                        time.sleep(1)
        except FileNotFoundError:
            logger.error("Log file not found.")
            self.error()
        except PermissionError:
            logger.error("Permission denied for log file.")
            self.error()
        except Exception as e:
            logger.error(f"Unexpected exception in tail service: {e}")
            self.error()

    def on_error(self):
        logger.info("System has encountered an error. Waiting for reset.")


fsm = ServiceFSM()


# ================================
# 5. Flask Routes
# ================================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/state", methods=["GET"])
def get_state():
    logger.debug(f"Current state: {fsm.state}")
    return jsonify({"state": fsm.state})


@app.route("/transition", methods=["POST"])
def transition():
    action = request.json.get("action")
    logger.debug(f"Received action: {action}")
    if action in ["start", "stop", "reset"]:
        try:
            logger.debug(f"Executing action: {action}")
            getattr(fsm, action)()
        except Exception as e:
            logger.error(f"Exception: {e}")
            fsm.error()
            return jsonify({"state": fsm.state, "error": str(e)}), 500
    else:
        logger.error("Invalid action received.")
    return jsonify({"state": fsm.state})


if __name__ == "__main__":
    app.run(debug=True)
