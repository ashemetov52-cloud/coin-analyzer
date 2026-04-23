import os
import subprocess
import requests
from datetime import datetime, timezone, timedelta

# Настройки
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
REPO = os.environ.get("GITHUB_REPOSITORY", "ashemetov52-cloud/coin-analyzer")
MSK = timezone(timedelta(hours=3))
TODAY = datetime.now(MSK).strftime("%Y-%m-%d")

def get_git_changes():
    """Получаем изменения за последние 24 часа"""
    try:
        # Коммиты за последние 24 часа
        commits = subprocess.check_output([
            "git", "log",
            "--since=24 hours ago",
            "--pretty=format:- %h | %an | %s",
            "--no-merges"
        ], text=True).strip()

        # Изменённые файлы
        changed_files = subprocess.check_output([
            "git", "diff",
            "--name-status",
            "HEAD~1", "HEAD"
        ], text=True).strip() if commits else ""

        # Статистика
        stats = subprocess.check_output([
            "git", "log",
            "--since=24 hours ago",
            "--shortstat",
            "--no-merges"
        ], text=True).strip()

        return commits, changed_files, stats

    except subprocess.CalledProcessError:
        return "", "", ""

def ask_claude(commits, changed_files, stats):
    """Отправляем данные в Claude через OpenRouter"""

    if not commits:
        content = f"Репозиторий: {REPO}\nДата: {TODAY}\n\nЗа последние 24 часа коммитов не было."
    else:
        content = f"""Репозиторий: {REPO}
Дата: {TODAY}

КОММИТЫ за последние 24 часа:
{commits}

ИЗМЕНЁННЫЕ ФАЙЛЫ:
{changed_files}

СТАТИСТИКА:
{stats}"""

    prompt = f"""Ты помощник разработчика. Проанализируй изменения в репозитории GitHub и составь краткий ежедневный отчёт на русском языке.

Данные об изменениях:
{content}

Составь отчёт в формате Markdown со следующими разделами:
1. 📊 Сводка дня (1-2 предложения)
2. 🔨 Что было сделано (список коммитов с пояснением)
3. 📁 Затронутые файлы (какие части проекта изменились)
4. 💡 Наблюдения (паттерны, риски, рекомендации если есть)

Если коммитов не было — напиши об этом коротко и дай совет по поддержанию активности."""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": f"https://github.com/{REPO}",
        },
        json={
            "model": "anthropic/claude-sonnet-4-5",
            "max_tokens": 1500,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def save_report(report_text):
    """Сохраняем отчёт в файл"""
    header = f"# Ежедневный отчёт — {TODAY}\n\n"
    full_report = header + report_text

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(full_report)

    print("=" * 50)
    print(full_report)
    print("=" * 50)
    print(f"\n✅ Отчёт сохранён в report.md")

def main():
    print(f"🚀 Генерация отчёта за {TODAY}...")
    print(f"📦 Репозиторий: {REPO}\n")

    commits, changed_files, stats = get_git_changes()
    print(f"📝 Найдено коммитов: {'нет' if not commits else len(commits.splitlines())}")

    print("🤖 Запрашиваем Claude...")
    report = ask_claude(commits, changed_files, stats)

    save_report(report)

if __name__ == "__main__":
    main()
