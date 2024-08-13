#PLAYWRIGHT FUNCTIONS
from playwright.async_api import Playwright


async def initialize(playwright: Playwright):
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()
    return browser, page

async def close(browser):
    await browser.close()

async def login(page, email, password):
    await page.goto("https://www.youtube.com/")
    await page.get_by_label("Reject the use of cookies and").click()
    await page.get_by_role("link", name="Sign in").first.click()
    await page.get_by_label("Email or phone").click()
    await page.get_by_label("Email or phone").fill(email)
    await page.get_by_role("button", name="Next").click()
    await page.get_by_label("Enter your password").click()
    await page.get_by_label("Enter your password").fill(password)
    await page.get_by_role("button", name="Next").click()
    await page.get_by_text("Shorts Shorts").click()

async def like_video(page):
    await page.get_by_label("like this video along with").last.click()

async def dislike_video(page):
    await page.get_by_label("Dislike this video").last.click()

async def next_video(page):
    await page.get_by_label("Next video").click()

async def share_video(page):
    await page.locator("ytd-button-renderer").filter(has_text="Share Share").locator("span").last.click()
    await page.get_by_label("Copy", exact=True).click()
    await page.locator("ytd-unified-share-panel-renderer").get_by_label("Cancel").click()


async def previous_video(page):
    await page.get_by_label("Previous video").click()

async def get_video_url_id(page):
    url = await page.evaluate("window.location.href")
    video_id = url.split('/shorts/')[-1]
    return url, video_id

async def is_video_ad(page):
    element = await page.query_selector("reels-ad-card-buttoned-view-model")
    # check if the element is visible
    if not element:
        return False
    return await element.is_visible()