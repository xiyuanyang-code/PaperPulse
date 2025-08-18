import json
import os
import re

from datetime import datetime
from openai import OpenAI


class AISummarizer:
    """
    A class to read data from a JSON file and generate summaries using the Anthropic API.
    """

    def __init__(self):
        """
        Initializes the class and authenticates the Anthropic client.

        :param data_file_path: The path to the JSON file.
        """
        self.time = datetime.now().strftime("%Y%m%d")
        self.data_file_path = os.path.join("./materials", (self.time + ".json"))
        self.client = OpenAI(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            base_url=os.environ.get("BASE_URL"),
        )
        if not self.client.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. Please set your key first."
            )

    def _load_data(self):
        """
        Loads JSON data from the specified path.
        """
        if not os.path.exists(self.data_file_path):
            raise FileNotFoundError(f"File not found: {self.data_file_path}")

        try:
            with open(self.data_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise ValueError("File content is not a valid JSON format.")

    def _get_summary_from_anthropic(self, text, length_limit=400):
        """
        Generates a text summary using the Anthropic API.

        :param text: The original text to be summarized.
        :param length_limit: The maximum number of words for the summary.
        :return: The generated summary string.
        """
        # Clean up Markdown and HTML tags
        clean_text = re.sub(r"</?p.*?>|\n{2,}", "\n", text)
        clean_text = re.sub(r"<[^>]*>", "", clean_text)

        # Define system prompt
        system_prompt = "You are a professional content summarization robot. Please summarize the text provided by the user in Chinese."

        # Build user prompt
        user_prompt = f"Please summarize the following content in Chinese, with the number of words limited to {length_limit} words:\n\n---\n\n{clean_text}, you only need to output the final answer.输出的最终结果不允许包含任何的markdown的小标题标记，包括加粗等，全部以自然段的形式呈现"

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model="gpt-4o-mini",
                max_tokens=2000,
                temperature=0.15,
            )
            answer = response.choices[0].message.content
            return answer
        
        except Exception as e:
            print(f"Failed to call API: {e}")
            return "Summary generation failed."

    def generate_full_report(self):
        """
        Generates a complete summary report, including papers and projects.
        """
        data = self._load_data()
        papers = data.get("huggingface_papers", [])
        repos = data.get("gh_trendings", [])

        reports = []

        # Summarize papers
        for paper in papers:
            title = paper.get("Title", "Untitled").strip()
            summary_text = paper.get("Summary", "No summary information.")
            summary = self._get_summary_from_anthropic(summary_text)
            reports.append(f"{title}\n\n{summary}")

        # Summarize GitHub projects
        for repo in repos:
            repo_url = repo.get("url", "No URL").strip()
            # Summarize combining description and README information
            full_text = f"Project Description: {repo.get('description', '')}\n\nREADME Summary: {repo.get('readme_summary', '')}"
            summary = self._get_summary_from_anthropic(full_text)
            reports.append(f"{repo_url}\n\n{summary}")

        self.final_report = reports

    def generate_L1_report(self):
        L2_text = "\n\n".join(self.final_report)
        # Define system prompt
        system_prompt = "You are a professional content summarization robot. Please summarize the text provided by the user in Chinese."

        # Build user prompt
        user_prompt = f"加下来我会提供一些paper和Github 仓库的摘要，摘要是{L2_text}。请你完成根据内容生成精简版的总结，每一个paper或者仓库只允许用1~2句话概括核心,你只需要输出最终的生成结果, 你输出的最终结果不允许包含任何的markdown的小标题标记，包括加粗等"

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model="gpt-4o-mini",
                max_tokens=2000,
                temperature=0.15,
            )
            self.L1_summary = response.choices[0].message.content
        except Exception as e:
            print(f"Failed to call Anthropic API: {e}")
            return "Summary generation failed."

    def save_L2_summary(self):
        with open(self.data_file_path, "r") as file:
            data = json.load(file)
            data["L2 Summary"] = self.final_report
            file.close()

        with open(self.data_file_path, "w") as file:
            json.dump(data, file, indent=4, ensure_ascii=False, sort_keys=True)

    def save_L1_summary(self):
        with open(self.data_file_path, "r") as file:
            data = json.load(file)
            data["L1 Summary"] = self.L1_summary
            file.close()

        with open(self.data_file_path, "w") as file:
            json.dump(data, file, indent=4, ensure_ascii=False, sort_keys=True)

    def run(self):
        try:
            self.generate_full_report()
            self.save_L2_summary()
            self.generate_L1_report()
            self.save_L1_summary()
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    test = AISummarizer()
    test.run()
