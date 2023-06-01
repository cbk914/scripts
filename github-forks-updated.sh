#!/bin/bash

# Check if -d or --debug option is provided
debug=0
if [[ $1 == "-d" ]] || [[ $1 == "--debug" ]]; then
  debug=1
fi

# Ask for GitHub username and Personal Access Token
read -p "Enter your GitHub username: " username
read -sp "Enter your GitHub Personal Access Token: " token
echo

# Get the user's public email address from GitHub API
email=$(curl -s -H "Authorization: token $token" "https://api.github.com/users/$username" | jq -r '.email')

# Get the current rate limit status
rate_limit=$(curl -s -H "Authorization: token $token" https://api.github.com/rate_limit)

# Extract the limit, remaining requests, and reset time from the response
limit=$(echo $rate_limit | jq -r '.resources.core.limit')
remaining=$(echo $rate_limit | jq -r '.resources.core.remaining')
reset=$(echo $rate_limit | jq -r '.resources.core.reset')

# Check if the remaining requests are less than a certain threshold
if [ $remaining -lt 100 ]; then
  # Calculate the time until the rate limit resets
  let "wait_time = $reset - $(date +%s)"

  # Wait until the rate limit resets
  echo "Rate limit exceeded. Waiting for $wait_time seconds."
  sleep $wait_time
fi

# Check if necessary commands are available and install if not
for cmd in git curl jq; do
  if ! command -v $cmd &> /dev/null; then
    echo "$cmd is required but not installed. Attempting to install..."
    sudo apt-get install -y $cmd
  fi
done

# Function to create a workflow file in a repository
create_workflow() {
  repo=$1
  if [ -d "/tmp/$repo" ]; then
    rm -rf "/tmp/$repo"
  fi
  git clone "https://$token@github.com/$username/$repo.git" "/tmp/$repo" || return 1
  cd "/tmp/$repo" || return 1

  # Check if sync.yml exists and compare it to the new one
  if [[ -e .github/workflows/sync.yml ]]; then
    local_change=$(stat -c %Y .github/workflows/sync.yml)
    remote_change=$(date +%s)

    if [[ $local_change -ge $remote_change ]]; then
      echo "Workflow file is up to date for $repo. Skipping."
    else
      if [[ "$auto_update" == "false" ]]; then
        echo "Workflow file is out of date for $repo. Do you want to update it? (Y/N/All)"
        read response
        if [[ "$response" == "N" || "$response" == "n" ]]; then
          cd ..
          rm -rf /tmp/$repo
          return 0
        fi
        # If response is "All" or "all", then update the workflow file without asking for the remaining repos
        if [[ "$response" == "All" || "$response" == "all" ]]; then
          auto_update=true
        fi
      fi
    fi
  fi

  mkdir -p .github/workflows || return 1
  cat > .github/workflows/sync.yml << EOL
# Your GitHub Actions workflow
name: Sync Repositories

on: [push] 

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Source Repo
        uses: actions/checkout@v2
        with:
          repository: '$username/$repo'
          token: \${{ secrets.YOUR_GITHUB_TOKEN }}
          path: src_repo

      - name: Checkout Destination Repo
        uses: actions/checkout@v2
        with:
          repository: '$username/$repo'
          token: \${{ secrets.YOUR_GITHUB_TOKEN }}
          path: dest_repo

      - name: Sync Repositories
        run: |
          rsync -a --delete src_repo/ dest_repo/
          cd dest_repo
          git config user.name '$username'
          git config user.email '$email'
          git add .
          git commit -m "Sync with source repo"
          git push
EOL

  git add . || return 1
  git commit -m "Add sync workflow to $repo on $(date)" || true
  git push || return 1
  cd .. || return 1
  rm -rf "/tmp/$repo" || return 1
}

# Enable command tracing and exit on error if debug is set
if [ $debug -eq 1 ]; then
  set -x
else
  set -euo pipefail
fi

# Get a list of all repositories for the user
response=$(curl -s -H "Authorization: token $token" "https://api.github.com/users/$username/repos" || exit 1)

# Check if the API request was successful
if [[ -z "$response" ]]; then
  echo "Empty response from GitHub API. Please check your username and token."
  exit 1
elif echo "$response" | jq -e '.message' | grep -q "API rate limit exceeded"; then
  echo "API rate limit exceeded. Please try again later."
  exit 1
fi

# Get the list of repositories from the response that are forks
repos=$(echo "$response" | jq -r '.[] | select(.fork==true) | .name')

# Loop over all repositories and create the workflow file
for repo in $repos; do
  if ! create_workflow $repo; then
    echo "Failed to create workflow for $repo"
    exit 1
  fi
done