import requests
import json
import arxiv
import sys
import os
sys.path.append(os.getcwd())

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from utils.log import setup_logging_config


class LinkConverter:
    """
    Converts Hugging Face paper links to arXiv links.
    """

    @staticmethod
    def to_arxiv(hf_link: str) -> str:
        """
        Converts a Hugging Face paper link to a standard arXiv link.

        Args:
            hf_link (str): The Hugging Face paper link (e.g., https://hf-mirror.com/papers/2508.11630).

        Returns:
            str: The corresponding arXiv link (e.g., https://arxiv.org/abs/2508.11630).
        """
        # The arXiv ID is at the end of the URL path
        arxiv_id = hf_link.split("/")[-1]
        return f"https://arxiv.org/abs/{arxiv_id}"


class ArxivScraper:
    """
    Scrapes paper information from arXiv using the official API.
    """

    def get_paper_details(self, arxiv_id: str) -> dict:
        """
        Fetches the summary and PDF link for a given arXiv paper ID.

        Args:
            arxiv_id (str): The arXiv paper ID (e.g., '2508.06429').

        Returns:
            dict: A dictionary containing the summary and PDF link, or N/A.
        """
        self.logger = setup_logging_config()
        try:
            client = arxiv.Client()
            search = arxiv.Search(id_list=[arxiv_id], max_results=1)
            results = list(client.results(search))

            if results:
                paper = results[0]
                print(paper.summary)
                return {"Summary": paper.summary, "PDF_Link": paper.pdf_url}
            else:
                return {"Summary": "N/A", "PDF_Link": "N/A"}

        except Exception as e:
            print(f"Error Getting arxiv: {e}")
            return {"Summary": "N/A", "PDF_Link": "N/A"}


class HuggingFacePaperScraper:
    """
    A scraper for fetching daily trending paper information from Hugging Face.

    This class handles the entire scraping process for a specific date, including
    fetching the HTML content, parsing the data, and saving it to a CSV file.
    It also supports using a mirror site for faster access.
    """

    # ! using mirror website
    HF_MIRROR_URL = "https://hf-mirror.com"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def __init__(self, date_str: str = None):
        """
        Initializes the scraper with a specific date and mirror URL.

        Args:
            date_str (str): The date string in 'YYYY-MM-DD' format.
        """
        self.date_str = (
            (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d") if date_str is None else date_str
        )
        # Combine the mirror URL with the relative path to the papers page
        self.url = f"{self.HF_MIRROR_URL}/papers/date/{self.date_str}"
        print(f"HuggingFace Page URL:{self.url}")
        self.link_convert = LinkConverter()
        self.arxiv_scraper = ArxivScraper()
        self.logger = setup_logging_config()

    def _fetch_page_content(self) -> str | None:
        """
        Fetches the HTML content of the target URL.

        Returns:
            str | None: The HTML content as a string, or None if the request failed.
        """
        print("Fetching Page content.")
        try:
            response = requests.get(self.url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def _parse_papers(self, html_content: str) -> list[dict]:
        """
        Parses the HTML content to extract paper details.

        Args:
            html_content (str): The HTML content of the page.

        Returns:
            list[dict]: A list of dictionaries, where each dictionary
                        represents a paper with its title and link.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        papers_list = []
        
        papers_containers = soup.find_all("h3", class_="mb-1 text-lg/6 font-semibold hover:underline peer-hover:underline 2xl:text-[1.2rem]/6")

        if not papers_containers:
            print("Error, no paper message")
            return papers_list
        
        print("Getting Paper messages")
        arxiv_scraper = ArxivScraper()
        print(f"Paper numbers: {len(papers_containers)}")
        for container in papers_containers:
            try:
                title_link_tag = container.find("a")
                title = title_link_tag.get_text(strip=True).replace("\n", "")
                print(title)
                # Ensure the link uses the mirror URL
                relative_link = title_link_tag['href']
                hf_link = f"{self.HF_MIRROR_URL}{relative_link}"
                
                # Convert the Hugging Face link to an arXiv link
                arxiv_link = LinkConverter.to_arxiv(hf_link)
                print(arxiv_link)
                # Extract arXiv ID
                arxiv_id = arxiv_link.split('/')[-1]

                # Fetch details from arXiv API
                arxiv_details = arxiv_scraper.get_paper_details(arxiv_id)

                papers_list.append({
                    "Title": str(title).replace("\n", ""),
                    "HF_Link": hf_link,
                    "Arxiv_Link": arxiv_link,
                    "Summary": str(arxiv_details["Summary"]).replace("\n", ""),
                    "PDF_Link": arxiv_details["PDF_Link"]
                })
            except Exception as e:
                print(f"Error: {e}")
                continue

        return papers_list

    def _save(self, new_data: list[dict]):
        """
        Saves the parsed data to a json file.

        Args:
            data (list[dict]): The list of paper data.
        """
        self.date_str = (datetime.now()).strftime("%Y%m%d")
        if not new_data:
            print("No data")
            return
        try:
            with open(f"materials/{self.date_str}.json", "r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not read existing JSON file. Error: {e}")
            data = {}

        data["huggingface_papers"] = new_data

        try:
            with open(f"materials/{self.date_str}.json", "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
                print(f"Successfully writing files into {self.date_str}.json")
        except Exception as e:
            print(f"An error occurred while saving the file: {e}")

    def run(self):
        """
        Runs the full scraping process.
        """
        html_content = self._fetch_page_content()
        if html_content:
            print('Success! Parsing papers...')
            papers = self._parse_papers(html_content)
            self._save(papers)
        else:
            print("Error: html content is none.")


if __name__ == "__main__":
    scraper = HuggingFacePaperScraper()
    scraper.run()
