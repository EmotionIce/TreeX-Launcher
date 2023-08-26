import os
import signal
import subprocess
import sys
import requests
import datetime
from subprocess import call
import tkinter as tk
from tkinter import messagebox
from tkinter import font
from tkinter import PhotoImage
import threading
from subprocess import Popen, call
import psutil

# Variables for user setup
GITHUB_REPO_API = 'https://api.github.com/repos/EmotionIce/TreeX-Launcher/contents/'
# Check if running as a script or a standalone executable
if getattr(sys, 'frozen', False):
    # we are running in a bundle (i.e., packaged as an exe)
    DIRECTORY_PATH = os.path.dirname(sys.executable)
else:
    # we are running in a normal Python environment
    DIRECTORY_PATH = os.path.dirname(os.path.abspath(__file__))

# Custom Colors
bgColor = "#303030"
btnColor = "#424242"
successColor = "#348054"
dangerColor = "#ba2722"


def find_jdk_path():
    """
    Locate the path of JDK 17's java executable.
    """
    command = "where" if os.name == "nt" else "which"

    try:
        # Try to find using 'where' or 'which' command
        result = subprocess.check_output(
            [command, "java"]).decode('utf-8').strip()

        # On Windows, 'where' might return multiple paths, iterate over them
        paths = result.splitlines() if os.name == "nt" else [result]

        for path in paths:
            try:
                version_check = subprocess.check_output(
                    [path, "-version"], stderr=subprocess.STDOUT).decode('utf-8')
                # Debugging line

                if "version \"17" in version_check:
                    return path
            except subprocess.CalledProcessError:
                continue
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")  # Debugging line

    # If not found using where/which, check common paths
    common_paths = [
        r"C:\Program Files\Java\jdk-17\bin\java.exe",  # Windows common path
        r"/usr/bin/java",  # Linux common path
        r"/usr/local/bin/java"  # MacOS common path
    ]

    for path in common_paths:
        if os.path.exists(path):
            try:
                version_check = subprocess.check_output(
                    [path, "-version"], stderr=subprocess.STDOUT).decode('utf-8')
                if "version \"17" in version_check:
                    return path
            except Exception as e:
                print(f"Error with path {path}: {e}")  # Debugging line
                continue

    return None


JDK17_PATH = find_jdk_path()
if not JDK17_PATH:
    raise EnvironmentError("JDK 17 not found on the system.")


def fetch_latest_jar_sha():
    response = requests.get(GITHUB_REPO_API)

    if response.status_code != 200:
        print(
            f"Failed to fetch data from GitHub API. Status code: {response.status_code}")
        print(response.text)  # Print the response for debugging
        return None

    response_data = response.json()
    if not isinstance(response_data, list):
        print("Unexpected response data format.")
        print(response_data)
        return None

    for item in response_data:
        if item['name'].endswith('.jar'):
            return item['sha']

    print("JAR file not found in the repository.")
    return None


def save_sha_value(sha):
    with open(os.path.join(DIRECTORY_PATH, 'latest_sha.txt'), 'w') as f:
        f.write(sha)


def get_saved_sha_value():
    try:
        with open(os.path.join(DIRECTORY_PATH, 'latest_sha.txt'), 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def find_and_remove_outdated_jars(latest_release_date):
    for item in os.listdir(DIRECTORY_PATH):
        item_path = os.path.join(DIRECTORY_PATH, item)
        if item.endswith('.jar'):
            item_modified_date = datetime.datetime.fromtimestamp(
                os.path.getmtime(item_path))
            if item_modified_date < latest_release_date:
                print(f"Removing outdated JAR: {item}")
                os.remove(item_path)


def download_latest_jar():
    response = requests.get(GITHUB_REPO_API)
    if response.status_code != 200:
        print(
            f"Failed to fetch data from GitHub API. Status code: {response.status_code}")
        return None

    response_data = response.json()
    if not isinstance(response_data, list):
        print("Unexpected response data format.")
        return None

    for item in response_data:
        if item['name'].endswith('.jar'):
            jar_name = item['name']
            save_path = os.path.join(DIRECTORY_PATH, jar_name)
            response = requests.get(item['download_url'], stream=True)
            with open(save_path, 'wb') as out_file:
                for chunk in response.iter_content(chunk_size=8192):
                    out_file.write(chunk)
            return save_path
    return None


def reset_status():
    global status_label
    if status_label:
        status_label.config(text="Ready", fg="white")


def restart_jar():
    stop_jar()
    reset_status()
    launch_jar()


def stop_jar():
    """
    Stops the running JAR process.
    """
    global jar_process
    if jar_process:
        print("Attempting to stop JAR...")  # Debug statement
        try:
            # Kill the process and its child processes
            parent = psutil.Process(jar_process.pid)
            for child in parent.children(recursive=True):
                child.terminate()
                child.wait()  # Wait for child processes to finish
            parent.terminate()
            parent.wait()  # Wait for parent process to finish
        except psutil.NoSuchProcess:
            print("Process already terminated.")  # Debug statement
            reset_status()
        finally:
            jar_process = None
            print("JAR process terminated.")  # Debug statement
            reset_status()


def launch_jar_thread():
    """
    A threaded method to launch the JAR.
    """
    global jar_process, status_label
    jar_to_launch = next((file for file in os.listdir(
        DIRECTORY_PATH) if file.endswith('.jar')), None)
    if jar_to_launch:
        print(f"Launching JAR: {jar_to_launch}")  # Debug statement
        jar_process = subprocess.Popen(
            [JDK17_PATH, '-jar', os.path.join(DIRECTORY_PATH, jar_to_launch)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        for line in iter(jar_process.stdout.readline, ''):
            if "Completed initialization" in line:
                if status_label:
                    print("JAR initialized.")
                    status_label.config(text="Initialized", fg=successColor)
                break


def launch_jar():
    """
    Launches the JAR if not already running.
    """
    print("Launch button clicked.")  # Debug statement
    thread = threading.Thread(target=launch_jar_thread)
    thread.start()


def update_jar():
    global status_label
    # Fetch the latest JAR sha from GitHub
    latest_sha = fetch_latest_jar_sha()

    # Get the saved sha value
    saved_sha = get_saved_sha_value()

    # If the sha values are the same, we already have the latest JAR
    if saved_sha == latest_sha:
        print("Already have the latest JAR.")
        if (status_label):
            status_label.config(text="Already up to date", fg=successColor)
        return

    # Otherwise, download the new JAR
    jar_path = download_latest_jar()
    if jar_path:
        # Save the new sha value
        save_sha_value(latest_sha)
        print(f"Downloaded new JAR: {jar_path}")
        if (status_label):
            status_label.config(text="Updated", fg=successColor)
        return
    if (status_label):
        status_label.config(text="Failed to update", fg=dangerColor)


def stop_button_command():
    print("Stop button clicked.")  # Debug statement
    stop_jar()


def on_enter(event):
    event.widget['background'] = '#4a4a4a'  # Darken the color on hover


def on_leave(event):
    event.widget['background'] = '#333333'  # Restore the original color


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(
        os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def show_gui():
    global status_label
    root = tk.Tk()
    root.title("TreeX")

    # Set window size and prevent resizing
    root.geometry("300x375")

    root.configure(bg=bgColor)

    logoSizeX = 100
    logoSizeY = 100
    # Create a canvas for the logo
    canvas = tk.Canvas(root, width=logoSizeX, height=logoSizeY,
                       bg=bgColor, highlightthickness=0)
    canvas.pack(pady=10)

    # Load and add the logo
    logo = PhotoImage(file=resource_path("logo.png"))
    canvas.create_image(logoSizeX / 2, logoSizeY / 2,
                        image=logo)  # Add the logo to the canvas

    status_label = tk.Label(root, text="Ready", fg="white", bg=bgColor)
    status_label.pack(pady=10)

    def update_status(message, color):
        status_label['text'] = message
        status_label['fg'] = color

    def custom_launch_jar():
        launch_jar()
        update_status("Launching...", "#FFD700")

    def custom_stop_jar():
        stop_jar()
        update_status("Stopped", dangerColor)

    def custom_restart_jar():
        restart_jar()
        update_status("Restarting...", "#FFD700")

    btnFont = font.Font(size=12, family="Arial")

    launch_button = tk.Button(root, text="Launch", command=custom_launch_jar,
                              bg=btnColor, fg="white", font=btnFont)
    launch_button.pack(pady=10)

    stop_button = tk.Button(root, text="Stop", command=custom_stop_jar,
                            bg=btnColor, fg="white", font=btnFont)
    stop_button.pack(pady=10)

    restart_button = tk.Button(root, text="Restart", command=custom_restart_jar,
                               bg=btnColor, fg="white", font=btnFont)
    restart_button.pack(pady=10)

    update_button = tk.Button(root, text="Update", command=update_jar,
                              bg=btnColor, fg="white", font=btnFont)
    update_button.pack(pady=10)

    root.mainloop()


status_label = None
jar_process = None


def main():
    update_jar()  # Check for updates before showing the GUI
    show_gui()


if __name__ == "__main__":
    main()
