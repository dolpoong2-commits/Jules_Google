import os
import re
import requests
from flask import Flask, render_template, jsonify, request
from scraper import scrape_github_repo, scrape_website_headless
import json

app = Flask(__name__)

# In-memory storage for simplicity
scraping_targets = []
scraping_results = []
target_id_counter = 0
result_id_counter = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/targets', methods=['GET', 'POST'])
def manage_targets():
    global target_id_counter
    if request.method == 'POST':
        data = request.json
        if not data or 'url' not in data or 'type' not in data:
            return jsonify({"error": "Invalid data"}), 400

        target = {
            "id": target_id_counter,
            "url": data['url'],
            "type": data['type'],
            "search_keyword": data.get('search_keyword', '')
        }
        scraping_targets.append(target)
        target_id_counter += 1
        return jsonify(target), 201

    elif request.method == 'GET':
        return jsonify(scraping_targets)

@app.route('/api/targets/<int:target_id>', methods=['DELETE'])
def delete_target(target_id):
    global scraping_targets
    target_to_remove = next((target for target in scraping_targets if target['id'] == target_id), None)
    if target_to_remove:
        scraping_targets.remove(target_to_remove)
        return jsonify({"message": "Target deleted"}), 200
    return jsonify({"error": "Target not found"}), 404

@app.route('/api/scrape', methods=['POST'])
def scrape_all_targets():
    global scraping_results, result_id_counter
    scraping_results.clear()

    for target in scraping_targets:
        result = {"id": result_id_counter, "source_url": target['url'], "content": None, "error": None, "type": target['type'], "zipball_url": None}

        if target['type'] == 'github_api':
            data = scrape_github_repo(target['url'])
            if data:
                result['content'] = f"Repo: {data.get('full_name')}, Stars: {data.get('stargazers_count')}, Desc: {data.get('description')}"
                result['zipball_url'] = data.get('zipball_url')
            else:
                result['error'] = f"Failed to fetch GitHub API for {target['url']}"
        else: # headless
            content = scrape_website_headless(target['url'], target.get('search_keyword'))
            if content:
                result['content'] = content
            else:
                result['error'] = f"Failed to scrape website {target['url']}"

        scraping_results.append(result)
        result_id_counter += 1

    return jsonify({"message": f"Scraping complete. Processed {len(scraping_targets)} targets."})

@app.route('/api/results', methods=['GET'])
def get_results():
    return jsonify(scraping_results)

def safe_filename(url, extension):
    """Creates a safe filename from a URL with a given extension."""
    filename = re.sub(r'https?://', '', url)
    filename = re.sub(r'[/\\?%*:|"<>]', '_', filename)
    return filename[:100] + extension

@app.route('/api/download', methods=['POST'])
def download_results():
    data = request.json
    result_ids_str = data.get('result_ids', [])
    result_ids = [int(i) for i in result_ids_str]
    save_path = data.get('save_path', 'collected_data')

    if not result_ids:
        return jsonify({"error": "No result IDs provided"}), 400

    os.makedirs(save_path, exist_ok=True)

    saved_files = []
    for result_id in result_ids:
        result = next((r for r in scraping_results if r['id'] == result_id), None)
        if not result or not result['content']:
            continue

        try:
            if result['type'] == 'github_api' and result['zipball_url']:
                filename = safe_filename(result['source_url'], ".zip")
                filepath = os.path.join(save_path, filename)
                zip_response = requests.get(result['zipball_url'], stream=True)
                zip_response.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in zip_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                saved_files.append(filepath)
            elif result['type'] == 'headless':
                filename = safe_filename(result['source_url'], ".html")
                filepath = os.path.join(save_path, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(result['content'])
                saved_files.append(filepath)
        except Exception as e:
            print(f"Error saving file for {result['source_url']}: {e}")

    return jsonify({"message": f"Successfully saved {len(saved_files)} files.", "files": saved_files})

if __name__ == '__main__':
    app.run(debug=True, port=5001)