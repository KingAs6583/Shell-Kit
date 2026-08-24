# Initialize a new repo, make first commit, push to remote
# Usage: setupGit "commit message" <repo-url>
setupGit() {
    if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
        echo "Usage: setupGit \"commit message\" <repo-url>"
        return 0
    fi

    if [ $# -lt 2 ]; then
        echo "Usage: setupGit \"commit message\" <repo-url>"
        echo "Example: setupGit \"initial commit\" https://github.com/user/repo"
        return 1
    fi

    local msg="$1"
    local repoUrl="$2"

    # Strip trailing .git if user included it
    repoUrl="${repoUrl%.git}"

    git init
    git add .
    git commit -m "$msg"
    git remote add origin "${repoUrl}.git"
    git branch -M main
    git push -u origin main
    git status
    echo ""
    echo "  Repo live at: ${repoUrl}"
    _git_hint
}
