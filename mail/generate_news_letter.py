import json
import os
from datetime import date
from tqdm import tqdm


class NewsLetterGenerator:
    def __init__(
        self,
        time_stamp: str,
        template_file_path: str = "./mail/email_template.html",
        output_dir: str = "./materials",
    ):
        # several configs
        self.time_stamp = time_stamp
        self.template_file_path = template_file_path
        self.output_dir = output_dir
        self.global_config = {
            "PaperPulse: Your Daily Latest Paper Acquisition Assistant": f"PaperPulse for {self.time_stamp}: Your Daily Latest Paper Acquisition Assistant",
            "📅 Date: XXXX-XX-XX": f"📅 Date: {self.time_stamp}",
        }

        # write and create some files
        os.makedirs(self.output_dir, exist_ok=True)
        if not os.path.exists(self.template_file_path):
            print(
                f"Error! The template mailing file path: {self.template_file_path} doesn't exists."
            )

    def generate_article_html(self):
        try:
            with open(self.template_file_path, "r", encoding="utf-8") as f:
                template_content = f.read()
        except FileNotFoundError as e:
            print(f"Error, could not found file: {e}")
            return

        html_insert_content = ""
        target_json_file = os.path.join(self.output_dir, f"{self.time_stamp}.json")
        with open(target_json_file, "r", encoding="utf-8") as file:
            file_data = json.load(file)
            paper_data = file_data["huggingface_papers"]
            l2_summary_data = file_data["L2 Summary"]
            l1_summary_data = file_data["L1 Summary"]

        length_of_data = len(paper_data)
        for index, paper_info in tqdm(enumerate(paper_data), total=length_of_data):
            html_insert_content += self.simple_format(
                title=paper_info["Title"],
                abstract_en=paper_info["Summary"],
                summary_cn=l2_summary_data[index],
                link=paper_info["PDF_Link"],
            )

        final_html = template_content
        for key, value in self.global_config.items():
            final_html = final_html.replace(key, value)
            
        # replace tldr
        final_html = final_html.replace("[GLOBAL_TLDR_SUMMARY]", l1_summary_data)

        START_MARKER = "<!-- START: 论文解读块模板 - Python脚本将填充此位置 -->"
        END_MARKER = "<!-- END: 论文解读块模板 -->"

        try:
            start_index = final_html.find(START_MARKER)
            end_index = final_html.find(END_MARKER) + len(END_MARKER)

            if start_index != -1 and end_index != -1:
                final_html = (
                    final_html[:start_index]
                    + html_insert_content
                    + final_html[end_index:]
                )
            else:
                final_html = final_html.replace(
                    "<!-- INSERT_ARTICLES_HERE -->", html_insert_content
                )

        except Exception as e:
            print(f"Error while replacing articles: {e}")
            return

        try:
            save_path = os.path.join(self.output_dir, f"{self.time_stamp}.html")
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(final_html)
        except Exception as e:
            print(f"Error: {e}")

    def simple_format(self, title: str, abstract_en: str, summary_cn: str, link: str):
        article_block_template = """
                            <!-- START: ARTICLE BLOCK -->
                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; margin-bottom: 25px; border: 1px solid #93c5fd; border-radius: 6px;">
                                <tr>
                                    <td style="padding: 20px 20px; background-color: #eff6ff;">
                                        <!-- 论文标题 (深蓝) -->
                                        <h2 style="margin: 0 0 15px 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 22px; color: #1e3a8a; font-weight: 700; line-height: 30px;">
                                            {title}
                                        </h2>

                                        <!-- 英文摘要 -->
                                        <h3 style="margin: 0 0 5px 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 16px; color: #3b82f6; font-weight: 600;">
                                            English Abstract:
                                        </h3>
                                        <p style="margin: 0 0 15px 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 16px; color: #475569; line-height: 24px;">
                                            {abstract_en}
                                        </p>
                                        
                                        <!-- 中文简略概括 -->
                                        <h3 style="margin: 0 0 5px 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 16px; color: #3b82f6; font-weight: 600;">
                                            中文简析:
                                        </h3>
                                        <p style="margin: 0 0 20px 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 16px; color: #475569; line-height: 24px;">
                                            {summary_cn}
                                        </p>

                                        <!-- 链接按钮 (居中) -->
                                        <table border="0" cellpadding="0" cellspacing="0" align="center" style="margin: auto;">
                                            <tr>
                                                <td align="center" style="border-radius: 4px;" bgcolor="#3b82f6">
                                                    <a href="{link}" target="_blank" style="font-size: 15px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #ffffff; text-decoration: none; border-radius: 4px; padding: 10px 20px; border: 1px solid #3b82f6; display: inline-block; font-weight: 600;">
                                                        阅读完整解读 &rarr;
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            <!-- END: ARTICLE BLOCK -->
                            """
        return article_block_template.format(
            title=title,
            abstract_en=abstract_en,
            summary_cn=summary_cn,
            link=link,
        )


if __name__ == "__main__":
    generator = NewsLetterGenerator(time_stamp="20251014")
    generator.generate_article_html()
