# Run and present Savor

## 1. Run it yourself from VS Code on this Mac

1. Close an already open Savor window so you can see VS Code launch it afresh.
2. In VS Code, choose **File → Open Folder**. In the folder picker, press **Command + Shift + G** and paste this folder path:

   ```text
   /Users/miguelmaliksi/Documents/Codex/2026-10-31/i-x20/outputs/Savor
   ```

3. Click **Open**. The file list should include `run.py`, `frontend`, `backend`, and `desktop`. The current app branch is **feat/savor-demo**; the app is awaiting review in [PR #1](https://github.com/miggymaliksi/CO-TC-Case-Comp-Winners/pull/1).
4. Choose **Terminal → Run Task → Savor: Open phone demo**.
5. Wait for Savor's separate phone-style Mac window to open. Keep the VS Code terminal open while you use it. On first setup, the launcher installs the required packages and builds the interface. This Mac's local AI runtime and model are already downloaded.
6. Close the Savor window to stop its backend and any model service it started. To launch again, repeat the task.

You can also choose **Terminal → New Terminal** and paste these two commands:

```sh
cd "/Users/miguelmaliksi/Documents/Codex/2026-10-31/i-x20/outputs/Savor"
python3 run.py --desktop
```

`cd` selects the project folder. `python3` runs Python. `run.py` is our setup/launch script. `--desktop` tells it to open the Mac app window. The task above runs the same command for you.

Your pantry and practice changes stay saved in the local `savor.db` file. Keep this project folder in place. No paid AI API account or key is needed for this version.

**If the terminal says `bquote>`:** press **Control + C**, then use the VS Code **Terminal → Run Task** menu. Paste only command text when using a terminal; omit Markdown markers such as three backticks and `sh`. “Run Task” is a menu item, not a command. If Savor is already open, another launch brings that window forward and prints an explanatory message.

## 2. The technical rundown

| Part | Explain it like this |
| --- | --- |
| **Electron** | The Mac app window. It starts our local Python service and displays the phone layout. |
| **React** | The screens, cards, buttons and forms. It sends actions to Python and updates what you see. |
| **Vite** | The tool that builds the React code into files the app can display. |
| **FastAPI / Python** | The backend: checks inputs and account access, calculates recipe matches, and controls requests and inventory changes. |
| **SQLite / SQLAlchemy** | SQLite saves records in a local database file. SQLAlchemy connects our Python data models to those records. |
| **Ollama / Qwen3 4B** | Ollama runs a downloaded, pretrained AI model on this computer. Qwen suggests recipes from pantry data. |

### Follow one button click

When you save a grocery quantity, React sends the values as **JSON**, a structured text format, to the Python **API**, the app's request interface. Python checks that the amount is valid and the sample account owns the item. It saves the change in SQLite and sends the refreshed state back. React updates the card. The record survives closing the app because it is in the database.

### How recipes and sharing work

Recipe coverage is calculated by code: **fully covered ingredient lines ÷ all ingredient lines**. Four of five gives 80%. A line only counts when the pantry has enough of a compatible quantity for the selected servings.

The sharing flow is **Pending → Accepted → Completed**. Acceptance reserves a real quantity from the provider. Confirmed pickup transfers it once to the requester. Cooking deducts the recipe quantities. Cancelling an accepted request before pickup returns reserved stock.

A **transaction** makes related database updates succeed together or roll back together. **Idempotency** means repeating the same action identifier cannot apply its inventory effect twice. These help prevent double sharing or duplicate deductions.

### Where AI is used

The user saves servings, diet and time with **Save preferences & generate**. Python sends compatible pantry ingredients and saved preferences to the local model, requests a recipe in a defined structure, then checks servings, quantities, ingredient names and coverage. **Your AI ideas** shows current-pantry/preference results, with the settings used. Compatible history remains under **Saved AI**. Only a valid result is saved. The model cannot directly alter inventory. Matching saved suggestions can be reused for 15 minutes when the pantry and preferences are unchanged.

We integrated a pretrained model; we did not train one. There are no per-request API fees, but generation uses memory and can take a minute or two. Validation is limited and does not guarantee recipe quality. Chat updates use periodic refreshes, rather than WebSockets: every four seconds for an open chat and eight seconds for general app state.

The food API and recipe library have been removed. New meal ideas come directly from local AI, with no external recipe lookup or paid AI API.

### Be clear about the prototype

This is a Mac app with a phone-style interface and three sample accounts. Each computer's checkout has its own database. Production sign-in, a shared hosted backend, iPhone/Android installation, real receipt-image extraction and external push notifications are future work. Storage age is not an expiration or food-safety prediction.

## 3. Your two-minute mock demo


Before the timer, generate one valid idea as Alex with **2 servings** and your chosen diet/time. Keep the pantry and settings unchanged. A matching request can reuse it for 15 minutes; say honestly that the result was generated earlier. Practice changes persist.

Aim for **1:40**, keeping **20 seconds for slower clicks**.

| Time | Show / do | Say aloud |
| --- | --- | --- |
| **0:00–0:10** | Home | “Savor helps you cook with what you have and borrow the small ingredients you're missing.” |
| **0:10–0:25** | Pantry; point to an amount and storage age | “Here's Alex's pantry. We track amounts and storage dates, and these records stay saved after closing the app.” |
| **0:25–0:45** | Recipes → Set preferences & generate. Show the prepared servings, diet and time, then Save preferences & generate. | “I choose servings, diet and time. AI uses these preferences and my pantry to create a meal idea.” |
| **0:45–1:10** | Your AI ideas → open the prepared result; point to its preferences, ingredients and method | “This idea was generated earlier on this computer. Repeating the same settings reuses it. Python checks the quantities and preferences before it appears.” |
| **1:10–1:30** | Show the result's pantry coverage, then Community | “The recipe shows how much my pantry covers. When something is missing, I can request a small amount from my community.” |
| **1:30–1:40** | Keep the current screen visible | “That's Savor: turn what you already have into a meal, with a little help from your community.” |

If behind at 1:30, close from the current screen. Keep fresh generation, account switching and the full pickup/cooking flow for Q&A. If generation is slow or rejected, show a saved AI result and identify it honestly; do not present a curated sample as AI output.


## Further reading

- [Detailed technical explanation and Q&A](TECHNICAL_RUNDOWN.md)
- [Demo preparation and optional full exchange](DEMO_GUIDE.md)
- [Team setup, important code files and GitHub workflow](TEAM_HANDOFF.md)
