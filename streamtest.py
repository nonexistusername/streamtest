import subprocess
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import chardet
import concurrent.futures
import re
from tkinter.ttk import Progressbar  # Import Progressbar from ttk

# Function to append logs to the GUI with colored text
def append_log(message, color="black"):
    log_output.config(state=tk.NORMAL)
    log_output.insert(tk.END, message + "\n")
    log_output.tag_add(color, "1.0", tk.END)  # Apply color to the entire text
    log_output.config(state=tk.DISABLED)
    log_output.yview(tk.END)  # Scroll output to the end

# Function to detect file encoding
def detect_file_encoding(file_path):
    append_log(f"Detecting file encoding: {file_path}", "green")
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)  # Read the first part of the file
        result = chardet.detect(raw_data)  # Detect encoding
        return result['encoding']

# Function to load URLs from M3U file with encoding detection
def load_urls_from_file(file_path):
    urls = []
    metadata = []  # To store metadata (e.g., #EXTINF)
    append_log(f"Loading URLs from M3U file: {file_path}", "green")
    try:
        encoding = detect_file_encoding(file_path)
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            lines = f.readlines()
            current_metadata = ""
            for line in lines:
                line = line.strip()
                if line.startswith("#EXTINF"):
                    current_metadata = line  # Store metadata
                elif not line.startswith("#"):
                    urls.append((current_metadata, line))  # Assign metadata to URL
                    current_metadata = ""  # Reset metadata for the next stream
    except Exception as e:
        append_log(f"Error loading file: {e}", "red")
    return urls

# Function to clean URL by removing null bytes or invalid characters
def clean_url(url):
    url = url.replace('\x00', '')  # Remove null byte
    url = re.sub(r'[^\x20-\x7E]', '', url)  # Remove invalid characters
    return url

# Function to test URL availability using curl
def test_url_with_curl(url):
    url = clean_url(url)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }

    curl_command = [
        'curl', '--silent', '--max-time', '5',  # Shorter timeout for faster results
        '--header', f'User-Agent: {headers["User-Agent"]}',
        '--header', f'Accept: {headers["Accept"]}', '--header', f'Accept-Encoding: {headers["Accept-Encoding"]}',
        '--header', f'Connection: {headers["Connection"]}', url
    ]
    
    try:
        result = subprocess.run(curl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        if result.returncode == 0:
            append_log(f"Stream is available", "green")  # Green for functional streams
            return True
        else:
            append_log(f"Stream is not available", "red")  # Red for non-functional streams
            return False
    except subprocess.TimeoutExpired:
        append_log(f"Stream timed out", "red")  # Red for non-functional streams
        return False
    except Exception as e:
        append_log(f"Error testing URL: {e}", "red")  # Red for non-functional streams
        return False

# Function to save a valid stream to a file
def save_valid_stream_to_file(metadata, url, valid_streams_file):
    try:
        with open(valid_streams_file, 'a') as f:
            f.write(f"{metadata}\n{url}\n")  # Save both metadata and URL
        append_log(f"Stream {url} has been saved to file {valid_streams_file}", "green")  # Green for functional streams
    except Exception as e:
        append_log(f"Error saving URL to file: {e}", "red")  # Red for non-functional streams

# Function to remove invalid URL from file
def remove_invalid_url_from_file(url, file_path, urls):
    if url in [item[1] for item in urls]:
        urls = [item for item in urls if item[1] != url]  # Remove URL from list
        try:
            with open(file_path, 'w') as f:
                for metadata, valid_url in urls:
                    f.write(f"{metadata}\n{valid_url}\n")  # Rewrite file with valid URLs
            append_log(f"Stream has been removed from file.", "red")  # Red for non-functional streams
        except Exception as e:
            append_log(f"Error removing URL from file: {e}", "red")  # Red for non-functional streams

# Function to test stream using ffmpeg
def test_stream_ffmpeg(url, file_path, urls, valid_streams_file, metadata, index, total_streams, success_counter):
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", url, "-t", "10", "-f", "null", "-", "-timeout", "30", "-loglevel", "error"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )

        error_output = result.stderr.decode('utf-8')

        # If no critical error in the error output, consider the stream functional
        if "Error opening input" in error_output or "Connection timed out" in error_output:
            remove_invalid_url_from_file(url, file_path, urls)
        else:
            save_valid_stream_to_file(metadata, url, valid_streams_file)
            append_log(f"Stream was functional and saved", "green")  # Green for functional streams
            success_counter[0] += 1

    except subprocess.TimeoutExpired:
        save_valid_stream_to_file(metadata, url, valid_streams_file)
        append_log(f"Stream was functional and saved", "green")  # Green for functional streams
        success_counter[0] += 1
    except Exception as e:
        remove_invalid_url_from_file(url, file_path, urls)

# Function to process stream and test URL and stream
def process_stream(url_data, file_path, urls, valid_streams_file, index, total_streams, success_counter):
    metadata, url = url_data
    if test_url_with_curl(url):
        test_stream_ffmpeg(url, file_path, urls, valid_streams_file, metadata, index, total_streams, success_counter)

# Function to test URLs in parallel using threads or processes
def test_urls_parallel(urls, file_path, valid_streams_file, max_workers=10):
    if not urls:
        append_log(f"No streams to test!", "red")  # Red for non-functional streams
        return

    total_streams = len(urls)
    success_counter = [0]  # Count of functional streams
    append_log(f"Starting test for {total_streams} streams.", "green")  # Green for starting test

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for index, url_data in enumerate(urls, 1):
            future = executor.submit(process_stream, url_data, file_path, urls, valid_streams_file, index, total_streams, success_counter)
            futures.append(future)

        try:
            concurrent.futures.wait(futures)
        except KeyboardInterrupt:
            append_log(f"Testing was interrupted.", "red")  # Red for interruption
            for future in futures:
                future.cancel()

    append_log("Testing complete, displaying results...", "green")  # Green for testing complete
    show_test_complete(success_counter[0], total_streams)

# Function to show a window after scanning is completed
def show_test_complete(success_count, total_count):
    messagebox.showinfo(
        "Testing Complete",
        f"Testing completed!\nFunctional streams: {success_count}/{total_count}",
    )
    update_stats(success_count, total_count)

# Function to update the number of loaded and functional streams
def update_stats(success_count, total_count):
    label_stats.config(text=f"Total streams: {total_count} | Functional streams: {success_count}")

# Function to load a file using a dialog
def load_file():
    file_path = filedialog.askopenfilename(title="Select M3U file", filetypes=[("M3U files", "*.m3u")])
    if file_path:
        label_file.config(text=f"File: {file_path}")
        return file_path
    return None

# Function to start testing
def start_testing():
    file_path = label_file.cget("text").split(":")[1].strip()
    if not file_path:
        messagebox.showerror("Error", "Please select an M3U file first!")
        return

    urls = load_urls_from_file(file_path)

    # Get scan speed from the slider
    max_workers = int(slider_speed.get())

    # Create path for valid streams
    valid_streams_file = os.path.expanduser("~/Desktop/validstreams.m3u")

    append_log(f"Starting test for {len(urls)} URLs...", "green")

    # Update static information
    update_stats(0, len(urls))

    # Start testing in a separate thread so GUI remains responsive
    threading.Thread(target=test_urls_parallel, args=(urls, file_path, valid_streams_file, max_workers)).start()

# Function to start VLC player
def start_vlc():
    try:
        subprocess.Popen(['vlc'])  # Opens VLC Player
    except Exception as e:
        append_log(f"Error starting VLC: {e}", "red")

# Function to open valid streams file
def open_valid_streams_file():
    valid_streams_file = os.path.expanduser("~/Desktop/validstreams.m3u")
    if os.path.exists(valid_streams_file):
        subprocess.Popen(['xdg-open', valid_streams_file])  # Uses xdg-open for Linux
    else:
        append_log(f"File with valid streams not found!", "red")

# Function to start VLC and load the valid streams file
def start_vlc_with_valid_streams():
    valid_streams_file = os.path.expanduser("~/Desktop/validstreams.m3u")
    if os.path.exists(valid_streams_file):
        try:
            subprocess.Popen(['vlc', valid_streams_file])  # Opens VLC Player with valid streams file
        except Exception as e:
            append_log(f"Error starting VLC with file: {e}", "red")
    else:
        append_log(f"File with valid streams not found!", "red")

# Create main window for GUI
root = tk.Tk()
root.title("STREAMTEST (BETA) by AI")  # Updated window title
label_file = tk.Label(root, text="File: Not selected")  # Changed to English
label_file.pack(pady=10)

# Buttons with smaller font size
button_load = tk.Button(root, text="LOAD FILE", command=load_file, font=('Arial', 10))
button_load.pack(pady=5)

button_start = tk.Button(root, text="START TESTING", command=start_testing, font=('Arial', 10))
button_start.pack(pady=10)

# Wider slider with new range 1-50
slider_speed = tk.Scale(root, from_=1, to=50, orient=tk.HORIZONTAL, label="TESTING SPEED")
slider_speed.set(1)  # Default value 1 thread
slider_speed.pack(padx=20, pady=10, fill=tk.X)

label_status = tk.Label(root, text="Status: Waiting for action...", font=('Arial', 8))
label_status.pack(pady=10)

# New label for displaying number of streams (without "Functional streams")
label_stats = tk.Label(root, text="Total streams: 0", font=('Arial', 8))  # Only "Total streams"
label_stats.pack(pady=10)

# Frame for log output and scrollbar
frame_log = tk.Frame(root)
frame_log.pack(pady=10)

log_output = tk.Text(frame_log, width=100, height=30, wrap=tk.WORD, state=tk.DISABLED)  # Reduced width and height
log_output.pack(side=tk.LEFT)

scrollbar = tk.Scrollbar(frame_log, command=log_output.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

log_output.config(yscrollcommand=scrollbar.set)

# Define color tags
log_output.tag_config("green", foreground="green")
log_output.tag_config("red", foreground="red")
log_output.tag_config("black", foreground="black")

# Create another frame for buttons
frame_buttons = tk.Frame(root)  # Frame for buttons
frame_buttons.pack(pady=10, fill="x", padx=20)  # Buttons will be centered and fill the width

button_vlc = tk.Button(frame_buttons, text="OPEN VLC", command=start_vlc, font=('Arial', 10))
button_vlc.pack(side=tk.LEFT, padx=5, expand=True)  # Button will be centered

button_open_valid_streams = tk.Button(frame_buttons, text="OPEN VALID STREAMS FILE", command=open_valid_streams_file, font=('Arial', 10))
button_open_valid_streams.pack(side=tk.LEFT, padx=5, expand=True)

button_start_vlc_valid = tk.Button(frame_buttons, text="OPEN VLC (WITH VALID STREAMS)", command=start_vlc_with_valid_streams, font=('Arial', 10))
button_start_vlc_valid.pack(side=tk.LEFT, padx=5, expand=True)

root.mainloop()