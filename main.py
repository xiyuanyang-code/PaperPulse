import os
import sys
import json

sys.path.append(os.getcwd())

from crawler.paper import HuggingFacePaperScraper
from crawler.gh_trending import GithubTrendingScraper
from mail.sender import EmailSender
from summary.ai import AISummarizer
from datetime import datetime

time_stamp = datetime.now().strftime("%Y%m%d")


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
    summary = AISummarizer()
    summary.run()
    print("Calling AI Ended")


def _finish_report():
    time_stamp = datetime.now().strftime("%Y%m%d")
    """generate the final readme.md file"""
    with open(f"./materials/{time_stamp}.json", encoding="utf-8") as file:
        data = json.load(file)
        body_text = data["L1 Summary"]
        file.close()

    # generate a markdown file
    with open(f"./materials/{time_stamp}.md", "w", encoding="utf-8") as file:
        file.write(f"# Welcome to {time_stamp} AI Report\n\n")
        file.write(f"{body_text}\n\n")
        file.write(f"## Introduction\n\n")
        summary = data["L2 Summary"]
        for content in summary:
            file.write(f"{content}\n\n\n")

        file.write(f"## Repo Trendings\n\n")
        data_gh = data["gh_trendings"]
        for content in data_gh:
            file.write(f"### Repo: {content["url"][19:]}\n\n")
            file.write(f"url: {content["url"]}\n\n")
            file.write(f"language: {content["language"]}\n\n")
            file.write(f"\n{content["description"]}\n\n\n")

        file.write(f"## Paper Trendings\n\n")
        data_paper = data["huggingface_papers"]
        for content in data_paper:
            file.write(f"### Paper: {content["Title"]}\n\n")
            file.write(f"url: {content["PDF_Link"]}\n\n")
            file.write(f"\n{content["Summary"]}\n\n\n")

        return body_text, f"./materials/{time_stamp}.md"


def _send_mail(body, path):
    mail_sender = EmailSender()
    with open("./summary/config.json") as file:
        email_list = json.load(file)
    for email in email_list:
        mail_sender.send_mail(
            email,
            subject=f"AI Trending {time_stamp}",
            body=body,
            attach_local_file_path=path,
        )


def main():

    os.makedirs("./materials", exist_ok=True)
    file_path = os.path.abspath(f"./materials/{time_stamp}.json")
    with open(file_path, "w") as file:
        # create the new file
        json.dump({}, file)
        file.close()

    print("Email Preparation Start!")
    crawling()
    _get_ai_info()
    body, path = _finish_report()
    _send_mail(body, path)


if __name__ == "__main__":
    main()
    # _finish_report()
