import subprocess
import argparse
import concurrent.futures
import re
import time

# Define color codes
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def get_status_and_title(url):
    try:
        # Use curl to get the HTTP status code and the HTML content
        result = subprocess.run(
            ['curl', '--insecure', '-s', '-o', '-', '-w', '%{http_code}', url],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        # Check the return code of curl
        if result.returncode == 0:  # Successful execution
            http_code = result.stdout[-3:].strip()

            # Check if the HTTP status code is valid
            if http_code.isdigit():
                # Find the title in the HTML content
                html_content = result.stdout[:-3]
                title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
                title = title_match.group(1) if title_match else 'No Title Found'
                return http_code, title.strip()
            else:
                return None, 'No HTTP Status Code'
        else:
            return None, 'Failed to fetch HTTP status code'
    except Exception as e:
        return None, str(e)

def check_url(url):
    status, title = get_status_and_title(url)
    
    if status:
        return f"[*] {url} {status} {title}"
    else:
        return f"[+] {url} Error: {title}"

def check_urls(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            urls = file.readlines()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return
    except UnicodeDecodeError:
        print(f"Failed to decode the file: {file_path}")
        return

    results = []

    # Use ThreadPoolExecutor to achieve concurrent requests
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit each URL to the executor
        future_to_url = {executor.submit(check_url, url.strip()): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
                if result.startswith("[+]"):
                    print(f"{RED}{result}{RESET}")
                else:
                    print(f"{GREEN}{result}{RESET}")
            except Exception as exc:
                print(f"Error fetching {url}: {exc}")

    # Generate current time string
    current_time = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"result_{current_time}.txt"

    # Save results to result_当前时间.txt
    with open(output_file, 'w', encoding='utf-8', errors='ignore') as result_file:
        for result in results:
            result_file.write(result + '\n')

    print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check URL accessibility using curl in concurrent mode.')
    parser.add_argument('-r', '--file', type=str, required=True, help='Path to the file containing URLs')
    args = parser.parse_args()

    check_urls(args.file)
