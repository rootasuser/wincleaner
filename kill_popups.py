import time
import os

# Processes that the malware relies on to display the windows
TARGET_PROCESSES = ["mshta.exe", "wscript.exe", "cscript.exe"]

def process_guard():
    print("=" * 60)
    print("  POPUP GUARDIAN ACTIVE: Monitoring system for rogue loops...")
    print("  Press Ctrl + C in this window to stop monitoring.")
    print("=" * 60)
    
    while True:
        try:
            # Query the Windows task system for active processes matching our targets
            for process in TARGET_PROCESSES:
                # taskkill /F forces closure, /T closes child processes it spawned, /IM specifies the image name
                # Redirecting output to devnull keeps your console clean from endless text logs
                exit_code = os.system(f"taskkill /F /T /IM {process} >nul 2>&1")
                
                # An exit code of 0 means a process was successfully caught and terminated
                if exit_code == 0:
                    print(f"[⚠️ WARNING] Intercepted and terminated an active '{process}' popup loop!")
            
            # Watch with high frequency (checks every 100 milliseconds)
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\nMonitoring stopped safely.")
            break
        except Exception as e:
            # Keep running even if an unexpected internal error happens
            continue

if __name__ == "__main__":
    process_guard()