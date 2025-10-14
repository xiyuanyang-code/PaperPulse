# Add two API modules: Bilibili-related video operations and automatic email sending assistant
import sys
import os
import json
import requests
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.getcwd())

from typing import List
from tqdm import tqdm
from utils.log import setup_logging_config


class EmailSender:
    def __init__(self, email_config_path: str):
        # get secret_id and api_key
        # for this class, we use GeekSeed for its efficiency
        self.email_config_path = email_config_path
        with open(self.email_config_path, "r", encoding="utf-8") as file:
            self.config_data = json.load(file)

        # get several config
        self.sender_mail = self._get_config("sender_mail")
        self.client_id = self._get_config("client_id")
        self.client_secret = self._get_config("client_secret")
        self.template_id = self._get_config("template_id")
        self.default_mail_lists = self._get_config("recipient email list")
        self.logger = setup_logging_config()
        self.token = self._get_access_token()

    def _get_config(self, config_name: str):
        return self.config_data[config_name]

    def _get_access_token(self):
        params = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        res = requests.post("https://open.geeksend.com/oauth/access_token", data=params)
        token = res.json()["data"]["access_token"]
        return token

    def send(
        self,
        mail_lists: List[str] = None,
        subject: str = "PaperPulse: Your Daily Latest Paper Acquisition Assistant",
        body: str = "Maybe something is wrong? Contact the author: yangxiyuan@sjtu.edu.cn",
    ):
        if mail_lists is None:
            # get default settings
            mail_lists = self.default_mail_lists

        if not isinstance(mail_lists, list):
            mail_lists = [mail_lists]
        all_response = []
        mail_length = len(mail_lists)

        # wrap with html
        body_new = body
        body_new = body_new.replace("\n", "<br>")
        body_new = "<p>" + body_new + "</p>"
        

        for mail in tqdm(mail_lists, total=mail_length):
            headers = {"Authorization": f"Bearer {self.token}"}
            params = {
                "emails": [mail],
                "prospect_id": 0,
                "template_id": self.template_id,
                "subject": subject,
                "content": body_new,
                "sender": self.sender_mail,
                "reply_email": self.sender_mail,
            }
            # sleeping for one seconds
            time.sleep(1)
            res = requests.post(
                "https://open.geeksend.com/send/email", headers=headers, data=params
            ).json()
            all_response.append(res)

        print(f"Result: {json.dumps(all_response,indent=2,ensure_ascii=False)}")
