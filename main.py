import collections
import csv
import re
import time
from selenium import webdriver
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from definitions import CHROME_DRIVER_PATH
from operator import itemgetter

main_url = 'https://globalepidemics.org/key-metrics-for-covid-suppression/'
Row = collections.namedtuple('row', 'county state cases level')


def create_chrome_driver(headless=False):
    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument('--headless')

    driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=chrome_options)
    driver.set_window_size(1920, 1080)
    return driver


def click_element(driver, element):
    driver.execute_script("arguments[0].click();", element)


def scroll_to_element(driver, element):
    driver.execute_script("arguments[0].scrollIntoView(true);", element)


def find_elements_with_regex(driver: WebDriver, css_selector: str, regex: re):
    elements = []
    for element in driver.find_elements_by_css_selector(css_selector):
        if element.text and regex.search(element.text):
            print("Match: " + element.text)
            elements.append(element)
    return elements


def write_rows_to_csv(rows: [Row]):
    with open('results.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow('County State Cases Level'.split())
        for row in rows:
            print(str(row))
            writer.writerow([row.county, row.state, row.cases, row.level])


def run():

    print("Initializing WebDriver")

    driver = create_chrome_driver()
    driver.get(main_url)
    time.sleep(10)

    iframe = driver.find_element_by_css_selector('iframe')
    scroll_to_element(driver, iframe)  # Data within iframe
    driver.switch_to.frame(iframe)

    tabular_button = driver.find_element_by_xpath("//*[contains(text(), 'Tabular')]")
    click_element(driver, tabular_button)
    time.sleep(10)  # Wait for Tabular data to load

    scroll_bar = driver.find_elements_by_css_selector('div[class="scroll-bar-part-bar"]')[1]

    parsed_counties = set()
    rows = []

    while True:

        try:
            body = driver.find_element_by_css_selector("div[class='bodyCells']")
            # Get columns for counties, cases & levels
            counties = body.find_element_by_xpath('div/div[1]/div[2]').find_elements_by_css_selector('div[title]')
            cases = body.find_element_by_xpath('div/div[1]/div[4]').find_elements_by_css_selector('div[title]')
            levels = body.find_element_by_xpath('div/div[1]/div[5]').find_elements_by_css_selector('div[title]')

            if scroll_bar.location['y'] == 580:
                print("Appending extra columns...")
                counties.extend(body.find_element_by_xpath('div/div[2]/div[2]').find_elements_by_css_selector('div[title]'))
                cases.extend(body.find_element_by_xpath('div/div[2]/div[4]').find_elements_by_css_selector('div[title]'))
                levels.extend(body.find_element_by_xpath('div/div[2]/div[5]').find_elements_by_css_selector('div[title]'))

            counties = reversed(counties)
            cases = reversed(cases)
            levels = reversed(levels)

            for e in zip(counties, cases, levels):
                county = e[0].text

                if county in parsed_counties and scroll_bar.location['y'] != 580:
                    break   # Reading from the bottom of the page

                if county not in parsed_counties:
                    print(f'Appended: {e[0].text} {e[1].text} {e[2].text}')

                    parsed_counties.add(county)
                    split_county = county.split(",")
                    county, state = split_county[0].strip(), split_county[1].strip()

                    cases = 0.0

                    try:
                        cases = float(e[1].text)
                    except ValueError:
                        pass

                    level = e[2].text
                    rows.append(Row(county, state, cases, level))

            if scroll_bar.location['y'] == 580:
                break

            actionChains = ActionChains(driver)
            actionChains.click_and_hold(scroll_bar) # .perform()
            actionChains.move_by_offset(0, 2.5)  # .perform()
            actionChains.release()
            actionChains.perform()

        except MoveTargetOutOfBoundsException:
            continue

    print("Exporting results")
    rows.sort(key=itemgetter(1, 2))
    write_rows_to_csv(rows)
    print("Execution complete")


if __name__ == '__main__':
    run()





