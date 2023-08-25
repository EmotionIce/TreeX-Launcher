import os
import requests
import datetime
from subprocess import call

# Variables for user setup
GITHUB_REPO_API = 'https://api.github.com/repos/EmotionIce/TreeX-Launcher/releases/latest'
DIRECTORY_PATH = os.path.dirname(os.path.abspath(__file__))

def fetch_latest_release_date():
    response = requests.get(GITHUB_REPO_API)
    response_data = response.json()
    return datetime.datetime.strptime(response_data['published_at'], '%Y-%m-%dT%H:%M:%SZ')

def find_and_remove_outdated_jars(latest_release_date):
    for item in os.listdir(DIRECTORY_PATH):
        item_path = os.path.join(DIRECTORY_PATH, item)
        if item.endswith('.jar'):
            item_modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(item_path))
            if item_modified_date < latest_release_date:
                print(f"Removing outdated JAR: {item}")
                os.remove(item_path)

def download_latest_jar(download_url):
    jar_name = download_url.split("/")[-1]
    save_path = os.path.join(DIRECTORY_PATH, jar_name)
    response = requests.get(download_url, stream=True)
    with open(save_path, 'wb') as out_file:
        for chunk in response.iter_content(chunk_size=8192):
            out_file.write(chunk)
    return save_path

def main():
    # Fetch the latest release date from GitHub
    latest_release_date = fetch_latest_release_date()

    # Remove outdated JARs in the directory
    find_and_remove_outdated_jars(latest_release_date)

    # Check if a JAR from the latest release already exists in the directory
    jar_present = False
    for item in os.listdir(DIRECTORY_PATH):
        if item.endswith('.jar'):
            item_path = os.path.join(DIRECTORY_PATH, item)
            item_modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(item_path))
            if item_modified_date == latest_release_date:
                jar_present = True
                break

    # If not present, download the latest JAR
    if not jar_present:
        response = requests.get(GITHUB_REPO_API)
        for asset in response.json().get('assets', []):
            if asset['name'].endswith('.jar'):
                jar_path = download_latest_jar(asset['browser_download_url'])
                print(f"Downloaded new JAR: {jar_path}")
                break

    # Launch the JAR (assuming there's only one JAR in the directory now)
    jar_to_launch = next((file for file in os.listdir(DIRECTORY_PATH) if file.endswith('.jar')), None)
    if jar_to_launch:
        call(['java', '-jar', os.path.join(DIRECTORY_PATH, jar_to_launch)])

if __name__ == "__main__":
    main()
