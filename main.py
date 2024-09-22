import requests
import os
from bs4 import BeautifulSoup
import pandas as pd
from dotenv import load_dotenv

# Loading the environment in the env file
load_dotenv()
JOB_API_KEY = os.getenv('JOB_API_KEY')  # Getting the API key from the env file

def fetch_jobs(job_title):
    # Using the jobs API to fetch the jobs, positions and locations when user inputs the job titles
    url = 'https://data.usajobs.gov/api/Search'
    headers = {
        'Authorization-Key': JOB_API_KEY,
        'User-Agent': 'Assignment3 (elyaziaabbas@hotmail.com)'
    }
    params = {
        'Keyword': job_title,
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:  # Checking if the status code is 200 which means it's successful
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

def filter_relevant_jobs(job_title, all_jobs):
    # This function will give us only the relevant jobs from the entire list of jobs
    relevant_jobs = []
    for job in all_jobs['SearchResult']['SearchResultItems']:  # Iterating over all the job listings
        position_title = job['MatchedObjectDescriptor']['PositionTitle'].lower()
        if job_title.lower() in position_title:  # Checking if the title is part of the position
            relevant_jobs.append(job)  # Appending only the relevant jobs
    return relevant_jobs

def scrape_h3_titles(url):
    # Scraping the h3 titles, which are the safest states to work in
    try:
        response = requests.get(url)  # Sending the GET request to get the URL
        if response.status_code != 200:
            print(f"Failed to get the webpage: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')  # Parsing the HTML with BeautifulSoup
        h3_titles = []  # Collecting all the h3 titles and appending them in a list
        for h3 in soup.find_all('h3'):
            h3_titles.append(h3.text.strip())
        return h3_titles
    except Exception as e:  # Exception handling
        print(f"An error has occurred: {e}")
        return []

def find_jobs(h3_states):
    # This final list will store relevant information related to each job (position, organization, city, state, safe_state)
    final_list = []

    while True:  # Continuously asking the user for input until we get a valid input
        job_title = input("Enter the job title you are looking for: ")
        all_jobs = fetch_jobs(job_title)

        if all_jobs:  # Checking if the fetch was successful
            relevant_jobs = filter_relevant_jobs(job_title, all_jobs)
            if not relevant_jobs:  # If the job is not one of the titles we fetched from the API
                print("Job not found. Please try again.")
            else:
                found_states = []  # List for the relevant jobs only

                for job in relevant_jobs:  # Iterating over the relevant jobs only
                    position_title = job['MatchedObjectDescriptor']['PositionTitle']  # Extracting the position title, organization name, and location
                    organization = job['MatchedObjectDescriptor']['OrganizationName']
                    location = job['MatchedObjectDescriptor']['PositionLocationDisplay']

                    # Part of data cleaning: split location into city and state
                    location_parts = location.split(", ")
                    city = location_parts[0]
                    state = location_parts[1] if len(location_parts) > 1 else "Unknown"  # In case the state was not mentioned, use "Unknown"

                    is_safe = "No"  # By default, set is_safe to "No"
                    for safest_state in h3_states:
                        if safest_state.lower() in location.lower():  # Check if the job's location matches any of the safest states
                            found_states.append(safest_state)
                            is_safe = "Yes"  # Switch is_safe to "Yes" once a match is found
                            break  # Once found, break to avoid redundant checks

                    # Create a dictionary to store the job information
                    job_info = {
                        'Position Title': position_title,
                        'Organization': organization,
                        'City': city,
                        'State': state,
                        'Safe State': is_safe
                    }

                    # Appending the job information to the final list
                    final_list.append(job_info)

                # Creating the DataFrame from the final list
                df_jobs = pd.DataFrame(final_list)

                # Renaming the DataFrame columns to ensure capital first letter and no dashes
                df_jobs.columns = df_jobs.columns.str.replace('_', ' ').str.title()

                # Handle missing values
                df_jobs = df_jobs.apply(lambda col: col.fillna(0) if col.dtype in ['int64', 'float64'] else col.fillna('Unknown'))

                # Reorder columns to keep 'Position Title' as the first column
                cols = ['Position Title'] + [col for col in df_jobs.columns if col != 'Position Title']
                df_jobs = df_jobs[cols]

                # Check the DataFrame format before saving
                print(df_jobs.head(5))  # Displaying the first few rows in terminal for debugging

                # Save to CSV
                safest_job = "safest_states_jobs"
                df_jobs.to_csv(f'{safest_job}_job_listings.csv', index=False)

                print("CSV file has been saved.")
                break  # Exit the loop once CSV is saved
        else:
            print("Error retrieving jobs. Please try again.")

def main():
    # URL for scraping the safest states to work in
    url = "https://www.mpamag.com/us/mortgage-industry/guides/which-are-the-safest-states-in-the-us/315091"
    h3_states = scrape_h3_titles(url)

    # Start job search and CSV creation process
    find_jobs(h3_states)

if __name__ == "__main__":
    main()
