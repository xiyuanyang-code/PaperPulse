# Add two API modules: Bilibili-related video operations and automatic email sending assistant
import sys
import smtplib
import os
import json
import subprocess
import mimetypes

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.getcwd())

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email_validator import validate_email, EmailNotValidError
from typing import Optional, List, Tuple
from pathlib import Path
from utils.log import setup_logging_config


logger = setup_logging_config()

CONFIG_PATH = "./config.json"


def get_config_block(config_path, config_name: str) -> dict:
    with open(config_path, "r", encoding="utf8") as file:
        data = json.load(file)
    for block in data:
        if block.get("config_name") == config_name:
            return block
    raise ValueError(f"Config block with config_name '{config_name}' not found.")


# feat: add adb pull command for pulling files into local for email.
def pull_file_from_android(
    device_file_path: str = "/sdcard/DCIM/Camera/",
    local_destination_dir: Path | str | None = None,
) -> Path | None:
    """
    Use the ADB pull command to pull files from an Android device to local.

    Args:
        device_file_path (str): Full path of the file on the Android device (e.g. /sdcard/Documents/my_file.txt).
        local_destination_dir (Path | str | None): Target directory to store the file on the local computer.
                                                   If None, defaults to 'api_task/log/android_file' under the current working directory.

    Returns:
        Path | None: If successful, returns the full Path object of the pulled local file; otherwise returns None.
    """
    # Handle default value and type for local_destination_dir
    if local_destination_dir is None:
        local_destination_dir = Path.cwd() / "api_task" / "log" / "android_file"
    elif isinstance(local_destination_dir, str):
        local_destination_dir = Path(local_destination_dir)

    try:
        os.makedirs(local_destination_dir, exist_ok=True)
        logger.info(f"Created local destination directory: {local_destination_dir}")
    except OSError as e:
        logger.error(
            f"Failed to create local destination directory {local_destination_dir}: {e}"
        )
        return None

    file_name = Path(device_file_path).name
    pulled_local_path = local_destination_dir / file_name  # Compose the full local path

    # Build the ADB pull command
    # Note: If the target path of adb pull is a directory, it will create a file with the same name in that directory
    command = [
        "adb",
        "pull",
        device_file_path,
        str(local_destination_dir),
    ]  # Convert Path object to string for subprocess
    logger.info(f"Attempting to pull file: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            check=True,  # Raises CalledProcessError if the command returns a non-zero exit code
            capture_output=True,  # Capture stdout and stderr
            text=True,  # Decode output as text
        )

        # Verify if the file was actually pulled to local
        if pulled_local_path.exists():
            logger.info(
                f"Successfully pulled {device_file_path} to {pulled_local_path}"
            )
            logger.debug(f"ADB stdout: {result.stdout.strip()}")
            logger.debug(f"ADB stderr: {result.stderr.strip()}")
            return pulled_local_path
        else:
            logger.error(
                f"Failed to pull file {device_file_path}. Local file not found at {pulled_local_path} after pull."
            )
            logger.debug(f"ADB stdout: {result.stdout.strip()}")
            logger.debug(f"ADB stderr: {result.stderr.strip()}")
            return None
    except subprocess.CalledProcessError as e:
        logger.error(
            f"Failed to pull file {device_file_path}. ADB Error: {e.stderr.strip()}"
        )
        logger.debug(f"ADB stdout: {e.stdout.strip()}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during file pull: {e}")
        return None


class EmailSender:
    """
    A class to send emails with optional attachments using SMTP.

    Attributes:
        email_config_path (str): Path to the JSON config file containing sender and SMTP info.
        sender_email (str): Sender's email address.
        sender_password (str): Sender's email password.
        smtp_server (str): SMTP server address.
        smtp_port (int): SMTP server port.
    """

    def __init__(self, email_config_path: str = CONFIG_PATH):
        """
        Initialize the EmailSender by loading configuration from a JSON file.

        Args:
            email_config_path (str): Path to the JSON config file.
        """
        self.email_config_path = email_config_path
        self.sender_email, self.sender_password = self._get_usr_config()
        self.smtp_server, self.smtp_port = self._get_smtp_config()
        self.logger = setup_logging_config()

    def _get_usr_config(self) -> Tuple[str, str]:
        block = get_config_block(CONFIG_PATH, "email")
        return str(block["sender_email"]).strip(), str(block["sender_password"]).strip()

    def _get_smtp_config(self) -> Tuple[str, int]:
        block = get_config_block(CONFIG_PATH, "email")
        return str(block["smtp_server"]).strip(), block["smtp_port"]

    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """
        Attach a file to the email message if the file exists.

        Args:
            msg (MIMEMultipart): The email message object.
            file_path (str): Path to the file to attach.
        """
        if os.path.exists(file_path):
            try:
                # Try to get MIME type based on file extension
                ctype, encoding = mimetypes.guess_type(file_path)
                if ctype is None or encoding is not None:
                    # Fallback to generic type if unable to guess or encoding exists
                    ctype = "application/octet-stream"

                maintype, subtype = ctype.split("/", 1)

                with open(file_path, "rb") as attachment:
                    part2 = MIMEBase(maintype, subtype)
                    part2.set_payload(attachment.read())

                encoders.encode_base64(part2)

                filename = os.path.basename(file_path)
                part2.add_header(
                    "Content-Disposition",
                    f"attachment; filename*=utf-8''{filename}",
                )
                part2.add_header(
                    "Content-Disposition", f"attachment; filename*=utf-8''{filename}"
                )
                # # Note: If the filename contains non-ASCII characters, there may be garbled text or replacements here
                # part2.add_header(
                #     "Content-Disposition",
                #     f"attachment; filename=\"{filename}\"" # Use double quotes to enclose the filename
                # )
                msg.attach(part2)
            except Exception as e:
                self.logger.warning(f"Could not attach file {file_path}: {e}")
        else:
            self.logger.warning(
                f"Warning: Attachment file not found at {file_path}. Skipping this attachment."
            )

    def send_mail(
        self,
        receiver_email: str,
        subject: str = "hello world",
        body: str = "hello world, just for fun!",
        attach_local_file_path: Optional[str | List[str]] = None,
        attach_android_file_path: Optional[str | List[str]] = None,
    ):
        """
        Send an email with optional attachments.

        Args:
            receiver_email (str): Recipient's email address.
            subject (str): Email subject.
            body (str): Email body (plain text).
            attach_file_path (Optional[str | List[str]]): Path(s) to files to attach.
            sender_email (Optional[str]): Override sender email (default: from config).
            sender_password (Optional[str]): Override sender password (default: from config).

        Raises:
            smtplib.SMTPAuthenticationError: If authentication fails.
            Exception: For other errors during sending.
        """
        # Validate sender email
        try:
            validate_email(self.sender_email, check_deliverability=False)
        except EmailNotValidError as e:
            self.logger.error(f"Sender email '{self.sender_email}' is not valid: {e}")
            return

        # --- Create the email ---
        msg = MIMEMultipart()
        msg["From"] = f"<{self.sender_email}>"
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        msg.add_header("Content-Type", 'multipart/mixed; charset="utf-8"')

        # --- Add attachments ---
        # --- Add attachments on Android
        if attach_android_file_path is not None:
            if isinstance(attach_android_file_path, str):
                attach_android_file_path = [attach_android_file_path]
            # all transfer into local devices
            new_path = [
                str(pull_file_from_android(device_file_path=an_file_path))
                for an_file_path in attach_android_file_path
            ]
            for file_path_n in new_path:
                self._attach_file(msg, file_path_n)

        if attach_local_file_path is not None:
            if isinstance(attach_local_file_path, str):
                attach_local_file_path = [attach_local_file_path]
            for file_path in attach_local_file_path:
                self._attach_file(msg, file_path)

        # --- Send the email ---
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            self.logger.info("Email sent successfully!")
            self.logger.info(
                f"Message sent from {self.sender_email} to {receiver_email}"
            )
        except smtplib.SMTPAuthenticationError:
            self.logger.error("Failed to send email!")
            self.logger.error(
                "Authentication failed: Please check if the sender email address and password/authorization code are correct."
            )
        except Exception as e:
            self.logger.error("Failed to send email!")
            self.logger.error(f"An error occurred: {e}")
