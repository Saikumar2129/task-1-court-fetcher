import os
import asyncio
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

from scraper import get_initial_captcha_and_state, submit_form_and_scrape
from database import init_app, log_query, get_db

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Initialize database functions with the app
init_app(app)

# Store Playwright state globally (simple approach for this app)
# A more robust app would use a proper session/task management system
playwright_state = {}

@app.route('/', methods=['GET', 'POST'])
async def index():
    if request.method == 'POST':
        # User is submitting the form
        case_type = request.form.get('case_type')
        case_number = request.form.get('case_number')
        year = request.form.get('year')
        captcha_text = request.form.get('captcha')

        query_params = {
            "case_type": case_type,
            "case_number": case_number,
            "year": year
        }

        page_id = session.get('page_id')
        if not page_id or page_id not in playwright_state:
            return render_template('index.html', error="Your session expired. Please refresh the page.", case_types=get_case_types())

        state = playwright_state.pop(page_id) # Consume the state
        page = state['page']
        browser = state['browser']

        data = await submit_form_and_scrape(page, browser, case_type, case_number, year, captcha_text)

        with app.app_context():
            if 'error' in data:
                log_query(query_params, 'ERROR', None, data['error'])
                # Get a new CAPTCHA for retry
                new_captcha_data = await get_new_captcha()
                return render_template('index.html', error=data['error'], **new_captcha_data, **request.form, case_types=get_case_types())
            else:
                log_query(query_params, 'SUCCESS', data)
                return render_template('results.html', data=data)

    # For GET request
    captcha_data = await get_new_captcha()
    if 'error' in captcha_data:
        return render_template('index.html', error=captcha_data['error'], case_types=get_case_types())
        
    return render_template('index.html', **captcha_data, case_types=get_case_types())

async def get_new_captcha():
    """Helper to fetch a new CAPTCHA and store state."""
    # Clean up old states to prevent memory leaks
    for key, val in list(playwright_state.items()):
        if key != session.get('page_id'):
            await val['browser'].close()
            playwright_state.pop(key)

    state = await get_initial_captcha_and_state()
    if state.get("error"):
        return {"error": state["error"]}

    page_id = os.urandom(8).hex()
    session['page_id'] = page_id
    playwright_state[page_id] = {
        "page": state["page"],
        "browser": state["browser"]
    }
    return {"captcha_image": state["captcha_image"], "error": None}

def get_case_types():
    # In a real app, this might also be scraped or come from a config
    return [
        {"value": "1", "name": "C.C. - CRIMINAL CASES"},
        {"value": "2", "name": "C.M.A. - CIVIL MISC. APPEAL"},
        # Add more case types as needed
    ]

@app.teardown_app_request
async def teardown_request(exception=None):
    # This ensures any dangling browser instances are closed if an error occurs mid-request
    page_id = session.get('page_id')
    if page_id in playwright_state:
        state = playwright_state.pop(page_id)
        await state['browser'].close()
