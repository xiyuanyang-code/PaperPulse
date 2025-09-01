# PaperPulse

Paper Pulse: automatic email sender, pushing trending papers and Github repos with AI summary.

> [!IMPORTANT]
> This project has been running! Contact with the author ([email](mailto:yangxiyuan@sjtu.edu.cn)) for subscribing.

## Installation

We recommend you to run this using `uv`.

```bash
git clone https://github.com/xiyuanyang-code/PaperPulse
cd PaperPulse
uv sync
source .venv/bin/activate
```

### Email Config settings

For automatically sending emails, several settings for email sender is required. The default config path is in `./mail/config.json`.

```json
{
    "recipient email list": [
        "1@outlook.com",
        "2@outlook.com"
    ],
    "config_name": "email",
    "sender_email": "Your email",
    "sender_password": "Your password",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 465
}
```

You can copy the file from [`./mail/config_template.json`](./mail/config_template.json) as rename it to `config.json`.

### LLM Model Config Settings

Then, finish the model config, write them into your `~/.bashrc` or `~/.zshrc`.

```bash
export OPENAI_API_KEY="change to yours"
export BASE_URL="change to yours"
```

### Github Tokens Settings

You can find them here: [Github Tokens](https://github.com/settings/tokens), and write them into your `~/.bashrc` or `~/.zshrc`. 

```bash
export GITHUB_TOKEN="Your GH tokens"
```

## Usage

```bash
# for one single action
python main.py

# scripts for running it everyday (23:00)
python run.py
```

### Advanced Usage

You can integrate it into your own workflow! It has been refactored as a module.

```python
reporter = AIReporter()
reporter.run_report()
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

- Optimizing prompts for better summary contents.

- Make the generated markdown file prettier.