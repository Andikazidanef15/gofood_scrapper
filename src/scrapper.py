import pandas as pd
import time
import uuid
import logging
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class GofoodScrapper:
    def __init__(self):
        # Create logger
        self.logger = logging.getLogger(__name__)
        self.logger.info('Initiate Webdriver')

        # Configure Chrome options to use the proxy server
        chrome_options = Options()

        # Add headless option
        chrome_options.add_argument("--headless")

        # Path to your ChromeDriver
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def page_scrolling(self, scroll_pause_time:int=1, add_index:float=0.5):
        self.logger.info('Scroll page')
        scroll_pause_time = scroll_pause_time
        screen_height = self.driver.execute_script("return window.screen.height;")   # get the screen height of the web
        i = 1

        while True:
            # scroll one screen height each time
            executed = False
            while executed == False:
                try:
                    self.driver.execute_script("window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))  
                    i += add_index
                    time.sleep(scroll_pause_time)
                    # update scroll height each time after scrolled, as the scroll height can change after we scrolled the page
                    scroll_height = self.driver.execute_script("return document.body.scrollHeight;")  
                    executed = True
                except:
                    time.sleep(0.5)
            # Break the loop when the height we need to scroll to is larger than the total scroll height
            if (screen_height) * i > scroll_height:
                break
    
    def get_restaurant_metadata(self, link:str):
        self.logger.info('Get all restaurant listed in current browser')
        # Go to the link
        self.driver.get(link)

        # Do page scrolling
        self.page_scrolling()

        # Refresh page
        self.driver.get(link)

        # Do page scrolling
        self.page_scrolling()

        # Get all restaurant info
        restaurant_boxes = self.driver.find_elements(by = By.XPATH, value = '//*[@id="__next"]/div/div[3]/div[1]/a')

        # Create metadata
        restaurant_metadata = {
            'id':[],
            'name':[],
            'category':[],
            'price_level':[],
            'link':[]
        }

        # Loop
        for box in restaurant_boxes:
            # Get new ID
            restaurant_metadata['id'].append(str(uuid.uuid4()))

            # Get restaurant name
            name = box.find_element(by = By.XPATH, value = 'div/div[2]/p[1]').text
            restaurant_metadata['name'].append(name)

            # Get restaurant category
            categories = box.find_element(by = By.XPATH, value = 'div/div[2]/p[2]').text
            restaurant_metadata['category'].append(categories)

            # Get price level
            price_level = len(box.find_elements(By.CLASS_NAME, 'text-gf-content-primary')) - 1
            restaurant_metadata['price_level'].append(price_level)

            # Get link
            link = box.get_attribute('href')
            restaurant_metadata['link'].append(link)
        
        # Convert to pandas dataframe
        restaurant_metadata = pd.DataFrame(restaurant_metadata)

        return restaurant_metadata

    def get_menu_metadata(self, resto_id:str, id_to_link:dict):
        self.logger.info(f'Get menu metadata from {resto_id}')
        # Get link
        resto_link = id_to_link[resto_id]

        # Go to the link
        self.driver.get(resto_link)

        # Scroll page
        self.page_scrolling(scroll_pause_time=1, add_index=0.7)

        # Get all section
        sections = self.driver.find_elements(by = By.XPATH, value = "//div[contains(@id, 'section-')]")

        # Remove section-0 since this is recommendation section
        section_0 = self.driver.find_elements(by = By.XPATH, value = "//div[@id='section--0']")
        if section_0 != []:
            sections.remove(section_0[0])

        # Create menu metadata
        menu_metadata = {
            'id':[],
            'resto_id':[],
            'section':[],
            'menu_name':[],
            'menu_detail':[],
            'price':[]
        }

        # Loop
        for section in sections:
            # Get section
            section_name = section.find_element(by = By.XPATH, value = "h2").text

            # Get menu list
            menus = section.find_elements(by = By.XPATH, value = "div/div")

            # Loop every menu
            for menu in menus:
                # Append restaurant ID
                menu_metadata['id'].append(str(uuid.uuid4()))
                menu_metadata['resto_id'].append(resto_id)

                # Append section name to the metadata
                menu_metadata['section'].append(section_name)

                # Get menuname
                menuname = menu.find_element(by = By.XPATH, value = 'div/div[1]/div[1]/h3').text
                menu_metadata['menu_name'].append(menuname)

                # Get menudetail
                try:
                    menudetail = menu.find_element(by = By.XPATH, value = 'div/div[1]/div[1]/p').text
                    menu_metadata['menu_detail'].append(menudetail)
                except:
                    menu_metadata['menu_detail'].append('')

                # Get price
                try:
                    price = menu.find_element(by = By.XPATH, value = 'div/div[1]/div[1]/div').text
                    price = int(price.replace('.',''))
                except:
                    # There must be a change in the price layout,
                    # This happen when the menu is on Promo, 
                    # Collect the original menu price
                    price = menu.find_element(by = By.XPATH, value = 'div/div[1]/div[1]/div/div[1]/span[2]').text
                    price = int(price.replace('.',''))

                menu_metadata['price'].append(price)
        
        # Return menu_metadata
        menu_metadata = pd.DataFrame(menu_metadata)

        return menu_metadata
    
    def quit_browser(self):
        self.driver.quit()