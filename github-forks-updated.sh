#!/bin/bash

# Ask for GitHub username and Personal Access Token
read -p "Enter your GitHub username: " username
read -sp "Enter your GitHub Personal Access Token: " token
echo

# Function to create a workflow file in a repository
create_workflow() {
  repo=$1
  git clone "https://$token@github.com/$username/$repo.git"
  cd $repo
  mkdir -p .github/workflows
  cat > .github/workflows/sync.yml << EOL
name: Sync Repositories

on:
  schedule:
    - cron: '0 0 * * *' # Runs every day at midnight

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Source Repo
        uses: actions/checkout@v2
        with:
          repository: 'src_user/src_repo'
          token: \${{ secrets.YOUR_GITHUB_TOKEN }}
          path: src_repo

      - name: Checkout Destination Repo
        uses: actions/checkout@v2
        with:
          repository: 'dest_user/dest_repo'
          token: \${{ secrets.YOUR_GITHUB_TOKEN }}
          path: dest_repo

      - name: Sync Repositories
        run: |
          rsync -a --delete src_repo/ dest_repo/
          cd dest_repo
          git config user.name 'Your Name'
          git config user.email 'your-email@example.com'
          git add .
          git commit -m "Sync with source repo"
          git push
EOL
  git add .
  git commit -m "Add sync workflow"
  git push
  cd ..
  rm -rf $repo
}

# Get a list of all repositories for the user
repos=$(curl -s -H "Authorization: token $token" "https://api.github.com/users/$username/repos" | grep -o 'git@[^"]*')

# Loop over all repositories and create the workflow file
for repo in $repos; do
  create_workflow $repo
done
