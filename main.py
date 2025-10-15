import os
import sys
import json
import dotenv
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime

sys.path.append(os.getcwd())

from crawler.paper import HuggingFacePaperScraper
from crawler.gh_trending import GithubTrendingScraper
from mail.sender_new import EmailSender
from mail.generate_news_letter import NewsLetterGenerator
from summary.ai import AISummarizer

EMAIL_CONFIG_PATH = "./mail/config.json"
dotenv.load_dotenv()


class AIReporter:
    """
    A class to automate the process of crawling, summarizing, and reporting
    on AI papers and GitHub trends.
    """

    def __init__(self, time_stamp: str = None):
        """
        Initializes the AIReporter with necessary scraper and sender objects.
        """
        self.time_stamp = (
            datetime.now().strftime("%Y%m%d") if time_stamp is None else time_stamp
        )
        self.materials_dir = "./materials"
        self.json_file_path = os.path.join(
            self.materials_dir, f"{self.time_stamp}.json"
        )
        self.markdown_file_path = os.path.join(
            self.materials_dir, f"{self.time_stamp}.md"
        )
        self.html_file_path = os.path.join(
            self.materials_dir, f"{self.time_stamp}.html"
        )

        # Initialize the tools used for the report generation
        self.paper_scraper = HuggingFacePaperScraper()
        self.gh_scraper = GithubTrendingScraper()
        self.ai_summarizer = AISummarizer()
        self.news_generator = NewsLetterGenerator(time_stamp=self.time_stamp)
        self.mail_sender = EmailSender(email_config_path=EMAIL_CONFIG_PATH)

        self.report_data = None
        self.report_body = None

    def _crawling(self):
        """
        Scrapes data from Hugging Face for papers and GitHub for trending repositories.
        """
        print("Start Scraping")

        try:
            print("Start Scraping for Papers.")
            self.paper_scraper.run()
        except Exception as e:
            print(f"Error: {e} in Papers fetching, skipping")

        print("Start Scraping for Github Trendings.")
        # Setting a timeout of 10 minutes (600 seconds) for the GitHub scraper
        TIMEOUT_SECONDS = 600
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.gh_scraper.run)
                future.result(timeout=TIMEOUT_SECONDS)
                print("Github Trendings scraping finished successfully.")
        except TimeoutError:
            print(f"Time out after {TIMEOUT_SECONDS} seconds. Skipping this task.")
        except Exception as e:
            print(f"Error: {e} in Github Trendings, skipping")

        print("Finish Scraping")

    def _get_ai_info(self):
        """
        Calls the AI summarizer to process the scraped data.
        """
        print("Calling AI")
        self.ai_summarizer.run()
        print("Calling AI Ended")

    def _finish_report(self):
        """
        Generates the final markdown report from the JSON data.
        """
        print("Generating report files")
        # Load the data from the JSON file created by the summarizer
        try:
            with open(self.json_file_path, "r", encoding="utf-8") as file:
                self.report_data = json.load(file)
        except FileNotFoundError:
            print(f"Error: JSON file not found at {self.json_file_path}")
            return False

        self.report_body = self.report_data["L1 Summary"]

        # Generate the markdown file
        with open(self.markdown_file_path, "w", encoding="utf-8") as file:
            file.write(f"# Welcome to {self.time_stamp} AI Report\n\n")
            file.write(f"{self.report_body}\n\n")
            file.write("## Introduction\n\n")

            summary = self.report_data.get("L2 Summary", [])
            for content in summary:
                file.write(f"{content}\n\n\n")

            file.write("## Repo Trendings\n\n")
            data_gh = self.report_data.get("gh_trendings", [])
            for content in data_gh:
                file.write(f"### Repo: {content.get('url', '')[19:]}\n\n")
                file.write(f"url: {content.get('url', '')}\n\n")
                file.write(f"language: {content.get('language', 'N/A')}\n\n")
                file.write(f"\n{content.get('description', '')}\n\n\n")

            file.write("## Paper Trendings\n\n")
            data_paper = self.report_data.get("huggingface_papers", [])
            for content in data_paper:
                file.write(f"### Paper: {content.get('Title', 'N/A')}\n\n")
                file.write(f"url: {content.get('PDF_Link', '')}\n\n")
                file.write(f"\n{content.get('Summary', '')}\n\n\n")

        # generate html file
        self.news_generator.generate_article_html()
        print("Report files generated successfully.")
        return True

    def _send_mail(self):
        """
        Sends the final report as an email with the markdown file as an attachment.
        """
        # Load the recipient list from the config file
        try:
            with open(EMAIL_CONFIG_PATH, "r") as file:
                email_list = (json.load(file)).get("recipient email list")
        except FileNotFoundError:
            print("Error: Email config file not found.")
            return

        with open(self.html_file_path, "r", encoding="utf-8") as file:
            send_body = file.read()

        send_body = send_body.replace("\n", "<div>")

        self.mail_sender.send(
            email_list,
            subject=f"PaperPulse for {self.time_stamp}: Your Daily Latest Paper Acquisition Assistant",
            body=send_body,
        )

    def run_report(self):
        """
        The main method to run the entire report generation process.
        """
        os.makedirs(self.materials_dir, exist_ok=True)

        if not os.path.exists(
            os.path.join(self.materials_dir, f"{self.time_stamp}.json")
        ):
            with open(self.json_file_path, "w") as file:
                json.dump({}, file)

            self._crawling()
            self._get_ai_info()

        if self._finish_report():
            print("Sending mail...")
            self._send_mail()
            print("Email Sending Done!")
        else:
            print("Report generation failed, skipping email step.")


if __name__ == "__main__":
    reporter = AIReporter(time_stamp="20251014")
    reporter.run_report()
