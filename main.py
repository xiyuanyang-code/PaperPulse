import os
import json
from crawler.paper import HuggingFacePaperScraper
from crawler.gh_trending import GithubTrendingScraper
from datetime import datetime


def crawling():
    paper_scraper = HuggingFacePaperScraper()
    gh_scraper = GithubTrendingScraper()
    print("Start Scraping")

    try:
        print("Start Scraping for Papers")
        paper_scraper.run()
    except Exception as e:
        print(f"Error, {e} in Papers fetching, skipping")

    try:
        print("Start Scraping for Github Trendings")
        gh_scraper.run()
    except Exception as e:
        print(f"Error: {e} in Github Trendings, skipping")

    print("Finish Scraping")

def _get_ai_info():
    print("Calling AI")
    pass


def _finish_report():
    pass


def _send_mail():
    pass


def main():
    time_stamp = datetime.now().strftime("%Y%m%d")
    os.makedirs("./materials", exist_ok=True)
    file_path = os.path.abspath(f"./materials/{time_stamp}.json")
    with open(file_path, "w") as file:
        # create the new file
        json.dump({}, file)
        file.close()

    print("Email Preparation Start!")
    crawling()
    _get_ai_info()
    _finish_report()
    _send_mail()


if __name__ == "__main__":
    main()
