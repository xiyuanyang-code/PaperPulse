import json
import os
import re
from datetime import datetime
from openai import OpenAI

# Define prompts as global variables at the beginning of the file.
# The variable names are in English, but the content is in Chinese.
L2_SUMMARIZATION_PROMPT = """你是一个专业的内容总结机器人。请根据用户提供的文本，使用中文进行总结。"""
L2_USER_PROMPT_TEMPLATE = """请使用中文总结以下内容，字数限制在 {length_limit} 字以内，并且仅输出最终结果。输出内容不允许包含任何Markdown小标题、加粗等标记，请以自然段形式呈现，并且要保证行文的逻辑性是顺畅的，不可以只是做翻译，每一个自然段的内容不要太短也不要太长。\n\n---\n\n{text}"""

L1_SUMMARIZATION_PROMPT = """你是一个专业的内容总结机器人。请根据用户提供的文本，使用中文进行总结。"""
L1_USER_PROMPT_TEMPLATE = """接下来我会提供一些paper和GitHub仓库的摘要，摘要内容为：\n\n{text}\n\n请你根据这些摘要，生成一个精简版的总结。要求每个paper或仓库包含：仓库的名称或者Paper的名称，并且在这之后用3到4句话凝练地概括其核心内容。你只需要输出最终的生成结果，并且该结果必须是一个Markdown无序列表，只允许有一层缩进，每个列表元素代表一个paper或仓库的介绍。输出中不允许包含任何Markdown小标题或加粗等标记。"""

class AISummarizer:
    """
    A class to read data from a JSON file and generate summaries using the OpenAI API.
    """

    def __init__(self):
        """
        Initializes the class and authenticates the OpenAI client.
        """
        self.time = datetime.now().strftime("%Y%m%d")
        self.data_file_path = os.path.join("./materials", (self.time + ".json"))
        self.client = OpenAI(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            base_url=os.environ.get("ANTHROPIC_BASE_URL"),
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
        Generates a text summary using the OpenAI API.

        :param text: The original text to be summarized.
        :param length_limit: The maximum number of words for the summary.
        :return: The generated summary string.
        """
        # Clean up Markdown and HTML tags
        clean_text = re.sub(r"</?p.*?>|\n{2,}", "\n", text)
        clean_text = re.sub(r"<[^>]*>", "", clean_text)

        # Build user prompt using the template
        user_prompt = L2_USER_PROMPT_TEMPLATE.format(
            length_limit=length_limit, text=clean_text
        )

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": L2_SUMMARIZATION_PROMPT},
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
        """
        Generates a concise, high-level summary (L1 report).
        """
        L2_text = "\n\n".join(self.final_report)
        user_prompt = L1_USER_PROMPT_TEMPLATE.format(text=L2_text)

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": L1_SUMMARIZATION_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                model="gpt-4o-mini",
                max_tokens=2000,
                temperature=0.15,
            )
            self.L1_summary = response.choices[0].message.content
        except Exception as e:
            print(f"Failed to call OpenAI API: {e}")
            self.L1_summary = "Summary generation failed."

    def save_L2_summary(self):
        """
        Saves the L2 summary to the JSON file.
        """
        with open(self.data_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        data["L2 Summary"] = self.final_report

        with open(self.data_file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def save_L1_summary(self):
        """
        Saves the L1 summary to the JSON file.
        """
        with open(self.data_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        data["L1 Summary"] = self.L1_summary

        with open(self.data_file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def run(self):
        """
        Main execution function to load data, generate, and save summaries.
        """
        try:
            self.generate_full_report()
            self.save_L2_summary()
            self.generate_L1_report()
            self.save_L1_summary()
        except FileNotFoundError as e:
            print(f"Error: {e}. Please ensure the JSON data file exists.")
        except ValueError as e:
            print(f"Error: {e}. Please check the format of the JSON file.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    test = AISummarizer()
    test.run()