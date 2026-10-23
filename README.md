# Mubit Hackathon

A single repository containing Fixi, a repair coordination demo, and the initial Mubit learning lab.

## Repair coordination app

The main application lives in **[RepairFlow](RepairFlow/README.md)**. It coordinates repair cases, shows the agent's decisions, and accepts simulated tenant and contractor responses. Mubit integration collects examples for a focused contractor-report classifier; adapter readiness and evaluation results are documented separately from provider-model results.

- [Setup and local database initialization](RepairFlow/SETUP.md)
- [Demo walkthrough](RepairFlow/docs/DEMO_WALKTHROUGH.md)
- [Mubit integration](RepairFlow/docs/MUBIT_INTEGRATION.md)
- [Adapter recovery and validation evidence](RepairFlow/docs/ADAPTER_RECOVERY_PLAN.md)

## Repository layout

```text
RepairFlow/
  backend/          Python API, agent, policy checks and tests
  frontend-fixi/    Web interface and frontend tests
  docs/             Architecture, demo guides and validation evidence
  prompts/          Agent prompt resources
docs/               Learning-lab guide
index.html          Initial learning-lab interface
server.mjs          Initial learning-lab server
```

RepairFlow is an ordinary directory, not a submodule or a separate Git repository. Its path is retained so existing local app and database configuration continues to work.

## Initial learning lab

The original support-message classification experiment remains available with `npm start`. See [its guide](docs/LEARNING_LAB.md). The repair app is the main hackathon demonstration.

## Local-only files

Credentials, databases, dependencies, build output and runtime collection logs are ignored. Configure the environment and populate a local database using the setup guide after cloning. Never commit API keys. Real contractor contact is disabled in the demo; model calls can consume provider credits.
