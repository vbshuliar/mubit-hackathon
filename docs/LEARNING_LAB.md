# Mubit learning lab

A tiny support-message sorter for learning the Mubit request → task → kept examples → adapter workflow. Requires Node.js 22+; no dependencies to install.

## Start

```sh
npm start
```

Open http://localhost:3000. Without a key, demo mode uses local keyword rules. It does not contact Mubit or simulate training success.

## Connect Mubit

Copy `.env.example` to `.env`, set `MUBIT_API_KEY` to your project's Mubit key, and choose a supported `MUBIT_MODEL` from your console. Configure provider access in Mubit or use available starter credit. Restart the server. Keep your key in `.env`; it is ignored by Git and never sent to the browser.

The gateway URL in `server.mjs` is `https://api.mubit.ai/openai/v1/chat/completions`. Confirm the host matches your console's Connect page. If your workspace uses another host, update that URL before starting.

1. Classify one message, then inspect it under Requests in the Mubit console.
2. Send the 40 samples. These are paid provider calls in live mode. Stop pauses the batch after the current call; failed batches are not automatically retried.
3. Find the task under Tasks. Instructions and model stay fixed; each independent message gets its own session ID.
4. Watch kept examples. The documented default first-training threshold is 25 kept examples, not 25 requests. Training must be enabled and the task eligible.
5. Inspect Adapters → History. Compare a passing version with your provider in Try models using new messages.

The app does not deploy adapters, fetch training status, or submit corrected labels. Those interfaces were not established by the public docs reviewed on 23 October 2026. Ask the hackathon team about event-specific correction and serving APIs. Public Try models calls do not train adapters. Provider agreement is not a guarantee of correctness.

Browser history is temporary. Mubit records live requests by default. This local teaching server binds only to the local computer; it is not a production deployment.

## Files

- `server.mjs`: local server, fixed task instructions, real Mubit request, and explicitly labeled demo rules.
- `index.html`: interface and sequential sample sender.

## Sources

- https://docs.mubit.ai/guides/first-adapter
- https://docs.mubit.ai/guides/tasks-and-sessions
- https://docs.mubit.ai/reference/api
