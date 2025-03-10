# EventDrivenStateMachine


#  **README: Event-Driven State Machine**

This README provides step-by-step instructions to set up and run the Event-Driven Finite State Machine (FSM) project.

---

##  **1. Prerequisites**

Before running the program, ensure you have the following installed:

- **Python 3.8+**  
- **pip** (Python package installer)

---

##  **2. Project Structure**

```
EventDrivenStateMachine/
├── BE/
│   ├── app.py              # Backend Flask app
│   ├── sample.log          # Log file required for the program
├── FE/
│   ├── index.html          # Frontend HTML file
├── README.md               # This file

```

---

##  **3. Installation Instructions**

###  **Step 1: Clone the Repository**
If you haven't downloaded the code yet, clone it using:
```bash
git clone https://github.com/AditiChikkali/EventDrivenStateMachine.git
cd EventDrivenStateMachine/BE
```

---

###  **Step 2: Create a Virtual Environment (Recommended)**
To avoid conflicts with other Python packages:
```bash
python -m venv venv
```

**Activate the environment:**
- **Windows:**  
   ```bash
   venv\Scripts\activate
   ```
- **Linux/Mac:**  
   ```bash
   source venv/bin/activate
   ```



---

###  **Step 4: Ensure `sample.log` Exists**
Ensure there is a file named `sample.log` inside the `BE` folder. If it doesn’t exist, create an empty file:
```bash
cd BE
type NUL > sample.log  # Windows
touch sample.log       # Linux/Mac
```

---

###  **Step 5: Run the Flask Server**
In the `BE` folder, run:
```bash
python app.py
```

**Expected Output:**
```
 * Running on http://127.0.0.1:5000/
```

---

## 🛠 **4. Access the Frontend**

Open a web browser and go to:
```
http://127.0.0.1:5000/
```

---

##  **5. Using the Application**

###  **Available Controls:**
- **Start:** Begin the log reading service.  
- **Stop:** Safely stop the service.  
- **Reset:** Clear errors and return to `idle` state.

---

###  **API Endpoints:**

1. **Get Current State:**
   ```
   GET /state
   ```
   **Example Response:**
   ```json
   { "state": "idle" }
   ```

2. **Trigger State Transitions:**
   ```
   POST /transition
   ```
   **Payload Example:**
   ```json
   { "action": "start" }
   ```

---

## 🛠 **6. Troubleshooting**

###  **Issue: `sample.log` Not Found**
- **Fix:** Ensure `sample.log` is in the `BE` folder.

###  **Issue: `ModuleNotFoundError`**
- **Fix:** Run:
   ```bash
   pip install flask transitions
   ```

---

## 🛠 **7. Stopping the Server**

To stop the server, press:
```
CTRL + C
```

---
