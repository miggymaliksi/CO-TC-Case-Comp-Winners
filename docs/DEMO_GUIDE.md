# Savor two-minute demo and practice guide

## Open and get ready

Open the built **Savor.app**, or in VS Code choose **Terminal → Run Task → Savor: Open phone demo**. Use the phone-shaped Mac window for your presentation. Keep the project folder where it is; the app uses its installed backend and local model.

The bottom buttons are **Home, Pantry, Recipes, Community, Impact**. The round letter at the top right opens sample accounts and preferences. Choose **Alex**, with **2 servings**, before this walkthrough. Alex, Jamie and Sam are demo identities that let one presenter show both sides of a request.

Practice changes are saved. There is no automatic reset between rehearsals. For the bread request below, Alex needs 150 g tomatoes, 10 ml olive oil, 3 g basil and 0.5 lemon, with no bread; Sam needs at least 2 slices of bread. These conditions were checked in the current local demo. Use the pantry forms to prepare sample quantities if a previous rehearsal changed them. Do this before preparing the AI result.

## Demo requesting an ingredient

1. Use the top-right round account button to choose **Alex**. Keep **2 servings**, **All** diets and **60 minutes** maximum so the recipe is visible.
2. Open **Recipes → All ideas → Garden tomato toast**. It should show **80%** and **Bread · missing 2 slice**.
3. Click **Ask** beside Bread. The form fills in **bread**, **2** and **slice**, and links the request to this recipe.
4. Choose **Community · PBL** and **In 30 minutes**, then **Send request**. The app opens **Community → My requests** with the pending request. Send it during the presentation so the deadline is fresh.
5. Switch to **Sam** using the top-right account button. Open **Community → Requests** and click **I can share** on Alex's bread request. It becomes **Accepted**; two slices are reserved from Sam's available pantry.
6. For Q&A, switch back to **Alex → Community → My requests → Confirm pickup**. The bread transfers once into Alex's pantry, and the toast recipe becomes **100%** covered. Acceptance alone does not transfer it.

**Repeat a rehearsal:** stop before Confirm pickup and choose **Cancel** on the accepted request as Alex or Sam. The two reserved slices return to Sam, leaving Alex short of bread for another run. Start the next run as Alex. Cancellation preserves the request history; it does not reset the database. If you already confirmed pickup, prepare the sample pantry again before another rehearsal.

**Quick alternative:** **Community → Request an ingredient** opens the same form without a recipe. You can request **1 clove of garlic** from **PBL**, then switch to **Jamie** to accept it if Jamie has a clove available. A request made this way is not linked to a recipe.

## The timed demo


Before the timer, use **Alex**, **2 servings**, **All** diets and **60 minutes** maximum. Prepare one valid local AI result, then keep the pantry unchanged. Check that **Garden tomato toast** shows **80%**, with **2 slices of bread** missing, and that **Sam** has at least 2 slices. The AI result and the curated sharing example are labeled separately. Practice changes persist.

Aim for **1:45**, keeping **15 seconds for slower clicks**. The timed demo includes sending and accepting a real request in the local sample-account app.

| Time | Show / do | Say aloud |
| --- | --- | --- |
| **0:00–0:10** | Home | “Savor helps you cook with what you have and borrow the small ingredients you're missing.” |
| **0:10–0:35** | Recipes → Your AI ideas. Point to the preference summary and open the prepared result, then close it. | “I choose servings, diet and time. Local AI creates a meal idea from my pantry. This result was generated earlier on this computer.” |
| **0:35–0:55** | All ideas → Garden tomato toast. Point to 80% and the missing bread. | “For sharing, this curated sample is missing two slices of bread. Four of its five ingredient lines are already covered.” |
| **0:55–1:20** | Ask beside Bread → check 2 slice, Community · PBL and In 30 minutes → Send request. | “I request just the missing amount from my private community, with a deadline. It now appears in My requests.” |
| **1:20–1:40** | Top-right account button → Sam → Community → Requests → I can share on Alex's bread request. | “Switching sample accounts shows the other side. Sam accepts, and the app reserves two slices until pickup.” |
| **1:40–1:45** | Keep the accepted request visible. | “A little help from your community makes dinner possible.” |

If behind at 1:20, finish on Alex's sent request and explain that a neighbor can accept it. Keep fresh AI generation, pickup chat and confirmed pickup for Q&A. Do not present the curated sharing example as AI output.


## Prepare the AI example before presenting

Open **Recipes → Set preferences & generate**, choose servings, diet and time, then save. Wait for a valid result in **Your AI ideas**. Repeat the exact same settings during the demo to reuse the saved result within 15 minutes. Say it was generated earlier. Fresh generation can take a minute or two and may fail validation. The food API is removed; Qwen generates the idea directly from the pantry and preferences.

## Optional walkthrough for questions afterward

After Sam accepts the bread request, show **Pickup chat**, switch back to **Alex**, and choose **Community → My requests → Confirm pickup**. The two slices transfer once, retaining their storage date. These account switches show both sides in the same local database; separate computers do not share this demo database.

Return to **Recipes → All ideas → Garden tomato toast**. It should show **100%**. Click **I cooked this** to deduct the recipe quantities, then open **Impact** to show recorded meals and exchanges. Those counts are saved actions, not measured dollar savings or food-waste reduction.

For a persistence example, edit a pantry quantity, save, and reopen the card. Choose an ingredient such as carrots that does not affect the toast example. Do pantry edits outside the timed demo: changing stock moves the current AI result into saved history.

## The technical explanation to remember

**Electron** is the Mac window. **React** draws the screens and updates them after an action. **FastAPI**, written in Python, checks inputs and applies the rules. **SQLite** saves the pantry, requests and messages. **Ollama** runs the downloaded **Qwen3 4B** model on this computer.

For example, when you save a grocery quantity, React sends a small JSON message to Python. Python checks the quantity and ownership, updates SQLite, and sends back the refreshed state. React then updates the card. The model is only asked for recipe suggestions; it cannot directly edit pantry records or complete exchanges.

## Questions you may get

- **Is it an actual phone app?** This demo is a Mac desktop app with a phone-style interface. An iPhone/Android package is future work.
- **Did you train the AI?** We integrated a pretrained Qwen model. Our contribution is the pantry context, recipe checks and application workflow.
- **Why local AI?** It avoids paid API calls and keeps inference on the demo computer. The tradeoff is memory use, slower generation and variable recipe quality.
- **Does it predict when food expires?** No. It displays storage age. It does not judge food safety.
- **Can anyone sign in?** This is a local prototype with three sample accounts. Production sign-in is future work.
- **Does the receipt camera really scan?** The current receipt flow is an editable sample. Live image extraction is future work.
- **How do you stop double sharing?** Accepting reserves actual stock. Pickup and cancellation happen through controlled database transactions, with duplicate protection.
- **Where is the data?** In the local project's SQLite database. The app has no public backend in this demo.

The longer explanation and architecture diagram are in [TECHNICAL_RUNDOWN.md](TECHNICAL_RUNDOWN.md).
