# Capability Bootstrap

Use this reference before collecting evidence or operating the timesheet.

## Capability Matrix

| Need | Preferred capability | Fallback |
| --- | --- | --- |
| Search Outlook Inbox and Sent | Outlook Email connector | Outlook UI through Computer Use |
| Search delegated mailbox | Outlook Email shared-mailbox tools | Outlook UI through Computer Use |
| Search Teams messages and meetings | Teams connector | Teams UI through Computer Use |
| Operate AFED Timesheet in Chrome | Chrome browser control | Computer Use |
| Operate an in-app browser | Browser control | Computer Use |
| Generate review and audit | Bundled Python script | None |

Connector results are preferred because they preserve metadata and support
focused searches without screenshot-by-screenshot extraction.

## Detect Before Use

1. Search available and deferred tools for Outlook Email, Teams, browser
   control, Computer Use, and Plugin Management.
2. Reuse a connected capability when it is already callable.
3. Do not initialize browser control for email extraction when an Outlook
   connector can perform the search.
4. Do not assume Teams was searched when its connector is absent.

## Guided First-Run Setup

Lead the capability setup from the conversation. Do not send the user away with
a generic installation guide. Use Plugin Management's search and suggestion
flow, search each missing capability, and suggest all relevant exact plugin IDs
in one call when possible.

Known plugin references:

- `outlook-email@openai-curated-remote`
- `teams@openai-curated-remote`
- `chrome@openai-bundled`
- `computer-use@openai-bundled`

Plugin availability and IDs can change. Prefer the exact IDs returned by Plugin
Management over this baseline.

Installation or connection suggestions require a user click and may require
Microsoft or browser authentication. Tell the user only the next action that
only the user can complete: approve the suggestion, authenticate the Microsoft
account, install or enable the browser extension, or open the signed-in page.
After the user completes the action, recheck that the tools are callable and
continue automatically. Never report an installation as complete from a
suggestion result alone.

If a capability remains unavailable:

- state exactly which source was not searched;
- continue with independent sources when useful;
- mark the review's evidence coverage accordingly;
- do not infer missing activity from an unavailable mailbox or channel.

## Authentication and Data Handling

- Ask the user to sign in within the selected app or browser when required.
- Never request, read, store, or transmit passwords, OTPs, access tokens, or
  browser session data.
- Treat email and Teams content as confidential company information.
- Use it only to prepare the employee's requested timesheet artifacts.
- Do not upload mail content to an unrelated service.

## Browser Selection

Respect an explicit browser choice. When the user leaves Chrome open with the
timesheet signed in, use Chrome control and claim that exact tab. Keep the final
monthly review open as a deliverable after entry.

For UI actions:

- inspect current state before acting;
- prefer stable labels and exact project names;
- verify unique controls before clicking;
- verify each saved entry from the resulting page;
- stop and explain a blocker instead of brute-forcing repeated screenshots or
  clicks.
