# AutoMail Sender

> [!IMPORTANT]
> This project has been running! Contact with the author ([email](mailto:yangxiyuan@sjtu.edu.cn)) for subscribing.

## Installation

### Cloning projects

We recommend you to run this using `uv`.

```bash
git clone https://github.com/xiyuanyang-code/AutoEmailSender
cd AutoEmailSender
uv sync
source .venv/bin/activate
```

### Email Config settings

Then, finish some config settings:

- `./config.json`:

```json
[
    {
        "config_name": "email",
        "sender_email": "your sender email",
        "sender_password": "your password",
        // switch to yours
        "smtp_server": "mail.sjtu.edu.cn",
        "smtp_port": 465
    }
]
```

- `./summary/config.json`: emails to be sent to. (subscribers)

```json
[
    "xiaohong@outlook.com",
    "xiaolan@sjtu.edu.cn",
    "xiaohuang@sjtu.edu.cn"
]
```

### LLM Model Config Settings

Then, finish the model config, write them into your `~/.bashrc` or `~/.zshrc`.

```bash
export OPENAI_API_KEY="change to yours"
export BASE_URL="change to yours"
```

## Usage

```bash
# for one single action
python main.py

# scripts for running it everyday (23:00)
python run.py
```

## Components

- AI Trending
    - Github Repo Trending
    - Paper Trending

- AI Summary

See [example json](./example/20250818.json) and [example markdown](./example/20250818.md) for more info.

> [!NOTE]
> More to be added in the future, see [todo list](#todo-list) for more info. PRs and contributions are all welcome.

## Todo List

- Add scraper for programming language learning. (Maybe Rust to be the first!)

- Optimizing prompts for better summary contents.

- Make the generated markdown file prettier.