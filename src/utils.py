import os
import pandas as pd

def upsert(file_path:str, current_df:pd.DataFrame, primary_key_list:list):
    if os.path.exists(file_path):
        # Read past metadata
        past_metadata = pd.read_csv(file_path)

        # Combine with house_metadata_df
        df = pd.concat([past_metadata, current_df], axis=0, ignore_index=True)

        # Drop duplicates on primary key
        df = df.drop_duplicates(subset = primary_key_list)

        # Save data
        df.to_csv(file_path, index=False)
    else:
        current_df.to_csv(file_path, index = False)