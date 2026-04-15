"""
nolurk. — AI-Powered Urban Safety Auditor
Flask Backend | Hackathon Build
"""

import os
import json
import re
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

load_dotenv()  # Pull GEMINI_API_KEY (and any other vars) from .env

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Safely configure Gemini client — crash early if the key is missing
_API_KEY = os.getenv("GEMINI_API_KEY")
if not _API_KEY:
    raise EnvironmentError(
        "GEMINI_API_KEY is not set. Add it to your .env file before starting the server."
    )

genai.configure(api_key=_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# Path to the mock data file (same directory as this script)
MOCK_DATA_PATH = os.path.join(os.path.dirname(__file__), "mock_data.json")


# ---------------------------------------------------------------------------
# Helper – load mock data
# ---------------------------------------------------------------------------

def load_mock_data() -> dict:
    """Read and return the contents of mock_data.json."""
    with open(MOCK_DATA_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Helper – build the Gemini prompt
# ---------------------------------------------------------------------------

def build_prompt(routes: list, hazards: list) -> str:
    """
    Assemble a plain-text prompt that injects the route + hazard data
    exactly where Gemini expects it.
    """
    data_block = json.dumps({"routes": routes, "hazards": hazards}, indent=2)

    prompt = f"""You are an AI Safety Auditor for the app 'nolurk.'. \
Here are 3 potential walking routes and local hazard zones:

{data_block}

Analyze them. Do NOT use numerical scores. \
Assign each route an aggressive, Gen-Z style safety tag \
(e.g., "nolurk. Verified", "Clear Grid", "Sketchy"). \
Return ONLY a valid JSON array matching this format:

[{{"route_id": "route_1", "tag": "nolurk. Verified", \
"reason": "Swerve the unlit alley. Sticking to main roads.", \
"is_recommended": true, "commuter_id": "ENG24CS0562"}}]"""

    return prompt


# ---------------------------------------------------------------------------
# Helper – extract JSON from Gemini's reply
# ---------------------------------------------------------------------------

def extract_json_array(text: str) -> list:
    """
    Gemini sometimes wraps its JSON in markdown fences.
    Strip those fences and parse the raw array.
    """
    # Remove ```json ... ``` or ``` ... ``` wrappers if present
    cleaned = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    return json.loads(cleaned)


# ---------------------------------------------------------------------------
# Endpoint – POST /evaluate_routes
# ---------------------------------------------------------------------------

@app.route("/evaluate_routes", methods=["POST"])
def evaluate_routes():
    """
    Main endpoint.

    Workflow:
      1. Load mock routes + hazards from mock_data.json
      2. Build the Gemini prompt
      3. Call Gemini 1.5 Pro
      4. Parse + return the JSON response

    Returns:
        200  – JSON array of route evaluations
        500  – Error details (safe for dev; tighten for prod)
    """
    try:
        # Step 1 — load data
        mock_data = load_mock_data()
        routes    = mock_data["routes"]
        hazards   = mock_data["hazards"]

        logger.info("Loaded %d routes and %d hazards.", len(routes), len(hazards))

        # Step 2 — build prompt
        prompt = build_prompt(routes, hazards)
        logger.info("Prompt assembled. Sending to Gemini…")

        # Step 3 — call Gemini
        response = model.generate_content(prompt)
        raw_text = response.text
        logger.info("Gemini response received (%d chars).", len(raw_text))

        # Step 4 — parse and return
        evaluations = extract_json_array(raw_text)

        return jsonify(evaluations), 200

    except FileNotFoundError:
        logger.error("mock_data.json not found at path: %s", MOCK_DATA_PATH)
        return jsonify({
            "status": "error",
            "message": "mock_data.json is missing. Ensure it sits in the project root."
        }), 500

    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Gemini response as JSON: %s", exc)
        return jsonify({
            "status": "error",
            "message": "Gemini returned a non-JSON response. Check logs.",
            "raw_response": response.text if "response" in dir() else "N/A"
        }), 500

    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error in /evaluate_routes: %s", exc)
        return jsonify({
            "status": "error",
            "message": str(exc)
        }), 500


# ---------------------------------------------------------------------------
# Health-check – GET /
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def health_check():
    """Simple liveness probe so the judges can confirm the server is up."""
    return jsonify({
        "app": "nolurk.",
        "status": "online",
        "tagline": "No lurk. No risk. Just the right route."
    }), 200


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # debug=False for any demo/prod run; flip to True locally for hot-reload
    app.run(host="0.0.0.0", port=5000, debug=False)
