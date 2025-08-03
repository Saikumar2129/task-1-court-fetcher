# Task 1: Court-Data Fetcher & Mini-Dashboard

This is a simple Flask web application that allows a user to choose a Case Type, Case Number, and Filing Year for the Faridabad District Court, then fetches and displays the case metadata and latest orders/judgments.

## Court Chosen
- **Faridabad District Court** on the eCourts portal (`httpsis://districts.ecourts.gov.in/faridabad`).
- This choice was made because the eCourts platform is standardized across many districts, making the scraping logic potentially more reusable than a bespoke High Court website.

## Technology Stack
- **Backend:** Python / Flask
- **Scraping Engine:** Playwright
- **Database:** SQLite
- **Frontend:** HTML / CSS / Vanilla JavaScript

## Setup & Running the Application

1.  **Clone the repository.**

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows
    # venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright's browser binaries:**
    ```bash
    playwright install
    ```

5.  **Create a `.env` file** from the `.env.sample`. No changes are needed for the default setup.

6.  **Initialize the database:**
    ```bash
    # Run this command once from your terminal in the project directory
    flask shell
    >>> from database import init_db
    >>> init_db()
    >>> exit()
    ```
    This will create a `queries.db` file.

7.  **Run the Flask application:**
    ```bash
    flask run
    ```
    The application will be available at `http://127.0.0.1:5000`.

## CAPTCHA Handling Strategy

This app uses a **"User-in-the-Loop"** approach to handle the CAPTCHA legally and without external services.

1.  The backend uses Playwright to navigate to the eCourts site and take a screenshot of the CAPTCHA image.
2.  This image is sent to the frontend and displayed to the user.
3.  The user solves the CAPTCHA by typing the text into a field in our app's UI.
4.  This user-provided text is sent back with the case details and used by Playwright to submit the form on the eCourts website.

This method is robust, free, and leverages human intelligence to bypass the anti-bot measure.

## License
This project is licensed under the Apache License 2.0. See the `LICENSE` file for details.
