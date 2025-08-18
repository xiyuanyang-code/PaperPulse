import requests
import json
import time
import os

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from github import Github

class GithubTrendingScraper:
    """
    A scraper class to fetch trending repositories from GitHub
    and save their details, including README content, to a JSON file.
    """
    def __init__(self, token=None):
        """
        Initializes the scraper with a GitHub instance.
        :param token: A GitHub Personal Access Token for higher API rate limits.
        """
        self.github_instance = Github(token)
        self.output_dir = "materials"
        self.trending_url = "https://github.com/trending"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _get_repo_details(self, repo_fullname):
        """
        Fetches the README content for a single repository using PyGithub.
        :param repo_fullname: The full name of the repository, e.g., "octocat/Spoon-Knife".
        :return: The README text content or an error message.
        """
        try:
            # Use the PyGithub instance to get the repository object
            repo = self.github_instance.get_repo(repo_fullname)
            
            # Get the README file content
            try:
                # get_readme() returns a ContentFile object
                readme_contents = repo.get_readme()
                # The decoded_content attribute holds the content, which needs to be decoded
                readme_text = readme_contents.decoded_content.decode('utf-8')
            except Exception:
                readme_text = "README not found."
                print(f"WARNING: {readme_text}")
                
            return readme_text
        except Exception as e:
            return f"An error occurred while fetching README: {e}"

    def _get_trending_repos(self):
        """
        Scrapes the top 10 trending repositories from GitHub's trending page.
        :return: A list of dictionaries with repository details, or None on failure.
        """
        try:
            response = requests.get(self.trending_url, headers=self.headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                repo_list = soup.find_all('article', class_='Box-row')
                
                trending_repos = []
                # Scrape only the top 10 repositories
                for repo in repo_list[:10]:
                    title_tag = repo.find('h2').find('a')
                    repo_path = title_tag['href'] if title_tag else None
                    
                    # Extract description
                    description_tag = repo.find('p')
                    description = description_tag.get_text(strip=True) if description_tag else 'No description provided.'
                    
                    # Extract language
                    language_tag = repo.find('span', itemprop='programmingLanguage')
                    language = language_tag.get_text(strip=True) if language_tag else 'Unknown'
                    
                    if repo_path:
                        # Get the full repository name, e.g., "octocat/Spoon-Knife"
                        repo_fullname = repo_path.strip('/')
                        
                        print(f"Fetching details for {repo_fullname}...")
                        # Call the method to get README content
                        readme_content = self._get_repo_details(repo_fullname)
                        
                        repo_info = {
                            'url': f"https://github.com/{repo_fullname}",
                            'language': language,
                            'description': description,
                            'readme_summary': readme_content
                        }
                        trending_repos.append(repo_info)
                        
                        time.sleep(1) # Pause to avoid triggering rate limits
                
                return trending_repos
            else:
                print(f"Failed to retrieve trending page. Status code: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None

    def _save_to_json(self, data):
        """
        Saves the data to a JSON file with a timestamp, handling existing content.
        :param data: The list of repository data to be saved.
        """
        # Create the materials directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Generate the filename with the current date
        timestamp = (datetime.now()).strftime('%Y%m%d')
        filename = os.path.join(self.output_dir, f"{timestamp}.json")
        
        # Load existing data if the file exists, otherwise start with an empty dictionary
        output_data = {}
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    output_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Warning: Could not read existing JSON file. Creating a new one. Error: {e}")
                output_data = {}
        
        # Update the specific key and save the entire object
        output_data['gh_trendings'] = data
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=4)
            print(f"Successfully saved data to {filename}")
        except Exception as e:
            print(f"An error occurred while saving the file: {e}")

    def run(self):
        """
        Executes the full scraping process.
        """
        repos = self._get_trending_repos()
        if repos:
            self._save_to_json(repos)
        else:
            print("No repositories found or an error occurred. Skipping file save.")

if __name__ == "__main__":
    #! required
    GH_TOKEN = os.getenv("GITHUB_TOKEN")
    scraper = GithubTrendingScraper(GH_TOKEN)
    scraper.run()
