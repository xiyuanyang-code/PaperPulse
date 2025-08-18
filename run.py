import schedule
import time
import subprocess

def run_script():
    print("Time to get AI data!")
    try:
        result = subprocess.run(['/GPFS/rhome/xiyuanyang/Agents/AutoEmailSender/.venv/bin/python', 'main.py'], check=True, capture_output=True, text=True)
        print("Success!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.returncode}")
        print(e.stderr)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    schedule.every().day.at("23:00").do(run_script)
    while True:
        schedule.run_pending()
        time.sleep(5)