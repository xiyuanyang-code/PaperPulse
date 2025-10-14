import schedule
import time
import subprocess
import datetime
import sys
from tqdm import tqdm

# * custom settings can be placed here
SETTING_TIME = "21:00"


# --- Function to get time remaining (still needed for tqdm's 'total') ---
def get_time_remaining(target_time_str):
    """Calculates the seconds remaining until the next scheduled run."""
    now = datetime.datetime.now()
    target_time = datetime.datetime.strptime(target_time_str, "%H:%M").time()
    next_run_dt = datetime.datetime.combine(now.date(), target_time)
    if now.time() >= target_time:
        next_run_dt += datetime.timedelta(days=1)

    time_remaining = next_run_dt - now
    return int(time_remaining.total_seconds())


# --- run_script remains the same ---
def run_script():
    # Use sys.stdout.write to clear the tqdm bar line before printing
    # This prevents the task output from overwriting the progress bar visually
    sys.stdout.write("\r" + " " * 150 + "\r")
    sys.stdout.flush()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "-" * 50)
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

        # Total seconds in a day for the progress bar's range
        TOTAL_DAY_SECONDS = 24 * 3600

        with tqdm(
            total=TOTAL_DAY_SECONDS,
            unit="s",
            bar_format="{desc}: |{bar}| {n_fmt}/{total_fmt} [{remaining}]",
        ) as pbar:

            while True:
                schedule.run_pending()
                seconds_remaining = get_time_remaining(SETTING_TIME)
                seconds_elapsed_since_last_run = TOTAL_DAY_SECONDS - seconds_remaining

                pbar.n = seconds_elapsed_since_last_run
                pbar.set_description(f"Next Run at {SETTING_TIME}")
                pbar.refresh()

                # The scheduler now checks for tasks and updates the bar every 5 seconds.
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n👋 PaperPulse Scheduler Stopped.")

    except Exception as e:
        print(f"\n\n❌ Unhandled Error in Scheduler Loop: {e}")
