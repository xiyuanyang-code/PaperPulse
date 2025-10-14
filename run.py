import schedule
import time
import subprocess
import datetime
import sys

# * custom settings can be placed here
SETTING_TIME = "21:00"


def get_progress_info(target_time_str):
    now = datetime.datetime.now()
    target_time = datetime.datetime.strptime(target_time_str, "%H:%M").time()
    next_run_dt = datetime.datetime.combine(now.date(), target_time)
    if now.time() >= target_time:
        next_run_dt += datetime.timedelta(days=1)

    time_remaining = next_run_dt - now
    total_seconds = int(time_remaining.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    countdown_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    TOTAL_DAY_SECONDS = 24 * 3600
    current_seconds = now.hour * 3600 + now.minute * 60 + now.second
    progress_percent = (current_seconds / TOTAL_DAY_SECONDS) * 100

    return countdown_str, progress_percent


def update_terminal_display(countdown_str, progress_percent):

    BAR_LENGTH = 30
    filled_length = int(BAR_LENGTH * progress_percent // 100)
    bar = "█" * filled_length + "-" * (BAR_LENGTH - filled_length)

    output = (
        f"⏳ Next Run at {SETTING_TIME} | "
        f"Countdown: {countdown_str} | "
        f"Progress: [{bar}] {progress_percent:.2f}%  "
    )

    sys.stdout.write(output + "\r")
    sys.stdout.flush()


def run_script():
    sys.stdout.write("\r" + " " * 150 + "\r")
    sys.stdout.flush()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("-" * 50)
    print(f"🤖 STARTING TASK: main.py | Time: {timestamp}")
    print("-" * 50)

    try:
        result = subprocess.run(
            [
                # ! switch to your own command
                "/data/xiyuanyang/PaperPulse/.venv/bin/python",
                "main.py",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=7200,
        )
        print("✅ Success!")
        print("\n".join(result.stdout.splitlines()))
        print("\n\n" + "-" * 50)
        print("-" * 50)

    except subprocess.CalledProcessError as e:
        print("❌ ERROR: Task failed with a non-zero exit code.")
        print(f"Return Code: {e.returncode}")
        print("Standard Error")
        print("\n".join(e.stderr.splitlines()))
        print("\n\n" + "-" * 50)

    except Exception as e:
        print(f"❌ Critical Error: {e}")
        print("-" * 50)


if __name__ == "__main__":
    try:
        schedule.every().day.at(SETTING_TIME).do(run_script)
        print(f"✅ PaperPulse Scheduler started. Target time: {SETTING_TIME}")
        print("--------------------------------------------------")

        while True:
            schedule.run_pending()
            countdown, percent = get_progress_info(SETTING_TIME)
            update_terminal_display(countdown, percent)
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n👋 PaperPulse Scheduler Stopped.")

    except Exception as e:
        print(f"\n\n❌ Unhandled Error in Scheduler Loop: {e}")
