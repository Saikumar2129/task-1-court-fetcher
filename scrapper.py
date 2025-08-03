import base64
from playwright.async_api import async_playwright, TimeoutError

# Note: These selectors are specific to the eCourts website layout as of Aug 2025.
# They are the most likely part of the code to break if the site is redesigned.
# Using more robust selectors (like data-testid if available) is always preferred.
CAPTCHA_IMAGE_SELECTOR = '#captcha_image'
CASE_TYPE_SELECTOR = '#case_type'
CASE_NUMBER_SELECTOR = '#search_case_no'
CASE_YEAR_SELECTOR = '#search_year'
CAPTCHA_INPUT_SELECTOR = '#captcha'
SUBMIT_BUTTON_SELECTOR = 'button[id="search-btn"][type="submit"]'
RESULT_TABLE_SELECTOR = '#showList'
ERROR_MESSAGE_SELECTOR = '.bg-danger' # A common class for error banners

async def get_initial_captcha_and_state():
    """
    Launches a browser, navigates to the court page, and captures the CAPTCHA.
    Returns the CAPTCHA image as a Base64 string and the page object for reuse.
    """
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch()
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    page = await context.new_page()
    
    try:
        await page.goto("https://services.ecourts.gov.in/ecourtindia/cases/case_no.php", timeout=30000)
        
        # Select the correct court
        await page.select_option('#sess_state_code', '6') # Haryana
        await page.wait_for_timeout(500) # Wait for district list to populate
        await page.select_option('#sess_dist_code', '10') # Faridabad
        await page.wait_for_timeout(500)
        await page.select_option('#court_code', '1') # District and Sessions Court
        await page.click('button[name="submit_court"]')
        await page.wait_for_load_state('networkidle')

        # Get CAPTCHA
        captcha_element = await page.wait_for_selector(CAPTCHA_IMAGE_SELECTOR, timeout=15000)
        captcha_screenshot = await captcha_element.screenshot()
        captcha_base64 = base64.b64encode(captcha_screenshot).decode('utf-8')
        
        return {
            "captcha_image": captcha_base64,
            "page": page,
            "browser": browser,
            "error": None
        }

    except TimeoutError:
        await browser.close()
        return {"error": "Failed to load the eCourts page or find the CAPTCHA. The site may be down."}
    except Exception as e:
        await browser.close()
        return {"error": f"An unexpected error occurred: {str(e)}"}

async def submit_form_and_scrape(page, browser, case_type, case_number, year, captcha_text):
    """
    Fills the form with the provided data and scrapes the results.
    """
    try:
        await page.select_option(CASE_TYPE_SELECTOR, value=case_type)
        await page.fill(CASE_NUMBER_SELECTOR, case_number)
        await page.select_option(CASE_YEAR_SELECTOR, value=year)
        await page.fill(CAPTCHA_INPUT_SELECTOR, captcha_text)
        
        await page.click(SUBMIT_BUTTON_SELECTOR)

        # Wait for either the results table or an error message
        await page.wait_for_selector(f"{RESULT_TABLE_SELECTOR}, {ERROR_MESSAGE_SELECTOR}", timeout=20000)

        # Check for invalid CAPTCHA or case not found errors
        error_element = await page.query_selector(ERROR_MESSAGE_SELECTOR)
        if error_element:
            error_text = await error_element.inner_text()
            return {"error": f"Site error: {error_text.strip()}"}

        # If we reached here, results should be visible
        result_table = await page.wait_for_selector(RESULT_TABLE_SELECTOR)
        
        # Click the "View" button to see details
        view_button = await result_table.query_selector('a.some-class-for-view-button') # NOTE: This selector needs to be identified from the real page
        if not view_button: # Fallback if direct view isn't there
             view_button = await result_table.query_selector('tbody tr:first-child td:last-child a')
        
        await view_button.click()
        await page.wait_for_load_state('networkidle')

        # Now on the details page, parse the required info
        parties = await page.locator("//div[contains(., 'Petitioner and Advocate')]").inner_text()
        filing_date = await page.locator("//div[contains(., 'Filing Date')]//span").inner_text()
        next_hearing_date = await page.locator("//div[contains(., 'Next Hearing Date')]//span").inner_text()

        # Get order links
        order_rows = await page.locator("//table[contains(., 'Orders')]//tbody/tr").all()
        pdf_links = []
        for row in order_rows:
            link_element = await row.query_selector('a[href$=".pdf"]')
            if link_element:
                date = await row.locator('td').nth(1).inner_text()
                link = await link_element.get_attribute('href')
                pdf_links.append({"date": date, "url": link})

        return {
            "parties": parties,
            "filing_date": filing_date,
            "next_hearing_date": next_hearing_date,
            "pdf_links": pdf_links[:5] # Show latest 5
        }

    except TimeoutError:
        return {"error": "Form submission timed out. The website might be slow or the details are incorrect."}
    except Exception as e:
        return {"error": f"An error occurred during scraping: {str(e)}"}
    finally:
        await browser.close()
