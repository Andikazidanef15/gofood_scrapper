import logging
import argparse
import pandas as pd
import os
from datetime import datetime
from concurrent_log_handler import ConcurrentRotatingFileHandler

from src.scrapper import GofoodScrapper
from src.utils import upsert

#setup logging to file
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] - %(name)s - %(levelname)s - %(message)s',
    datefmt='%d %B %Y %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        ConcurrentRotatingFileHandler(
            filename='./logs/GofoodScrapper.log',
            mode='a',
            maxBytes=20 * 1024 * 1024,
            backupCount=3
        )
    ],
)
parser = argparse.ArgumentParser(description='Gofood scrapper for retrieving restaurant and menu information')
parser.add_argument("--get_restaurants", "-gr", type=str, default='', help='Link to get restaurant list')
parser.add_argument("--get_menu_detail", "-gmd", action="store_true", help="Get menu detail from scrapped restaurant metadata")

args = parser.parse_args()

def main():
    logger = logging.getLogger("Main")
    logger.info('*'*45 + ' START ' + '*'*45)

    start_main = datetime.now()
    exit_status = 0

    try:
        resto_link = args.get_restaurants
        get_menu_detail = args.get_menu_detail

        # Initiate scrapper
        scrapper = GofoodScrapper()

        if resto_link != '':
            # Get restaurant metadata
            restaurant_metadata = scrapper.get_restaurant_metadata(resto_link)

            # Save restaurant metadata
            upsert('data/restaurant_metadata.csv', restaurant_metadata, ['name'])

            # Quit browser session
            logger.info('Web scraping completed, quitting the current session')
            scrapper.quit_browser()
        
        if get_menu_detail:
            # Load restaurant metadata
            restaurant_metadata = pd.read_csv('data/restaurant_metadata.csv')

            # Check if menu metadata exist
            if os.path.exists('data/menu_metadata.csv'):
                # Load menu metadata
                menu_metadata = pd.read_csv('data/menu_metadata.csv')

                # Get all unique restaurant id
                unique_resto_id = menu_metadata['resto_id'].unique().tolist()

                # Filter all restaurant ID that do not exist on the menu metadata
                restaurant_metadata = restaurant_metadata[~restaurant_metadata['id'].isin(unique_resto_id)]

            # Generate mapping from ID to link
            id_to_link = dict(zip(restaurant_metadata['id'], restaurant_metadata['link']))

            # Loop every ID
            for id in restaurant_metadata['id']:
                # Get menu metadata
                result = scrapper.get_menu_metadata(resto_id = id, id_to_link = id_to_link)

                # Save menu metadata
                upsert('data/menu_metadata.csv', result, ['resto_id', 'menu_name'])

            # Quit browser session
            logger.info('Web scraping completed, quitting the current session')
            scrapper.quit_browser()
    
    except BaseException as e:
        exit_status = 1
        logger.exception(e)
        raise e
    finally:
        end_main = datetime.now()
        logger.info(f'Exited after {end_main - start_main} with status {exit_status}')
        logger.info('*'*45 + ' FINISH ' + '*'*45)

if __name__ == '__main__':
    main()