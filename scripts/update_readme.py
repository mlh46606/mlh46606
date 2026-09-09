import os
import sys
import json
import urllib.request
from datetime import datetime, timezone, timedelta

# リポジトリの説明がGitHub上で未設定（None）の場合のデフォルト補完説明
DEFAULT_DESCRIPTIONS = {
    "Tools": "顕微鏡画像処理・解析ツール統合開発リポジトリ（正本）",
    "CfPsf": "共焦点顕微鏡 PSF（点像強度分布関数）高速計算・生成ツール（アーカイブ）",
    "MFDcv": "多焦点画像 3D デコンボリューション処理ツール（CUDA GPU対応、アーカイブ）",
    "Unmix": "蛍光スペクトル画像アンミキシング（波長分離）処理ツール（アーカイブ）",
    "SFIV": "単体画像ビューア WPF アプリケーション（ImageView / IVW、アーカイブ）",
    "MDIT": "MDIT 関連プロジェクト",
    "MDIT.Plugins": "MDIT プラグインライブラリ",
    "ImageView": "画像ビューア旧構成プロジェクト"
}

def get_token():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    # ローカル実行時のフォールバック: git credential から取得
    try:
        import subprocess
        p = subprocess.Popen(["git", "credential", "fill"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        out, _ = p.communicate("protocol=https\nhost=github.com\n\n")
        for line in out.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1]
    except Exception:
        pass
    return None

def fetch_repositories(token):
    headers = {
        "User-Agent": "UpdateReadmeScript",
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"token {token}"
        url = "https://api.github.com/user/repos?per_page=100&sort=updated"
    else:
        url = "https://api.github.com/users/mlh46606/repos?per_page=100&sort=updated"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def format_date(iso_str):
    if not iso_str:
        return "-"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        # JST (UTC+9) に変換
        jst = timezone(timedelta(hours=9))
        dt_jst = dt.astimezone(jst)
        return dt_jst.strftime("%Y-%m-%d")
    except Exception:
        return iso_str[:10]

def build_table(repos):
    lines = [
        "| リポジトリ | 説明 | 区分 | 最終更新 |",
        "| :--- | :--- | :---: | :---: |"
    ]
    
    # mlh46606 自身は除外
    filtered = [r for r in repos if r.get("name") != "mlh46606"]
    
    for r in filtered:
        name = r.get("name", "")
        url = r.get("html_url", "")
        desc = r.get("description")
        if not desc or desc.strip() == "" or desc == "None" or desc == name or desc.lower() == "create":
            desc = DEFAULT_DESCRIPTIONS.get(name, desc if desc else "—")
        
        is_private = r.get("private", False)
        badge = "🔒 Private" if is_private else "🌐 Public"
        updated = format_date(r.get("pushed_at") or r.get("updated_at"))
        
        lines.append(f"| [**{name}**]({url}) | {desc} | {badge} | `{updated}` |")
        
    return "\n".join(lines)

def update_readme(readme_path, table_content):
    if not os.path.exists(readme_path):
        print(f"File not found: {readme_path}")
        return False
        
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    start_tag = "<!-- REPOS-LIST:START -->"
    end_tag = "<!-- REPOS-LIST:END -->"
    
    if start_tag not in content or end_tag not in content:
        print("Marker tags not found in README.md")
        return False
        
    before = content.split(start_tag)[0]
    after = content.split(end_tag)[1]
    
    jst = timezone(timedelta(hours=9))
    now_str = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S JST")
    
    new_content = f"{before}{start_tag}\n{table_content}\n\n*自動更新日時: {now_str}*\n{end_tag}{after}"
    
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print("README.md updated successfully.")
    return True

def main():
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(repo_dir, "README.md")
    
    token = get_token()
    print("Fetching repositories from GitHub API...")
    repos = fetch_repositories(token)
    print(f"Retrieved {len(repos)} repositories.")
    
    table_content = build_table(repos)
    update_readme(readme_path, table_content)

if __name__ == "__main__":
    main()
