# Savor two-minute demo and practice guide

## Open and get ready

Open the built **Savor.app**, or in VS Code choose **Terminal → Run Task → Savor: Open phone demo**. Use the phone-shaped Mac window for your presentation. Keep the project folder where it is; the app uses its installed backend and local model.

The bottom buttons are **Home, Pantry, Recipes, Community, Impact**. The round letter at the top right opens sample accounts and preferences. Choose **Alex**, with **2 servings**, before this walkthrough. Alex, Jamie and Sam are demo identities that let one presenter show both sides of a request.

Practice changes are saved. There is no automatic reset between rehearsals. Check quantities before starting. The Sunday tomato pasta needs 200 g pasta, 300 g tomatoes, 20 ml olive oil, 5 g basil and 1 clove garlic. For the missing-ingredient story, Alex should have those amounts except garlic, and Jamie should have at least 1 clove. Use the pantry forms to prepare sample quantities if a previous rehearsal used them up.

## The timed demo


Before the timer, generate an idea for Alex with **2 servings**, your chosen diet and time. Keep pantry/preferences unchanged so it stays in **Your AI ideas**. Check the library while online. Fresh generation can take most of the demo slot; show a saved result honestly. Practice changes persist.

Aim for **1:40**, keeping **20 seconds for slower clicks**.

| Time | Show / do | Say aloud |
| --- | --- | --- |
| **0:00–0:10** | Home | “Savor helps you cook with what you have and borrow the small ingredients you're missing.” |
| **0:10–0:25** | Pantry; point to an amount and storage age | “Here's Alex's pantry. We track amounts and storage dates, and these records stay saved after closing the app.” |
| **0:25–0:45** | Recipes → Set preferences & generate; show the controls, then close the dialog | “I choose servings, diet and time. Saving these preferences asks AI to create a meal using this pantry.” |
| **0:45–1:10** | Your AI ideas → open the prepared result, show its preference label and coverage | “I generated this earlier on this computer. Python checked the quantities and preferences. The model suggests a meal; it cannot change our groceries.” |
| **1:10–1:30** | Close result → Recipe library → open a recipe | “We also search TheMealDB for real recipes with sources. Set preferences and adapt makes a new pantry-based version. Missing ingredients can be requested through our community flow.” |
| **1:30–1:40** | Keep the recipe visible | “That's Savor: turn what you already have into a meal, with a little help from your community.” |

If behind at 1:30, close from the current screen. Keep fresh generation, account switching and the complete request/pickup/cooking flow for Q&A. If the library is offline, use the saved AI result and explain the external search needs internet.


## Prepare the AI example before presenting

Open **Recipes → Set preferences & generate**, select servings, diet and time, then save. Wait for a valid result under **Your AI ideas**. If validation fails, retry or use a compatible older suggestion in **Saved AI** and identify it honestly. A matching pantry, preferences and inspiration can reuse a result for 15 minutes. Changing settings creates a different request; previous ideas do not count as current suggestions.

Check **Recipe library** while online before presenting. Use one ingredient or a meal name. **Set preferences & adapt** creates a separate AI suggestion; the original API recipe is not directly cookable in Savor because its serving and measure conversions are unverified.

## Optional walkthrough for questions afterward

To demonstrate the full exchange, switch to **Jamie** using the top-right account button. Open **Community → Requests → I can share** on Alex's garlic request. Jamie's clove is reserved. Show **Pickup chat**, switch back to **Alex**, and choose **Confirm pickup**. The clove transfers once, retaining its storage date.

Return to **Recipes → All ideas → Sunday tomato pasta**. It should show **100%**. Click **I cooked this** to deduct the recipe quantities, then open **Impact** to show recorded meals and exchanges. Those counts are saved actions, not measured dollar savings or food-waste reduction.

For a persistence example, edit a pantry quantity, save, and reopen the card. Choose an ingredient such as carrots that does not affect the pasta example. Do this outside the timed demo: any pantry change moves the current AI result into saved history.

## The technical explanation to remember

**Electron** is the Mac window. **React** draws the screens and updates them after an action. **FastAPI**, written in Python, checks inputs and applies the rules. **SQLite** saves the pantry, requests and messages. **Ollama** runs the downloaded **Qwen3 4B** model on this computer.

For example, when you save a grocery quantity, React sends a small JSON message to Python. Python checks the quantity and ownership, updates SQLite, and sends back the refreshed state. React then updates the card. The model is only asked for recipe suggestions; it cannot directly edit pantry records or complete exchanges.

TheMealDB supplies original recipe data through a free educational API. Only a search term or recipe ID is sent to it; preference and pantry quantities stay local. Photos load from the provider.

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
