import schedule
import time
import subprocess

# * custom settings can be placed here
SETTING_TIME = "21:00"


def run_script():
    print(f"Time to get AI data! Time: {time.strftime("%Y%m%d%H%M%S")}")
    try:
        result = subprocess.run(
            [
                # !switch to your own command
                "/GPFS/rhome/xiyuanyang/Agents/AutoEmailSender/.venv/bin/python",
                "main.py",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=7200
        )
        print("Success! The following output: ")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.returncode}")
        print(e.stderr)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print(time.strftime("%Y%m%d%H%M%S"))
    schedule.every().day.at(SETTING_TIME).do(run_script)
    while True:
        schedule.run_pending()
        time.sleep(5)
