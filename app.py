import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from celery import Celery
from werkzeug.exceptions import BadRequest
import json
import redis

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure from environment variables
app.config["CELERY_BROKER_URL"] = os.getenv("CELERY_BROKER_URL")
app.config["CELERY_RESULT_BACKEND"] = os.getenv("CELERY_RESULT_BACKEND")

celery = Celery("tasks", broker=app.config["CELERY_BROKER_URL"])
celery.conf.update(app.config)

# Add Redis client initialization after celery configuration
redis_client = redis.from_url(app.config["CELERY_BROKER_URL"])


@app.route("/")
def index():
    """Serve the main page with the addition form."""
    return render_template("index.html")


@app.route("/tasks/history")
def get_task_history():
    """Get all tasks from Redis."""
    try:
        tasks = redis_client.lrange("task_history", 0, -1)
        return jsonify([json.loads(task) for task in tasks])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/add", methods=["POST"])
def add():
    """Submit a new addition task to the Celery queue.

    Expects a JSON payload with 'a' and 'b' numeric values.

    Returns:
        JSON response with task_id (202) on success
        JSON error response (400) for invalid input
        JSON error response (500) for server errors
    """
    try:
        data = request.get_json()
        if not data or "a" not in data or "b" not in data:
            raise BadRequest("Missing required parameters 'a' or 'b'")

        a = float(data["a"])
        b = float(data["b"])

        task = celery.send_task("tasks.add_together", args=[a, b])

        task_data = {
            "id": task.id,
            "a": a,
            "b": b,
            "operation": "add",
            "status": "PENDING",
            "result": None
        }
        redis_client.lpush("task_history", json.dumps(task_data))

        return jsonify({"task_id": task.id}), 202
    except (ValueError, TypeError) as e:
        return jsonify({"error": "Invalid input values"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/multiply", methods=["POST"])
def multiply():
    """Submit a new multiplication task to the Celery queue."""
    try:
        data = request.get_json()
        if not data or "a" not in data or "b" not in data:
            raise BadRequest("Missing required parameters 'a' or 'b'")

        a = float(data["a"])
        b = float(data["b"])

        task = celery.send_task("tasks.multiply_together", args=[a, b])

        task_data = {
            "id": task.id,
            "a": a,
            "b": b,
            "operation": "multiply",
            "status": "PENDING",
            "result": None
        }
        redis_client.lpush("task_history", json.dumps(task_data))

        return jsonify({"task_id": task.id}), 202
    except (ValueError, TypeError) as e:
        return jsonify({"error": "Invalid input values"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/result/<task_id>")
def task_result(task_id):
    """Retrieve the result of a previously submitted task."""
    try:
        # First check if task exists in history
        task_exists = False
        tasks = redis_client.lrange("task_history", 0, -1)
        for task_data in tasks:
            task_dict = json.loads(task_data)
            if task_dict["id"] == task_id:
                task_exists = True
                break
        
        if not task_exists:
            return jsonify({"error": "Task not found"}), 404

        task = celery.AsyncResult(task_id)
        
        # Update task status in Redis
        for i, task_data in enumerate(tasks):
            task_dict = json.loads(task_data)
            if task_dict["id"] == task_id:
                task_dict["status"] = task.state
                if task.state == "SUCCESS":
                    task_dict["result"] = task.result
                elif task.state == "FAILURE":
                    task_dict["result"] = str(task.info)
                redis_client.lset("task_history", i, json.dumps(task_dict))
                break

        if task.state == "PENDING":
            response = {"state": task.state, "status": "Pending..."}
        elif task.state == "FAILURE":
            response = {"state": task.state, "status": str(task.info)}
        else:
            response = {"state": task.state, "result": task.result}
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/tasks/delete/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Delete a task from history and revoke it if pending."""
    try:
        # First revoke the task in Celery
        task = celery.AsyncResult(task_id)
        task.revoke(terminate=True)  # terminate=True will kill the task if running

        # Then remove from Redis history
        tasks = redis_client.lrange("task_history", 0, -1)
        for i, task_data in enumerate(tasks):
            task_dict = json.loads(task_data)
            if task_dict["id"] == task_id:
                redis_client.lrem("task_history", 1, task_data)
                # Also clean up any result data
                redis_client.delete(f"celery-task-meta-{task_id}")
                return jsonify({"success": True}), 200
                
        return jsonify({"error": "Task not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Modified to explicitly bind to all interfaces
    app.run(host="0.0.0.0", port=5001, debug=True)
