# Savor two-minute demo and practice guide

## Open and get ready

Open the built **Savor.app**, or in VS Code choose **Terminal → Run Task → Savor: Open phone demo**. Use the phone-shaped Mac window for your presentation. Keep the project folder where it is; the app uses its installed backend and local model.

The bottom buttons are **Home, Pantry, Recipes, Community, Impact**. The round letter at the top right opens sample accounts and preferences. Choose **Alex**, with **2 servings**, before this walkthrough. Alex, Jamie and Sam are demo identities that let one presenter show both sides of a request.

Practice changes are saved. There is no automatic reset between rehearsals. Check quantities before starting. The Sunday tomato pasta needs 200 g pasta, 300 g tomatoes, 20 ml olive oil, 5 g basil and 1 clove garlic. For the missing-ingredient story, Alex should have those amounts except garlic, and Jamie should have at least 1 clove. Use the pantry forms to prepare sample quantities if a previous rehearsal used them up.

## The timed demo: 1 minute 40 seconds, with 20 seconds to spare

Start on **Home** as Alex. Have a previously generated recipe available under **Recipes → Local AI**. Rehearse with a timer. The times below include clicking and scrolling; keep moving when each segment ends.

| Time | Show | Say |
| --- | --- | --- |
| **0:00–0:10** | Home | Savor helps you cook with what you have and borrow the small ingredients you're missing. |
| **0:10–0:25** | **Pantry**. Point out one ingredient's quantity and storage age. | Here's Alex's pantry. We track amounts and storage dates, and the records stay saved after closing the app. |
| **0:25–0:55** | **Recipes → All ideas → Sunday tomato pasta**. Scroll to garlic, click **Ask**, and send a request for **1 clove** to **PBL**, with a **30-minute** deadline. | This pasta matches four of five ingredients. Garlic is missing, so it shows 80%. I can ask my community for just one clove. |
| **0:55–1:10** | Close the recipe if needed. Open **Community → Requests** and point to the new request. | The request is now in Alex's community. A neighbor can accept it, and confirmed pickup updates both pantries. |
| **1:10–1:30** | **Recipes → Local AI**. Open a saved generated recipe. | This recipe was generated earlier on this computer from the pantry. We use a local AI model without paid API calls, and our code checks the result before showing it. |
| **1:30–1:40** | Keep the recipe visible. | That's Savor: turn what you already have into a meal, with a little help from your community. |

Use the remaining **20 seconds** for slower clicks. If you reach **1:30** before the AI screen, deliver the closing sentence from the current screen and finish. Keep edits, account switching, pickup, cooking, and the technical explanation for questions afterward.

## Prepare the AI example before presenting

Before the timed demo, open **Recipes → Generate a dinner idea** and let it finish. A valid result is saved under **Local AI**. The first generation on an 8 GB Mac can take one or two minutes and can fail validation, so show the saved result during the presentation and say it was generated earlier.

Matching results for an unchanged pantry and preferences can be reused for 15 minutes. The app identifies a cached result as a saved idea. A curated recipe demonstrates matching, not AI generation. If no generated result is available, use the time to explain the sharing workflow instead of waiting for generation onstage.

## Optional walkthrough for questions afterward

To demonstrate the full exchange, switch to **Jamie** using the top-right account button. Open **Community → Requests → I can share** on Alex's garlic request. Jamie's clove is reserved. Show **Pickup chat**, switch back to **Alex**, and choose **Confirm pickup**. The clove transfers once, retaining its storage date.

Return to **Recipes → All ideas → Sunday tomato pasta**. It should show **100%**. Click **I cooked this** to deduct the recipe quantities, then open **Impact** to show recorded meals and exchanges. Those counts are saved actions, not measured dollar savings or food-waste reduction.

For a persistence example, edit a pantry quantity, save, and reopen the card. Choose an ingredient such as carrots that does not affect the pasta example. A carrot item was added during the phone-form check and is ordinary editable sample data.

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
