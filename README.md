# nolurk.: Prompt-Driven Urban Navigation

> "Standard maps tell you how to get there. nolurk. ensures nobody is waiting for you when you do."

**Author USN:** ENG24CS0562
**Core Innovation:** Bypassing traditional algorithmic safety scoring using a Prompt-Driven Architecture powered by Gemini 1.5 Pro.

---

## 1. Challenge Vertical Chosen
**Smart Urban Mobility & Personal Assistant**

## 2. Problem Solved (High Impact)
Urban commuters face unpredictable safety hazards at night. Standard routing apps optimize purely for time (utilizing shortest-path algorithms like Dijkstra's), which frequently leads users into isolated, unlit, or high-risk areas just to save a few minutes. 

**nolurk.** introduces **"Surgical Micro-Detouring"** to keep users on active, visible paths. 

## 3. Approach and Logic
Instead of relying on arbitrary, hardcoded numerical safety scores (e.g., "Route is 85% safe"), we completely rethought spatial reasoning. 

nolurk. utilizes a **Prompt-Driven Architecture**. We use Google's `gemini-1.5-pro` as an "Active Safety Auditor." By passing raw Google Maps route coordinates and local hazard bounding boxes to the LLM as spatial text context, the AI cross-references the data and outputs **Contextual Safety Tags** (e.g., "nolurk. Verified", "Clear Grid"). This gives the user agency and understandable context, rather than a robotic percentage score.

## 4. How the Solution Works
1. A lightweight Python (Flask) backend receives simulated Google Maps Route data and real-time hazard bounding boxes (`hazards.json`).
2. This data is aggregated and formatted into an optimal spatial context string.
3. The data is passed to the `google-generativeai` SDK using zero-shot prompt instructions.
4. Gemini processes the spatial constraints and returns strict, parseable JSON containing the safest route, its contextual tag, and a user-friendly UI notification.

## 5. Assumptions Made
* **Hardware/Sensors:** We assume the frontend application natively handles user geolocation via GPS.
* **Data Availability:** We assume the availability of a real-time hazard data feed (simulated via local JSON in this prototype).
* **User Psychology:** We assume the commuter prefers a minor ETA delay (e.g., +2 minutes) in exchange for a significantly safer, well-lit route.

## 6. Evaluation Focus Alignment

This project was built with strict adherence to the evaluation rubric:

* **Code Quality:** The Python backend is built with modular, single-responsibility functions and comprehensive docstrings outlining the logic flow.
* **Security:** Strict separation of environment variables. The Gemini API key is loaded securely via `python-dotenv`. **No keys are hardcoded or exposed.**
* **Efficiency (Algorithmic Reduction):** Complex spatial intersection algorithms (O(n²) complexity) are bypassed. By leveraging the LLM for complex spatial reasoning, backend compute overhead is kept near zero, making the application highly scalable.
* **Testing:** Implemented automated unit testing (`test_app.py`) using Python's native `unittest` framework to validate endpoint health and strict JSON schema adherence from the AI response.
* **Accessibility (Inclusive Design):** Standard safety apps rely heavily on Red/Yellow/Green map overlays, which are inaccessible to colorblind or visually impaired users. nolurk.'s text-based "Contextual Safety Tags" makes route safety **100% compatible with mobile screen readers**.
* **Google Services:** Deep, native integration of the Google Gemini API (`gemini-1.5-pro`) as the core logic routing engine.
