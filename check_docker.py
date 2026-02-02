import subprocess
import time

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    except Exception as e:
        return str(e)

print("Checking docker ps:")
print(run_command("docker ps"))

print("\nStarting services:")
print(run_command("docker compose up -d"))

print("\nWaiting 5 seconds for services to start...")
time.sleep(5)

print("\nChecking docker ps again:")
print(run_command("docker ps"))

print("\nChecking logs of voice-journal-bot:")
print(run_command("docker compose logs voice-journal-bot --tail 20"))
