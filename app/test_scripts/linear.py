
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

import requests
import app.config.settings as settings

# 1. Configuration
API_KEY = settings.settings.LINEAR_API_KEY  # Ensure this is set in your .env file
TEAM_ID = settings.settings.LINEAR_TEAM_ID  # Get this from Linear settings or via Cmd+K "Copy model UUID"
URL = "https://api.linear.app/graphql"

# 2. Define the GraphQL Mutation
mutation = """
mutation IssueCreate($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue {
      id
      title
      url
    }
  }
}
"""

# 3. Setup Variables
variables = {
    "input": {
        "teamId": TEAM_ID,
        "title": "Test issue from Python",
        "description": "This issue was created for testing purposes.",
        "priority": 2  # High priority
    }
}

# 4. Execute the request
headers = {
    "Content-Type": "application/json",
    "Authorization": API_KEY
}

response = requests.post(URL, json={'query': mutation, 'variables': variables}, headers=headers)

# 5. Output results
if response.status_code == 200:
    data = response.json()
    if data.get('data', {}).get('issueCreate', {}).get('success'):
        issue = data['data']['issueCreate']['issue']
        print(f"✅ Success! Created issue: {issue['title']}")
        print(f"🔗 Link: {issue['url']}")
    else:
        print(f"❌ Error: {data.get('errors')}")
else:
    print(f"HTTP Error {response.status_code}: {response.text}")
