import time
import re
import os
import pandas as pd
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright

def linkedin_login(email, password):
    """Log in to LinkedIn and return the authenticated page, browser, and Playwright instance."""
    p = sync_playwright().start()
    # Run in headless mode.
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.linkedin.com/login", timeout=15000)
    
    page.fill("input[name='session_key']", email)
    page.fill("input[name='session_password']", password)
    page.click("button[type='submit']")
    
    # Wait for the search input which reliably indicates a successful login.
    try:
        page.wait_for_selector("input[aria-label='Search']", timeout=15000)
    except Exception as e:
        print("Login may have failed or page structure may have changed:", e)
    return page, browser, p

def scroll_page(page):
    """Scroll to the bottom to trigger lazy loading, then wait briefly."""
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1)  # Reduced sleep time

def get_total_jobs(page):
    """Extract the total number of jobs from the header."""
    try:
        total_elem = page.query_selector("span.results-context-header__job-count")
        if total_elem:
            text = total_elem.inner_text().strip()
            total_jobs = int(re.sub(r"[^\d]", "", text))
            print(f"Total jobs detected: {total_jobs}")
            return total_jobs
    except Exception as e:
        print("Could not extract total jobs count:", e)
    return None

# def extract_apply_redirect_link(page):
#     """Capture the redirected URL after clicking the Apply button using explicit waits."""
#     apply_redirect = "N/A"
#     apply_button = page.query_selector("button#jobs-apply-button-id")
#     if apply_button:
#         try:
#             with page.expect_popup(timeout=5000) as popup_info:
#                 apply_button.click()
#             new_page = popup_info.value
#             new_page.wait_for_load_state("load", timeout=5000)
#             apply_redirect = new_page.url
#             print(f"Captured apply URL from popup: {apply_redirect}")
#             new_page.close()
#             time.sleep(1)
#         except Exception as popup_error:
#             print("No popup detected, trying same-tab navigation...")
#             try:
#                 with page.expect_navigation(timeout=5000) as nav_info:
#                     apply_button.click()
#                 apply_redirect = nav_info.value.url
#                 print(f"Captured apply URL from same-tab navigation: {apply_redirect}")
#                 page.go_back()
#                 time.sleep(1)
#             except Exception as nav_error:
#                 print("Error capturing apply redirect URL:", nav_error)
#     return apply_redirect

def scrape_current_page_jobs(page, job_role):
    """
    For each job card on the current page, click it, wait for the details panel, and extract:
      - Title, company, link, apply redirect, and description.
    """
    jobs = []
    scroll_page(page)
    job_cards_locator = page.locator("ul.jobs-search__results-list li")
    count = job_cards_locator.count()
    print(f"Found {count} job cards on the current page.")
    
    for idx in range(count):
        card = job_cards_locator.nth(idx)
        try:
            card.click(timeout=5000)
        except Exception as e:
            print(f"Error clicking card {idx}: {e}")
            continue
        # Wait for a key element in the job details panel.
        try:
            page.wait_for_selector("div.show-more-less-html__markup", timeout=5000)
        except Exception:
            pass

        title_text = card.locator("h3").first.text_content().strip() if card.locator("h3").count() > 0 else "N/A"
        company_text = card.locator("h4").first.text_content().strip() if card.locator("h4").count() > 0 else "N/A"
        link = card.locator("a").first.get_attribute("href") if card.locator("a").count() > 0 else "N/A"
        apply_href = extract_apply_redirect_link(page)
        try:
            description_elem = page.wait_for_selector("div.show-more-less-html__markup", timeout=5000)
            description_text = description_elem.inner_text().strip() if description_elem else "N/A"
        except Exception:
            description_text = "N/A"
        
        jobs.append({
            "job_role": job_role,
            "title": title_text,
            "company": company_text,
            "link": link,
            "apply_href": apply_href,
            "description": description_text,
            "source": "LinkedIn"
        })
    return jobs

def scrape_linkedin_jobs_for_role(page, job_role):
    """Scrape jobs for a given role using pagination and return a list of job dictionaries."""
    jobs = []
    offset = 0
    page_size = 25
    base_url = (
        "https://www.linkedin.com/jobs/search/?f_E=2&f_TPR=r86400&geoId=103644278"
        "&keywords={}&origin=JOB_SEARCH_PAGE_LOCATION_AUTOCOMPLETE&refresh=true&start={}"
    )
    query = quote_plus(job_role)
    
    first_url = base_url.format(query, 0)
    print(f"Loading first page for '{job_role}': {first_url}")
    page.goto(first_url, timeout=15000)
    page.wait_for_load_state("domcontentloaded", timeout=15000)
    scroll_page(page)
    total_jobs = get_total_jobs(page)
    
    while total_jobs is None or offset < total_jobs:
        url = base_url.format(query, offset)
        print(f"Scraping '{job_role}' at offset {offset}: {url}")
        page.goto(url, timeout=15000)
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        scroll_page(page)
        
        job_cards = page.query_selector_all("ul.jobs-search__results-list li")
        if not job_cards:
            print("No job cards found, ending pagination.")
            break
        
        page_jobs = scrape_current_page_jobs(page, job_role)
        jobs.extend(page_jobs)
        
        if len(job_cards) < page_size:
            print("Fewer job cards than expected; assuming end of results.")
            break
        
        offset += page_size
        print(f"Increasing offset to {offset}.")
    return jobs

def scrape_all_roles_linkedin(email, password, job_roles):
    """Log in and scrape jobs for each specified job role."""
    page, browser, p = linkedin_login(email, password)
    all_jobs = []
    for role in job_roles:
        role_jobs = scrape_linkedin_jobs_for_role(page, role)
        all_jobs.extend(role_jobs)
    return all_jobs, browser, p

def append_new_jobs(new_jobs, csv_path):
    """Append new jobs to CSV based on unique job link."""
    new_df = pd.DataFrame(new_jobs)
    if os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path)
        combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=["link"], keep="last")
    else:
        combined_df = new_df
    combined_df.to_csv(csv_path, index=False)
    print(f"Updated CSV saved to {csv_path}")

if __name__ == "__main__":
    import os
    # Use secure storage for credentials in production.
    email = "gouthamsolleti3@gmail.com"
    password = "Hruday@000"  # Updated as per your test credentials.
    
    job_roles = ["Software Engineer", "Software Developer", "Backend Engineer"]
    csv_path = "linkedin_jobs.csv"
    
    while True:
        print("Starting new scraping iteration...")
        all_jobs, browser, p = scrape_all_roles_linkedin(email, password, job_roles)
        print(f"\nTotal jobs scraped in this iteration: {len(all_jobs)}\n")
        for job in all_jobs:
            print(job)
        
        append_new_jobs(all_jobs, csv_path)
        
        browser.close()
        p.stop()
        
        # Wait a shorter interval (e.g., 5 minutes) for faster iterations.
        wait_time = 5 * 60
        print(f"Sleeping for {wait_time/60} minutes before next iteration...")
        time.sleep(wait_time)
