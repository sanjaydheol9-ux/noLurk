"""
nolurk. — AI-Powered Urban Safety Auditor
Flask Backend | Hackathon Build
"""

import os
import json
import re
import logging
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq

# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

load_dotenv()  # Pull GEMINI_API_KEY (and any other vars) from .env

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Safely configure Groq client — crash early if the key is missing
_API_KEY = os.getenv("GROQ_API_KEY")
if not _API_KEY:
    raise EnvironmentError(
        "GROQ_API_KEY is not set. Add it to your .env file before starting the server."
    )

client = Groq(api_key=_API_KEY)

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
    for the AI safety auditor.
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
# Helper – extract JSON from API response
# ---------------------------------------------------------------------------

def extract_json_array(text: str) -> list:
    """
    Extract JSON array from API response.
    Sometimes the response wraps JSON in markdown fences.
    Strip those fences and parse the raw array.
    """
    # Remove ```json ... ``` or ``` ... ``` wrappers if present
    cleaned = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    return json.loads(cleaned)


# ---------------------------------------------------------------------------
# Helper – generate mock evaluations (fallback when API quota exceeded)
# ---------------------------------------------------------------------------

def generate_mock_evaluations(routes: list) -> list:
    """
    Generate mock route evaluations for demo/fallback purposes.
    Returns realistic safety tags based on route properties.
    """
    evaluations = []
    
    for route in routes:
        is_safe = not route.get("passes_through_hazards", [])
        lighting = route.get("lighting", "").lower()
        
        # Logic: safe if no hazards AND good lighting
        if is_safe and ("good" in lighting or "well" in lighting):
            tag = "nolurk. Verified"
            reason = "All main roads, fully lit, busy foot traffic. This is the move."
            recommended = True
        elif route.get("passes_through_hazards", []):
            tag = "Sketchy"
            reason = "Hazard zones detected. Swerve it."
            recommended = False
        else:
            tag = "Clear Grid"
            reason = "Moderate safety. Acceptable route with minor cautions."
            recommended = True
        
        evaluations.append({
            "route_id": route.get("route_id", "unknown"),
            "tag": tag,
            "reason": reason,
            "is_recommended": recommended,
            "commuter_id": "ENG24CS0562"
        })
    
    return evaluations


# ---------------------------------------------------------------------------
# Endpoint – POST /evaluate_routes
# ---------------------------------------------------------------------------

@app.route("/evaluate_routes", methods=["POST"])
def evaluate_routes():
    """
    Main endpoint.

    Workflow:
      1. Load mock routes + hazards from mock_data.json
      2. Build the prompt
      3. Call Groq API (mixtral-8x7b)
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
        logger.info("Prompt assembled. Sending to Groq…")

        # Step 3 — call Groq (with fallback on quota exceeded)
        try:
            response = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1024
            )
            raw_text = response.choices[0].message.content
            logger.info("Groq response received (%d chars).", len(raw_text))

            # Step 4 — parse and return
            evaluations = extract_json_array(raw_text)
        except Exception as api_err:
            logger.warning("Groq API failed (%s). Using mock evaluations as fallback.", str(api_err)[:100])
            # Fallback to mock evaluations
            evaluations = generate_mock_evaluations(routes)

        return jsonify({
            "status": "success",
            "evaluations": evaluations
        }), 200

    except FileNotFoundError:
        logger.error("mock_data.json not found at path: %s", MOCK_DATA_PATH)
        return jsonify({
            "status": "error",
            "message": "mock_data.json is missing. Ensure it sits in the project root."
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
def serve_frontend():
    """Serve the index.html frontend."""
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    return send_file(html_path, mimetype="text/html")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for verification."""
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
