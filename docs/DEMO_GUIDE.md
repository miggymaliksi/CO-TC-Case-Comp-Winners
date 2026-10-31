# Savor live demo and practice guide

## Open and get ready

Open the built **Savor.app**, or in VS Code choose **Terminal → Run Task → Savor: Open phone demo**. Use the phone-shaped Mac window for your presentation. Keep the project folder where it is; the app uses its installed backend and local model.

The bottom buttons are **Home, Pantry, Recipes, Community, Impact**. The round letter at the top right opens sample accounts and preferences. Choose **Alex**, with **2 servings**, before this walkthrough. Alex, Jamie and Sam are demo identities that let one presenter show both sides of a request.

Practice changes are saved. There is no automatic reset between rehearsals. Check quantities before starting. The Sunday tomato pasta needs 200 g pasta, 300 g tomatoes, 20 ml olive oil, 5 g basil and 1 clove garlic. For the missing-ingredient story, Alex should have those amounts except garlic, and Jamie should have at least 1 clove. Use the pantry forms to prepare sample quantities if a previous rehearsal used them up.

## A five-minute product walkthrough

| Do this | Explain what the audience is seeing | What the code is doing |
| --- | --- | --- |
| **Home → Pantry**. Open an ingredient card. | We keep track of food you already have, including its amount and storage date. | React shows records read from SQLite through the Python API. Storage age is calculated from the stored date. |
| Change a sample quantity and choose **Save changes**. Reopen the card. | These changes persist when the app closes. | Python validates the values, checks the sample account owns the item, then updates the database. |
| **Recipes → All ideas → Sunday tomato pasta**. Scroll inside the recipe. | Four of five ingredients are covered. Garlic is missing, so this recipe shows 80%. | Code checks compatible units and sufficient quantities for two servings. This percentage is calculated, not guessed by AI. |
| Click **Ask** next to garlic. Request **1 clove** from **PBL**, with a **30-minute** deadline. | Instead of buying a whole package for one ingredient, we can ask a private community. | The server saves a timed request linked to Alex and the community. |
| Close the recipe if needed. Use the top-right account button to choose **Jamie**. Open **Community → Requests**, then **I can share** on Alex's garlic request. | Now we are showing the neighbor's side of the exchange. | The backend checks Jamie's stock and reserves one real clove. It cannot be promised to another person at the same time. |
| Open **Pickup chat**. | The two people can arrange pickup privately. | The server only permits the requester and accepted provider to read this chat. |
| Switch back to **Alex**. Open **Community**, find the accepted request, and choose **Confirm pickup**. | Alex confirms receiving the ingredient. | The reserved clove transfers once to Alex's pantry, retaining its storage date. |
| Return to **Recipes → All ideas → Sunday tomato pasta**. Show **100%**, then **I cooked this**. | Once the missing ingredient arrives, the whole recipe is covered. | A database transaction deducts the exact quantities and saves a cooking record. Repeating the same confirmation cannot deduct them twice. |
| Open **Impact**. | We show recorded meals and confirmed exchanges. | These counts come from saved actions. They are not claimed dollar savings or measured food-waste reduction. |

When practicing a quantity edit, choose an amount that still covers the recipe. For example, changing carrots does not affect the tomato-pasta story. A 50 g carrot item was added during the phone-form persistence check; it is ordinary editable sample data.

## Show the local AI

Open **Recipes → Generate a dinner idea**. Leave the app open while it works. The computer reads the pantry and preferences, sends them to the local Qwen3 model through Ollama, then checks the returned recipe. A valid result appears under **Local AI**. No paid API account is used.

The first generation on an 8 GB Mac can take one or two minutes and can fail validation. Run it once before presenting. If the pantry and preferences stay unchanged, a matching result is reused for 15 minutes and the app says it loaded a saved idea. Explain that honestly. You can also open a previously generated recipe and say it was generated earlier on this Mac. A curated recipe demonstrates matching, not a fresh AI response.

If generation fails, show a curated recipe and explain that the app keeps working when the model is unavailable or returns an invalid result. The pantry has not been changed by the failed generation. Avoid multiple generation attempts at once.

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
