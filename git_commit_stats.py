import subprocess
import csv
import os
from datetime import datetime

def run_git_command(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, encoding='utf-8')
    if result.returncode != 0:
        raise Exception(f"Git command failed: {result.stderr}")
    return result.stdout

def get_commits(start_date, end_date):
    # 获取所有非merge提交hash、作者、日期、提交信息
    cmd = f"git log --no-merges --since='{start_date}' --until='{end_date} 23:59:59' --pretty=format:'%H|%an|%ad|%s' --date=short"
    output = run_git_command(cmd)
    commits = []
    for line in output.strip().split('\n'):
        if line:
            parts = line.split('|', 3)
            if len(parts) == 4:
                commit_hash, author, date, message = parts
                commits.append({'hash': commit_hash, 'author': author, 'date': date, 'message': message})
    return commits

def get_commit_file_stats(commit_hash):
    # 获取每个文件的增删行数
    cmd = f"git show --numstat --format='' {commit_hash}"
    output = run_git_command(cmd)
    file_stats = []
    for line in output.strip().split('\n'):
        if line:
            parts = line.split('\t')
            if len(parts) == 3:
                added, deleted, filename = parts
                try:
                    added = int(added)
                except ValueError:
                    added = 0
                try:
                    deleted = int(deleted)
                except ValueError:
                    deleted = 0
                file_stats.append({'file': filename, 'added': added, 'deleted': deleted})
    return file_stats

def format_files_list(file_stats):
    # 形如：path/to/file1 (+10/-2); path/to/file2 (+3/-1)
    return "; ".join([
        f"{stat['file']} (+{stat['added']}/-{stat['deleted']})" for stat in file_stats
    ])

def main():
    # 日期区间
    start_date = '2025-06-23'
    end_date = '2025-07-07'
    repo_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(repo_path)

    commits = get_commits(start_date, end_date)
    total_rows = []
    author_rows = {}

    for commit in commits:
        file_stats = get_commit_file_stats(commit['hash'])
        files_changed = len(file_stats)
        lines_added = sum(f['added'] for f in file_stats)
        lines_deleted = sum(f['deleted'] for f in file_stats)
        total_changes = lines_added + lines_deleted
        files_list = format_files_list(file_stats)
        # 日期格式化为 2025/6/30
        try:
            date_fmt = datetime.strptime(commit['date'], '%Y-%m-%d').strftime('%Y/%-m/%-d')
        except Exception:
            date_fmt = commit['date']
        row = {
            'Commit_Hash': commit['hash'],
            'Author': commit['author'],
            'Date': date_fmt,
            'Message': commit['message'],
            'Files_Changed': files_changed,
            'Lines_Added': lines_added,
            'Lines_Deleted': lines_deleted,
            'Total_Changes': total_changes,
            'Files_List': files_list
        }
        total_rows.append(row)
        # 个人表
        if commit['author'] not in author_rows:
            author_rows[commit['author']] = []
        author_row = row.copy()
        del author_row['Author']
        author_rows[commit['author']].append(author_row)

    # 导出总表
    with open('commit_details_20250623_20250707.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Commit_Hash','Author','Date','Message','Files_Changed','Lines_Added','Lines_Deleted','Total_Changes','Files_List'])
        writer.writeheader()
        writer.writerows(total_rows)

    # 导出个人表
    for author, rows in author_rows.items():
        filename = f"{author}_commits_20250623_20250707.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Commit_Hash','Date','Message','Files_Changed','Lines_Added','Lines_Deleted','Total_Changes','Files_List'])
            writer.writeheader()
            writer.writerows(rows)

    print('统计完成，已导出 commit_details_20250623_20250707.csv 和每个人的个人表')

if __name__ == '__main__':
    main()
